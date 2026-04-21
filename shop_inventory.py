"""
shop_inventory.py
─────────────────
使用者背包與主動效果管理
"""

import random
import time

from state_db import (
    get_inventory,
    add_inventory_item as add_item,
    consume_inventory_item as consume_item,
    get_all_effects as get_effects,
    set_effect,
    clear_effect,
    has_effect,
)

RAINBOW_GOAL = 7       # 集滿幾片換大獎
RAINBOW_PRIZE = 5000


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
        expires = time.time() + 60
        set_effect(account, "free_skip", {"expires": expires})
        message = "傳送捲軸已啟動！1 分鐘內換題不扣 CPC。"

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
        inv = get_inventory(account)
        frags_remaining = inv.get("rainbow_frag", 0)
        total_frags = frags_remaining + 1  # 1 was just consumed
        if total_frags >= RAINBOW_GOAL:
            # We need to consume RAINBOW_GOAL - 1 more
            if consume_item(account, item_id, RAINBOW_GOAL - 1):
                delta   = RAINBOW_PRIZE
                message = f"🌈 集齊 {RAINBOW_GOAL} 片！兌換 {RAINBOW_PRIZE} CPC 大獎！"
            else:
                # Fallback if something went wrong
                add_item(account, item_id, 1)
                message = "彩虹碎片數量異常。"
        else:
            # Refund the consumed fragment, since it hasn't reached the goal
            add_item(account, item_id, 1)
            message = f"已擁有 {total_frags} 片彩虹碎片，再收集 {RAINBOW_GOAL - total_frags} 片可兌換 {RAINBOW_PRIZE} CPC。"

    # ── 社交效果 ─────────────────────────────────────────────────────────────
    elif effect == "send_gift":
        recv = target if target else account
        if recv == account:
            # Open for self
            delta = 500
            message = "你打開了神秘禮盒！獲得 500 CPC！"
        else:
            # Send the gift_box item to recipient's bag — they open it themselves
            add_item(recv, "gift_box")
            extra["gift_to_bag"] = recv
            message = f"🎁 禮盒已送入 {recv} 的背包！對方可以自己開啟。"

    elif effect == "curse_target":
        recv = target if target else account
        set_effect(recv, "cursed_penalty", 50)
        extra["cursed"] = recv
        if recv == account:
            message = "你詛咒了自己……下次答錯將罰 50 CPC。"
        else:
            message = f"詛咒已施放至 {recv}！他下次答錯將罰 50 CPC。"

    elif effect == "bless_target":
        recv = target if target else account
        set_effect(recv, "double_reward", True)
        extra["blessed"] = recv
        if recv == account:
            message = "你祝福了自己！下次答對獎勵翻倍。"
        else:
            message = f"祝福已傳送給 {recv}！他下次答對獎勵翻倍。"

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

    elif effect == "credit_plus3":
        set_effect(account, "credit_plus3", True)
        message = "🎓 恭喜！雲端系統學分 +3 已生效！（教授：等等，這不在系統裡...）"

    return {
        "ok":        True,
        "message":   message,
        "cpc_delta": delta,
        "extra":     extra,
    }
