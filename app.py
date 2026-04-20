import csv
import io
import re
import sys
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request


BASE_DIR = Path(__file__).resolve().parent
SHARED_STORAGE_DIR = BASE_DIR / "shared_storage"
sys.path.insert(0, str(SHARED_STORAGE_DIR))

from ledger_core import (  # noqa: E402
    append_transaction,
    get_account_log,
    get_account_stats,
    get_balance,
    get_transactions,
    iter_block_paths,
    last_block_index,
    ledger_lock,
    parse_metadata,
    register_account,
    verify_account,
    verify_chain,
)

# ── LLM assistant (falls back gracefully if import fails) ────────────────────
try:
    from llm_assistant import build_assistant_reply as _llm_reply, clear_history as _clear_history
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# ── Puzzle RAG (falls back gracefully if import fails) ────────────────────────
try:
    from puzzle_rag import evaluate_answer as _evaluate_answer
    from puzzle_data import PUZZLES, get_puzzle_by_id, get_all_ids
    PUZZLE_AVAILABLE = True
except ImportError:
    PUZZLE_AVAILABLE = False

# ── Shop (falls back gracefully if import fails) ──────────────────────────────
try:
    from shop_data import ITEMS as SHOP_ITEMS, get_item_by_id, CATEGORIES as SHOP_CATEGORIES
    from shop_inventory import (
        get_inventory, add_item, consume_item, use_item,
        get_effects, has_effect, clear_effect, set_effect,
    )
    SHOP_AVAILABLE = True
except ImportError:
    SHOP_AVAILABLE = False


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

    # 一次掃描取得餘額與交易記錄，不重複 I/O
    stats = get_account_stats(account)
    rows  = stats["log"]
    income  = sum(amount for _, sender, receiver, amount in rows if receiver == account)
    expense = sum(amount for _, sender, receiver, amount in rows if sender == account)

    recent = []
    for block_index, sender, receiver, amount in reversed(rows[-8:]):
        direction = "in" if receiver == account else "out"
        recent.append({
            "block": block_index,
            "sender": sender,
            "receiver": receiver,
            "amount": amount,
            "direction": direction,
            "counterparty": sender if direction == "in" else receiver,
        })

    return {
        "account": account,
        "balance": stats["balance"],
        "transaction_count": len(rows),
        "block_count": latest_index,
        "latest_block": latest_index,
        "latest_pointer": latest_pointer,
        "income": income,
        "expense": expense,
        "chain_ok": len(verify_chain()) == 0,
        "recent_transactions": recent,
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
def landing():
    return render_template("landing.html")


@app.get("/login")
def login_page():
    return render_template("login.html")


@app.get("/dashboard")
def dashboard():
    account = request.args.get("account", "b1128015")
    return render_template("dashboard.html", initial_account=account, overview=build_dashboard_payload(account))


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
    password   = (payload.get("password") or "").strip()
    amount_raw = payload.get("amount")

    if not sender or not receiver:
        return jsonify({"ok": False, "error": "Sender and receiver are required."}), 400

    if not verify_account(sender, password):
        return jsonify({"ok": False, "error": "帳號或密碼錯誤。"}), 403

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


@app.post("/api/login")
def api_login():
    payload  = request.get_json(silent=True) or {}
    account  = (payload.get("account") or "").strip()
    password = (payload.get("password") or "").strip()

    if not account or not password:
        return jsonify({"ok": False, "error": "Account and password are required."}), 400

    if not verify_account(account, password):
        return jsonify({"ok": False, "error": "Invalid account or password."}), 401

    return jsonify({"ok": True, "account": account, "overview": build_dashboard_payload(account)})


@app.post("/api/register")
def api_register():
    payload  = request.get_json(silent=True) or {}
    account  = (payload.get("account")  or "").strip()
    password = (payload.get("password") or "").strip()

    if not account or not password:
        return jsonify({"ok": False, "error": "帳號與密碼不能為空。"}), 400

    if not register_account(account, password):
        return jsonify({"ok": False, "error": f"帳號 {account} 已存在。"}), 409

    return jsonify({"ok": True, "message": f"帳號 {account} 註冊成功。"})


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


@app.get("/api/search")
def api_search():
    account      = request.args.get("account", "b1128015")
    counterparty = request.args.get("counterparty", "").strip().lower()
    min_amount   = request.args.get("min_amount", type=int)
    max_amount   = request.args.get("max_amount", type=int)
    block_filter = request.args.get("block", type=int)

    rows = get_account_log(account)
    results = []
    for block_index, sender, receiver, amount in rows:
        if counterparty and counterparty not in (sender.lower(), receiver.lower()):
            continue
        if min_amount is not None and amount < min_amount:
            continue
        if max_amount is not None and amount > max_amount:
            continue
        if block_filter is not None and block_index != block_filter:
            continue
        direction = "in" if receiver == account else "out"
        results.append({
            "block": block_index,
            "sender": sender,
            "receiver": receiver,
            "amount": amount,
            "direction": direction,
            "counterparty": sender if direction == "in" else receiver,
        })
    results.reverse()
    return jsonify({"account": account, "transactions": results})


@app.get("/api/export/csv")
def api_export_csv():
    account = request.args.get("account", "b1128015")
    rows    = get_account_log(account)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Block", "Sender", "Receiver", "Amount", "Direction"])
    for block_index, sender, receiver, amount in rows:
        direction = "in" if receiver == account else "out"
        writer.writerow([block_index, sender, receiver, amount, direction])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={account}_transactions.csv"},
    )


