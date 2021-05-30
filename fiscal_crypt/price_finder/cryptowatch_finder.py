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

import datetime
import requests

from decimal import *
from fiscal_crypt.price_finder.abs_price_finder import PriceFinder


class CryptowatchFinder(PriceFinder):
    """
    Class allowing to get the price of a crypto-currency at any moment of
    time, using the Cryptowatch interface. It is necessary to have an account
    and an API key for that.
    """

    def __init__(self, api_key: str, exchange: str) -> None:
        # Call the upper class initialization
        super().__init__()

        # Save the api_key
        self.api_key = api_key

        # Save the exchange market to use
        self.exchange_market = exchange

    @staticmethod
    def _calculate_average(rates: list) -> Decimal:
        """
        Calculate the average of the price from a list of "candlesticks" data.
        For more information, see:

        https://docs.cryptowat.ch/rest-api/markets/ohlc

        :param rates: List of "candlesticks" data
        :type rates: list
        :returns: Decimal -- The average over all the rates
        """
        # Go through the different rates and get what we want
        full_volume = Decimal(0.0)
        full_prices = Decimal(0.0)
        for rate in rates:
            # Get the quote volume
            quote_volume = Decimal(rate[6])

            # Get the volume
            volume = Decimal(rate[5])

            # Add the quote volume to full_prices
            full_prices = full_prices + quote_volume

            # Add the volume to the full_volume
            full_volume = full_volume + volume

        if full_volume != Decimal(0.0):
            # Calculate the average
            average = full_prices / full_volume
        else:
            average = Decimal(0.0)

        return average

    def _get_candle_sticks_list(self, currency: str, start_timestamp: int, end_timestamp: int) -> list:
        """
        This function allows to get a list of cnadle sticks for the given period

        :param currency: (Currency-fiat) we want the price of, example: BTC-EUR, BTCEUR, btceur, etc.
        :type currency: str
        :param start_timestamp: Unix timestamp of the begin of the period wanted
        :type start_timestamp: int
        :param end_timestamp: Unix timestamp of the end of the period wanted
        :type end_timestamp: int
        :returns: list -- List of candle sticks
        """
        # Initialize the return value
        result = []

        # Create the request to send to cryptowatch
        # Create the authentication header
        headers = {'X-CW-API-Key': self.api_key}

        # Create the query parameters
        url_parameters = {'after': start_timestamp, 'before': end_timestamp}

        # Initiate the full URL
        full_url = f"https://api.cryptowat.ch/markets/{self.exchange_market}/{currency}/ohlc"

        # Send the request
        answer = requests.get(full_url, params=url_parameters, headers=headers)

        # Convert the request to json
        json_answer = answer.json()

        # Get list of results
        results_lists = json_answer.get('result')
        if results_lists is not None:
            for list in results_lists.values():
                result = result + list

        return result

    def get_rate_of(self, currency: str, time: datetime.datetime) -> Decimal:
        """
        This function allows to get the rate of a crypto-currency with
        a fiat currency at a given datetime.

        :param currency: (Currency-fiat) we want the price of, example: BTC-EUR
        :type currency: str
        :param time: Time where the price is wanted
        :type time: datetime.datetime
        :returns: Decimal -- The average rate of the given currency
        """
        # Convert to utc time
        time_utc = time.replace(tzinfo=datetime.timezone.utc)

        # From the time given, get the "start" time, we will calculate average
        # on only one hour
        startTime = time_utc.replace(microsecond=0, second=0, minute=0)
        endTime = startTime + datetime.timedelta(hours=1.0)

        # Convert to unix timestamp
        timestamp_start = int(startTime.timestamp())
        timestamp_end = int(endTime.timestamp())

        # For currency, get rid of dash and set to lower
        currency_used = currency.replace("-", "").lower()

        # Send the request to cryptowatch
        historic_rates = self._get_candle_sticks_list(currency_used, timestamp_start, timestamp_end)

        if isinstance(historic_rates, list):
            # Calculate the average for the hour that interest us
            average = self._calculate_average(historic_rates)
        else:
            average = Decimal(0.0)

        return average
