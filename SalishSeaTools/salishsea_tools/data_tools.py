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
from collections import OrderedDict
import datetime as dtm
import ftplib
import functools
import json
import logging
import re
import os
try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

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
import arrow.parser
import dateutil.parser as dparser
from dateutil import tz
import numpy as np
import requests
from retrying import retry
import scipy.interpolate
import scipy.io
import xarray
import pandas as pd
import zeep
import zeep.helpers

from salishsea_tools import (
    onc_sog_adcps,
    teos_tools,
)
from salishsea_tools.places import PLACES


logging.getLogger(__name__).addHandler(logging.NullHandler())


def load_drifters(
        deployments=range(1, 10),
        filename='driftersPositions.geojson',
        drifterpath='/ocean/rcostanz/Drifters/data'
):
    """Loads drifter coordinates and times from the ODL Drifters Project.

    UBC Ocean Dynamics Laboratory Drifters Project
    http://drifters.eoas.ubc.ca/
    Contact Rich Pawlowicz: rich@eos.ubc.ca
    Contact Romain Costanz: rcostanz@eos.ubc.ca

    :arg deployments: python iterable containing requested deployment numbers
        (ex. [1, 2, 5], range(1, 9), etc...)
    :type deployments: python iterable of integers

    :arg filename: Filename
    :type filename: str

    :arg drifterpath: Drifter data storage directory
    :type drifterpath: str

    :returns: Nested ordered dictionaries of xarray dataset objects.
    :rtype: :py:class:`collections.OrderedDict` >
            :py:class:`collections.OrderedDict` >
            :py:class:`xarray.Dataset`
    """

    # Preallocate output dictionary
    drifters = OrderedDict()

    # Iterate through deployment directories
    for deployment_num in deployments:

        # Deployment ID
        deployment = 'deployment{}'.format(deployment_num)

        # Preallocate deployment dictionary
        drifters[deployment] = OrderedDict()

        # Open deployment file
        filepath = os.path.join(drifterpath, deployment, filename)
        with open(filepath) as data_file:
            data = json.load(data_file)

        # Iterate through drifters in deployment
        for drifter in data['features']:

            # Extract lon/lat values
            lon, lat = zip(*drifter['geometry']['coordinates'])

            # Parse date strings into python datetime
            pytime = [dparser.parse(t) for t in drifter['properties']['dateTime']]

            # Combine lon/lat/time into xarray Dataset
            unsorted = xarray.Dataset({
                'lon': ('time', list(lon)),
                'lat': ('time', list(lat))},
                coords={'time': pytime})

            # Get time-sorted indices
            index = unsorted.time.argsort()

            # Make a new sorted Dataset for each drifter
            drifters[deployment][drifter['properties']['title']] = xarray.Dataset({
                'lon': unsorted.lon[index],
                'lat': unsorted.lat[index]})

    return drifters


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

    :arg station: Requested profile location ('central', 'east', or 'ddl')
    :type station: str

    :arg adcp_data_dir: ADCP file storage location
    :type adcp_data_dir: str

    :returns: :py:class:`xarray.Dataset` of zonal u and meridional v velocity
        with time and depth dimensions.
    :rtype: 2-D, 2 element :py:class:`xarray.Dataset`
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
                    https://data.oceannetworks.ca/Profile

    :arg dict query_params: Query parameters expressed as key/value pairs.

    :returns: Mapping created from the JSON content of the response from the
              data web service
    :rtype: dict
    """
    url_tmpl = 'https://data.oceannetworks.ca/api/{endpoint}?{query}'
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
        if sensor['sensorName'] == 'Practical Salinity' and teos:
            data = teos_tools.psu_teos([d['value'] for d in sensor['data']])
            sensor['sensorName'] = 'Reference Salinity'
            sensor['unitOfMeasure'] = 'g/kg'
        else:
            data = [d['value'] for d in sensor['data']]
        data_vars[sensor['sensor']] = xarray.DataArray(
            name=sensor['sensor'],
            data=data,
            coords={
                'sampleTime': [arrow.get(d['sampleTime']).naive for d in sensor['data']],
            },
            dims=('sampleTime',),
            attrs={
                'qaqcFlag': np.array([d['qaqcFlag'] for d in sensor['data']]),
                'sensorName': sensor['sensorName'],
                'unitOfMeasure': sensor['unitOfMeasure'],
                'actualSamples': sensor['actualSamples'],
            }
        )
    return xarray.Dataset(data_vars, attrs=onc_json['serviceMetadata'])


def get_chs_tides(data_type, stn_id, begin, end, retry_args={
        'wait_exponential_multiplier': 1000,
        'wait_exponential_max': 30000,
        'stop_max_delay': 36000,
    }):
    """Retrieve a time series of observed or predicted water levels for a CHS
    recording tide gauge station from the https://ws-shc.qc.dfo-mpo.gc.ca/
    web service for the date/time range given by begin and end.

    The time series is returned as a :py:class:`pandas.Series` object.

    The values of begin and end, and the returned time series date/time index
    are all UTC.

    Water levels are relative to chart datum for the station requested.

    :param str data_type: Type of data to retrieve; :kbd:`obs` or :kbd:`pred`.

    :param int or str stn_id: Tide gauge station number or name.
                              Names use
                              :py:object:`~salishsea_tools.places.PLACES` to
                              look up the station number.

    :param begin: UTC beginning date or date/time for data request.
                  If a date only is used the time defaults to 00:00:00.
    :type begin: str or :py:class:`arrow.Arrow`

    :param end: UTC end date or date/time for data request.
                If a date only is used the time defaults to 00:00:00.
    :type end: str or :py:class:`arrow.Arrow`

    :param dict retry_args: Key/value pair arguments to control how the request
                            is retried should it fail the first time.
                            The defaults provide a 2^x * 1 second exponential
                            back-off between each retry, up to 30 seconds,
                            then 30 seconds afterwards, to a maximum of 10 minutes
                            of retrying.
                            See https://pypi.python.org/pypi/retrying for a full
                            discussion of the parameters available to control
                            retrying.

    :return: Water level time series.
    :rtype: :py:class:`pandas.Series`
    """
    valid_data_types = {
        # keyed by data_type arg value
        'obs': {
            # endpoint data type word
            'endpoint': 'observations',
            # search service data name
            'data name': 'wl',
        },
        'pred': {
            'endpoint': 'predictions',
            'data name': 'wl15',
        },
    }
    if data_type not in valid_data_types:
        raise ValueError(
            'invalid data_type: {data_type}; please use one of '
            '{valid_data_types}'.format(
                data_type=data_type,
                valid_data_types=set(valid_data_types.keys())))
    endpoint_tmpl = 'https://ws-shc.qc.dfo-mpo.gc.ca/{data_type}?WSDL'
    endpoint = endpoint_tmpl.format(
        data_type=valid_data_types[data_type]['endpoint'])
    data_name = valid_data_types[data_type]['data name']
    msg = (
        'retrieving {data_type} water level data from {endpoint}'.format(
            data_type=data_type, endpoint=endpoint)
    )
    try:
        stn_number = '{:05d}'.format(stn_id)
    except ValueError:
        try:
            stn_number = '{:05d}'.format(PLACES[stn_id]['stn number'])
        except KeyError as e:
            logging.error(
                'station id not found in places.PLACES: {station_id}; '
                'maybe try an integer station number?'.format(
                    station_id=stn_id))
            return
    if int(stn_number) == stn_id:
        msg = ' '.join((
            msg,
            'for station {stn_number}'.format(
                endpoint=endpoint, stn_number=stn_number))
        )
    else:
        msg = ' '.join((
            msg,
            'for station {stn_number} {stn_id}'.format(
                endpoint=endpoint, stn_number=stn_number, stn_id=stn_id))
        )
    try:
        if not hasattr(begin, 'range'):
            begin = arrow.get(begin)
    except arrow.parser.ParserError:
        logging.error('invalid start date/time: {}'.format(begin))
        return
    msg = ' '.join((
        msg, 'from {begin}'.format(begin=begin.format('YYYY-MM-DD HH:mm:ss'))
    ))
    try:
        if not hasattr(end, 'range'):
            end = arrow.get(end)
    except arrow.parser.ParserError:
        logging.error('invalid end date/time: {}'.format(end))
        return
    msg = ' '.join((
        msg, 'to {end}'.format(end=end.format('YYYY-MM-DD HH:mm:ss'))
    ))
    logging.info(msg)
    client = zeep.Client(endpoint)
    lat_min, lat_max = -90, 90
    lon_min, lon_max = -180, 180
    depth_min, depth_max = 0, 0
    first_value = 1
    n_values = 1000
    metadata, order = True, 'asc'
    datetimes, water_levels = [], []
    search_begin = begin
    while search_begin < end:
        @retry(**retry_args)
        def search_service(
            data_name, lat_min, lat_max, lon_min, lon_max, depth_min, depth_max,
            begin, end, first_value, n_values, metadata, stn_number, order
        ):
            return client.service.search(
                data_name, lat_min, lat_max, lon_min, lon_max, depth_min, depth_max,
                begin, end, first_value, n_values, metadata, stn_number, order
            )
        response = search_service(
            data_name, lat_min, lat_max, lon_min, lon_max, depth_min, depth_max,
            search_begin.format('YYYY-MM-DD HH:mm:ss'),
            end.format('YYYY-MM-DD HH:mm:ss'),
            first_value, n_values, metadata, 'station_id={}'.format(stn_number),
            order
        )
        response = zeep.helpers.serialize_object(response)
        if response['size'] <= 1:
            break
        datetimes.extend(d['boundaryDate']['min'] for d in response['data'])
        water_levels.extend(float(d['value']) for d in response['data'])
        search_begin = arrow.get(datetimes[-1])
    name = (
        '{stn_number} water levels' if int(stn_number) == stn_id
        else '{stn_number} {stn_id} water levels').format(
        stn_number=stn_number, stn_id=stn_id)
    time_series = pd.Series(
        data=water_levels, index=pd.to_datetime(datetimes), name=name
    )
    return time_series


def request_onc_sog_adcp(date, node, userid):
    """Request a :kbd:`.mat` file of ADCP data for 1 day from an
    Ocean Networks Canada (ONC) node in the Strait of Georgia.

    This function relies on a soon-to-be-deprecated ONC web service.
    It is based on a Matlab script provided by Marlene Jefferies of ONC.
    It is primarily intended for use in an automation pipeline that also
    includes ADCP data processing Matlab scripts developed by Rich Pawlowicz
    of UBC EOAS.

    :arg str date: Date for which to request the ADCP data.

    :arg str node: Strait of Georgia node for which to request the ONC data;
                   must be a key in
                   :py:obj:`salishsea_tools.onc_sog_adcps.deployments`
                   (e.g. "Central node").

    :arg str userid: Email address associated with an ONC data.oceannetworks.ca account.

    :returns: Search info data provided by the ONC data service;
              contains search header id.
    :rtype: dict
    """
    SERVICE_URL = 'https://data.oceannetworks.ca/VSearchByInstrumentServiceAjax'
    data_date = arrow.get(
        *map(int, date.split('-')), tzinfo=tz.gettz('Canada/Pacific'))
    query = _build_adcp_query(data_date, node, userid)
    @retry(wait_exponential_multiplier=1*1000, wait_exponential_max=30*1000)
    def _requests_get():
        return requests.get(SERVICE_URL, query)
    response = _requests_get()
    response.raise_for_status()
    search_info = json.loads(response.text.lstrip('(').rstrip().rstrip(')'))
    return search_info


def _build_adcp_query(data_date, node, userid):
    """Build the query parameters for
    :py:func:`~salishsea_tools.data_tools_get_onc_sog_adcp_mat`.

    :arg data_date: Date for which to request the ADCP data.
    :type data_date: :py:class:`arrow.Arrow`

    :arg str node: Strait of Georgia node for which to request the ONC data;
                   must be a key in
                   :py:obj:`salishsea_tools.onc_sog_adcps.deployments`
                   (e.g. "Central node").

    :arg str userid: Email address associated with an ONC data.oceannetworks.ca account.

    :rtype: dict
    """
    OPERATION = 0  # createAndRunSearch()
    MAT_FILE_FORMAT = 3  # Matlab v7
    REGION_ID = 2  # Strait of Georgia
    META = 23  # HTML metadata
    try:
        location_id = onc_sog_adcps.deployments[node]['location id']
    except KeyError:
        raise KeyError(
            'Unrecognized node name: {}; must be one of {}'
            .format(node, set(onc_sog_adcps.deployments.keys())))
    for depl in onc_sog_adcps.deployments[node]['history']:
        if depl.start < data_date <= depl.end:
            deployment = depl
            break
    else:
        raise ValueError(
            'No ADCP deployment found for {} on {}'.format(node, data_date))
    try:
        device_id = onc_sog_adcps.adcps[deployment.serial_no].device_id
        sensor_id = onc_sog_adcps.adcps[deployment.serial_no].sensor_id
    except KeyError:
        raise KeyError(
            'Unrecognized ADCP serial number: {}; must be one of {}'
                .format(deployment.serial_no, set(onc_sog_adcps.adcps.keys())))
    query = {
        'operation': OPERATION,
        'userid': userid,
        'dataformatid': MAT_FILE_FORMAT,
        'timefrom': data_date.replace(hour=0).format('DD-MMM-YYYY HH:mm:ss'),
        'timeto':
            data_date.replace(hour=0, days=+1).format('DD-MMM-YYYY HH:mm:ss'),
        'deviceid': device_id,
        'sensorid': sensor_id,
        'regionid': REGION_ID,
        'locationid': location_id,
        'siteid': deployment.site_id,
        'meta': META,
        'params': '{"qc":"1","avg":"0","rotVar":"0"}',
    }
    return query


def get_onc_sog_adcp_search_status(search_hdr_id, userid):
    """Return a JSON blob containing information about the status of a search
    for ADCP data from an Ocean Networks Canada (ONC) node in the Strait of
    Georgia.

    :arg int search_hdr_id: ONC search header id.

    :arg str userid: Email address associated with an ONC data.oceannetworks.ca account.

    This function relies on a soon-to-be-deprecated ONC web service.
    It is based on a Matlab script provided by Marlene Jefferies of ONC.
    It is primarily intended for debugging requests produced by
    :py:func:`~salishsea_tools.data_tools.get_onc_sog_adcp_mat`.
    """
    SERVICE_URL = 'https://data.oceannetworks.ca/VSearchByInstrumentServiceAjax'
    OPERATION = 1  # getSearchResult()
    query = {
        'operation': OPERATION,
        'userid': userid,
        'searchHdrId': search_hdr_id,
    }
    @retry(wait_exponential_multiplier=1*1000, wait_exponential_max=30*1000)
    def _requests_get():
        return requests.get(SERVICE_URL, query)
    response = _requests_get()
    response.raise_for_status()
    search_info = json.loads(response.text.lstrip('(').rstrip().rstrip(')'))
    return search_info


def get_onc_sog_adcp_mat(date, search_info, dest_path, userno):
    """Download a :kbd:`.mat` file of ADCP data for 1 day from an
    Ocean Networks Canada (ONC) node in the Strait of Georgia.

    This function relies on a soon-to-be-deprecated ONC web service.
    It is based on a Matlab script provided by Marlene Jefferies of ONC.
    It is primarily intended for use in an automation pipeline that also
    includes ADCP data processing Matlab scripts developed by Rich Pawlowicz
    of UBC EOAS.

    :arg str date: Date for which to request the ADCP data.

    :arg str node: Strait of Georgia node for which to request the ONC data;
                   must be a key in
                   :py:obj:`salishsea_tools.onc_sog_adcps.deployments`
                   (e.g. "Central node").

    :arg str dest_path: Path at which to store the downloaded :kbd:`.mat` file.

    :arg str userno: User number with an ONC data.oceannetworks.ca account.

    :rtype: str
    """
    FTP_SERVER = 'ftp.neptunecanada.ca'
    FTP_PATH_TMPL = (
        'pub/user{userno}/searchHeader{searchHdrId}/'
        '{data_date.year}/{data_date.month:02d}')
    data_date = arrow.get(
        *map(int, date.split('-')), tzinfo=tz.gettz('Canada/Pacific'))
    ftp_path = FTP_PATH_TMPL.format(
        data_date=data_date, userno=userno,
        searchHdrId=search_info['searchHdrId'])
    with ftplib.FTP(FTP_SERVER) as ftp:
        ftp.login()
        _poll_onc_ftp_path(ftp, ftp_path)
        filepath = _get_onc_adcp_matfile_name(ftp, ftp_path)
        downloaded_file = _get_onc_sog_adcp_matfile(
            ftp, filepath, Path(dest_path))
    return str(downloaded_file)


def _retry_if_not_matfile(mlsd):
    """Return :py:obj:`True` (i.e. retry) when the :kbd:`.mat` file is not
    found, and :py:obj:`False` (i.e. stop retrying) when the :kbd:`.mat` file
    is present.

    For use by :py:func:`~salishsea_tools.data_tools_get_onc_sog_adcp_mat`.
    """
    for filename, facts in mlsd:
        if not filename.startswith('.'):
            return os.path.splitext(filename)[1] != '.mat'
    return True


def _retry_if_ftp_error(exception):
    """Return :py:obj:`True` if exception is an FTP error,
    otherwise :py:obj:`False`.

    For use by :py:func:`~salishsea_tools.data_tools_get_onc_sog_adcp_mat`.
    """
    return any((
        isinstance(exception, ftplib.error_reply),
        isinstance(exception, ftplib.error_temp),
        isinstance(exception, ftplib.error_perm),
        isinstance(exception, ftplib.error_proto),
    ))


@retry(
    retry_on_exception=_retry_if_ftp_error,
    wrap_exception=True,
    wait_fixed=60*1000,
    stop_max_delay=120*60*1000,
)
@retry(
    retry_on_result=_retry_if_not_matfile,
    wait_fixed=60*1000,
    stop_max_delay=120*60*1000,
)
def _poll_onc_ftp_path(ftp, path):
    """Return a generator that yields elements of a directory listing in a
    standardized format by using MLSD command (RFC 3659).

    For use by :py:func:`~salishsea_tools.data_tools_get_onc_sog_adcp_mat`.
    """
    return ftp.mlsd(path)


@retry(
    retry_on_exception=_retry_if_ftp_error,
    wrap_exception=True,
    wait_exponential_multiplier=5*1000,
    wait_exponential_max=60*1000,
)
def _get_onc_adcp_matfile_name(ftp, path):
    """Return the file path and name of the requested ADCP :kbd:`.mat` file.

    For use by :py:func:`~salishsea_tools.data_tools_get_onc_sog_adcp_mat`.

    :rtype: :py:class:`pathlib.Path`
    """
    for filename, facts in ftp.mlsd(path):
        if os.path.splitext(filename)[1] == '.mat':
            return Path(path)/filename


@retry(
    retry_on_exception=_retry_if_ftp_error,
    wrap_exception=True,
    wait_exponential_multiplier=5*1000,
    wait_exponential_max=60*1000,
)
def _get_onc_sog_adcp_matfile(ftp, filepath, dest):
    """Download the ADCP :kbd:`.mat` file to the directory given by dest.

    For use by :py:func:`~salishsea_tools.data_tools_get_onc_sog_adcp_mat`.

    :rtype: :py:class:`pathlib.Path`
    """
    dest_path = dest/filepath.name
    ftp.retrbinary('RETR {}'.format(filepath), dest_path.open('wb').write)
    return dest_path


def load_nowcast_station_tracers(
    tracers,
    stations,
    months,
    hours,
    depth_indices,
    file_ending = "ptrc_T.nc",
    nowcast_dir="/results/SalishSea/nowcast-green/",
    save_path=None,
    verbose = True,
):
    """Iterate through nowcast results directory, return tracer data that
    matches request in pandas dataframe.

    Example:

    .. code-block:: python

        station_phy2 = load_nowcast_station_tracers(
            tracers = ["PHY2"],
            stations = {'BS1': (636, 126),'BS11': (605, 125)},
            months = ['apr'],
            hours = [0,6,12,18],
            depth_indices = range(20),
        )

    Returns pandas dataframe with this format::

        STATION  HOUR      DEPTH      PHY2       DATE  MONTH
        0      BS11     0   0.500000  3.903608 2016-04-06      4
        1      BS11     0   1.500003  4.114840 2016-04-06      4
        2      BS11     0   2.500011  5.080880 2016-04-06      4
        3      BS11     0   3.500031  5.082539 2016-04-06      4
        4      BS11     0   4.500071  5.076756 2016-04-06      4
        5      BS11     0   5.500151  5.030882 2016-04-06      4
        6      BS11     0   6.500310  4.975801 2016-04-06      4
    """
    month_num = {"jan": "01","feb": "02", "mar": "03", "apr": "04",
                 "may": "05", "jun": "06", "jul": "07", "aug": "08",
                 "sep": "09", "oct": "10", "nov": "11", "dec": "12" }
    station_names = list(stations.keys())
    station_points = stations.values()
    model_js = [x[0] for x in station_points]
    model_is = [x[1] for x in station_points]

    mixed_format_dates = os.listdir(nowcast_dir)
    number_format_dates = ["20" + x[5:7] + month_num[x[2:5]] + x[0:2] for x in mixed_format_dates]
    sorted_dirs = [mixed_format_date for (number_format_date, mixed_format_date) in sorted(zip(number_format_dates,mixed_format_dates))]

    dataframe_list = []
    num_files = 0
    start_time = dtm.datetime.now()

    for subdir in sorted_dirs:
        if os.path.isdir(nowcast_dir + '/' + subdir) and re.match("[0-9]{2}[a-z]{3}[0-9]{2}", subdir):
            month_str = subdir[2:5]
            date_str = "20" + subdir[5:7] + month_num[month_str] + subdir[0:2]
            tracer_file = "SalishSea_1h_" + date_str + "_" + date_str + "_" + file_ending
            tracer_path = nowcast_dir + "/" + subdir + "/" + tracer_file
            if os.path.isfile(tracer_path) and month_str in months:
                grid_t = xarray.open_dataset(tracer_path)
                result_hours = pd.DatetimeIndex(grid_t.time_centered.values).hour
                time_indices = np.where([(x in hours) for x in result_hours])

                J, T, Z = np.meshgrid(model_js,time_indices,depth_indices, indexing = 'ij')
                I, T, Z = np.meshgrid(model_is,time_indices,depth_indices, indexing = 'ij')

                tracer_dataframes = []
                for trc in tracers:
                    station_slice = grid_t[trc].values[T,Z,J,I]
                    slice_xarray = xarray.DataArray(station_slice,
                                     [station_names,result_hours[time_indices], grid_t.deptht.values[depth_indices]],
                                     ["STATION", "HOUR", "DEPTH"],
                                     trc)
                    slice_dataframe = slice_xarray.to_dataframe()
                    slice_dataframe.reset_index(inplace = True)
                    tracer_dataframes.append(slice_dataframe)
                merged_tracers = functools.reduce(lambda left,right: pd.merge(left,right,on=["STATION", "HOUR", "DEPTH"]), tracer_dataframes)
                merged_tracers["DATE"] =  pd.to_datetime(date_str, infer_datetime_format=True)
                merged_tracers["MONTH"] = int(month_num[month_str])
                dataframe_list.append(merged_tracers)

                num_files = num_files + 1
                if verbose:
                    run_time = dtm.datetime.now() - start_time
                    print("Files loaded:" + str(num_files))
                    print("Date of most recent nowcast load: " + date_str)
                    print("Time loading: ")
                    print(run_time)
    if verbose:
        print("Files loaded:" + str(num_files))

    nowcast_df = pd.concat(dataframe_list)

    if save_path is not None:
        nowcast_df.to_pickle(save_path)
        if verbose:
            print("Done, dataframe saved to: " + save_path)
    return(nowcast_df)
