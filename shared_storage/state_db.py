import json
import sqlite3
import time
from pathlib import Path
from contextlib import contextmanager

SHARED_DIR = Path(__file__).resolve().parent
DB_PATH = SHARED_DIR / "state.db"
INVENTORY_JSON = SHARED_DIR / "inventory.json"
EFFECTS_JSON = SHARED_DIR / "effects.json"


@contextmanager
def db_transaction():
    """Generator context manager for safe SQLite transactions."""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    # Enable Write-Ahead Logging for better concurrency
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _init_db():
    with db_transaction() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                account TEXT,
                item_id TEXT,
                count INTEGER DEFAULT 0,
                PRIMARY KEY (account, item_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS effects (
                account TEXT,
                effect_id TEXT,
                value_json TEXT,
                expires_at REAL,
                PRIMARY KEY (account, effect_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS puzzle_sessions (
                session_id TEXT PRIMARY KEY,
                account TEXT,
                puzzle_id TEXT,
                state TEXT,
                attempt_count INTEGER DEFAULT 0,
                hint_count INTEGER DEFAULT 0,
                reward_granted INTEGER DEFAULT 0,
                created_at REAL,
                updated_at REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reward_registry (
                reward_key TEXT PRIMARY KEY,
                account TEXT,
                amount INTEGER,
                created_at REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS puzzle_knowledge (
                id TEXT PRIMARY KEY,
                category TEXT,
                difficulty TEXT,
                question TEXT,
                hint TEXT,
                answer TEXT,
                key_points TEXT,
                aliases TEXT,
                embedding_text TEXT
            )
        """)


def _migrate_from_json():
    """Migrate data from legacy JSON files if they exist and DB is empty."""
    with db_transaction() as conn:
        # Check if inventory is empty
        cur = conn.execute("SELECT COUNT(*) FROM inventory")
        if cur.fetchone()[0] == 0:
            if INVENTORY_JSON.exists():
                try:
                    data = json.loads(INVENTORY_JSON.read_text(encoding="utf-8"))
                    for account, items in data.items():
                        for item_id, count in items.items():
                            conn.execute(
                                "INSERT INTO inventory (account, item_id, count) VALUES (?, ?, ?)",
                                (account, item_id, count)
                            )
                    print(f"Migrated inventory.json to SQLite.")
                except Exception as e:
                    print(f"Failed to migrate inventory.json: {e}")

        # Check if effects is empty
        cur = conn.execute("SELECT COUNT(*) FROM effects")
        if cur.fetchone()[0] == 0:
            if EFFECTS_JSON.exists():
                try:
                    data = json.loads(EFFECTS_JSON.read_text(encoding="utf-8"))
                    for account, fx_map in data.items():
                        for effect_id, value in fx_map.items():
                            expires_at = None
                            if isinstance(value, dict) and "expires" in value:
                                expires_at = value.get("expires")
                            conn.execute(
                                "INSERT INTO effects (account, effect_id, value_json, expires_at) VALUES (?, ?, ?, ?)",
                                (account, effect_id, json.dumps(value, ensure_ascii=False), expires_at)
                            )
                    print(f"Migrated effects.json to SQLite.")
                except Exception as e:
                    print(f"Failed to migrate effects.json: {e}")


# ── Inventory Methods ────────────────────────────────────────────────────────

def get_inventory(account: str) -> dict:
    """Returns {item_id: count} for a given account."""
    with db_transaction() as conn:
        rows = conn.execute("SELECT item_id, count FROM inventory WHERE account = ? AND count > 0", (account,))
        return {row["item_id"]: row["count"] for row in rows}

def add_inventory_item(account: str, item_id: str, count: int = 1):
    with db_transaction() as conn:
        conn.execute("""
            INSERT INTO inventory (account, item_id, count)
            VALUES (?, ?, ?)
            ON CONFLICT(account, item_id) DO UPDATE SET count = count + excluded.count
        """, (account, item_id, count))

def consume_inventory_item(account: str, item_id: str, count: int = 1) -> bool:
    """Consumes items and returns True if successful, False if insufficient limit."""
    with db_transaction() as conn:
        cur = conn.execute("SELECT count FROM inventory WHERE account = ? AND item_id = ?", (account, item_id))
        row = cur.fetchone()
        if not row or row["count"] < count:
            return False
        
        new_count = row["count"] - count
        if new_count <= 0:
            conn.execute("DELETE FROM inventory WHERE account = ? AND item_id = ?", (account, item_id))
        else:
            conn.execute("UPDATE inventory SET count = ? WHERE account = ? AND item_id = ?", (new_count, account, item_id))
        return True

# ── Effects Methods ──────────────────────────────────────────────────────────

def get_all_effects(account: str) -> dict:
    """Return all valid (unexpired) effects for an account."""
    now = time.time()
    valid_effects = {}
    with db_transaction() as conn:
        rows = conn.execute("SELECT effect_id, value_json, expires_at FROM effects WHERE account = ?", (account,))
        for row in rows:
            effect_id = row["effect_id"]
            expires_at = row["expires_at"]
            value = json.loads(row["value_json"])

            if expires_at and now > expires_at:
                conn.execute("DELETE FROM effects WHERE account = ? AND effect_id = ?", (account, effect_id))
            else:
                valid_effects[effect_id] = value
                
    return valid_effects

def set_effect(account: str, effect_id: str, value):
    expires_at = None
    if isinstance(value, dict) and "expires" in value:
        expires_at = value.get("expires")
        
    value_json = json.dumps(value, ensure_ascii=False)
    with db_transaction() as conn:
        conn.execute("""
            INSERT INTO effects (account, effect_id, value_json, expires_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(account, effect_id) DO UPDATE SET 
                value_json = excluded.value_json,
                expires_at = excluded.expires_at
        """, (account, effect_id, value_json, expires_at))

def clear_effect(account: str, effect_id: str):
    with db_transaction() as conn:
        conn.execute("DELETE FROM effects WHERE account = ? AND effect_id = ?", (account, effect_id))

def has_effect(account: str, effect_id: str) -> bool:
    """Check if effect exists and is unexpired."""
    now = time.time()
    with db_transaction() as conn:
        cur = conn.execute("SELECT expires_at FROM effects WHERE account = ? AND effect_id = ?", (account, effect_id))
        row = cur.fetchone()
        if not row:
            return False
            
        if row["expires_at"] and now > row["expires_at"]:
            conn.execute("DELETE FROM effects WHERE account = ? AND effect_id = ?", (account, effect_id))
            return False
            
        return True

# ── Idempotency Methods ──────────────────────────────────────────────────────

def mark_reward_granted(account: str, reward_key: str, amount: int) -> bool:
    """Returns True if reward was not given before and is successfully marked. False if already received."""
    with db_transaction() as conn:
        cur = conn.execute("SELECT 1 FROM reward_registry WHERE reward_key = ?", (reward_key,))
        if cur.fetchone():
            return False # Already rewarded
        
        conn.execute(
            "INSERT INTO reward_registry (reward_key, account, amount, created_at) VALUES (?, ?, ?, ?)",
            (reward_key, account, amount, time.time())
        )
        return True

# ── Puzzle Sessions Methods ───────────────────────────────────────────────────

def get_active_puzzle_session(account: str) -> dict:
    """Returns the active puzzle session for the account, or None."""
    with db_transaction() as conn:
        cur = conn.execute(
            "SELECT * FROM puzzle_sessions WHERE account = ? AND state NOT IN ('closed', 'rewarded', 'failed', 'expired') ORDER BY created_at DESC LIMIT 1", 
            (account,)
        )
        row = cur.fetchone()
        return dict(row) if row else None

def create_puzzle_session(session_id: str, account: str, puzzle_id: str, state: str):
    now = time.time()
    with db_transaction() as conn:
        conn.execute("""
            INSERT INTO puzzle_sessions (session_id, account, puzzle_id, state, attempt_count, hint_count, reward_granted, created_at, updated_at)
            VALUES (?, ?, ?, ?, 0, 0, 0, ?, ?)
        """, (session_id, account, puzzle_id, state, now, now))

def update_puzzle_session(session_id: str, **kwargs):
    if not kwargs:
        return
    updates = []
    values = []
    for k, v in kwargs.items():
        updates.append(f"{k} = ?")
        values.append(v)
    updates.append("updated_at = ?")
    values.append(time.time())
    values.append(session_id)
    
    query = f"UPDATE puzzle_sessions SET {', '.join(updates)} WHERE session_id = ?"
    with db_transaction() as conn:
        conn.execute(query, tuple(values))



# ── Puzzle Knowledge (RAG) Methods ──────────────────────────────────────────

def init_puzzle_db(puzzles_list: list) -> None:
    with db_transaction() as conn:
        cur = conn.execute("SELECT COUNT(*) FROM puzzle_knowledge")
        if cur.fetchone()[0] == 0:
            for p in puzzles_list:
                embed_text = f"Question: {p['question']} Answer: {p['answer']}"
                conn.execute("""
                    INSERT INTO puzzle_knowledge (id, category, difficulty, question, hint, answer, key_points, aliases, embedding_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p["id"], p["category"], p.get("difficulty", "normal"), p["question"],
                    p.get("hint", ""), p["answer"], json.dumps(p.get("key_points", []), ensure_ascii=False),
                    json.dumps(p.get("aliases", []), ensure_ascii=False), embed_text
                ))
            print("Migrated PUZZLES array to puzzle_knowledge SQLite table.")

def get_puzzle_from_db(puzzle_id: str) -> dict:
    with db_transaction() as conn:
        cur = conn.execute("SELECT * FROM puzzle_knowledge WHERE id = ?", (puzzle_id,))
        row = cur.fetchone()
        if not row: return None
        res = dict(row)
        res["key_points"] = json.loads(res["key_points"])
        res["aliases"] = json.loads(res["aliases"])
        res["category_label"] = "敘事推理" if res["category"] == "narrative" else "邏輯算術" if res["category"] == "logic" else "語言諧音"
        return res

def get_all_puzzles_from_db() -> list:
    puzzles = []
    with db_transaction() as conn:
        cur = conn.execute("SELECT * FROM puzzle_knowledge")
        for row in cur:
            res = dict(row)
            res["key_points"] = json.loads(res["key_points"])
            res["aliases"] = json.loads(res["aliases"])
            res["category_label"] = "敘事推理" if res["category"] == "narrative" else "邏輯算術" if res["category"] == "logic" else "語言諧音"
            puzzles.append(res)
    return puzzles

# Initialize database upon import
_init_db()
_migrate_from_json()