@app.get("/api/blocks")
def api_blocks():
    blocks = []
    for index, path in iter_block_paths():
        prev_hash, next_block = parse_metadata(path)
        txs = get_transactions(path)
        blocks.append({
            "index":    index,
            "prev_hash": prev_hash[:20] + "..." if len(prev_hash) > 20 else prev_hash,
            "next_block": next_block,
            "tx_count": len(txs),
            "transactions": [{"sender": s, "receiver": r, "amount": a} for s, r, a in txs],
        })
    return jsonify({"blocks": blocks})


@app.get("/api/leaderboard")
def api_leaderboard():
    balances: dict[str, int] = {}
    for _, path in iter_block_paths():
        for sender, receiver, amount in get_transactions(path):
            balances[sender]   = balances.get(sender, 0)   - amount
            balances[receiver] = balances.get(receiver, 0) + amount

    leaderboard = sorted(
        [{"account": k, "balance": v} for k, v in balances.items()],
        key=lambda x: x["balance"],
        reverse=True,
    )
    return jsonify({"leaderboard": leaderboard})


# ── Puzzle endpoints ──────────────────────────────────────────────────────────

def _safe_puzzle_dict(puzzle: dict) -> dict:
    return {
        "id":             puzzle["id"],
        "category":       puzzle["category"],
        "category_label": puzzle["category_label"],
        "question":       puzzle["question"],
        "hint":           puzzle.get("hint", ""),
    }


@app.get("/api/puzzle/three")
def api_puzzle_three():
    """傳說 RPG 骰專用：回傳 3 道不同的隨機謎題供使用者選擇。"""
    if not PUZZLE_AVAILABLE:
        return jsonify({"ok": False, "error": "Puzzle module not available."}), 503
    import random
    exclude = request.args.getlist("exclude")
    candidates = [p for p in PUZZLES if p["id"] not in exclude]
    if not candidates:
        candidates = PUZZLES
    chosen = random.sample(candidates, min(3, len(candidates)))
    return jsonify({"ok": True, "puzzles": [_safe_puzzle_dict(p) for p in chosen]})


@app.get("/api/puzzle/random")
def api_puzzle_random():
    """回傳一道隨機謎題（不含答案），可用 exclude 排除已答過的 ID。"""
    if not PUZZLE_AVAILABLE:
        return jsonify({"ok": False, "error": "Puzzle module not available."}), 503

    import random
    exclude = request.args.getlist("exclude")
    candidates = [p for p in PUZZLES if p["id"] not in exclude]
    if not candidates:
        candidates = PUZZLES  # 全部答完就重新循環

    puzzle = random.choice(candidates)
    return jsonify({"ok": True, "puzzle": _safe_puzzle_dict(puzzle)})


@app.post("/api/puzzle/answer")
def api_puzzle_answer():
    """評分並依結果轉帳獎勵或罰款。"""
    if not PUZZLE_AVAILABLE:
        return jsonify({"ok": False, "error": "Puzzle module not available."}), 503

    payload   = request.get_json(silent=True) or {}
    account   = (payload.get("account") or "").strip()
    puzzle_id = (payload.get("puzzle_id") or "").strip()
    user_ans  = (payload.get("answer") or "").strip()

    if not account or not puzzle_id:
        return jsonify({"ok": False, "error": "account and puzzle_id required."}), 400

    puzzle = get_puzzle_by_id(puzzle_id)
    if not puzzle:
        return jsonify({"ok": False, "error": "Puzzle not found."}), 404

    # RAG 評分
    result = _evaluate_answer(puzzle_id, user_ans)
    correct = result["correct"]

    BASE_REWARD  = 1000
    BASE_PENALTY = 10

    # ── 計算實際獎懲（道具效果） ─────────────────────────────────────────────
    active_effects = []
    if SHOP_AVAILABLE:
        # 雙倍獎勵（自己或別人祝福）
        if has_effect(account, "double_reward"):
            BASE_REWARD = 2000
            clear_effect(account, "double_reward")
            active_effects.append("double_reward")
        # 月光精華 ×1.5
        if has_effect(account, "moonlight"):
            BASE_REWARD = int(BASE_REWARD * 1.5)
            active_effects.append("moonlight")
        # 護盾
        if not correct and has_effect(account, "shield"):
            BASE_PENALTY = 0
            clear_effect(account, "shield")
            active_effects.append("shield")
        # 詛咒（別人對你施的）
        if not correct and has_effect(account, "cursed_penalty"):
            BASE_PENALTY = get_effects(account).get("cursed_penalty", BASE_PENALTY)
            clear_effect(account, "cursed_penalty")
            active_effects.append("cursed_penalty")

    if correct:
        with ledger_lock():
            block_index, _ = append_transaction("angel", account, BASE_REWARD)
        overview = build_dashboard_payload(account)
        return jsonify({
            "ok": True,
            "correct": True,
            "delta": BASE_REWARD,
            "feedback": result["feedback"],
            "official_answer": "",
            "block_index": block_index,
            "overview": overview,
            "active_effects": active_effects,
        })
    else:
        balance = get_balance(account)
        deduct  = min(BASE_PENALTY, balance) if BASE_PENALTY > 0 and balance > 0 else 0
        block_index = None
        if deduct > 0:
            with ledger_lock():
                block_index, _ = append_transaction(account, "angel", deduct)
        overview = build_dashboard_payload(account)
        return jsonify({
            "ok": True,
            "correct": False,
            "delta": -deduct,
            "feedback": result["feedback"],
            "official_answer": result.get("official_answer", ""),
            "block_index": block_index,
            "overview": overview,
            "active_effects": active_effects,
        })


