"""Console bank: create an account, log in, and move (pretend) money around.

Data is saved to bank_data.json next to this file. Passwords are salted + hashed (PBKDF2).
"""
from __future__ import annotations

import getpass
import sys
from datetime import datetime
from pathlib import Path

from bank_core import Bank, BankError, naira

DATA_FILE = Path(__file__).with_name("bank_data.json")


def ask_password(prompt: str) -> str:
    # getpass hides typing in a real terminal; fall back to input() when piped.
    return getpass.getpass(prompt) if sys.stdin.isatty() else input(prompt)


def sign_up(bank: Bank) -> None:
    print("\n— Create an account —")
    username = input("Choose a username: ")
    password = ask_password("Choose a password: ")
    confirm = ask_password("Confirm your password: ")
    try:
        bank.create_account(username, password, confirm)
        print("Account created. You can log in now.")
    except BankError as e:
        print(f"⚠ {e}")


def dashboard(bank: Bank, acct) -> None:
    print(f"\nWelcome back, {acct.username}.")
    while True:
        print(f"\nBalance: {naira(acct.balance)}")
        print("[1] Deposit  [2] Withdraw  [3] Transfer  [4] History  [5] Log out")
        choice = input("> ").strip()
        try:
            if choice == "1":
                bank.deposit(acct, input("Amount to deposit: ₦"))
                print("Deposited.")
            elif choice == "2":
                bank.withdraw(acct, input("Amount to withdraw: ₦"))
                print("Withdrawn.")
            elif choice == "3":
                to = input("Send to (username): ")
                bank.transfer(acct, to, input("Amount: ₦"))
                print("Sent.")
            elif choice == "4":
                for h in acct.history[-10:]:
                    when = datetime.fromtimestamp(h["t"]).strftime("%d %b %H:%M")
                    print(f"  {when}  {h['kind']:<12} {naira(h['amount']):>14}  → {naira(h['balance'])} {h.get('note', '')}")
            elif choice in {"5", "q"}:
                print("Logged out.")
                return
            else:
                print("Pick 1–5.")
        except BankError as e:
            print(f"⚠ {e}")


def main() -> None:
    bank = Bank(DATA_FILE)
    print("CONSOLE BANK  (practice project, not real money)")
    while True:
        print("\n[1] Log in  [2] Create account  [3] Quit")
        choice = input("> ").strip()
        if choice == "1":
            try:
                acct = bank.login(input("Username: "), ask_password("Password: "))
                dashboard(bank, acct)
            except BankError as e:
                print(f"⚠ {e}")
        elif choice == "2":
            sign_up(bank)
        elif choice in {"3", "q", "quit"}:
            print("Goodbye.")
            return
        else:
            print("Pick 1, 2, or 3.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye.")
