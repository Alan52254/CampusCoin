import sys

from ledger_core import get_account_log


def main():
    account = sys.argv[1] if len(sys.argv) > 1 else "b1128015"
    print(f"=== Transaction Log for {account} ===")
    rows = get_account_log(account)
    if not rows:
        print("No transactions found.")
        return

    for block_index, sender, receiver, amount in rows:
        print(f"Block #{block_index}: {sender}, {receiver}, {amount}")


if __name__ == "__main__":
    main()
