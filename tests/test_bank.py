import tempfile
import unittest
from pathlib import Path

from bank_core import Bank, BankError, parse_amount, naira


class BankTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "data.json"
        self.bank = Bank(self.path)
        self.ada = self.bank.create_account("Ada", "secret1", "secret1")
        self.tobi = self.bank.create_account("tobi", "secret2", "secret2")

    def tearDown(self):
        self.dir.cleanup()

    def test_signup_rules(self):
        with self.assertRaises(BankError):
            self.bank.create_account("ada", "whatever", "whatever")  # taken (case-insensitive)
        with self.assertRaises(BankError):
            self.bank.create_account("newbie", "abc", "abc")  # too short
        with self.assertRaises(BankError):
            self.bank.create_account("newbie", "secret1", "secret2")  # mismatch

    def test_password_is_hashed_and_login_works(self):
        self.assertNotIn("secret1", self.path.read_text())
        self.assertIs(self.bank.login(" ADA ", "secret1"), self.ada)
        with self.assertRaises(BankError):
            self.bank.login("ada", "wrong")
        with self.assertRaises(BankError):
            self.bank.login("nobody", "secret1")

    def test_money_moves(self):
        self.bank.deposit(self.ada, "10,000")
        self.bank.withdraw(self.ada, 2500.50)
        self.bank.transfer(self.ada, "tobi", "1000")
        self.assertEqual(naira(self.ada.balance), "₦6,499.50")
        self.assertEqual(self.tobi.balance, 100000)
        with self.assertRaises(BankError):
            self.bank.withdraw(self.ada, "999999")
        with self.assertRaises(BankError):
            self.bank.transfer(self.ada, "ada", "1")

    def test_persistence(self):
        self.bank.deposit(self.ada, "500")
        again = Bank(self.path)
        self.assertEqual(again.login("ada", "secret1").balance, 50000)

    def test_parse_amount(self):
        self.assertEqual(parse_amount("₦1,500.25"), 150025)
        for bad in ["0", "-5", "abc", "1.005"]:
            with self.assertRaises(BankError):
                parse_amount(bad)


if __name__ == "__main__":
    unittest.main()
