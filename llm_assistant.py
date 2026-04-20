"""
llm_assistant.py
────────────────
Master Router for CampusCoin
Routes between BankerAgent and PuzzleAgent based on active sessions and intents.
"""
import os
import json
from openai import OpenAI
from typing import Any

from banker_agent import get_banker_tools, get_banker_system_prompt, handle_banker_action
from puzzle_agent import get_puzzle_tools, get_puzzle_system_prompt, handle_puzzle_turn
from shared_storage.state_db import get_active_puzzle_session

MODEL    = os.getenv("LM_STUDIO_MODEL", "qwen/qwen2.5-3b-instruct")
BASE_URL = os.getenv("LM_STUDIO_URL",   "http://127.0.0.1:1234/v1")
TIMEOUT  = int(os.getenv("LM_TIMEOUT", "30"))

_histories: dict[str, list[dict]] = {}
MAX_HISTORY = 10

def _get_client() -> OpenAI:
    return OpenAI(api_key="lm-studio", base_url=BASE_URL, timeout=TIMEOUT)

def clear_history(account: str) -> None:
    _histories.pop(account, None)

def get_history(account: str) -> list[dict]:
    return list(_histories.get(account, []))

def _trim_history(account: str) -> None:
    h = _histories.get(account, [])
    if len(h) > MAX_HISTORY:
        _histories[account] = h[-MAX_HISTORY:]

def build_assistant_reply(
    message: str,
    account: str,
    get_balance_fn=None,
    get_log_fn=None,
) -> dict[str, Any]:
    # ── Active Agent Lock ───────────────────────────────────────────────────
    # If the user is currently IN a puzzle session, bypass Banker/LLM and direct to PuzzleAgent
    session = get_active_puzzle_session(account)
    if session and session["state"] in ("offered", "awaiting_answer"):
        return handle_puzzle_turn(account, message)

    suggestions = [
        "幫我轉 15 CPC 給 guest",
        "找點樂子 (謎題挑戰)",
        "驗證帳本鏈",
        "查詢我的餘額",
    ]

    try:
        client = _get_client()
    except Exception as e:
        return _error_reply(f"無法連線到 LLM：{e}")

    history = _histories.setdefault(account, [])
    history.append({"role": "user", "content": message})

    # Combine tools and system promos
    tools = get_banker_tools() + get_puzzle_tools()
    sys_prompt = get_banker_system_prompt(account) + "\n" + get_puzzle_system_prompt(account)

    messages = [
        {"role": "system", "content": sys_prompt},
        *history,
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.2,
            max_tokens=300,
        )
    except Exception as exc:
        history.pop()
        return _error_reply(f"LLM 回應錯誤：{exc}")

    choice = response.choices[0]
    finish_reason = choice.finish_reason
    msg = choice.message

    # No tool called -> general chat
    if finish_reason != "tool_calls" or not msg.tool_calls:
        reply_text = msg.content or "好的，請問還有什麼我可以幫你的嗎？"
        history.append({"role": "assistant", "content": reply_text})
        _trim_history(account)
        return {
            "reply": reply_text,
            "intent": "general",
            "suggestions": suggestions,
            "action_preview": None,
        }

    tool_call = msg.tool_calls[0]
    tool_name = tool_call.function.name

    # Route to PuzzleAgent if user wants to play
    if tool_name == "start_puzzle":
        history.append({"role": "assistant", "content": "準備開始一場解謎遊戲！"})
        _trim_history(account)
        return handle_puzzle_turn(account, message)

    # Route to BankerAgent for financial actions
    if tool_name in ["transfer", "verify_chain", "check_balance", "check_log"]:
        reply_data = handle_banker_action(tool_call, account, get_balance_fn, get_log_fn)
        history.append({"role": "assistant", "content": reply_data["reply"]})
        _trim_history(account)
        return reply_data

    return {
        "reply": "已收到請求，但無法識別對應動作。",
        "intent": "general",
        "suggestions": suggestions,
        "action_preview": None,
    }

def _error_reply(msg: str) -> dict:
    return {
        "reply": msg,
        "intent": "error",
        "suggestions": [],
        "action_preview": None,
    }
