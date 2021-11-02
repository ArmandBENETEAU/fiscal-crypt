"""
File containing the FrenchTaxes class

.. moduleauthor:: Armand BENETEAU <armand.beneteau@iot.bzh>

*Date: 17/10/2021*

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
from typing import List

from fiscal_crypt.tax_processing.abs_tax_processing import TaxProcessing
from fiscal_crypt.price_finder.abs_price_finder import PriceFinder
from fiscal_crypt.platforms.abs_platforms import PlatformInterface
from fiscal_crypt.fcrypt_logging import fcrypt_log


class FrenchTaxes(TaxProcessing):
    """
    Class implementing all the methods allowing to calculate the taxes declaration
    a crypto-owner has to do when living in France.
    """

    def __init__(self, currency: str, platforms_ls: List[PlatformInterface]) -> None:
        # Call the upper class initialization
        super().__init__(currency, platforms_ls)

        # Initialize the different values we will need later
        self.total_acquisition_price = Decimal(0)

    def _merge_and_pre_process_transactions(self) -> List[dict]:
        """
        This function merge the "buy" and "sell" transaction together, transform any 'string' number
        to Decimal and take the absolute value of this number. Moreover, it sorts the transaction in "ascending" order

        :returns: List[dict] -- List of transactions, labelled and in the right order to do the calculations
        """
        # Initialize the objects we will use
        tmp_transactions = []

        # Add all the buy transactions in that list, while processing them a bit
        for buy in self.buy_transactions:
            # Create the absolute value of the amount
            absolute_value = buy["amount"].replace("-", "")
            # Create the absolute value of the fees
            absolute_value_fee = buy["fee"].replace("-", "")
            # Create an object to add to the result
            tmp_object = {
                "type": "buy",
                "date": buy["date"],
                "currency": buy["currency"],
                "amount": Decimal(absolute_value),
                "fee": Decimal(absolute_value_fee)
            }
            # Add the tmp object to the result
            tmp_transactions.append(tmp_object)

        # Add all the sell transactions in that list, while processing them a bit
        for sell in self.sell_transactions:
            # Create the absolute value of the amount
            absolute_value = sell["amount"].replace("-", "")
            # Create the absolute value of the fees
            absolute_value_fee = sell["fee"].replace("-", "")
            # Create an object to add to the result
            tmp_object = {
                "type": "sell",
                "date": sell["date"],
                "currency": sell["currency"],
                "amount": Decimal(absolute_value),
                "fee": Decimal(absolute_value_fee)
            }
            # Add the tmp object to the result
            tmp_transactions.append(tmp_object)

        # Now, sort the list!

        # Logs info
        fcrypt_log.info("[TAXES PROCESSING] Sorting the transactions by date...")
        all_transactions = sorted(tmp_transactions, key=lambda x: x['date'])

        return all_transactions

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
        # Firstly, load and sort all transactions
        self._load_and_sort_all_transactions(end_time)

        # Logs info
        fcrypt_log.info("[TAXES PROCESSING] Pre-processing the transactions...")

        # Now merge all transactions and arrange it like we want
        preprocessed_transactions = self._merge_and_pre_process_transactions()

        # Logs info
        fcrypt_log.info("[TAXES PROCESSING] Pre-processing done!")

        # Now, calculate the capital gain and all the needed fields for tax declaration

        # Logs info
        fcrypt_log.info("[TAXES PROCESSING] Processing the transactions to get capital gains...")

        # Create the total count of capital gains
        total_capital_gains = Decimal(0)

        # Loop over the transactions
        for transaction in preprocessed_transactions:
            current_type = transaction["type"]
            if current_type == "buy":

                # Get the amount bought
                bought_amount = transaction["amount"]
                bought_am_display = self._convert_to_printable_decimal(bought_amount)

                # This is a buy, simply increment the acqusition price
                self.total_acquisition_price += bought_amount
                acqu_price_display = self._convert_to_printable_decimal(self.total_acquisition_price)

                # Show details to user
                fcrypt_log.info(
                    f"[TAXES PROCESSING] BUY OPERATION: +{bought_am_display} {fiat_currency} \
=> {acqu_price_display} {fiat_currency}")

            elif current_type == "sell":

                # Get the cession price
                cession_price = transaction["amount"]
                cession_p_display = self._convert_to_printable_decimal(cession_price)
                # Get the fees
                cession_fee = transaction["fee"]
                cession_fee_display = self._convert_to_printable_decimal(cession_fee)
                # Get the current acquisition price
                acquisition_price = self.total_acquisition_price
                acqu_price_display = self._convert_to_printable_decimal(acquisition_price)
                # Get the global value of the wallets
                global_value = self._get_overall_wallets_value(transaction["date"] - datetime.timedelta(milliseconds=1))
                global_value_display = self._convert_to_printable_decimal(global_value)

                # Calculating the "plus-value" (capital gain)
                capital_gain = cession_price - (cession_price * acquisition_price / global_value)
                capital_gain_display = self._convert_to_printable_decimal(capital_gain)

                # Creation of the date string
                date_str = transaction["date"].strftime("%d-%b-%Y (%H:%M:%S.%f)")

                # Displaying the operation
                fcrypt_log.info(f"[TAXES PROCESSING] SELL OPERATION")
                fcrypt_log.info(f"    Date:              {date_str}")
                fcrypt_log.info(f"    Capital gain:      {capital_gain_display} {fiat_currency}")
                fcrypt_log.info(f"    Cession price:     {cession_p_display} {fiat_currency}")
                fcrypt_log.info(f"    Fee:               {cession_fee_display} {fiat_currency}")
                fcrypt_log.info(f"    Acquisition price: {acqu_price_display} {fiat_currency}")
                fcrypt_log.info(f"    Global value:      {global_value_display} {fiat_currency}")

                # Calculate the new total acquisition price
                self.total_acquisition_price = self.total_acquisition_price - \
                    (cession_price * self.total_acquisition_price / global_value)

                # Add to the total capital gain
                total_capital_gains += capital_gain

            else:
                fcrypt_log.error(f"[TAXES PROCESSING] Current type not supported: {current_type}")

        # Print the overall capital gain
        total_cap_price_display = self._convert_to_printable_decimal(total_capital_gains)
        fcrypt_log.info(f"[TAXES PROCESSING] TOTAL CAPITAL GAIN: {total_cap_price_display} {fiat_currency}")
