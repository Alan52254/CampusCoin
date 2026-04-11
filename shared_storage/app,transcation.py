import sys

from ledger_core import append_transaction, ledger_lock


def main():
    if len(sys.argv) != 4:
        print("Usage: python app_transaction.py <sender> <receiver> <amount>")
        raise SystemExit(1)

    sender, receiver, amount_text = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        amount = int(amount_text)
    except ValueError:
        print("Amount must be an integer.")
        raise SystemExit(1)

    try:
        with ledger_lock():
            block_index, _ = append_transaction(sender, receiver, amount)
    except ValueError as exc:
        print(str(exc))
        raise SystemExit(1)

    print(f"OK: {sender} -> {receiver} ({amount}) in Block #{block_index}")


if __name__ == "__main__":
    main()
