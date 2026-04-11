"""
llm_assistant.py
────────────────
CampusCoin LLM assistant — 支援所有相容 OpenAI API 的本地模型
（LM Studio、Ollama 等）

設定方式（.env 或環境變數）：
  LM_STUDIO_MODEL   模型名稱，需與 LM Studio 介面上顯示的完全一致
                    （預設：qwen2.5-7b-instruct）
  LM_STUDIO_URL     伺服器位址（預設：http://localhost:1234/v1）

查詢目前載入模型名稱的方法：
  啟動 LM Studio → Local Server → 上方顯示的 model identifier 複製過來貼到環境變數
  或執行：curl http://localhost:1234/v1/models
"""

import json
import os
from typing import Any

from openai import OpenAI

# ── 設定 ──────────────────────────────────────────────────────────────────────
MODEL    = os.getenv("LM_STUDIO_MODEL", "qwen2.5-7b-instruct")
BASE_URL = os.getenv("LM_STUDIO_URL",   "http://localhost:1234/v1")

# ── 對話歷史（每個帳戶獨立儲存） ─────────────────────────────────────────────
_histories: dict[str, list[dict]] = {}
MAX_HISTORY = 20   # 保留最近 10 輪對話（20 則訊息）

# ── LM Studio 客戶端 ──────────────────────────────────────────────────────────
def _get_client() -> OpenAI:
    return OpenAI(api_key="lm-studio", base_url=BASE_URL)

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
    return f"""你是 CampusCoin 助手，一個校園區塊鏈帳本系統的 AI 代理人。
目前登入帳戶：{account}

你可以呼叫以下工具幫助使用者：
- transfer      → 帳戶間轉帳 CPC
- verify_chain  → 驗證帳本完整性並領取 10 CPC 獎勵
- check_balance → 查詢帳戶餘額
- check_log     → 查詢最近交易紀錄

規則：
1. 使用者意圖符合上述工具時，一律呼叫對應工具。
2. 轉帳與驗證屬於「寫入操作」，需回傳 action_preview 讓前端請使用者確認，不要自行執行。
3. 餘額查詢與交易紀錄屬於「讀取操作」，可直接描述結果。
4. 意圖不明時，請簡短反問使用者。
5. 使用使用者相同的語言（中文或英文）回答。
6. 回答簡潔友善，記住之前的對話內容。
"""

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
            max_tokens=400,
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


# ── 私有工具函式 ──────────────────────────────────────────────────────────────

def _narrate(client, original_messages, assistant_msg, tool_call, tool_result: dict) -> str:
    """把工具結果送回模型，讓它組成自然語言回答。"""
    follow_up_messages = original_messages + [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id":       tool_call.id,
                    "type":     "function",
                    "function": {
                        "name":      tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
            ],
        },
        {
            "role":         "tool",
            "tool_call_id": tool_call.id,
            "content":      json.dumps(tool_result, ensure_ascii=False),
        },
    ]

    try:
        follow_up = client.chat.completions.create(
            model=MODEL,
            messages=follow_up_messages,
            tools=TOOLS,
            tool_choice="none",
            temperature=0.2,
            max_tokens=300,
        )
        return follow_up.choices[0].message.content or ""
    except Exception:
        return f"已解析你的請求：{tool_call.function.name}（{tool_result}）"


def _error_reply(msg: str) -> dict:
    return {
        "reply": msg,
        "intent": "error",
        "suggestions": [],
        "action_preview": None,
    }
