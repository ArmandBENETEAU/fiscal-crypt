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
from typing import Generator
from dateutil.parser import isoparse

import urllib.parse as urlparse
from urllib.parse import parse_qs

from coinbase.wallet.client import Client
from fiscal_crypt.price_finder.abs_price_finder import PriceFinder
from fiscal_crypt.platforms.abs_platforms import PlatformInterface
from fiscal_crypt.fcrypt_logging import fcrypt_log


class CoinbaseInterface(PlatformInterface):
    """
    Class implementing all the methods allowing to calculate the differents
    overall values of accounts at given times. It allows also to enumerate
    all the transactions that can be impacted by taxes
    """

    def __init__(self, api_key: str, api_secret: str, price_finder: PriceFinder) -> None:
        # Call the upper class initialization
        super().__init__()

        # Create the Coinbase authenticated client that we will use
        self.api_client = Client(api_key, api_secret)

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
        accounts_list = []
        other_pages = True
        last_id = ""
        while other_pages:
            # Get account according to pagination
            if last_id == "":
                api_answer = self.api_client.get_accounts()
            else:
                api_answer = self.api_client.get_accounts(starting_after=last_id)

            accounts_list = accounts_list + api_answer['data']
            if ((api_answer.pagination is not None) and (api_answer.pagination["next_uri"] is not None) and
                    (api_answer.pagination["next_uri"] != "")):
                # Get the pagination object
                pagination_obj = api_answer.pagination
                # Extract 'starting_after' key from next_uri
                parsed = urlparse.urlparse(pagination_obj["next_uri"])
                last_id = parse_qs(parsed.query)['starting_after'][0]
            else:
                other_pages = False

        # Save all used accounts
        for account in accounts_list:

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
            transactions_list = []
            other_pages = True
            last_id = ""

            while other_pages:
                # Get account according to pagination
                if last_id == "":
                    # Get the transactions for this account
                    tmp_transactions = self.api_client.get_transactions(account['id'])
                else:
                    # Get the transactions for this account
                    tmp_transactions = self.api_client.get_transactions(account['id'], starting_after=last_id)

                transactions_list = transactions_list + tmp_transactions['data']
                if ((tmp_transactions.pagination is not None) and
                    (tmp_transactions.pagination["next_uri"] is not None) and
                        (tmp_transactions.pagination["next_uri"] != "")):
                    # Get the pagination object
                    pagination_obj = tmp_transactions.pagination
                    # Extract 'starting_after' key from next_uri
                    parsed = urlparse.urlparse(pagination_obj["next_uri"])
                    last_id = parse_qs(parsed.query)['starting_after'][0]
                else:
                    other_pages = False

            # Print the transactions
            for transaction in transactions_list:
                # print(transaction)
                transaction_type = transaction['type']
                amount = transaction['amount']['amount']
                currency = transaction['amount']['currency']
                date = transaction['updated_at']
                if not str.startswith(amount, "-"):
                    amount = "+" + amount
                account = self._extract_account_id(transaction['resource_path'])
                fcrypt_log.debug(f"[TRANSACTION][{transaction_type}] {date}: {amount} {currency} ==> {account}")

            self.transactions.extend(transactions_list)

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

    def all_sell_transactions_generator(self, currency: str, end_time: datetime.datetime) -> Generator:
        """
        This function returns a generator that can be used in a for loop to get
        every "sell" transactions done between "start_time" and "end_time"

        :param currency: Fiat currency we want for the value (ISO 4217)
        :type currency: str
        :param start_time: Begin of the tax period
        :type start_time: datetime.datetime
        :param end_time: End of the tax period
        :type end_time: datetime.datetime
        :returns: Generator -- Generator to get each transaction object \
        """
        # Get the correct ID for this currency in order to ignore it
        account_to_ignore_id = self._find_account_for_currency(currency)

        if account_to_ignore_id == "":
            raise ValueError("Account not found with the given currency")

        # Now that we have the right account
        for transaction in self.transactions:
            # Extract the account ID from the resource path
            account = self._extract_account_id(transaction['resource_path'])

            # Check that this is the right account and that is a match
            if (account != account_to_ignore_id) and (transaction["type"] == "sell"):
                # Get the amount of the transaction
                amount = transaction["native_amount"]["amount"]
                local_currency = transaction["native_amount"]["currency"]

                if local_currency != currency:
                    error_msg = f"The local currency found \"{local_currency}\" does not match \
                                  the specified currency \"{currency}\"!"
                    raise ValueError(error_msg)

                # Check the time when this sell appeared
                transaction_time = isoparse(transaction['created_at'])

                if (transaction_time < end_time):
                    # This is something we want, find the corresponding fee

                    # Request the full sell transaction object
                    current_sell = self.api_client.get_sell(account, transaction["sell"]["id"])

                    # Get the fee amount from the full sell object
                    fee_amount = current_sell["fees"][0]["amount"]["amount"]

                    # Declare the dictionnary to return
                    tmp_dict = {
                        "date": transaction_time,
                        "currency": local_currency,
                        "amount": amount,
                        "fee": fee_amount
                    }

                    yield tmp_dict

    def all_buy_transactions_generator(self, currency: str, end_time: datetime.datetime) -> Generator:
        """
        This function returns a generator that can be used in a for loop to get
        every "buy" transactions done before "end_time"

        :param currency: Fiat currency we want for the value (ISO 4217)
        :type currency: str
        :param end_time: End of the tax period
        :type end_time: datetime.datetime
        :returns: Generator -- Generator to get each transaction object
        """
        # Get the correct ID for this currency in order to ignore it
        account_to_ignore_id = self._find_account_for_currency(currency)

        if account_to_ignore_id == "":
            raise ValueError("Account not found with the given currency")

        # Now that we have the right account
        for transaction in self.transactions:
            # Extract the account ID from the resource path
            account = self._extract_account_id(transaction['resource_path'])

            # Check that this is the right account and that is a match
            if (account != account_to_ignore_id) and (transaction["type"] == "buy"):
                # Get the amount of the transaction
                amount = transaction["native_amount"]["amount"]
                local_currency = transaction["native_amount"]["currency"]

                if local_currency != currency:
                    error_msg = f"The local currency found \"{local_currency}\" does not match \
                                 the specified currency \"{currency}\"!"
                    raise ValueError(error_msg)

                # Check the time when this sell appeared
                transaction_time = isoparse(transaction['created_at'])

                if (transaction_time < end_time):
                    # This is something we want, find the corresponding fee

                    # Request the full sell transaction object
                    current_buy = self.api_client.get_buy(account, transaction["buy"]["id"])

                    # Get the fee amount from the full sell object
                    fee_amount = current_buy["fees"][0]["amount"]["amount"]

                    # Declare the dictionnary to return
                    tmp_dict = {
                        "date": transaction_time,
                        "currency": local_currency,
                        "amount": amount,
                        "fee": fee_amount
                    }

                    yield tmp_dict
