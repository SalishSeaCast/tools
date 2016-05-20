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
from collections import namedtuple
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

    :returns: :py:attr:`datetime` attribute holds a :py:class:`numpy.ndarray`
              of data datatime stamps,
              :py:attr:`depth` holds the depth at which the ADCP sensor is
              deployed,
              :py:attr:`u` and :py:attr:`v` hold :py:class:`numpy.ndarray`
              of the zonal and meridional velocity profiles at each datetime.
    :rtype: 4 element :py:class:`collections.namedtuple`
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
    adcp_data = namedtuple('ADCP_data', 'datetime, depth, u, v')
    return adcp_data(datetime, depth, u, v)
