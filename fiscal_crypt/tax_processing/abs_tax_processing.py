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
from typing import List

from fiscal_crypt.platforms.abs_platforms import PlatformInterface


class TaxProcessing(abc.ABC):
    """
    Abstract class giving a model for the implementation of tax processing.
    Of course, the tax processing is country dependent.
    For each country we want to use a sub-class of "TaxProcessing"
    """

    def __init__(self, platforms_ls: List[PlatformInterface]) -> None:
        # Save the list of all platforms where the user own crypto-currencies
        self.platforms_list = platforms_ls

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
