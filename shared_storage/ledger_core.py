import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path


BLOCK_HEADER_PREFIX = "Sha256 of previous block: "
NEXT_HEADER_PREFIX = "Next block: "
GENESIS_HASH = "0" * 64
BLOCK_SIZE = 5


def get_storage_path() -> Path:
    configured = os.environ.get("STORAGE_PATH")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parent


STORAGE = get_storage_path()
LOCK_PATH = STORAGE / ".ledger.lock"


def ensure_storage() -> None:
    STORAGE.mkdir(parents=True, exist_ok=True)


def block_path(index: int) -> Path:
    return STORAGE / f"{index}.txt"


def iter_block_paths():
    index = 1
    while block_path(index).exists():
        yield index, block_path(index)
        index += 1


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_block_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def parse_metadata(path: Path) -> tuple[str, str]:
    lines = read_block_lines(path)
    prev_hash = ""
    next_block = "None"
    if lines and lines[0].startswith(BLOCK_HEADER_PREFIX):
        prev_hash = lines[0][len(BLOCK_HEADER_PREFIX):].strip()
    if len(lines) > 1 and lines[1].startswith(NEXT_HEADER_PREFIX):
        next_block = lines[1][len(NEXT_HEADER_PREFIX):].strip()
    return prev_hash, next_block


def parse_transaction_line(line: str):
    stripped = line.strip()
    if not stripped or stripped.startswith(BLOCK_HEADER_PREFIX) or stripped.startswith(NEXT_HEADER_PREFIX):
        return None

    parts = [part.strip() for part in stripped.split(",")]
    if len(parts) != 3:
        return None

    sender, receiver, amount_text = parts
    try:
        amount = int(amount_text)
    except ValueError:
        return None
    return sender, receiver, amount


def get_transactions(path: Path) -> list[tuple[str, str, int]]:
    txs = []
    for line in read_block_lines(path):
        parsed = parse_transaction_line(line)
        if parsed:
            txs.append(parsed)
    return txs


def last_block_index() -> int:
    last = 0
    for last, _ in iter_block_paths():
        pass
    return last


def initialize_genesis_if_needed() -> Path:
    ensure_storage()
    genesis = block_path(1)
    if not genesis.exists():
        genesis.write_text(
            f"{BLOCK_HEADER_PREFIX}{GENESIS_HASH}\n{NEXT_HEADER_PREFIX}None\n",
            encoding="utf-8",
        )
    return genesis


def get_or_create_active_block() -> tuple[int, Path]:
    initialize_genesis_if_needed()
    active_index = last_block_index()
    active_path = block_path(active_index)
    txs = get_transactions(active_path)

    if len(txs) < BLOCK_SIZE:
        return active_index, active_path

    old_lines = read_block_lines(active_path)
    if len(old_lines) < 2:
        old_lines = [f"{BLOCK_HEADER_PREFIX}{GENESIS_HASH}", f"{NEXT_HEADER_PREFIX}None"]
    new_index = active_index + 1
    new_path = block_path(new_index)
    old_lines[1] = f"{NEXT_HEADER_PREFIX}{new_index}.txt"
    active_path.write_text("\n".join(old_lines) + "\n", encoding="utf-8")

    prev_hash = sha256_file(active_path)
    new_path.write_text(
        f"{BLOCK_HEADER_PREFIX}{prev_hash}\n{NEXT_HEADER_PREFIX}None\n",
        encoding="utf-8",
    )
    return new_index, new_path


def append_transaction(sender: str, receiver: str, amount: int) -> tuple[int, Path]:
    if amount <= 0:
        raise ValueError("Amount must be a positive integer.")
    if sender == receiver:
        raise ValueError("Sender and receiver must be different accounts.")

    index, path = get_or_create_active_block()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{sender}, {receiver}, {amount}\n")
    return index, path


def get_account_stats(account: str) -> dict:
    """一次掃描所有區塊，同時取得餘額與交易記錄，避免重複 I/O。"""
    balance = 0
    rows: list[tuple[int, str, str, int]] = []
    for index, path in iter_block_paths():
        for sender, receiver, amount in get_transactions(path):
            if receiver == account:
                balance += amount
                rows.append((index, sender, receiver, amount))
            elif sender == account:
                balance -= amount
                rows.append((index, sender, receiver, amount))
    return {"balance": balance, "log": rows}


def get_balance(account: str) -> int:
    return get_account_stats(account)["balance"]


def get_account_log(account: str) -> list[tuple[int, str, str, int]]:
    return get_account_stats(account)["log"]


def verify_chain() -> list[str]:
    issues = []
    previous_path = None

    for index, path in iter_block_paths():
        prev_hash, next_block = parse_metadata(path)

        if index == 1:
            if prev_hash != GENESIS_HASH:
                issues.append(f"Block 1 previous hash should be {GENESIS_HASH}.")
        elif previous_path is not None:
            actual_hash = sha256_file(previous_path)
            if prev_hash != actual_hash:
                issues.append(
                    f"Block {index} previous hash mismatch: expected {actual_hash}, found {prev_hash}."
                )

        expected_next = f"{index + 1}.txt" if block_path(index + 1).exists() else "None"
        if next_block != expected_next:
            issues.append(
                f"Block {index} next pointer mismatch: expected {expected_next}, found {next_block}."
            )

        previous_path = path

    return issues


# ── 帳號密碼管理 ──────────────────────────────────────────────────────────────

def _accounts_path() -> Path:
    return STORAGE / "accounts.json"


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def load_accounts() -> dict:
    path = _accounts_path()
    if not path.exists():
        # 預設帳號（密碼明文：password）
        defaults = {
            "b1128015": _hash_password("password"),
            "guest":    _hash_password("password"),
            "angel":    _hash_password("angel"),
        }
        path.write_text(json.dumps(defaults, indent=2), encoding="utf-8")
        return defaults
    return json.loads(path.read_text(encoding="utf-8"))


def verify_account(account: str, password: str) -> bool:
    """回傳 True 表示帳號密碼正確。"""
    accounts = load_accounts()
    hashed = accounts.get(account)
    if hashed is None:
        return False
    return hashed == _hash_password(password)


def register_account(account: str, password: str) -> bool:
    """新增帳號，若帳號已存在回傳 False。"""
    accounts = load_accounts()
    if account in accounts:
        return False
    accounts[account] = _hash_password(password)
    _accounts_path().write_text(json.dumps(accounts, indent=2), encoding="utf-8")
    return True


@contextmanager
def ledger_lock():
    ensure_storage()
    lock_handle = LOCK_PATH.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(lock_handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        if os.name == "nt":
            import msvcrt

            lock_handle.seek(0)
            msvcrt.locking(lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        lock_handle.close()
