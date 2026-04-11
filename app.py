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


app = Flask(__name__)


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


def build_dashboard_payload(account: str):
    blocks = list(iter_block_paths())
    latest_index = blocks[-1][0] if blocks else 0
    latest_pointer = "None"
    if blocks:
        _, latest_path = blocks[-1]
        _, latest_pointer = parse_metadata(latest_path)

    rows = get_account_log(account)
    income = sum(amount for _, sender, receiver, amount in rows if receiver == account)
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


def build_assistant_reply(message: str, account: str):
    normalized = " ".join(message.strip().split())
    lowered = normalized.lower()
    suggestions = [
        "Transfer 15 CPC from b1128015 to guest",
        "Verify the chain and explain the reward",
        "Show my latest transactions",
    ]

    if not normalized:
        return {
            "reply": "Tell me what you want to do on-chain. I can preview transfers, explain balances, or prepare a chain verification flow.",
            "intent": "empty",
            "suggestions": suggestions,
            "action_preview": None,
        }

    transfer_match = re.search(
        r"(?:transfer|send)\s+(\d+)\s*(?:cpc)?\s+(?:from\s+([A-Za-z0-9_]+)\s+)?(?:to|into)\s+([A-Za-z0-9_]+)",
        lowered,
    )
    if transfer_match:
        amount = int(transfer_match.group(1))
        sender = transfer_match.group(2) or account
        receiver = transfer_match.group(3)
        return {
            "reply": f"I parsed a transfer request: {sender} -> {receiver} for {amount} CPC. The live LLM agent can later confirm and execute this through the transfer API.",
            "intent": "transfer",
            "suggestions": suggestions,
            "action_preview": {
                "type": "transfer",
                "sender": sender,
                "receiver": receiver,
                "amount": amount,
            },
        }

    if "verify" in lowered or "chain" in lowered or "audit" in lowered:
        return {
            "reply": "This looks like a chain verification request. Once your LLM is connected, it can call the verify endpoint and explain any broken hash links before rewarding the user.",
            "intent": "verify",
            "suggestions": suggestions,
            "action_preview": {
                "type": "verify",
                "account": account,
            },
        }

    if "balance" in lowered or "how much" in lowered:
        balance = get_balance(account)
        return {
            "reply": f"{account} currently has {balance} CPC available. A future LLM tool call can also compare inflow versus outflow and narrate the result.",
            "intent": "balance",
            "suggestions": suggestions,
            "action_preview": {
                "type": "balance_lookup",
                "account": account,
                "balance": balance,
            },
        }

    if "transaction" in lowered or "history" in lowered or "recent" in lowered:
        return {
            "reply": "I can surface recent activity and summarize it for the user. The future LLM layer can turn this into natural-language insights like unusual spending, transfer streaks, or recent counterparties.",
            "intent": "history",
            "suggestions": suggestions,
            "action_preview": {
                "type": "history_lookup",
                "account": account,
            },
        }

    return {
        "reply": "The chat surface is ready for an LLM connector. Right now I can classify requests and prepare action previews; later you can wire this to OpenAI or another model for tool-driven on-chain execution.",
        "intent": "general",
        "suggestions": suggestions,
        "action_preview": None,
    }


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
    limit = int(request.args.get("limit", "20"))
    rows = serialize_transactions(account, limit=limit)
    return jsonify({"account": account, "transactions": rows})


@app.post("/api/transfer")
def api_transfer():
    payload = request.get_json(silent=True) or {}
    sender = (payload.get("sender") or "").strip()
    receiver = (payload.get("receiver") or "").strip()
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
        block_index, _ = append_transaction(sender, receiver, amount)
        sealed_block = block_index > previous_last_block

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
