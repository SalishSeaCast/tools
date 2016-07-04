# Copyright 2013-2016 The Salish Sea MEOPAR contributors
# and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Salish Sea NEMO model geographic places information.

It is recommended that library code that uses the :py:data:`PLACES` data
structure from this module should use :kbd:`try...except` to catch
:py:exc:`KeyError` exceptions and produce an error message that is more
informative than the default, for example:

.. code-block:: python

    try:
        max_tide_ssh = max(ttide.pred_all) + PLACES[site_name]['mean sea lvl']
        max_historic_ssh = PLACES[site_name]['hist max sea lvl']
    except KeyError as e:
        raise KeyError(
            'place name or info key not found in '
            'salishsea_tools.places.PLACES: {}'.format(e))
"""


#: Information about geographic places used in the analysis and
#: presentation of Salish Sea NEMO model results.
PLACES = {
    # Tide gauge stations
    'Campbell River': {
        # deg E, deg N
        'lon lat': (-125.24, 50.04),
        # Canadian Hydrographic Service (CHS) or NOAA
        'stn number': 8074,
        # m above chart datum
        'mean sea lvl': 2.916,
        # m above chart datum
        'hist max sea lvl': 5.35,
        # indices of nearest weather forcing grid point
        # j is the latitude (y) direction, i is the longitude (x) direction
        'wind grid ji': (190, 102),
        # indices of nearest NEMO model grid point
        # j is the latitude (y) direction, i is the longitude (x) direction
        'NEMO grid ji': (747, 125),
    },
    'Cherry Point': {
        'lon lat': (-122.766667, 48.866667),
        'stn number': 9449424,
        'mean sea lvl': 3.543,
        'hist max sea lvl': 5.846,
        'wind grid ji': (122, 166),
        'NEMO grid ji': (343, 341),
    },
    'Nanaimo': {
        'lon lat': (-123.93, 49.16),
        'mean sea lvl': 3.08,
        'hist max sea lvl': 5.47,
        'wind grid ji': (142, 133),
        'NEMO grid ji': (484, 208),
    },
    'Point Atkinson': {
        'lon lat': (-123.25, 49.33),
        'stn number': 7795,
        'mean sea lvl': 3.09,
        'hist max sea lvl': 5.61,
        'wind grid ji': (146, 155),
        'NEMO grid ji': (468, 329),
    },
    'Victoria': {
        'lon lat': (-123.36, 48.41),
        'stn number': 7120,
        'mean sea lvl': 1.8810,
        'hist max sea lvl': 3.76,
        'wind grid ji': (104, 144),
        'NEMO grid ji': (297, 197),
    },

    # Ferry terminals
    'Tsawwassen': {
        'lon lat': (-123.1281, 49.0084),
    },
    'Duke Pt.': {
        'lon lat': (-123.8909, 49.1632),
    },
    'Horseshoe Bay': {
        'lon lat': (-123.2728, 49.3742),
    },
    'Departure Bay': {
        'lon lat': (-123.8909, 49.1632),
    },
    'Swartz Bay': {
        'lon lat': (-123.4102, 48.6882),
    },

    # Cities
    'Vancouver': {
        'lon lat': (-123.1207, 49.2827),
    },

    # Provinces and states
    'British Columbia': {
        'lon lat': (-123.6, 49.9),
    },
    'Washington State': {
        'lon lat': (-123.8, 47.8),
    },

    # Bodies of water
    'Pacific Ocean': {
        'lon lat': (-125.6, 48.1),
    },
    'Juan de Fuca Strait': {
        'lon lat': (-124.7, 48.47),
    },
    'Puget Sound': {
        'lon lat': (-122.67, 48),
    },
    'Strait of Georgia': {
        'lon lat': (-123.8, 49.3),
    },

    # VENUS
    'East node': {
        'lon lat': (-123.3176, 49.0419),
        # depth in m, taken from ONC website
        'depth': 170,
        # NEMO python grid indices: j in y direction, i in x direction
        'NEMO grid ji': (416, 283),
        # Ocean Networks Canada (ONC) data web services API station code
        'ONC stationCode': 'SEVIP',
    },
    'Central node': {
        'lon lat': (-123.4261, 49.0401),
        'depth': 300,
        'NEMO grid ji': (424, 266),
        'ONC stationCode': 'SCVIP',
    },
    'DDL node': {
        # ONC's description is "Delta/Lower Slope/Bottom Boundary Layer"
        'lon lat': (-123.3400617, 49.0807167),
        'depth': 143,
        'NEMO grid ji': (425, 284),
        'ONC stationCode': 'LSBBL',
    },

    # Weather buoys
    'Sandheads': {
        'lon lat': (-123.30, 49.10),
        'NEMO grid ji': (426, 292),
    }

}


#: Names of tide gauge sites,
#: ordered from south and west to north and east.
#: These names are keys of the :py:data:`~salishsea_tools.places.PLACES` dict.
TIDE_GAUGE_SITES = (
    'Victoria', 'Cherry Point', 'Point Atkinson', 'Nanaimo', 'Campbell River',
)
