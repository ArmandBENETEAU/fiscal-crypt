"""
File containing the CoinbaseInterface class

.. moduleauthor:: Armand BENETEAU <armand.beneteau@iot.bzh>

*Date: 24/04/2021*

*License:*
    Copyright (C) 2021 Armand Bénéteau

    This file is part of the Fiscal Crypt project.

    GNU General Public License Usage
    This file may be used under the terms of the GNU General \
    Public license version 3. This license is as published by the Free Software \
    Foundation and appearing in the file LICENSE included in the packaging \
    of this file. Please review the following information to ensure the GNU \
    General Public License requirements will be met \
    https://www.gnu.org/licenses/gpl-3.0.html.
"""

from abc import abstractmethod
import datetime
import re

from decimal import *
from dateutil.parser import isoparse

from coinbase.wallet.client import Client
from fiscal_crypt.price_finder.coinbasepro_finder import CoinbaseProFinder
from fiscal_crypt.platforms.abs_platforms import PlatformInterface
from fiscal_crypt.fcrypt_logging import fcrypt_log


class CoinbaseInterface(PlatformInterface):
    """
    Class implementing all the methods allowing to calculate the differents
    overall values of accounts at given times. It allows also to enumerate
    all the transactions that can be impacted by taxes
    """

    def __init__(self, api_key: str, api_secret: str) -> None:
        # Call the upper class initialization
        super().__init__()

        # Create the Coinbase authenticated client that we will use
        self.api_client = Client(api_key, api_secret)

        # Initialize what will be used next
        self.accounts = []
        self.transactions = []

        # Initialize the price finder
        self.price_finder = CoinbaseProFinder()

        # Load all accounts and transactions
        self._load_all_accounts()
        self._load_all_transactions()

    @staticmethod
    def _extract_account_id(path: str) -> str:
        """
        Function allowing to extract an account UUID from a "resource_path" given
        for each transaction done on Coinbase.
        """
        items = path.split("/")

        # Check that the path look like we want
        if items[2] != "accounts":
            raise ValueError("It looks like the resource path is not like we want...")

        # Return the account id
        return items[3]

    def _load_all_accounts(self):
        """
        This function allows to load every account that the user has on Coinbase
        These accounts will be used to calculate the taxes, 'in fine'.
        Only the accounts with an real UUID are taken into account
        """
        # Get all accounts
        tmp_accounts_list = self.api_client.get_accounts()

        # Print all used accounts
        for account in tmp_accounts_list['data']:

            # If the ID is a valid UUID, save the account and print it in DEBUG logs
            match = re.search(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", account['id'])
            if match:
                # Get the various values
                id = account['id']
                name = account['name']
                crypto_balance = account['balance']['amount']
                crypto_currency = account['currency']
                native_balance = account['native_balance']['amount']
                native_currency = account['native_balance']['currency']

                # Debug print
                fcrypt_log.debug(
                    f"Adding account: {id} ==> {name}: {crypto_balance} {crypto_currency}" +
                    f" ({native_balance} {native_currency})")

                # Add the account in our list
                self.accounts.append(account)

    def _load_all_transactions(self):
        """
        This function allows to load every transaction that the user has done on Coinbase
        These transactions, in fine, will allow us to go back in time in the account, to know
        what was on each account, at a given time
        """
        # Get all transactions
        for account in self.accounts:
            # Get the transactions for this account
            tmp_transactions = self.api_client.get_transactions(account['id'])

            # Print the transactions
            for transaction in tmp_transactions['data']:
                # print(transaction)
                amount = transaction['amount']['amount']
                currency = transaction['amount']['currency']
                date = transaction['updated_at']
                if not str.startswith(amount, "-"):
                    amount = "+" + amount
                account = self._extract_account_id(transaction['resource_path'])
                fcrypt_log.debug(f"[TRANSACTION] {date}: {amount} {currency} ==> {account}")

            self.transactions.extend(tmp_transactions['data'])

    def get_wallet_balance_at(self, currency: str, time: datetime.datetime) -> Decimal:
        """
        This function allows to get the balance of a wallet at a given time.

        :param currency: Currency we want the value for
        :type currency: str
        :param time: Time where the value is wanted
        :type time: datetime.datetime
        """
        # Firstly, get the corresponding account ID
        account_id = ""
        for account in self.accounts:
            if ('currency' in account) and (account['currency'] == currency):
                account_id = account['id']
                current_balance = Decimal(account['balance']['amount'])

        if account_id == "":
            raise ValueError("No account found for this currency")

        # Then apply every transaction in reverse if the datetime of this transaction
        # is posterior to the wanted datetime
        for transaction in self.transactions:
            # Extract account ID
            tmp_account_id = self._extract_account_id(transaction['resource_path'])
            # Check if the account ids correspond
            if (tmp_account_id == account_id) and transaction['status'] == 'completed':
                # Extract the datetime
                operation_datetime = isoparse(transaction['updated_at'])
                # If datetime posterior or equal to the time given by user, reverse it
                if operation_datetime >= time:
                    trans_amount = Decimal(transaction['amount']['amount'])
                    tmp_balance = current_balance - trans_amount
                    fcrypt_log.debug(f"[REVERSED TRANSACTION] {trans_amount} {currency} ==> {account_id}")
                    fcrypt_log.debug(
                        f"[REVERSED TRANSACTION] Operation {current_balance}-{trans_amount} = {tmp_balance}")
                    current_balance = tmp_balance

        return current_balance

    def get_wallet_value_at(self, crypto_currency: str, fiat_currency: str, time: datetime.datetime) -> Decimal:
        """
        This function allows to get the value of a wallet at a given time.

        :param crypto_currency: Crypto currency of the wallet
        :type crypto_currency: str
        :param fiat_currency: Fiat currency for the result (EUR, USD, etc.)
        :type fiat_currency: str
        :param time: Time where the value is wanted
        :type time: datetime.datetime
        """
        # Firstly, get the wallet balance at the given time
        balance = self.get_wallet_balance_at(crypto_currency, time)

        time_str = str(time)
        normal_balance = str(balance.normalize())
        fcrypt_log.info(f"[WALLET] Balance at {time_str}: {normal_balance} {crypto_currency}")

        # Now get the equivalent value in fiat
        rate_currency = crypto_currency + "-" + fiat_currency
        wallet_value = self.price_finder.get_rate_of(rate_currency, time) * balance

        return wallet_value

    def get_all_wallets_value(self, currency: str, time: datetime.datetime):
        """
        This function allows to get the value of all the crypto-wallets of
        a user at a given time

        :param currency: Fiat currency we want for the value (ISO 4217)
        :type currency: str
        :param time: Time where the value is wanted
        :type time: datetime.datetime
        """
        pass