@app.get("/puzzle")
def puzzle_page():
    account = request.args.get("account", "b1128015")
    return render_template("puzzle.html", account=account)


# ── Shop endpoints ────────────────────────────────────────────────────────────

@app.get("/shop")
def shop_page():
    account = request.args.get("account", "b1128015")
    return render_template("shop.html", account=account)


@app.get("/api/shop/items")
def api_shop_items():
    if not SHOP_AVAILABLE:
        return jsonify({"ok": False, "error": "Shop unavailable."}), 503
    return jsonify({
        "ok": True,
        "items": SHOP_ITEMS,
        "categories": SHOP_CATEGORIES,
    })


@app.get("/api/shop/inventory")
def api_shop_inventory():
    if not SHOP_AVAILABLE:
        return jsonify({"ok": False, "error": "Shop unavailable."}), 503
    account = request.args.get("account", "").strip()
    if not account:
        return jsonify({"ok": False, "error": "account required."}), 400
    inv = get_inventory(account)
    fx  = get_effects(account)
    return jsonify({"ok": True, "inventory": inv, "effects": fx})


@app.post("/api/shop/buy")
def api_shop_buy():
    if not SHOP_AVAILABLE:
        return jsonify({"ok": False, "error": "Shop unavailable."}), 503
    payload  = request.get_json(silent=True) or {}
    account  = (payload.get("account")  or "").strip()
    password = (payload.get("password") or "").strip()
    item_id  = (payload.get("item_id")  or "").strip()

    if not verify_account(account, password):
        return jsonify({"ok": False, "error": "帳號或密碼錯誤。"}), 403

    item = get_item_by_id(item_id)
    if not item:
        return jsonify({"ok": False, "error": "商品不存在。"}), 404

    price   = item["price"]
    balance = get_balance(account)
    if balance < price:
        return jsonify({"ok": False, "error": f"餘額不足（需要 {price} CPC，目前 {balance} CPC）。"}), 400

    # 扣款
    with ledger_lock():
        append_transaction(account, "angel", price)

    # 加入背包
    add_item(account, item_id)
    inv      = get_inventory(account)
    overview = build_dashboard_payload(account)

    return jsonify({
        "ok": True,
        "message": f"成功購買「{item['emoji']} {item['name']}」！",
        "inventory": inv,
        "overview": overview,
    })


@app.post("/api/shop/use")
def api_shop_use():
    if not SHOP_AVAILABLE:
        return jsonify({"ok": False, "error": "Shop unavailable."}), 503
    payload  = request.get_json(silent=True) or {}
    account  = (payload.get("account")  or "").strip()
    item_id  = (payload.get("item_id")  or "").strip()
    target   = (payload.get("target")   or "").strip()

    if not account or not item_id:
        return jsonify({"ok": False, "error": "account and item_id required."}), 400

    result = use_item(account, item_id, target=target)
    if not result["ok"]:
        return jsonify(result), 400

    # 若有 CPC 獎勵（骰子、寶箱等）
    if result["cpc_delta"] > 0:
        with ledger_lock():
            append_transaction("angel", account, result["cpc_delta"])

    # 若有社交轉帳（禮盒送 500 CPC）
    extra = result.get("extra", {})
    if extra.get("gift_to"):
        with ledger_lock():
            append_transaction(account, extra["gift_to"], 500)

    # 若觸發驗證（礦工頭盔）
    if extra.get("trigger_verify"):
        with ledger_lock():
            issues = verify_chain()
            if not issues:
                append_transaction("angel", account, 10)
                result["message"] += " 驗證通過，額外獲得 10 CPC！"

    inv      = get_inventory(account)
    overview = build_dashboard_payload(account)
    return jsonify({
        "ok":       True,
        "message":  result["message"],
        "cpc_delta": result["cpc_delta"],
        "inventory": inv,
        "effects":   get_effects(account),
        "overview":  overview,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
