"""
llm_assistant.py
────────────────
CampusCoin LLM assistant — 支援所有相容 OpenAI API 的本地模型
（LM Studio、Ollama 等）

設定方式（.env 或環境變數）：
  LM_STUDIO_MODEL   模型名稱（預設：qwen2.5-3b-instruct）
  LM_STUDIO_URL     伺服器位址（預設：http://localhost:1234/v1）
"""

import json
import os
from typing import Any

from openai import OpenAI

# ── 設定 ──────────────────────────────────────────────────────────────────────
MODEL    = os.getenv("LM_STUDIO_MODEL", "qwen/qwen2.5-3b-instruct")
BASE_URL = os.getenv("LM_STUDIO_URL",   "http://127.0.0.1:1234/v1")
TIMEOUT  = int(os.getenv("LM_TIMEOUT", "30"))   # 秒，超時直接 fallback

# ── 對話歷史（每個帳戶獨立儲存） ─────────────────────────────────────────────
_histories: dict[str, list[dict]] = {}
MAX_HISTORY = 10   # 保留最近 5 輪對話（context 越短越快）

# ── LM Studio 客戶端 ──────────────────────────────────────────────────────────
def _get_client() -> OpenAI:
    return OpenAI(api_key="lm-studio", base_url=BASE_URL, timeout=TIMEOUT)

# ── 工具定義 ──────────────────────────────────────────────────────────────────
TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "transfer",
            "description": (
                "在 CampusCoin 帳本中將 CPC 從一個帳戶轉到另一個帳戶。"
                "使用者想轉帳時呼叫此工具。執行前需使用者確認。"
            ),
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
            "description": (
                "驗證整條帳本鏈的 SHA256 完整性。"
                "驗證通過後，帳戶可從 angel 獲得 10 CPC 獎勵。"
                "使用者想審計或驗證區塊鏈時呼叫。執行前需使用者確認。"
            ),
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

# ── System prompt（包含帳戶資訊，不需要每則訊息重複） ─────────────────────────
def _system_prompt(account: str) -> str:
    return f"""You are CampusCoin assistant. Current account: {account}

Tools available:
- transfer(sender, receiver, amount): send CPC between accounts
- verify_chain(account): audit ledger integrity, earn 10 CPC reward
- check_balance(account): query CPC balance
- check_log(account, limit): query recent transactions

Intent recognition (call the matching tool):
- Transfer intent: "transfer", "send", "轉帳", "匯款", "我要轉", "幫我轉", "send money", "I want to transfer"
  → If receiver or amount is missing, ask the user for the missing info.
- Verify intent: "verify", "audit", "驗證", "帳本", "check chain"
- Balance intent: "balance", "how much", "餘額", "多少錢", "查餘額"
- History intent: "history", "transactions", "交易", "記錄", "log"

Rules:
1. When intent matches a tool, ALWAYS call the tool — never just reply with text.
2. If transfer parameters are incomplete, ask for the missing ones (e.g. "Who do you want to send to, and how much?").
3. Reply in the same language the user used (Chinese or English).
4. Keep replies concise."""

# ── 對話歷史操作 ──────────────────────────────────────────────────────────────
def clear_history(account: str) -> None:
    """清除指定帳戶的對話歷史。"""
    _histories.pop(account, None)

def get_history(account: str) -> list[dict]:
    return list(_histories.get(account, []))

def _trim_history(account: str) -> None:
    h = _histories.get(account, [])
    if len(h) > MAX_HISTORY:
        _histories[account] = h[-MAX_HISTORY:]

# ── 公開介面 ──────────────────────────────────────────────────────────────────
def build_assistant_reply(
    message: str,
    account: str,
    get_balance_fn=None,
    get_log_fn=None,
) -> dict[str, Any]:
    suggestions = [
        "幫我轉 15 CPC 給 guest",
        "查詢我的餘額",
        "驗證帳本鏈並領取獎勵",
        "顯示最近的交易紀錄",
    ]

    try:
        client = _get_client()
    except Exception as e:
        return _error_reply(f"無法連線到 LM Studio：{e}\n請確認 LM Studio 已啟動並載入模型。")

    # ── 取得（或初始化）對話歷史 ─────────────────────────────────────────────
    history = _histories.setdefault(account, [])
    history.append({"role": "user", "content": message})

    messages = [
        {"role": "system", "content": _system_prompt(account)},
        *history,
    ]

    # ── 第一次 API 呼叫：讓模型決定是否使用工具 ──────────────────────────────
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.2,
            max_tokens=300,
        )
    except Exception as exc:
        history.pop()   # 失敗時撤銷剛加入的訊息
        return _error_reply(
            f"LM Studio 回應錯誤：{exc}\n\n"
            "請確認：\n"
            "1. LM Studio 的 Local Server 已啟動\n"
            f"2. 目前使用的模型名稱是「{MODEL}」\n"
            "   → 若不符請設定環境變數 LM_STUDIO_MODEL=<正確名稱>\n"
            "   → 或執行 curl http://localhost:1234/v1/models 查詢\n"
            "3. http://localhost:1234 可以連線"
        )

    choice        = response.choices[0]
    finish_reason = choice.finish_reason
    msg           = choice.message

    # ── 沒有呼叫工具 → 純文字對話（也支援多輪） ─────────────────────────────
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

    try:
        tool_input: dict = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError:
        tool_input = {}

    # ── 讀取操作：直接格式化結果，不再第二次呼叫模型（省去一半延遲） ──────────
    if tool_name == "check_balance":
        target  = tool_input.get("account", account)
        balance = get_balance_fn(target) if get_balance_fn else "?"
        reply_text = f"帳戶 {target} 目前餘額為 {balance} CPC。"
        history.append({"role": "assistant", "content": reply_text})
        _trim_history(account)
        return {
            "reply": reply_text,
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
        history.append({"role": "assistant", "content": reply_text})
        _trim_history(account)
        return {
            "reply": reply_text,
            "intent": "history",
            "suggestions": suggestions,
            "action_preview": {"type": "history_lookup", "account": target, "transactions": rows},
        }

    # ── 寫入操作：直接格式化，不再第二次呼叫模型 ────────────────────────────
    if tool_name == "transfer":
        sender   = tool_input.get("sender", account)
        receiver = tool_input.get("receiver", "")
        amount   = tool_input.get("amount", 0)
        reply_text = f"準備將 {amount} CPC 從 {sender} 轉給 {receiver}，請確認後執行。"
        history.append({"role": "assistant", "content": reply_text})
        _trim_history(account)
        return {
            "reply": reply_text,
            "intent": "transfer",
            "suggestions": suggestions,
            "action_preview": {"type": "transfer", "sender": sender, "receiver": receiver, "amount": amount},
        }

    if tool_name == "verify_chain":
        target = tool_input.get("account", account)
        reply_text = f"準備驗證帳本鏈，通過後 {target} 將從 angel 獲得 10 CPC 獎勵，請確認後執行。"
        history.append({"role": "assistant", "content": reply_text})
        _trim_history(account)
        return {
            "reply": reply_text,
            "intent": "verify",
            "suggestions": suggestions,
            "action_preview": {"type": "verify", "account": target},
        }

    return {
        "reply": "已收到請求，但無法識別對應動作，請再說清楚一點。",
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
