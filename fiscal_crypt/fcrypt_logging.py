"""
File containing the logging object

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
import logging
import logging.handlers

# --------------------------------------------
# Logging configuration ----------------------
# --------------------------------------------
logging.basicConfig(format='%(asctime)s => [%(levelname)s] %(message)s', level=logging.INFO)
fcrypt_log = logging.getLogger('fiscal_crypt')
