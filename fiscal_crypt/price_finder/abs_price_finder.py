"""
File containing the PriceFinder abstract class

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
from decimal import Decimal


class PriceFinder(abc.ABC):
    """
    Abstract class giving a model for the implementation of price finders.
    Several platforms can be used to retrieve the price of a crypto-currency
    at a given time. For each platform we want to use a sub-class of "PriceFinder"
    """

    @abc.abstractmethod
    def get_rate_of(self, currency: str, time: datetime.datetime) -> Decimal:
        """
        This function allows to get the price of a crypto-currency at a given
        datetime.

        :param currency: Currency we want the price of (ISO 4217)
        :type currency: str
        :param time: Time where the price is wanted
        :type time: datetime.datetime
        :returns: Decimal -- The average rate of the given currency
        """
        pass
