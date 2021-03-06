"""
File containing the PlatformInterface abstract class

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

import abc
import datetime

from decimal import *
from typing import Generator, List

from fiscal_crypt.price_finder.abs_price_finder import PriceFinder


class PlatformInterface(abc.ABC):
    """
    Abstract class giving a model for the implementation of platform interface.
    Several platforms can be used to calculate the amount of crypto detained by a user
    at a given time. For each platform we want to use, a sub-class of "PlatformInterface"
    """

    def __init__(self, price_finder: List[PriceFinder]) -> None:
        self.accounts = []
        self.transactions = []

        # Initialize the price finder
        self.price_finder = price_finder

    def _find_account_for_currency(self, currency: str) -> str:
        """
        This function allows to return the account id for a given currency

        :param currency: The currency we want the account id for
        :type currency: str
        :returns: str -- The account id for this currency
        """
        account_id = ""

        # First, get the account ID of that corresponds to the currency
        for account in self.accounts:
            # Get the currency for the account
            tmp_currency = account.get("currency", "[NOT KNOWN]")
            # Check if it is the currency we are looking for
            if tmp_currency == currency:
                account_id = account.get("id", "")
                break

        return account_id

    def _find_rate_value_from_finders(self, currency: str, time: datetime.datetime) -> Decimal:
        """
        This function allows to get the rate of a crypto-currency with
        a fiat currency at a given datetime. It tries on every finders available as long as a 0
        value is returned.

        :param currency: (Currency-fiat) we want the price of, example: BTC-EUR
        :type currency: str
        :param time: Time where the price is wanted
        :type time: datetime.datetime
        :returns: Decimal -- The average rate of the given currency
        """
        # Initialize the return value
        rate_value = Decimal(0)

        # Go over the different price finders available
        for finder in self.price_finder:

            # Get the evaluation of price from this finder
            rate_value = finder.get_rate_of(currency, time)

            if rate_value != Decimal(0):
                break

        # Check that the rate is not 0, if it is, request a manual entry
        if rate_value == Decimal(0):
            date_str = time.strftime("%d-%b-%Y (%H:%M:%S.%f)")
            user_input = input(
                f"No rate found for \"{currency}\" on {date_str}, please provide it manually (ex: \"1.87\"): ")
            # Convert the input to Decimal
            rate_value = Decimal(user_input)

        return rate_value

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    def all_sell_transactions_generator(self, currency: str, end_time: datetime.datetime) -> Generator:
        """
        This function returns a generator that can be used in a for loop to get
        every "sell" transactions done before "end_time"

        :param currency: Fiat currency we want for the value (ISO 4217)
        :type currency: str
        :param end_time: End of the tax period
        :type end_time: datetime.datetime
        :returns: Generator -- Generator to get each transaction object \
            The transaction object being:
            {
                "date": datetime.datetime,
                "currency": "EUR",
                "amount": "95.34",
                "fee": "0.499"
            }
        """
        pass

    @abc.abstractmethod
    def all_buy_transactions_generator(self, currency: str, end_time: datetime.datetime) -> Generator:
        """
        This function returns a generator that can be used in a for loop to get
        every "buy" transactions done before "end_time"

        :param currency: Fiat currency we want for the value (ISO 4217)
        :type currency: str
        :param end_time: End of the tax period
        :type end_time: datetime.datetime
        :returns: Generator -- Generator to get each transaction object \
            The transaction object being:
            {
                "date": datetime.datetime,
                "currency": "EUR",
                "amount": "-95.34",
                "fee": "0.499"
            }
        """
        pass
