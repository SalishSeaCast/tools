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
from collections import OrderedDict
import datetime as dtm
import os
try:
    from urllib.parse import (
        quote,
        urlencode,
    )
except ImportError:
    # Python 2.7
    from urllib import (
        quote,
        urlencode,
    )

import arrow
import dateutil.parser as dparser
import numpy as np
import requests
from retrying import retry
import scipy.interpolate
import scipy.io
import xarray

from salishsea_tools import teos_tools


def load_ADCP(
        daterange, station='central',
        adcp_data_dir='/ocean/dlatorne/MEOPAR/ONC_ADCP/',
):
    """Returns the ONC ADCP velocity profiles at a given station
    over a specified datetime range.
    
    This function uses the nearest neighbor to the specified datetime
    bounds. ONC ADCP data is returned at approximately 15 and 45 minutes
    past the hour, so choose datetime bounds accordingly.
    
    :arg daterange: start and end datetimes for the requested data range.
        (ex. ['yyyy mmm dd HH:MM', 'yyyy mmm dd HH:MM'])
    :type daterange: list or tuple of str
    
    :arg adcp_path: ADCP file storage location
    :type adcp_path: str

    :arg str station: Requested profile location ('central', 'east', or 'ddl')

    :returns: :py:class:`xarray.Dataset` of zonal u and meridional v velocity
        with time and depth dimensions.
    :rtype: 2-D, 2 element :py:class:`xarray.Dataset` object
    """

    # Load ADCP data
    grid = scipy.io.loadmat(
                 os.path.join(adcp_data_dir, 'ADCP{}.mat'.format(station)))
    
    # Generate datetime array
    mtimes = grid['mtime'][0]
    datetimes = np.array([dtm.datetime.fromordinal(int(mtime)) +
                          dtm.timedelta(days=mtime % 1) -
                          dtm.timedelta(days=366) for mtime in mtimes])
    
    # Find daterange indices
    index = [abs(datetimes - dparser.parse(date)).argmin() for date in daterange]
    
    # Create xarray output object
    ADCP = xarray.Dataset({
        'u': (['time', 'depth'],
              np.ma.masked_invalid(
                  grid['utrue'][:, index[0]:index[1] + 1] / 100).transpose()),
        'v': (['time', 'depth'],
              np.ma.masked_invalid(
                  grid['vtrue'][:, index[0]:index[1] + 1] / 100).transpose())},
        coords={'time': datetimes[index[0]:index[1] + 1],
                'depth': grid['chartdepth'][0]})
    
    return ADCP


def interpolate_to_depth(
    var, var_depths, interp_depths, var_mask=0, var_depth_mask=0,
):
    """Calculate the interpolated value of var at interp_depth using linear
    interpolation.

    :arg var: Depth profile of a model variable or data quantity.
    :type var: :py:class:`numpy.ndarray`

    :arg var_depths: Depths at which the model variable or data quantity has
                     values.
    :type var_depths: :py:class:`numpy.ndarray`

    :arg interp_depths: Depth(s) at which to calculate the interpolated value
                        of the model variable or data quantity.
    :type interp_depths: :py:class:`numpy.ndarray` or number

    :arg var_mask: Mask to use for the model variable or data quantity.
                   For model results it is best to use the a 1D slice of the
                   appropriate mesh mask array;
                   e.g. :py:attr:`tmask` for tracers.
                   Masking the model variable or data quantity increases the
                   accuracy of the interpolation.
                   If var_mask is not provided the model variable or data
                   quantity is zero-masked.
    :type var_mask: :py:class:`numpy.ndarray` or number

    :arg var_depth_mask: Mask to use for the depths.
                         For model results it is best to use the a 1D slice
                         of the appropriate mesh mask array;
                         e.g. :py:attr:`tmask` for tracers.
                         Masking the depths array increases the accuracy of
                         the interpolation.
                         If var_depth_mask is not provided the depths array
                         is zero-masked.
    :type var_mask: :py:class:`numpy.ndarray` or number

    :returns: Value(s) of var linearly interpolated to interp_depths.
    :rtype: :py:class:`numpy.ndarray` or number
    """
    raise NotImplementedError(
        'Implementation of this function turns out to be complicated that '
        'expected, especially for variables other than tracers. Please see '
        'nowcast.figures.interpolate_depth or '
        'nowcast.figures.shared.interpolate_tracer_to_depths.'
    )
    # var_mask = (
    #     np.logical_not(var_mask) if hasattr(var_mask, 'shape')
    #     else var_mask == var_mask)
    # print(var_depths)
    # print(var_depths[var_depth_mask == True])
    # var_depth_mask = (
    #     np.logical_not(var_depth_mask) if hasattr(var_depth_mask, 'shape')
    #     else var_depth_mask == var_depth_mask)
    depth_interp = scipy.interpolate.interp1d(
        var_depths[var_depth_mask == True], var[var_mask == True],
        # np.ma.array(var_depths, mask=var_depth_mask),
        # np.ma.array(var, mask=var_mask),
        fill_value='extrapolate',
        assume_sorted=True)
    return depth_interp(interp_depths)


