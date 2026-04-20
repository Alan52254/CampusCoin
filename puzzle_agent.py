import uuid
import random

from shared_storage.state_db import (
    get_active_puzzle_session, 
    create_puzzle_session, 
    update_puzzle_session,
    has_effect,
    clear_effect,
    mark_reward_granted,
    add_inventory_item,
    consume_inventory_item,
)
from puzzle_data import PUZZLES, get_puzzle_by_id
from puzzle_rag import evaluate_answer

BASE_REWARD = 1000
BASE_PENALTY = 10

def get_puzzle_system_prompt(account: str) -> str:
    return f"""You are the CampusCoin Puzzle Agent. Current account: {account}.
Your only goal is to ask the user if they want to play a game, and then transition them into the puzzle session.
If the user indicates they want to play, use the tool `start_puzzle`.
"""

def get_puzzle_tools() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": "start_puzzle",
                "description": "Start a new puzzle session.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }
    ]

def handle_puzzle_turn(account: str, message: str) -> dict:
    session = get_active_puzzle_session(account)
    
    # 1. State: idle -> offer game
    if not session:
        # We start a session.
        session_id = str(uuid.uuid4())
        
        # Optionally allow choosing from 3 if they have legend_die effect?
        # For simplicity, pick one at random.
        puzzle = random.choice(PUZZLES)
        
        create_puzzle_session(session_id, account, puzzle["id"], "offered")
        return {
            "reply": f"我找到一題：\n\n【{puzzle['category_label']}】{puzzle['question']}\n\n準備好要挑戰了嗎？",
            "intent": "puzzle_offer",
            "action_preview": None,
            "suggestions": ["好，我挑戰", "算了，跳過"],
        }
        
    state = session["state"]
    puzzle_id = session["puzzle_id"]
    puzzle_info = get_puzzle_by_id(puzzle_id)
    session_id = session["session_id"]
    
    # 2. State: offered -> awaiting_answer
    if state == "offered":
        lowered = message.lower()
        if any(w in lowered for w in ["不", "跳過", "算了", "no", "skip"]):
            update_puzzle_session(session_id, state="closed")
            return {"reply": "好吧，那我們下次再玩！", "intent": "general", "action_preview": None, "suggestions": []}
            
        update_puzzle_session(session_id, state="awaiting_answer")
        return {
            "reply": "請告訴我你的答案！如果需要提示可以跟我說「提示」。",
            "intent": "puzzle_gaming",
            "action_preview": {"type": "puzzle_gaming", "puzzle_id": puzzle_id},
            "suggestions": ["提示", "投降"],
        }
        
    # 3. State: awaiting_answer -> evaluate or hint
    if state == "awaiting_answer":
        lowered = message.lower()
        
        # Check free skip
        if has_effect(account, "free_skip") and any(w in lowered for w in ["skip", "跳過"]):
            clear_effect(account, "free_skip")
            update_puzzle_session(session_id, state="closed")
            return {"reply": "已使用傳送捲軸跳過題目！", "intent": "general", "action_preview": None, "suggestions": []}
            
        # Check hint request
        if "提示" in message or "hint" in lowered:
            if has_effect(account, "super_hint"):
                # Ideally, if it's a multi-use buff, reduce limit. We will just provide the hint.
                update_puzzle_session(session_id, hint_count=session.get('hint_count', 0) + 1)
                return {
                    "reply": f"提示：{puzzle_info.get('hint', '沒有更多提示了！')}",
                    "intent": "puzzle_gaming",
                    "action_preview": {"type": "puzzle_gaming"},
                    "suggestions": [],
                }
            return {
                "reply": "你目前沒有超級提示效果。可至商店購買提示藥水。",
                "intent": "puzzle_gaming",
                "action_preview": {"type": "puzzle_gaming"},
                "suggestions": ["投降"],
            }
            
        # Check surrender
        if any(w in lowered for w in ["這太難了", "放棄", "投降", "surrender", "退"]):
            update_puzzle_session(session_id, state="closed")
            return {"reply": "謎題已結束。", "intent": "general", "action_preview": None, "suggestions": []}
            
        # Evaluate user answer!
        update_puzzle_session(session_id, state="judging")
        res = evaluate_answer(puzzle_id, message)
        
        correct = res["correct"]
        feedback = res["feedback"]
        
        if correct:
            update_puzzle_session(session_id, state="rewarded", reward_granted=1)
            
            # Form an idempotency key
            reward_key = f"puzzle:{account}:{session_id}"
            actual_reward = BASE_REWARD
            
            # Apply Shop double effects... handled downstream or here?
            # It's safer to calculate actual_reward here and pass to action_preview.
            # App handles the actual ledger.
            if has_effect(account, "double_reward"):
                actual_reward = 2000
                clear_effect(account, "double_reward")
            
            return {
                "reply": f"{feedback}\n準備發送獎勵！",
                "intent": "puzzle_reward",
                "action_preview": {
                    "type": "puzzle_reward",
                    "reward_key": reward_key,
                    "session_id": session_id,
                    "puzzle_id": puzzle_id,
                    "amount": actual_reward,
                    "feedback": feedback
                },
                "suggestions": [],
            }
        else:
            # Handle failure cases
            if has_effect(account, "shield"):
                clear_effect(account, "shield")
                update_puzzle_session(session_id, state="awaiting_answer")
                return {"reply": f"{feedback}\n護盾發動！未扣款，請再試一次。", "intent": "puzzle_gaming", "action_preview": None, "suggestions": []}
                
            if has_effect(account, "undo_pending"):
                clear_effect(account, "undo_pending")
                update_puzzle_session(session_id, state="awaiting_answer")
                return {"reply": f"{feedback}\n時光寶石發動！撤銷記錄，請再試一次。", "intent": "puzzle_gaming", "action_preview": None, "suggestions": []}
                
            update_puzzle_session(session_id, state="failed")
            
            reward_key = f"puzzle_fail:{account}:{session_id}"
            actual_penalty = BASE_PENALTY
            
            if has_effect(account, "cursed_penalty"):
                actual_penalty = 50
                clear_effect(account, "cursed_penalty")
                
            return {
                "reply": f"{feedback}\n答錯了！準備扣款...",
                "intent": "puzzle_failed",
                "action_preview": {
                    "type": "puzzle_failed",
                    "reward_key": reward_key,
                    "session_id": session_id,
                    "puzzle_id": puzzle_id,
                    "amount": actual_penalty,
                    "feedback": feedback,
                    "official_answer": res.get("official_answer", "")
                },
                "suggestions": [],
            }

    return {"reply": "發生未知錯誤，系統將強制結束謎題狀態。", "intent": "error", "action_preview": None, "suggestions": []}
