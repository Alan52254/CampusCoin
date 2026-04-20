"""
shop_inventory.py
─────────────────
使用者背包與主動效果管理
"""

import json
import random
import time
from pathlib import Path

STORAGE = Path(__file__).resolve().parent / "shared_storage"
INVENTORY_PATH = STORAGE / "inventory.json"
EFFECTS_PATH   = STORAGE / "effects.json"

RAINBOW_GOAL = 7       # 集滿幾片換大獎
RAINBOW_PRIZE = 5000


# ── 讀寫工具 ──────────────────────────────────────────────────────────────────
def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(path: Path, data: dict) -> None:
    STORAGE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 背包 ──────────────────────────────────────────────────────────────────────
def get_inventory(account: str) -> dict:
    """回傳帳號的道具清單 {item_id: count}"""
    return _load(INVENTORY_PATH).get(account, {})


def add_item(account: str, item_id: str, count: int = 1) -> dict:
    all_inv = _load(INVENTORY_PATH)
    inv = all_inv.setdefault(account, {})
    inv[item_id] = inv.get(item_id, 0) + count
    _save(INVENTORY_PATH, all_inv)
    return inv


def consume_item(account: str, item_id: str) -> bool:
    """消耗 1 個道具，成功回傳 True，不足回傳 False。"""
    all_inv = _load(INVENTORY_PATH)
    inv = all_inv.get(account, {})
    if inv.get(item_id, 0) <= 0:
        return False
    inv[item_id] -= 1
    if inv[item_id] == 0:
        del inv[item_id]
    all_inv[account] = inv
    _save(INVENTORY_PATH, all_inv)
    return True


# ── 主動效果 ──────────────────────────────────────────────────────────────────
def get_effects(account: str) -> dict:
    return _load(EFFECTS_PATH).get(account, {})


def set_effect(account: str, effect: str, value) -> None:
    all_fx = _load(EFFECTS_PATH)
    all_fx.setdefault(account, {})[effect] = value
    _save(EFFECTS_PATH, all_fx)


def clear_effect(account: str, effect: str) -> None:
    all_fx = _load(EFFECTS_PATH)
    all_fx.get(account, {}).pop(effect, None)
    _save(EFFECTS_PATH, all_fx)


def has_effect(account: str, effect: str) -> bool:
    fx = get_effects(account)
    val = fx.get(effect)
    if val is None:
        return False
    # 計時效果：檢查是否過期
    if isinstance(val, dict) and "expires" in val:
        if time.time() > val["expires"]:
            clear_effect(account, effect)
            return False
    return True


