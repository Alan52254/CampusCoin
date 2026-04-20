import json
from typing import Callable, Optional

def get_banker_tools() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": "transfer",
                "description": "在 CampusCoin 帳本中將 CPC 從一個帳戶轉到另一個帳戶。使用者想轉帳時呼叫此工具。執行前需使用者確認。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sender":   {"type": "string",  "description": "匯款帳戶 ID"},
                        "receiver": {"type": "string",  "description": "收款帳戶 ID"},
                        "amount":   {"type": "integer", "description": "轉帳金額（正整數 CPC）"},
                    },
                    "required": ["sender", "receiver", "amount"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "verify_chain",
                "description": "驗證整條帳本鏈的完整性。驗證通過後，帳戶可獲得 10 CPC 獎勵。使用者想審計或驗證區塊鏈時呼叫。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account": {"type": "string", "description": "驗證通過後接收獎勵的帳戶 ID"},
                    },
                    "required": ["account"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "check_balance",
                "description": "查詢帳戶目前的 CPC 餘額。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account": {"type": "string", "description": "要查詢的帳戶 ID"},
                    },
                    "required": ["account"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "check_log",
                "description": "查詢帳戶的最近交易紀錄。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account": {"type": "string", "description": "要查詢的帳戶 ID"},
                        "limit":   {"type": "integer", "description": "最多回傳幾筆（預設 10）"},
                    },
                    "required": ["account"],
                },
            },
        },
    ]

def get_banker_system_prompt(account: str) -> str:
    return f"""You are the CampusCoin Banker Agent. Current account: {account}.
Strictly adhere to financial tasks.

Tools available:
- transfer(sender, receiver, amount)
- verify_chain(account)
- check_balance(account)
- check_log(account, limit)

Rules:
1. When intent matches a tool, ALWAYS call the tool — never just reply with text.
2. If transfer parameters are incomplete, ask for the missing ones.
3. Reply in the same language the user used (Chinese or English).
4. Keep replies concise.
"""

def handle_banker_action(tool_call, account: str, get_balance_fn: Optional[Callable], get_log_fn: Optional[Callable]) -> dict:
    tool_name = tool_call.function.name
    try:
        tool_input = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError:
        tool_input = {}

    suggestions = [
        "幫我轉 15 CPC 給 guest",
        "查詢我的餘額",
        "驗證帳本鏈",
        "顯示最近的交易紀錄",
    ]

    if tool_name == "check_balance":
        target = tool_input.get("account", account)
        balance = get_balance_fn(target) if get_balance_fn else "?"
        return {
            "reply": f"帳戶 {target} 目前餘額為 {balance} CPC。",
            "intent": "balance",
            "suggestions": suggestions,
            "action_preview": {"type": "balance_lookup", "account": target, "balance": balance},
        }

    if tool_name == "check_log":
        target = tool_input.get("account", account)
        limit  = tool_input.get("limit", 10)
        rows   = get_log_fn(target, limit) if get_log_fn else []
        if rows:
            lines = [f"• Block #{r['block']}　{r['sender']} → {r['receiver']}　{'+' if r['direction']=='in' else '-'}{r['amount']} CPC" for r in rows]
            reply_text = f"{target} 最近 {len(rows)} 筆交易：\n" + "\n".join(lines)
        else:
            reply_text = f"帳戶 {target} 目前沒有交易紀錄。"
        return {
            "reply": reply_text,
            "intent": "history",
            "suggestions": suggestions,
            "action_preview": {"type": "history_lookup", "account": target, "transactions": rows},
        }

    if tool_name == "transfer":
        sender = tool_input.get("sender", account)
        receiver = tool_input.get("receiver", "")
        amount = tool_input.get("amount", 0)
        return {
            "reply": f"準備將 {amount} CPC 從 {sender} 轉給 {receiver}，請確認後執行。",
            "intent": "transfer",
            "suggestions": suggestions,
            "action_preview": {"type": "transfer", "sender": sender, "receiver": receiver, "amount": amount},
        }

    if tool_name == "verify_chain":
        target = tool_input.get("account", account)
        return {
            "reply": f"準備驗證帳本鏈，通過後 {target} 將從 angel 獲得 10 CPC 獎勵，請確認後執行。",
            "intent": "verify",
            "suggestions": suggestions,
            "action_preview": {"type": "verify", "account": target},
        }

    return {
        "reply": "已收到請求，但我不知道該如何處理。",
        "intent": "general",
        "suggestions": suggestions,
        "action_preview": None,
    }
