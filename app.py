import re
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request


BASE_DIR = Path(__file__).resolve().parent
SHARED_STORAGE_DIR = BASE_DIR / "shared_storage"
sys.path.insert(0, str(SHARED_STORAGE_DIR))

from ledger_core import (  # noqa: E402
    append_transaction,
    get_account_log,
    get_balance,
    iter_block_paths,
    last_block_index,
    ledger_lock,
    parse_metadata,
    verify_chain,
)

# ── LLM assistant (falls back gracefully if import fails) ────────────────────
try:
    from llm_assistant import build_assistant_reply as _llm_reply, clear_history as _clear_history
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


app = Flask(__name__)


# ── Helper: serialise transactions ────────────────────────────────────────────

def serialize_transactions(account: str, limit: int = 8):
    rows = get_account_log(account)
    rows.reverse()
    items = []
    for block_index, sender, receiver, amount in rows[:limit]:
        direction = "in" if receiver == account else "out"
        counterparty = sender if direction == "in" else receiver
        items.append(
            {
                "block": block_index,
                "sender": sender,
                "receiver": receiver,
                "amount": amount,
                "direction": direction,
                "counterparty": counterparty,
            }
        )
    return items


# ── Helper: build full dashboard payload ──────────────────────────────────────

def build_dashboard_payload(account: str):
    blocks = list(iter_block_paths())
    latest_index = blocks[-1][0] if blocks else 0
    latest_pointer = "None"
    if blocks:
        _, latest_path = blocks[-1]
        _, latest_pointer = parse_metadata(latest_path)

    rows = get_account_log(account)
    income  = sum(amount for _, sender, receiver, amount in rows if receiver == account)
    expense = sum(amount for _, sender, receiver, amount in rows if sender == account)

    return {
        "account": account,
        "balance": get_balance(account),
        "transaction_count": len(rows),
        "block_count": latest_index,
        "latest_block": latest_index,
        "latest_pointer": latest_pointer,
        "income": income,
        "expense": expense,
        "chain_ok": len(verify_chain()) == 0,
        "recent_transactions": serialize_transactions(account),
    }


# ── Rule-based fallback (kept for reference / offline use) ───────────────────

def _rule_based_reply(message: str, account: str) -> dict:
    """Original rule-based parser, used when LLM is unavailable."""
    normalized = " ".join(message.strip().split())
    lowered = normalized.lower()
    suggestions = [
        "幫我轉 15 CPC 給 guest",
        "查詢我的餘額",
        "驗證帳本鏈並領取獎勵",
        "顯示最近的交易紀錄",
    ]

    if not normalized:
        return {
            "reply": "請輸入你想做的事，例如轉帳、查餘額或驗證帳本。",
            "intent": "empty",
            "suggestions": suggestions,
            "action_preview": None,
        }

    transfer_match = re.search(
        r"(?:transfer|send|轉)\s+(\d+)\s*(?:cpc)?\s+(?:from\s+([A-Za-z0-9_]+)\s+)?(?:to|into|給)\s+([A-Za-z0-9_]+)",
        lowered,
    )
    if transfer_match:
        amount   = int(transfer_match.group(1))
        sender   = transfer_match.group(2) or account
        receiver = transfer_match.group(3)
        return {
            "reply": f"偵測到轉帳請求：{sender} → {receiver}，金額 {amount} CPC。請確認後執行。",
            "intent": "transfer",
            "suggestions": suggestions,
            "action_preview": {"type": "transfer", "sender": sender, "receiver": receiver, "amount": amount},
        }

    if any(k in lowered for k in ("verify", "chain", "audit", "驗證", "帳本")):
        return {
            "reply": "偵測到帳本驗證請求。驗證通過後將從 angel 取得 10 CPC 獎勵。",
            "intent": "verify",
            "suggestions": suggestions,
            "action_preview": {"type": "verify", "account": account},
        }

    if any(k in lowered for k in ("balance", "how much", "餘額", "多少")):
        balance = get_balance(account)
        return {
            "reply": f"{account} 目前餘額為 {balance} CPC。",
            "intent": "balance",
            "suggestions": suggestions,
            "action_preview": {"type": "balance_lookup", "account": account, "balance": balance},
        }

    if any(k in lowered for k in ("transaction", "history", "recent", "交易", "記錄")):
        return {
            "reply": "已找到最近的交易記錄，顯示在下方。",
            "intent": "history",
            "suggestions": suggestions,
            "action_preview": {"type": "history_lookup", "account": account},
        }

    return {
        "reply": "無法識別指令。你可以試試：「轉 10 CPC 給 guest」或「驗證帳本」。",
        "intent": "general",
        "suggestions": suggestions,
        "action_preview": None,
    }


