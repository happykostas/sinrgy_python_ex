from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional
from statistics import median
import os


DEBUG = os.environ.get("DEBUG") == "1"


def debug_log(message: str):
    if DEBUG:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[DEBUG {timestamp}] {message}")


class BankAccount(ABC):
    _account_counter = 1000

    def __init__(self, owner: str, initial_balance: float = 0):
        self.account_number = f"ACC{BankAccount._account_counter}"
        BankAccount._account_counter += 1
        self.balance = initial_balance
        self.owner = owner
        self.transaction_history: List[Dict] = []

        debug_log(
            f"Creating account {self.account_number} for {owner} with balance {initial_balance}"
        )

        if initial_balance > 0:
            self.transaction_history.append(
                {
                    "date": datetime.now(),
                    "type": "opening",
                    "amount": initial_balance,
                    "balance_after": initial_balance,
                }
            )

    def deposit(self, amount: float) -> bool:
        debug_log(f"Account {self.account_number}: attempting deposit of {amount}")
        if amount <= 0:
            debug_log(f"Account {self.account_number}: deposit failed - invalid amount")
            return False
        self.balance += amount
        self.transaction_history.append(
            {
                "date": datetime.now(),
                "type": "deposit",
                "amount": amount,
                "balance_after": self.balance,
            }
        )
        debug_log(
            f"Account {self.account_number}: deposit successful, new balance: {self.balance}"
        )
        return True

    def withdraw(self, amount: float) -> bool:
        withdrawal_limit = self.get_withdrawal_limit()
        debug_log(
            f"Account {self.account_number}: attempting withdrawal of {amount}, limit: {withdrawal_limit}"
        )

        if amount <= 0:
            debug_log(
                f"Account {self.account_number}: withdrawal failed - invalid amount"
            )
            return False
        if amount > withdrawal_limit:
            debug_log(
                f"Account {self.account_number}: withdrawal failed - exceeds limit"
            )
            return False
        self.balance -= amount
        self.transaction_history.append(
            {
                "date": datetime.now(),
                "type": "withdrawal",
                "amount": amount,
                "balance_after": self.balance,
            }
        )
        debug_log(
            f"Account {self.account_number}: withdrawal successful, new balance: {self.balance}"
        )
        return True

    @abstractmethod
    def get_withdrawal_limit(self) -> float:
        pass

    @classmethod
    def create_account(cls, owner: str, initial_balance: float = 0, **kwargs):
        debug_log(f"Creating account via class method for {owner}")
        return cls(owner, initial_balance, **kwargs)


class Card:
    def __init__(self, number: str, card_type: str):
        self.number = number
        self.card_type = card_type
        debug_log(f"Card created: {number} ({card_type})")


class CurrentAccount(BankAccount):
    def __init__(self, owner: str, initial_balance: float = 0, **kwargs):
        super().__init__(owner, initial_balance)
        self.daily_limit = 50000
        self.linked_cards: List[Card] = []
        debug_log(f"CurrentAccount initialized with daily limit: {self.daily_limit}")

    def get_withdrawal_limit(self) -> float:
        return min(self.balance, self.daily_limit)

    def add_card(self, card: Card):
        self.linked_cards.append(card)
        debug_log(f"Card {card.number} linked to account {self.account_number}")


class SavingsAccount(BankAccount):
    def __init__(self, owner: str, initial_balance: float = 0, **kwargs):
        super().__init__(owner, initial_balance)
        self.monthly_limit = 100000
        debug_log(
            f"SavingsAccount initialized with monthly limit: {self.monthly_limit}"
        )

    def get_withdrawal_limit(self) -> float:
        return min(self.balance, self.monthly_limit)

    def accrue_interest(self, rate: float):
        debug_log(f"Account {self.account_number}: accruing interest at rate {rate}%")
        interest = self.balance * rate / 100
        self.deposit(interest)
        debug_log(f"Account {self.account_number}: interest accrued: {interest}")


