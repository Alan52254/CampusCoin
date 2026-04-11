import sys

from ledger_core import get_balance


def main():
    account = sys.argv[1] if len(sys.argv) > 1 else "b1128015"
    print(f"Account: {account} | Balance: {get_balance(account)} CPC")


if __name__ == "__main__":
    main()
