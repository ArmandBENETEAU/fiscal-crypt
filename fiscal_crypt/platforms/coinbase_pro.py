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
import cbpro
import datetime
import re

from decimal import *
from dateutil.parser import isoparse

import urllib.parse as urlparse
from urllib.parse import parse_qs

from fiscal_crypt.price_finder.abs_price_finder import PriceFinder
from fiscal_crypt.platforms.abs_platforms import PlatformInterface
from fiscal_crypt.fcrypt_logging import fcrypt_log


class CoinbaseProInterface(PlatformInterface):
    """
    Class implementing all the methods allowing to calculate the differents
    overall values of accounts at given times. It allows also to enumerate
    all the transactions that can be impacted by taxes
    """

    def __init__(self, api_key: str, api_secret: str, api_passphrase: str, price_finder: PriceFinder) -> None:
        # Call the upper class initialization
        super().__init__()

        # Create the Coinbase Pro authenticated client that we will use
        self.api_client = cbpro.AuthenticatedClient(api_key, api_secret, api_passphrase)

        # Initialize what will be used next
        self.accounts = []
        self.transactions = []

        # Initialize the price finder
        self.price_finder = price_finder

        # Load all accounts and transactions
        fcrypt_log.info("[INITIALIZATION] Loading all accounts...")
        self._load_all_accounts()
        fcrypt_log.info("[INITIALIZATION] Loading all transactions...")
        self._load_all_transactions()

    @staticmethod
    def _extract_account_id(path: str) -> str:
        """
        Function allowing to extract an account UUID from a "resource_path" given
        for each transaction done on Coinbase.
        :param path: "resource_path" to extract the account id from
        :type path: str
        :returns: str -- The account id
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

        # Get the list of accounts (not paginated for coinbase pro)
        accounts_list = self.api_client.get_accounts()

        # Save all used accounts
        for account in accounts_list:

            # If the ID is a valid UUID, save the account and print it in DEBUG logs
            match = re.search(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", account['id'])
            if match:
                # Get the various values
                id = account['id']
                name = "Account in " + account['currency']
                crypto_balance = account['available']
                crypto_currency = account['currency']

                # Debug print
                fcrypt_log.debug(f"Adding account: {id} ==> {name}: {crypto_balance} {crypto_currency}")

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

            # Get all account history for the current account
            history_gen = self.api_client.get_account_history(account['id'])
            movements_list = list(history_gen)

            # Print and take into account the transactions
            for movement in movements_list:
                movement_type = movement.get("type", "[NOT KNOWN]")
                amount = movement.get("amount", "[NOT KNOWN]")
                balance = movement.get("balance", "[NOT KNOWN]")
                details = movement.get("details", "[NOT KNOWN]")
                date = movement.get("created_at", "[NOT KNOWN]")

                if not str.startswith(amount, "-"):
                    amount = "+" + amount

                # fcrypt_log.debug(f"[TRANSACTION] {date}: {amount} {currency} ==> {account}")
                fcrypt_log.debug(
                    f"[TRANSACTION] {movement_type} | {date}: {amount} {account['currency']} ==> {account['id']}")
                fcrypt_log.debug(f"              Balance: {balance} {account['currency']}")
                fcrypt_log.debug(f"              Details: {details}")

            self.transactions.extend(movements_list)

    def get_wallet_balance_at(self, currency: str, time: datetime.datetime) -> Decimal:
        """
        This function allows to get the balance of a wallet at a given time.

        :param currency: Currency we want the value for
        :type currency: str
        :param time: Time where the value is wanted
        :type time: datetime.datetime
        :returns: Decimal -- The wallet balance at the given time
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
        :returns: Decimal -- The wallet value at the given time
        """
        # Firstly, get the wallet balance at the given time
        balance = self.get_wallet_balance_at(crypto_currency, time)

        time_str = str(time)
        normal_balance = str(balance.normalize())

        # Print info
        fcrypt_log.info(f"[WALLET] Balance at {time_str}: {normal_balance} {crypto_currency}")

        if balance != 0:

            # Now get the equivalent value in fiat
            rate_currency = crypto_currency + "-" + fiat_currency
            rate_value = self.price_finder.get_rate_of(rate_currency, time)

            if rate_value == Decimal(0):
                # Print error
                fcrypt_log.error(
                    f"[WALLET] NO RATE FOUND FOR NOT NULL BALANCE !!! Currency: {crypto_currency}",
                    f"Fiat: {fiat_currency}")
                # Return 0
                wallet_value = Decimal(0)
            else:
                # Calculate the wallet value
                wallet_value = rate_value * balance

                # Print info
                fcrypt_log.info(
                    f"[WALLET] Value of {crypto_currency} wallet at {time_str}: {wallet_value} {fiat_currency}")

        else:
            wallet_value = Decimal(0)

        return wallet_value

    def get_all_wallets_value(self, currency: str, time: datetime.datetime) -> Decimal:
        """
        This function allows to get the value of all the crypto-wallets of
        a user at a given time

        :param currency: Fiat currency we want for the value (ISO 4217)
        :type currency: str
        :param time: Time where the value is wanted
        :type time: datetime.datetime
        :returns: Decimal -- The overall value at the given time
        """
        # Initialize overall value of the wallet
        overall_value = Decimal(0)

        # For each crypto account (except fiat currency), calculate the wallet value
        for account in self.accounts:
            if account['currency'] != currency:
                wallet_value = self.get_wallet_value_at(account['currency'], currency, time)
                # Add the wallet value to the overall value
                overall_value += wallet_value

        return overall_value