class CreditAccount(BankAccount):
    def __init__(
        self,
        owner: str,
        initial_balance: float = 0,
        credit_limit: float = 10000,
        **kwargs,
    ):
        super().__init__(owner, initial_balance)
        self.credit_limit = credit_limit
        debug_log(f"CreditAccount initialized with credit limit: {credit_limit}")

    def get_withdrawal_limit(self) -> float:
        return self.credit_limit + self.balance


class Client:
    def __init__(self, name: str):
        self.name = name
        self.accounts: Dict[str, List[BankAccount]] = {
            "current": [],
            "savings": [],
            "credit": [],
        }
        debug_log(f"Client created: {name}")

    def open_account(self, account_type: str, **kwargs) -> Optional[BankAccount]:
        debug_log(f"Client {self.name}: opening {account_type} account")

        account_types = {
            "current": CurrentAccount,
            "savings": SavingsAccount,
            "credit": CreditAccount,
        }

        if account_type not in account_types:
            debug_log(f"Client {self.name}: invalid account type {account_type}")
            return None

        account = account_types[account_type].create_account(self.name, **kwargs)
        self.accounts[account_type].append(account)
        debug_log(
            f"Client {self.name}: account {account.account_number} opened successfully"
        )
        return account

    def get_total_balance(self) -> float:
        total = sum(
            account.balance
            for accounts_list in self.accounts.values()
            for account in accounts_list
        )
        debug_log(f"Client {self.name}: total balance calculated: {total}")
        return total

    def find_accounts_by_type(self, account_type: str) -> List[BankAccount]:
        accounts = self.accounts.get(account_type, [])
        debug_log(
            f"Client {self.name}: found {len(accounts)} accounts of type {account_type}"
        )
        return accounts


class BankAnalytics:
    @staticmethod
    def calculate_median_balance(accounts: List[BankAccount]) -> float:
        debug_log(f"Calculating median balance for {len(accounts)} accounts")
        if not accounts:
            return 0.0
        balances = [account.balance for account in accounts]
        result = median(balances)
        debug_log(f"Median balance: {result}")
        return result

    @staticmethod
    def find_large_transactions(account: BankAccount, threshold: float) -> List[Dict]:
        debug_log(
            f"Searching for transactions >= {threshold} in account {account.account_number}"
        )
        large_transactions = [
            transaction
            for transaction in account.transaction_history
            if transaction["amount"] >= threshold
        ]
        debug_log(f"Found {len(large_transactions)} large transactions")
        return large_transactions

    @classmethod
    def generate_report(cls, client: Client) -> str:
        debug_log(f"Generating report for client {client.name}")

        report = f"=== REPORT FOR CLIENT: {client.name} ===\n\n"

        for account_type, accounts in client.accounts.items():
            if accounts:
                report += f"{account_type.upper()} ACCOUNTS:\n"
                for account in accounts:
                    report += f"  {account.account_number}: ${account.balance:.2f}\n"
                report += "\n"

        report += f"TOTAL BALANCE: ${client.get_total_balance():.2f}\n"

        all_accounts = [
            account for accounts in client.accounts.values() for account in accounts
        ]
        if all_accounts:
            median_balance = cls.calculate_median_balance(all_accounts)
            report += f"MEDIAN BALANCE: ${median_balance:.2f}\n"

        debug_log(f"Report generated for client {client.name}")
        return report


if __name__ == "__main__":
    debug_log("===================== START =====================")

    client = Client("John Smith")

    current = client.open_account("current", initial_balance=50000)
    savings = client.open_account("savings", initial_balance=200000)
    credit = client.open_account("credit", initial_balance=0, credit_limit=50000)

    card = Card("1234-5678-9012-3456", "Visa")
    current.add_card(card)

    current.deposit(10000)
    current.withdraw(15000)
    savings.accrue_interest(5)
    credit.withdraw(20000)

    print(BankAnalytics.generate_report(client))

    large_transactions = BankAnalytics.find_large_transactions(current, 10000)
    print(f"\nLarge transactions: {len(large_transactions)}")

    debug_log("===================== END =====================")