def onc_datetime(date_time, timezone='Canada/Pacific'):
    """Return a string representation of a date/time in the particular
    ISO-8601 extended format required by the Ocean Networks Canada (ONC)
    data web services API.

    :arg date_time: Date/time to transform into format required by
                    ONC data web services API.
    :type date_time: str
                     or :py:class:`datetime.datetime`
                     or :py:class:`arrow.Arrow`

    :arg str timezone: Timezone of date_time.

    :returns: UTC date/time formatted as :kbd:`YYYY-MM-DDTHH:mm:ss.SSSZ`
    :rtype: str
    """
    d = arrow.get(date_time)
    d_tz = arrow.get(d.datetime, timezone)
    d_utc = d_tz.to('utc')
    return '{}Z'.format(d_utc.format('YYYY-MM-DDTHH:mm:ss.SSS'))


def get_onc_data(
    endpoint, method, token,
    retry_args={
        'wait_exponential_multiplier': 1000,
        'wait_exponential_max': 30000,
    },
    **query_params):
    """Request data from one of the Ocean Networks Canada (ONC) web services.

    See https://wiki.oceannetworks.ca/display/help/API for documentation
    of the ONC data web services API.
    See the `ONC-DataWebServices notebook`_ for example of use of the API
    and of this function.

    .. _ONC-DataWebServices notebook: http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/analysis-doug/raw/tip/notebooks/ONC-DataWebServices.ipynb

    :arg dict retry_args: Key/value pair arguments to control how the request
                          is retried should it fail the first time.
                          The defaults provide a 2^x * 1 second exponential
                          back-off between each retry, up to 30 seconds,
                          then 30 seconds afterwards
                          See https://pypi.python.org/pypi/retrying for a full
                          discussion of the parameters available to control
                          retrying.

    :arg str endpoint: ONC web service end-point; e.g. :kbd:`scalardata`.
                       See https://wiki.oceannetworks.ca/display/help/API
                       for available web service end-points.

    :arg str method: ONC web service method; e.g. :kbd:`getByStation`.
                     See https://wiki.oceannetworks.ca/display/help/API
                     and the pages linked from it for the method available
                     on each of the web service end-points.

    :arg str token: ONC web services API token generated on the
                    :guilabel:`Web Services API` tab of
                    http://dmas.uvic.ca/Profile

    :arg dict query_params: Query parameters expressed as key/value pairs.

    :returns: Mapping created from the JSON content of the response from the
              data web service
    :rtype: dict
    """
    url_tmpl = 'http://dmas.uvic.ca/api/{endpoint}?{query}'
    query = {'method': method, 'token': token}
    query.update(query_params)
    data_url = url_tmpl.format(
        endpoint=endpoint,
        query=urlencode(query, quote_via=quote, safe='/:'))
    @retry(**retry_args)
    def requests_get(data_url):
        return requests.get(data_url)
    response = requests_get(data_url)
    response.raise_for_status()
    return response.json()


