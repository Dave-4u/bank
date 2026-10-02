"""Core logic for the console bank. No input()/print() here, so it's easy to test."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field, asdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

PBKDF2_ROUNDS = 120_000
MIN_PASSWORD = 6


class BankError(Exception):
    """A friendly, user-facing error."""


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ROUNDS).hex()
    return salt, digest


def parse_amount(raw: str | float | int) -> int:
    """Turn '1,500.50' into kobo (150050). Raises BankError for bad input."""
    try:
        value = Decimal(str(raw).replace(",", "").replace("₦", "").strip())
    except InvalidOperation:
        raise BankError("That doesn't look like an amount.") from None
    if value <= 0:
        raise BankError("Amount must be more than zero.")
    if value != value.quantize(Decimal("0.01")):
        raise BankError("Use at most two decimal places.")
    return int(value * 100)


def naira(kobo: int) -> str:
    return f"₦{kobo / 100:,.2f}"


@dataclass
class Account:
    username: str
    salt: str
    pw_hash: str
    balance: int = 0  # stored in kobo to avoid float rounding
    history: list = field(default_factory=list)

    def log(self, kind: str, amount: int, note: str = "") -> None:
        self.history.append({"t": int(time.time()), "kind": kind, "amount": amount, "balance": self.balance, "note": note})


class Bank:
    def __init__(self, path: str | os.PathLike | None = None):
        self.path = Path(path) if path else None
        self.accounts: dict[str, Account] = {}
        if self.path and self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.accounts = {u: Account(**a) for u, a in raw.get("accounts", {}).items()}

    def save(self) -> None:
        if not self.path:
            return
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"accounts": {u: asdict(a) for u, a in self.accounts.items()}}, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    @staticmethod
    def _clean(username: str) -> str:
        u = username.strip().lower()
        if not (3 <= len(u) <= 20) or not u.replace("_", "").isalnum():
            raise BankError("Usernames are 3–20 letters, numbers, or underscores.")
        return u

    def create_account(self, username: str, password: str, confirm: str) -> Account:
        u = self._clean(username)
        if u in self.accounts:
            raise BankError("That username is taken. Try another one.")
        if len(password) < MIN_PASSWORD:
            raise BankError(f"Passwords need at least {MIN_PASSWORD} characters.")
        if password != confirm:
            raise BankError("Password and confirmation don't match. Please try again.")
        salt, digest = hash_password(password)
        acct = Account(u, salt, digest)
        acct.log("open", 0, "Account opened")
        self.accounts[u] = acct
        self.save()
        return acct

    def login(self, username: str, password: str) -> Account:
        acct = self.accounts.get(username.strip().lower())
        # Same message either way so we don't reveal which usernames exist.
        if not acct or not hmac.compare_digest(hash_password(password, acct.salt)[1], acct.pw_hash):
            raise BankError("Incorrect username or password.")
        return acct

    def deposit(self, acct: Account, amount) -> int:
        k = parse_amount(amount)
        acct.balance += k
        acct.log("deposit", k)
        self.save()
        return acct.balance

    def withdraw(self, acct: Account, amount) -> int:
        k = parse_amount(amount)
        if k > acct.balance:
            raise BankError(f"Not enough money. Your balance is {naira(acct.balance)}.")
        acct.balance -= k
        acct.log("withdraw", k)
        self.save()
        return acct.balance

    def transfer(self, acct: Account, to_username: str, amount) -> int:
        target = self.accounts.get(to_username.strip().lower())
        if not target:
            raise BankError("No account with that username.")
        if target is acct:
            raise BankError("You can't send money to yourself.")
        k = parse_amount(amount)
        if k > acct.balance:
            raise BankError(f"Not enough money. Your balance is {naira(acct.balance)}.")
        acct.balance -= k
        target.balance += k
        acct.log("transfer_out", k, f"to @{target.username}")
        target.log("transfer_in", k, f"from @{acct.username}")
        self.save()
        return acct.balance
