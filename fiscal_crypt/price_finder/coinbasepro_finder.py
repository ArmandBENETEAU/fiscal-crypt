"""
File containing the CoinbaseProFinder subclass

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

import cbpro
import datetime
from fiscal_crypt.price_finder.abs_price_finder import PriceFinder


class CoinbaseProFinder(PriceFinder):
    """
    Class allowing to get the price of a crypto-currency at any moment of
    time, using the Coinbase Pro interface. No authentication is needed for
    this operation on Coinbase Pro.
    """

    def __init__(self) -> None:
        # Call the upper class initialization
        super().__init__()

        # Create the Coinbase Pro client that we will use
        self.api_client = cbpro.PublicClient()

    @staticmethod
    def _calculate_average(rates: list) -> float:
        """
        Calculate the average of the price from a list of "bucket".
        For more information, see:

        https://docs.pro.coinbase.com/?javascript#get-historic-rates

        :param rates: List of "buckets" containing the prices candles
        :type rates: list
        """
        # Go through the different rates and get what we want
        full_volume = 0.0
        full_prices = 0.0
        for rate in rates:
            # Calculate the middle price
            middle_price = (float(rate[1]) + float(rate[2])) / 2

            # Get the volume
            volume = float(rate[5])

            # Add the middle_price multiplied by the volume to full_prices
            full_prices = full_prices + (middle_price * volume)

            # Add the volume to the full_volume
            full_volume = full_volume + volume

        # Calculate the average
        average = full_prices / full_volume

        return average

    def get_rate_of(self, currency: str, time: datetime.datetime) -> float:
        """
        This function allows to get the rate of a crypto-currency with
        a fiat currency at a given datetime.

        :param currency: (Currency-fiat) we want the price of, example: BTC-EUR
        :type currency: str
        :param time: Time where the price is wanted
        :type time: datetime.datetime
        """
        # From the time given, get the "start" time, we will calculate average
        # on only one hour
        startTime = time.replace(microsecond=0, second=0, minute=0)
        endTime = startTime + datetime.timedelta(hours=1.0)

        # Get the historic price for this time
        historic_rates = self.api_client.get_product_historic_rates(
            currency, start=startTime.isoformat(), end=endTime.isoformat(), granularity=60)

        # Calculate the average for the hour that interest us
        average = self._calculate_average(historic_rates)

        return average