def onc_json_to_dataset(onc_json, teos=True):
    """Return an :py:class:`xarray.Dataset` object containing the data and
    metadata obtained from an Ocean Networks Canada (ONC) data web service API
    request.

    :arg dict onc_json: Data structure returned from an ONC data web service
                        API request.
                        Typically produces by calling the :py:meth:`json`
                        method on the :py:class:`~requests.Response` object
                        produced by calling :py:meth:`requests.get`.

    :arg boolean teos: Convert salinity data from PSU
                       (Practical Salinity  Units) to TEOS-10 reference
                       salinity in g/kg.
                       Defaults to :py:obj:`True`.

    :returns: Data structure containing data and metadata
    :rtype: :py:class:`xarray.Dataset`
    """
    data_vars = {}
    for sensor in onc_json['sensorData']:
        if sensor == 'salinity' and teos:
            data = teos_tools.psu_teos([d['value'] for d in sensor['data']])
        else:
            data = [d['value'] for d in sensor['data']]
        data_vars[sensor['sensor']] = xarray.DataArray(
            name=sensor['sensor'],
            data=data,
            coords={
                'sampleTime': [arrow.get(d['sampleTime']).datetime
                               for d in sensor['data']],
            },
            attrs={
                'qaqcFlag': np.array([d['qaqcFlag'] for d in sensor['data']]),
                'sensorName': sensor['sensorName'],
                'unitOfMeasure': sensor['unitOfMeasure'],
                'actualSamples': sensor['actualSamples'],
            }
        )
    return xarray.Dataset(data_vars, attrs=onc_json['serviceMetadata'])


def load_drifters(prefix='driftersPositions',
                  path='/ocean/bmoorema/research/MEOPAR/analysis-ben/data'):
    """
    """
    
    # Initialize drifter storage dictionary
    drifters = OrderedDict()
    
    # Drifter IDs
    drifterids = OrderedDict()
    drifterids['1'] = [1, 2, 3, 4, 5, 6, 311, 312, 313]
    drifterids['2'] = [21, 22]
    drifterids['3'] = [23, 24, 25, 31, 32, 33, 34, 35, 36, 381, 382, 388]
    
    for deployment in drifterids.keys():
        # Construct filename
        filename = prefix + deployment + '.mat'
        
        # Load drifter matfile
        driftermat = scipy.io.loadmat(os.path.join(path, filename))
        
        # Iterate through drifters
        for drifterid in drifterids[deployment]:
            
            # Construct time list and convert to datetime
            times = driftermat['drifters'][0][drifterid-1][4]
            if isinstance(times[0][0], float):
                pytime = [dtm.datetime.fromordinal(int(t[0])) +
                          dtm.timedelta(days = t[0]%1) -
                          dtm.timedelta(days = 366) - dtm.timedelta(hours=1)
                          for t in times]
            elif isinstance(times[0][0], str):
                pytime = [dparser.parse(t) for t in times]
            else:
                raise ValueError(
                    'Unknown time type: {}'.format(type(times[0][0])))
            
            # Store drifter lon and lat as xarray DataArray objects
            lons = xarray.DataArray(
                [lon[0] for lon in driftermat['drifters'][0][drifterid-1][3]],
                coords=[pytime], dims=['time'])
            lats = xarray.DataArray(
                [lat[0] for lat in driftermat['drifters'][0][drifterid-1][2]],
                coords=[pytime], dims=['time'])
            
            # Sort lon/lat by increasing datetime and store in dictionary
            drifters[driftermat['drifters'][0][drifterid-1][0][0]] = {
                'lon': lons[lons.time.argsort()],
                'lat': lats[lats.time.argsort()]}

    return drifters
