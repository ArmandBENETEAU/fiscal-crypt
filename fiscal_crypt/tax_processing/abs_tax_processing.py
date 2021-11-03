"""
File containing the TaxProcessing abstract class

.. moduleauthor:: Armand BENETEAU <armand.beneteau@iot.bzh>

*Date: 12/10/2021*

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
from typing import List

from fiscal_crypt.platforms.abs_platforms import PlatformInterface
from fiscal_crypt.fcrypt_logging import fcrypt_log


class TaxProcessing(abc.ABC):
    """
    Abstract class giving a model for the implementation of tax processing.
    Of course, the tax processing is country dependent.
    For each country we want to use a sub-class of "TaxProcessing"
    """

    def __init__(self, currency: str, platforms_ls: List[PlatformInterface]) -> None:
        # Save the list of all platforms where the user own crypto-currencies
        self.platforms_list = platforms_ls

        # Save the currency wanted to calculate
        self.currency = currency
        self.buy_transactions = []
        self.sell_transactions = []

    def _convert_to_printable_decimal(self, number: Decimal) -> Decimal:
        """
        This function allows to convert a Decimal to a printable "Devise" (with 2 number after coma)

        :param number: Number to convert to printable
        :type number: Decimal
        """
        # Normalized value
        norm_nb = number.normalize()

        # Convert to Decimal with tow digits
        TWOPLACES = Decimal(10) ** -2
        display_value = norm_nb.quantize(TWOPLACES)

        return display_value

    def _load_and_sort_all_transactions(self, end_time: datetime.datetime) -> None:
        """
        This function allows to load in memory all the transactions done by the user until end_time

        :param end_time: Datetime corresponding to the end of the tax period
        :type end_time: datetime.datetime
        """

        # Logs info
        fcrypt_log.info("[TAXES PROCESSING] Loading all buy and sell transactions...")

        # Get the buy and sell transactions
        for crypto_platform in self.platforms_list:

            # First the buy transactions
            for buy in crypto_platform.all_buy_transactions_generator(self.currency, end_time):
                self.buy_transactions.append(buy)

            # Then the sell transactions
            for sell in crypto_platform.all_sell_transactions_generator(self.currency, end_time):
                self.sell_transactions.append(sell)

        # Logs info
        fcrypt_log.info(f"[TAXES PROCESSING] Number of platforms scanned: {len(self.platforms_list)}")
        fcrypt_log.info(f"[TAXES PROCESSING] Number of \"BUY\" transactions found: {len(self.buy_transactions)}")
        fcrypt_log.info(f"[TAXES PROCESSING] Number of \"SELL\" transactions found: {len(self.sell_transactions)}")

        # Logs info
        fcrypt_log.info("[TAXES PROCESSING] Load done")

    def _get_overall_wallets_value(self, time: datetime.datetime) -> Decimal:
        """
        This function allows to get the overall value of all the wallets hold by the crypto-owner.
        Basically, it does a sum of all the crypto-owner wallets values.

        :param time: Datetime wanted for the values evaluation
        :type time: datetime.datetime
        :returns: Decimal -- Decimal value of the wallets
        """
        # Initialize the result
        result = Decimal(0)

        # Go over the different platform
        for crypto_platform in self.platforms_list:
            tmp_result = crypto_platform.get_all_wallets_value(self.currency, time)
            result += tmp_result

        return result

    @abc.abstractmethod
    def get_tax_declaration_for(self, fiat_currency: str, start_time: datetime.datetime,
                                end_time: datetime.datetime) -> List[dict]:
        """
        This function allows to get exactly what the user needs to declare to the tax service of his government

        :param fiat_currency: Fiat currency of the country
        :type fiat_currency: str
        :param start_time: Datetime from which the tax declaration takes effect
        :type start_time: datetime.datetime
        :param end_time: Datetime until which the tax declaration takes effect
        :type end_time: datetime.datetime
        :returns: List[dict] -- List of each declaration to report to the government
        """
        pass
