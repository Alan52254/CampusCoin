import sys

from ledger_core import append_transaction, ledger_lock, verify_chain


def main():
    account = sys.argv[1] if len(sys.argv) > 1 else None
    issues = verify_chain()

    if issues:
        print("CHAIN ERROR")
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(1)

    print("OK")
    if account:
        with ledger_lock():
            block_index, _ = append_transaction("angel", account, 10)
        print(f"Rewarded {account} with 10 CPC in Block #{block_index}")


if __name__ == "__main__":
    main()
