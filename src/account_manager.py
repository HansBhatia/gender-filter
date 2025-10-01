import json
import pyotp
from pathlib import Path
from typing import List, Dict, Optional
from threading import Lock
import logging

class AccountManager:
    """Manages multiple Instagram accounts with OTP and proxy assignments."""

    def __init__(self, accounts_file: str = "accounts.json"):
        self.accounts_file = accounts_file
        self.accounts: List[Dict] = []
        self.current_index = 0
        self.lock = Lock()
        self.logger = logging.getLogger(__name__)

        self._load_accounts()

    def _load_accounts(self):
        """Load accounts from JSON file."""
        accounts_path = Path(self.accounts_file)

        if not accounts_path.exists():
            self.logger.error(f"Accounts file not found: {self.accounts_file}")
            self.logger.info("Please create accounts.json based on accounts.example.json")
            raise FileNotFoundError(f"Accounts file not found: {self.accounts_file}")

        with open(accounts_path, 'r') as f:
            self.accounts = json.load(f)

        if not self.accounts:
            raise ValueError("No accounts found in accounts.json")

        self.logger.info(f"Loaded {len(self.accounts)} Instagram accounts")

    def get_otp(self, otp_seed: str) -> str:
        """Generate OTP code from seed."""
        totp = pyotp.TOTP(otp_seed)
        return totp.now()

    def get_next_account(self) -> Dict:
        """Get next account in round-robin fashion."""
        with self.lock:
            account = self.accounts[self.current_index].copy()
            self.current_index = (self.current_index + 1) % len(self.accounts)

            # Generate current OTP
            if account.get('otp_seed'):
                account['otp'] = self.get_otp(account['otp_seed'])

            return account

    def get_account_by_index(self, index: int) -> Dict:
        """Get specific account by index."""
        if index < 0 or index >= len(self.accounts):
            raise IndexError(f"Account index {index} out of range")

        account = self.accounts[index].copy()

        # Generate current OTP
        if account.get('otp_seed'):
            account['otp'] = self.get_otp(account['otp_seed'])

        return account

    def get_all_accounts(self) -> List[Dict]:
        """Get all accounts with current OTPs."""
        accounts = []
        for account in self.accounts:
            acc = account.copy()
            if acc.get('otp_seed'):
                acc['otp'] = self.get_otp(acc['otp_seed'])
            accounts.append(acc)
        return accounts

    def count(self) -> int:
        """Return number of accounts."""
        return len(self.accounts)