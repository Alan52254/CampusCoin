import os
import random
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
TRANSACTION_SCRIPT = BASE_DIR / "app_transaction.py"
DEFAULT_STORAGE = BASE_DIR


def main():
    storage = Path(os.environ.get("STORAGE_PATH", str(DEFAULT_STORAGE))).resolve()
    storage.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["STORAGE_PATH"] = str(storage)

    accounts = ["b1128015", "guest", "A", "B", "C"]
    seed_rows = [("angel", "b1128015", 1000)]

    for _ in range(99):
        sender = random.choice(accounts)
        receiver = random.choice([acct for acct in accounts if acct != sender])
        amount = random.randint(1, 10)
        seed_rows.append((sender, receiver, amount))

    for sender, receiver, amount in seed_rows:
        subprocess.run(
            [sys.executable, str(TRANSACTION_SCRIPT), sender, receiver, str(amount)],
            check=True,
            env=env,
        )

    print(f"Seed data generated in {storage}: {len(seed_rows)} transactions.")


if __name__ == "__main__":
    main()
