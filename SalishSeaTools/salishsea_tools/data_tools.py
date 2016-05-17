# Copyright 2016 The Salish Sea NEMO Project and
# The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Functions for loading and processing observational data
"""
import datetime as dtm
import os

import dateutil.parser as dparser
import numpy as np
import scipy.io


def load_ADCP(
        daterange, station='central',
        adcp_data_dir='/ocean/dlatorne/MEOPAR/ONC_ADCP/',
):
    """Returns the ONC ADCP velocity profiles at a given station
    over a specified daterange.
    
    :arg sequence daterange: Start and end datetimes for the requested data
                             range
                             (e.g. ['yyyy mmm dd', 'yyyy mmm dd']).

    :arg str station: Requested profile location ('central', 'east', or 'ddl')

    :returns: Arrays of :py:class:`Datetime` and depth and masked arrays of
        zonal and meridional velocity
    :rtype: :py:class:`Numpy.array` and :py:class:`Numpy.ma.MaskedArray`
    """
    startdate = dparser.parse(daterange[0])
    enddate = dparser.parse(daterange[1])
    grid = scipy.io.loadmat(
        os.path.join(adcp_data_dir, 'ADCP{}.mat'.format(station)))
    # Generate datetime array
    mtimes = grid['mtime'][0]
    datetimes = np.array([dtm.datetime.fromordinal(int(mtime)) +
                          dtm.timedelta(days=mtime % 1) -
                          dtm.timedelta(days=366) for mtime in mtimes])
    # Find daterange indices
    indexstart = abs(datetimes - startdate).argmin()
    indexend = abs(datetimes - enddate).argmin()
    # Extract time, depth, and velocity vectors
    datetime = datetimes[indexstart:indexend + 1]
    u0 = grid['utrue'][:, indexstart:indexend + 1] / 100  # to m/s
    v0 = grid['vtrue'][:, indexstart:indexend + 1] / 100  # to m/s
    depth = grid['chartdepth'][0]
    u = np.ma.masked_invalid(u0)
    v = np.ma.masked_invalid(v0)
    return datetime, depth, u, v
