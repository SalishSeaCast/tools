# Copyright 2013 – present by the SalishSeaCast contributors
# and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A library of basic utility Python functions"""

import arrow
import glob
import os


def findnamelist(
    namelist, year, month, day, pathname="/results/SalishSea/nowcast-green"
):
    """Find the most recent namelist from a results file.

    arg str namelist: name of the namelist you are looking for

    arg int year: year

    arg int month: month

    arg int day: day

    arg int pathname: pathname to the results directory
    """

    myday = arrow.get(year, month, day)
    pathname = "/results/SalishSea/nowcast-green"
    directory = myday.format("DDMMMYY").lower()
    mynamelist = glob.glob(os.path.join(pathname, directory, namelist))
    while not mynamelist:
        myday = myday.shift(days=-1)
        directory = myday.format("DDMMMYY").lower()
        mynamelist = glob.glob(os.path.join(pathname, directory, namelist))
    return mynamelist[0]
