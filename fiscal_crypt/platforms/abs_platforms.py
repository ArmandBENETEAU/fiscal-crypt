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


class PlatformInterface(abc.ABC):
    """
    Abstract class giving a model for the implementation of platform interface.
    Several platforms can be used to calculate the amount of crypto detained by a user
    at a given time. For each platform we want to use, a sub-class of "PlatformInterface"
    """

    @abc.abstractmethod
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