# ── Unified assistant entry point ─────────────────────────────────────────────

def build_assistant_reply(message: str, account: str) -> dict:
    """
    Try the LLM assistant first; fall back to rule-based if unavailable.
    Injects ledger helpers so llm_assistant.py stays decoupled from Flask.
    """
    if LLM_AVAILABLE:
        def _get_log(acc, limit=10):
            return serialize_transactions(acc, limit=limit)

        return _llm_reply(
            message=message,
            account=account,
            get_balance_fn=get_balance,
            get_log_fn=_get_log,
        )

    return _rule_based_reply(message, account)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    account = request.args.get("account", "b1128015")
    return render_template("index.html", initial_account=account, overview=build_dashboard_payload(account))


@app.get("/api/overview")
def api_overview():
    account = request.args.get("account", "b1128015")
    return jsonify(build_dashboard_payload(account))


@app.get("/api/log")
def api_log():
    account = request.args.get("account", "b1128015")
    limit   = int(request.args.get("limit", "20"))
    rows    = serialize_transactions(account, limit=limit)
    return jsonify({"account": account, "transactions": rows})


@app.post("/api/transfer")
def api_transfer():
    payload    = request.get_json(silent=True) or {}
    sender     = (payload.get("sender")   or "").strip()
    receiver   = (payload.get("receiver") or "").strip()
    amount_raw = payload.get("amount")

    if not sender or not receiver:
        return jsonify({"ok": False, "error": "Sender and receiver are required."}), 400

    try:
        amount = int(amount_raw)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Amount must be an integer."}), 400

    if sender != "angel" and get_balance(sender) < amount:
        return jsonify({"ok": False, "error": "Insufficient balance for this transfer."}), 400

    with ledger_lock():
        previous_last_block = last_block_index()
        block_index, _      = append_transaction(sender, receiver, amount)
        sealed_block        = block_index > previous_last_block

    return jsonify(
        {
            "ok": True,
            "message": f"{sender} sent {amount} CPC to {receiver}.",
            "block_index": block_index,
            "sealed_block": sealed_block,
            "overview": build_dashboard_payload(sender),
        }
    )


@app.post("/api/verify")
def api_verify():
    payload = request.get_json(silent=True) or {}
    account = (payload.get("account") or "b1128015").strip()

    with ledger_lock():
        issues = verify_chain()
        if issues:
            return jsonify({"ok": False, "issues": issues, "overview": build_dashboard_payload(account)}), 400

        block_index, _ = append_transaction("angel", account, 10)

    return jsonify(
        {
            "ok": True,
            "message": f"Chain verified. angel rewarded {account} with 10 CPC.",
            "reward_block": block_index,
            "overview": build_dashboard_payload(account),
        }
    )


@app.post("/api/assistant")
def api_assistant():
    payload = request.get_json(silent=True) or {}
    account = (payload.get("account") or "b1128015").strip()
    message = payload.get("message") or ""
    return jsonify(build_assistant_reply(message, account))


@app.post("/api/assistant/clear")
def api_assistant_clear():
    payload = request.get_json(silent=True) or {}
    account = (payload.get("account") or "b1128015").strip()
    if LLM_AVAILABLE:
        _clear_history(account)
    return jsonify({"ok": True})


# ── Health check (useful inside Docker) ───────────────────────────────────────

@app.get("/api/health")
def api_health():
    return jsonify({"ok": True, "llm_enabled": LLM_AVAILABLE})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
