import random
from collections import Counter

# Use the direct ledger_core API for much faster and cleaner execution
from shared_storage.ledger_core import append_transaction, verify_chain

# ── Config ────────────────────────────────────────────────────────────────────
# PDF spec: 100 tx / 20 blocks (5 tx per block)
BLOCK_SIZE   = 5     # must match ledger_core's BLOCK_SIZE
TOTAL_BLOCKS = 20    # PDF spec: 20 blocks
TOTAL_TX     = BLOCK_SIZE * TOTAL_BLOCKS  # = 100

ACCOUNTS = ["b1128015", "guest", "A", "B", "C"]

# ── Build transaction list ─────────────────────────────────────────────────────
def build_seed_rows(total: int) -> list[tuple[str, str, int]]:
    # First tx: fund the main demo account
    rows = [("angel", "b1128015", 1000)]

    for _ in range(total - 1):
        sender   = random.choice(ACCOUNTS)
        receiver = random.choice([a for a in ACCOUNTS if a != sender])
        amount   = random.randint(1, 10)
        rows.append((sender, receiver, amount))

    return rows

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    seed_rows = build_seed_rows(TOTAL_TX)
    print(f"Generating {len(seed_rows)} transactions ({TOTAL_BLOCKS} blocks × {BLOCK_SIZE} tx)…")

    tx_counter: Counter = Counter()
    for sender, receiver, amount in seed_rows:
        append_transaction(sender, receiver, amount)
        tx_counter[sender] += 1

    print(f"Transactions committed: {sum(tx_counter.values())}")

    issues = verify_chain()
    if issues:
        print("WARNING - verify_chain found issues:")
        for issue in issues:
            print("   -", issue)
    else:
        print(f"Seed completed successfully -- {TOTAL_TX} transactions, {TOTAL_BLOCKS} blocks expected.")

if __name__ == "__main__":
    main()