# ── 道具使用邏輯 ──────────────────────────────────────────────────────────────
def use_item(account: str, item_id: str, target: str = "") -> dict:
    """
    使用道具，回傳 {"ok": bool, "message": str, "cpc_delta": int, "extra": dict}
    """
    from shop_data import get_item_by_id
    item = get_item_by_id(item_id)
    if not item:
        return {"ok": False, "message": "道具不存在。", "cpc_delta": 0}

    if not consume_item(account, item_id):
        return {"ok": False, "message": f"你沒有「{item['name']}」。", "cpc_delta": 0}

    effect  = item["effect"]
    message = ""
    delta   = 0
    extra   = {}

    # ── 解謎效果 ─────────────────────────────────────────────────────────────
    if effect == "next_wrong_no_penalty":
        set_effect(account, "shield", True)
        message = "護盾已啟動！下一題答錯不扣 CPC。"

    elif effect == "next_correct_double":
        set_effect(account, "double_reward", True)
        message = "雙倍水晶已啟動！下一題答對得 2000 CPC。"

    elif effect == "free_skip":
        set_effect(account, "free_skip", True)
        message = "傳送捲軸已啟動！下次 Skip 不計罰款。"

    elif effect == "super_hint_3":
        fx = get_effects(account)
        remaining = fx.get("super_hint", 0) + 3
        set_effect(account, "super_hint", remaining)
        message = f"超級提示啟動！接下來 {remaining} 題有加強提示。"

    elif effect == "undo_last_wrong":
        set_effect(account, "undo_pending", True)
        message = "時光寶石已就緒，將撤銷你下一次的答錯記錄。"

    # ── 賭運效果 ─────────────────────────────────────────────────────────────
    elif effect == "random_reward":
        weights = [30, 25, 20, 15, 8, 2]
        prizes  = [1, 50, 100, 300, 600, 800]
        delta   = random.choices(prizes, weights=weights, k=1)[0]
        message = f"骰子擲出！獲得 {delta} CPC！"

    elif effect == "mystery_box":
        if random.random() < 0.5:
            # 隨機道具（排除自身和稱號）
            from shop_data import ITEMS
            pool = [i for i in ITEMS if i["type"] == "consumable" and i["id"] != "mystery_box"]
            gift = random.choice(pool)
            add_item(account, gift["id"])
            message = f"寶箱開出了「{gift['emoji']} {gift['name']}」！已加入背包。"
            extra["gift_item"] = gift["id"]
        else:
            delta = random.randint(100, 3000)
            message = f"寶箱裡有 {delta} CPC 現金！"

    elif effect == "rainbow_fragment":
        all_inv = _load(INVENTORY_PATH)
        inv = all_inv.get(account, {})
        frags = inv.get("rainbow_frag", 0)
        if frags >= RAINBOW_GOAL:
            inv["rainbow_frag"] = frags - RAINBOW_GOAL
            all_inv[account] = inv
            _save(INVENTORY_PATH, all_inv)
            delta   = RAINBOW_PRIZE
            message = f"🌈 集齊 {RAINBOW_GOAL} 片！兌換 {RAINBOW_PRIZE} CPC 大獎！"
        else:
            message = f"已擁有 {frags} 片彩虹碎片，再收集 {RAINBOW_GOAL - frags} 片可兌換 {RAINBOW_PRIZE} CPC。"

    # ── 社交效果 ─────────────────────────────────────────────────────────────
    elif effect == "send_gift":
        if not target:
            add_item(account, item_id)   # 退還
            return {"ok": False, "message": "請指定收禮帳號。", "cpc_delta": 0}
        delta   = 500
        extra["gift_to"] = target
        message = f"已向 {target} 送出神秘禮盒（500 CPC）！"

    elif effect == "curse_target":
        if not target:
            add_item(account, item_id)
            return {"ok": False, "message": "請指定詛咒目標。", "cpc_delta": 0}
        set_effect(target, "cursed_penalty", 50)
        extra["cursed"] = target
        message = f"詛咒已施放至 {target}！他下次答錯將罰 50 CPC。"

    elif effect == "bless_target":
        if not target:
            add_item(account, item_id)
            return {"ok": False, "message": "請指定祝福對象。", "cpc_delta": 0}
        set_effect(target, "double_reward", True)
        extra["blessed"] = target
        message = f"祝福已傳送給 {target}！他下次答對獎勵翻倍。"

    # ── 特殊效果 ─────────────────────────────────────────────────────────────
    elif effect == "moonlight_10min":
        expires = time.time() + 600   # 10 分鐘
        set_effect(account, "moonlight", {"expires": expires, "mult": 1.5})
        message = "月光精華啟動！10 分鐘內所有答對獎勵 ×1.5。"

    elif effect == "instant_verify":
        extra["trigger_verify"] = True
        message = "礦工頭盔啟動！立即觸發區塊鏈驗證並領取 10 CPC。"

    elif effect == "choose_from_3":
        set_effect(account, "choose_3", True)
        message = "傳說骰已啟動！下一題將從 3 道謎題中選一道。"

    # ── 裝飾效果（永久） ─────────────────────────────────────────────────────
    elif effect in ("title_crown", "title_master", "hide_leaderboard"):
        set_effect(account, effect, True)
        message = f"「{item['name']}」已永久啟用！"

    return {
        "ok":        True,
        "message":   message,
        "cpc_delta": delta,
        "extra":     extra,
    }
