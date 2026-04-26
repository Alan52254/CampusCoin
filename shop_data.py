"""
shop_data.py
────────────
校園商店道具目錄
"""

ITEMS: list[dict] = [
    # ── 解謎道具 ──────────────────────────────────────────────────────────────
    {
        "id": "shield",
        "name": "護盾符文",
        "emoji": "🛡️",
        "description": "使用後，下一題答錯不會扣 CPC。",
        "price": 200,
        "type": "consumable",
        "effect": "next_wrong_no_penalty",
        "category": "puzzle",
    },
    {
        "id": "double_crystal",
        "name": "雙倍魔法水晶",
        "emoji": "💎",
        "description": "使用後，下一題答對獲得雙倍獎勵（2000 CPC）。",
        "price": 350,
        "type": "consumable",
        "effect": "next_correct_double",
        "category": "puzzle",
    },
    {
        "id": "skip_scroll",
        "name": "傳送捲軸",
        "emoji": "📜",
        "description": "使用後，1 分鐘內換題不扣任何 CPC。效果倒數計時，可連續免費換題。",
        "price": 30,
        "type": "consumable",
        "effect": "free_skip",
        "category": "puzzle",
    },
    {
        "id": "hint_potion",
        "name": "超級提示藥水",
        "emoji": "🧪",
        "description": "使用後，接下來 3 題額外顯示一段關鍵字提示。",
        "price": 120,
        "type": "consumable",
        "effect": "super_hint_3",
        "category": "puzzle",
    },
    {
        "id": "time_gem",
        "name": "時光回溯寶石",
        "emoji": "🔮",
        "description": "使用後，撤銷上一題的錯誤記錄，CPC 退還給你。",
        "price": 300,
        "type": "consumable",
        "effect": "undo_last_wrong",
        "category": "puzzle",
    },

    # ── 賭運道具 ──────────────────────────────────────────────────────────────
    {
        "id": "lucky_dice",
        "name": "幸運骰子",
        "emoji": "🎲",
        "description": "立即擲出隨機金額，獲得 50～800 CPC（也可能只有 1 CPC，自求多福）。",
        "price": 150,
        "type": "consumable",
        "effect": "random_reward",
        "category": "gamble",
    },
    {
        "id": "mystery_box",
        "name": "神秘寶箱",
        "emoji": "📦",
        "description": "50% 機率獲得另一件隨機道具；50% 機率直接獲得 100～3000 CPC。",
        "price": 500,
        "type": "consumable",
        "effect": "mystery_box",
        "category": "gamble",
    },
    {
        "id": "rainbow_frag",
        "name": "彩虹碎片",
        "emoji": "🌈",
        "description": "收集 7 片後自動兌換 5000 CPC 大獎。每次購買獲得 1 片。",
        "price": 50,
        "type": "collectible",
        "effect": "rainbow_fragment",
        "category": "gamble",
    },

    # ── 社交道具 ──────────────────────────────────────────────────────────────
    {
        "id": "gift_box",
        "name": "神秘禮盒",
        "emoji": "🎁",
        "description": "指定帳號，送出一個包含 500 CPC 的驚喜禮盒。",
        "price": 200,
        "type": "consumable",
        "effect": "send_gift",
        "category": "social",
    },
    {
        "id": "curse_scroll",
        "name": "詛咒卷軸",
        "emoji": "💀",
        "description": "對指定帳號施加詛咒：他下一次答錯罰款變為 50 CPC。",
        "price": 180,
        "type": "consumable",
        "effect": "curse_target",
        "category": "social",
    },
    {
        "id": "blessing",
        "name": "祝福靈符",
        "emoji": "✨",
        "description": "送給指定帳號，讓他下一題答對獎勵翻倍。",
        "price": 160,
        "type": "consumable",
        "effect": "bless_target",
        "category": "social",
    },

    # ── 特殊功能 ──────────────────────────────────────────────────────────────
    {
        "id": "moonlight",
        "name": "月光精華",
        "emoji": "🌙",
        "description": "啟動後 10 分鐘內，所有答對獎勵 ×1.5。",
        "price": 600,
        "type": "consumable",
        "effect": "moonlight_10min",
        "category": "special",
    },
    {
        "id": "miner_helmet",
        "name": "礦工頭盔",
        "emoji": "⛏️",
        "description": "立即觸發區塊鏈驗證並領取 10 CPC 獎勵（跳過冷卻限制）。",
        "price": 800,
        "type": "consumable",
        "effect": "instant_verify",
        "category": "special",
    },
    {
        "id": "legend_die",
        "name": "傳說 RPG 骰",
        "emoji": "🎭",
        "description": "出題時從 3 道隨機謎題中選一道你最有把握的來作答。",
        "price": 250,
        "type": "consumable",
        "effect": "choose_from_3",
        "category": "special",
    },

    # ── 成大西瓜道具 ──────────────────────────────────────────────────────────
    {
        "id": "suika_amulet",
        "name": "西瓜護符",
        "emoji": "🍉",
        "description": "下一局大西瓜遊戲 CPC 獎勵上限翻倍（500 → 1000）。遊戲開始後自動啟用，結算時生效。",
        "price": 400,
        "type": "consumable",
        "effect": "suika_cap_boost",
        "category": "suika",
    },
    {
        "id": "suika_wild",
        "name": "萬能球",
        "emoji": "🎱",
        "description": "下一局大西瓜遊戲，可以指定下一顆要投放的球是哪種類型，精準佈局！",
        "price": 300,
        "type": "consumable",
        "effect": "suika_wild",
        "category": "suika",
    },
    {
        "id": "suika_boom",
        "name": "隕石清場",
        "emoji": "☄️",
        "description": "下一局大西瓜遊戲，啟動後點擊任一顆球，場上所有同類型的球全部消除！",
        "price": 350,
        "type": "consumable",
        "effect": "suika_boom",
        "category": "suika",
    },

    # ── 裝飾稱號 ──────────────────────────────────────────────────────────────
    {
        "id": "crown",
        "name": "榮耀皇冠",
        "emoji": "👑",
        "description": "永久顯示於排行榜帳號名稱旁。彰顯你的財力與地位。",
        "price": 100000,
        "type": "cosmetic",
        "effect": "title_crown",
        "category": "cosmetic",
    },
    {
        "id": "title_master",
        "name": "謎題大師稱號",
        "emoji": "🏆",
        "description": "永久在你的帳號旁顯示「謎題大師」稱號。只有真正的頂尖玩家才能擁有。",
        "price": 100000,
        "type": "cosmetic",
        "effect": "title_master",
        "category": "cosmetic",
    },
    {
        "id": "ghost_cloak",
        "name": "隱身披風",
        "emoji": "👻",
        "description": "永久從排行榜隱藏你的帳號（神秘感 MAX）。",
        "price": 100000,
        "type": "cosmetic",
        "effect": "hide_leaderboard",
        "category": "cosmetic",
    },
    {
        "id": "credit_plus3",
        "name": "雲端系統學分加3",
        "emoji": "🎓",
        "description": "【終極道具】傳說級稀有物品。使用後，你的雲端系統課程學分加 3。",
        "price": 100000,
        "type": "cosmetic",
        "effect": "credit_plus3",
        "category": "cosmetic",
    },
]

_id_map: dict = {item["id"]: item for item in ITEMS}


def get_item_by_id(item_id: str):
    return _id_map.get(item_id)


def get_items_by_category(category: str) -> list:
    return [i for i in ITEMS if i["category"] == category]


CATEGORIES = [
    {"id": "puzzle",   "label": "解謎道具"},
    {"id": "gamble",   "label": "賭運道具"},
    {"id": "social",   "label": "社交道具"},
    {"id": "special",  "label": "特殊功能"},
    {"id": "suika",    "label": "🍉 大西瓜道具"},
    {"id": "cosmetic", "label": "裝飾稱號"},
]
