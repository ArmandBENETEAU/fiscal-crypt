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
from typing import Generator


class PlatformInterface(abc.ABC):
    """
    Abstract class giving a model for the implementation of platform interface.
    Several platforms can be used to calculate the amount of crypto detained by a user
    at a given time. For each platform we want to use, a sub-class of "PlatformInterface"
    """

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
