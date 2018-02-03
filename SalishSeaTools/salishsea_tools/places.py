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
        # indices of nearest wave model grid point
        # j is the latitude (y) direction, i is the longitude (x) direction
        'ww3 grid ji': (453, 109)
    },
    'Cherry Point': {
        'lon lat': (-122.766667, 48.866667),
        'stn number': 9449424,
        'mean sea lvl': 3.543,
        'hist max sea lvl': 5.846,
        'wind grid ji': (122, 166),
        'NEMO grid ji': (343, 342),
        'ww3 grid ji': (193, 462),

    },
    'Friday Harbor': {
        'lon lat': (-123.016667, 48.55),
        'stn number': 9449880,
        'mean sea lvl': 2.561,
        'hist max sea lvl': 4.572,
        'wind grid ji': (108, 155),
        'NEMO grid ji': (300, 267),
        'ww3 grid ji': (124, 427),
    },
    'Halfmoon Bay': {
        'lon lat': (-123.912, 49.511),
        'NEMO grid ji': (549, 254),
        'wind grid ji': (158, 136),
        'ww3 grid ji': (331, 297),
        'mean sea lvl': 3.14,
        'hist max sea lvl': 5.61,      # copied from Point Atkinson
    },
    'Nanaimo': {
        'lon lat': (-123.93, 49.16),
        'stn number': 7917,
        'mean sea lvl': 3.08,
        'hist max sea lvl': 5.47,
        'wind grid ji': (142, 133),
        'NEMO grid ji': (484, 208),  # current a little different
        'ww3 grid ji': (261, 298),

    },
    'Neah Bay': {
        'lon lat': (-124.6, 48.4),
        'stn number': 9443090,
        'mean sea lvl': 1.925,
        'hist max sea lvl': 4.359,
        'wind grid ji': (111, 105),
        'NEMO grid ji': (384, 15),
        'ww3 grid ji': (89, 200),
    },
    'New Westminster': {
        'lon lat': (-122.90535, 49.203683),
        'stn number': 7654,
        'mean sea lvl': 1.881+0.6,  # correction for model mean sea lvl, messes up with datum though.  We should actually correct the model
        'hist max sea lvl': 4.66,
        'NEMO grid ji': (423, 363),
        'wind grid ji': (138, 164),
        # no nearby waves
    },
    'Patricia Bay': {
        'lon lat': (-123.4515, 48.6536),
        'stn number': 7277,
        'mean sea lvl': 2.256,
        'hist max sea lvl': 4.38,
        'NEMO grid ji': (351, 214),
        'wind grid ji': (115, 143),
        'ww3 grid ji': (145, 363),
    },
    'Point Atkinson': {
        'lon lat': (-123.25, 49.33),
        'stn number': 7795,
        'mean sea lvl': 3.09,
        'hist max sea lvl': 5.61,
        'wind grid ji': (146, 155),
        'NEMO grid ji': (468, 329),
        'ww3 grid ji': (296, 393),
    },
    'Port Renfrew': {
        'lon lat': (-124.421, 48.555),
        'stn number': 8525,
        'mean sea lvl': 1.937,
        'hist max sea lvl': 4.359,  # from Neah Bay
        'NEMO grid ji': (401, 61),
        'wind grid ji': (117, 112),
        'ww3 grid ji': (123, 226),
    },
    'Sandy Cove': {
        'lon lat': (-123.23, 49.34),
        'stn number': 7786,
        'NEMO grid ji': (468, 333),
        'wind grid ji': (146, 155),
        'ww3 grid ji': (294, 396),
        'mean sea lvl': 3.09,
        'hist max sea lvl': 5.61, # from Pt Atk
    },
    'Squamish': {
        'lon lat': (-123.155, 49.694),
        'stn number': 7811,
        'NEMO grid ji': (532, 389),
        'wind grid ji': (162, 160),
        'ww3 grid ji': (370, 404),
        'mean sea lvl': 3.14,
        'hist max sea lvl': 5.61 # from Pt Atk
    },
    'Victoria': {
        'lon lat': (-123.3707, 48.424666),
        'stn number': 7120,
        'mean sea lvl': 1.8810,
        'hist max sea lvl': 3.76,
        'wind grid ji': (104, 144),
        'NEMO grid ji': (302, 196),
        'ww3 grid ji': (90, 374),
    },
    'Woodwards Landing': {
        'lon lat': (-123.0754, 49.1251),
        'stn number': 7610,
        'hist max sea lvl': 4.66,  # based on New West
        'mean sea lvl': 2.215,
        'NEMO grid ji': (414, 329),
        'wind grid ji': (135, 138),
    },
    'Boundary Bay': {
        'lon lat': (-122.925, 49.0),
        'stn number': None,
        'hist max sea lvl': 5.61,            # based on Point Atk
        'mean sea lvl': 3.09,                # based on Point Atk
        'NEMO grid ji': (380, 335),
        'wind grid ji': (129, 162),
        'ww3 grid ji': (222, 439),
    },

    # Ferry terminals
    'Tsawwassen': {
        'lon lat': (-123.132722, 49.006165),
        'in berth radius': 0.0015,
    },
    'Duke Pt.': {
        'lon lat': (-123.89095676900132, 49.16340592936349),
        'in berth radius': 0.002,
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

    # STRATOGEM STATION S3(lat,lon)=(49 7.5 N, 123 33.5 W)
    'S3': {
        'lon lat': (-123.558, 49.125),
        'NEMO grid ji': (450, 258),
    },
    # Tereza's cluster stations, aligned with Vector Stations where possible.
    'Cluster_1': {
        'NEMO grid ji': (241, 212),
        'lon lat': (48.215, -123.099),
        'Vector Stn': '64'
    },
    'Cluster_2': {
        'NEMO grid ji': (294, 127),
        'lon lat': (48.261, -123.717),
        'Vector Stn': '69'
    },
    'Cluster_3': {
        'NEMO grid ji': (376, 291),
        'lon lat': (48.899, -123.138),
        'Vector Stn': '45'
    },
    'Cluster_4': {
        'NEMO grid ji': (282, 305),
        'lon lat': (48.555, -122.750),
        'Vector Stn': '53'
    },
    'Cluster_5': {
        'NEMO grid ji': (344, 271),
        'lon lat': (48.735, -123.135),
        'Vector Stn': '57'
    },
    'Cluster_6': {
        'NEMO grid ji': (320, 68),
        'lon lat': (48.249, -124.110),
        'Vector Stn': '73'
    },
    'Cluster_7': {
        'NEMO grid ji': (504, 246),
        'lon lat': (49.317, -123.801),
        'Vector Stn': '27'
    },
    'Cluster_8': {
        'NEMO grid ji': (646, 168),
        'lon lat': (49.726, -124.679),
        'Vector Stn': '12'
    },
    'Cluster_9': {
        'NEMO grid ji': (423, 300),
        'lon lat': (49.101, -123.249),
    },

    # VENUS
    'Central node': {
        # location from Ocean Networks Canada (ONC) website
        'lon lat': (-123.425825, 49.040066666),
        # depth in metres from ONC website
        'depth': 294,
        # NEMO python grid indices: j in y direction, i in x direction
        'NEMO grid ji': (424, 266),
        # ONC data web services API station code
        'ONC stationCode': 'SCVIP',
    },
    'Delta BBL node': {
        # ONC's description is "Delta/Lower Slope/Bottom Boundary Layer"
        'lon lat': (-123.339633, 49.074766),
        'depth': 143,
        'NEMO grid ji': (424, 283),
        'ONC stationCode': 'LSBBL',
    },
    'Delta DDL node': {
        # ONC's description is "Delta/Upper Slope/Delta Dynamics Laboratory"
        'lon lat': (-123.32972, 49.08495),
        'depth': 107,
        'NEMO grid ji': (426, 286),
        'ONC stationCode': 'USDDL',
    },
    'East node': {
        'lon lat': (-123.316836666, 49.04316),
        'depth': 164,
        'NEMO grid ji': (417, 283),
        'ONC stationCode': 'SEVIP',
    },

    # Lightstations
    'Sand Heads': {
        'lon lat': (-123.30, 49.10),
        'stn number': 7594,  # Marlene's coordinates for Tide Station are slightly different.  Leaving as is.
        'NEMO grid ji': (426, 293),  # match Domain file
        'mean sea lvl': 2.875,
        'hist max sea lvl': 5.61-3.09+2.875,  # based on Point Atk.
        'GEM2.5 grid ji': (135, 151),
        'wind grid ji': (135, 151),
        'ww3 grid ji': (246, 385),
    },
    'Sisters Islet': {
        'lon lat': (-124.43, 49.49),
        'NEMO grid ji': (582, 175),
        'GEM2.5 grid ji': (160, 120),
    },

    # Wave buoys
    'Halibut Bank': {
        'lon lat': (-123.72, 49.34),
        'NEMO grid ji': (503, 261),
        'GEM2.5 grid ji': (149, 141),
        'EC buoy number': 46146,
    },
    'Sentry Shoal': {
        'lon lat': (-125.0, 49.92),
        'NEMO grid ji': (707, 145),
        'GEM2.5 grid ji': (183, 107),
        'EC buoy number': 46131,
    }
}
# Aliases:
PLACES['Sandheads'] = PLACES['Sand Heads']


#: Names of tide gauge sites,
#: ordered from south and west to north and east.
#: These names are keys of the :py:data:`~salishsea_tools.places.PLACES` dict.
TIDE_GAUGE_SITES = (
    'Neah Bay', 'Victoria', 'Cherry Point', 'Point Atkinson', 'Nanaimo',
    'Campbell River',
)
#: Other tide sites, no wind data at these (just to keep the number of arrows under control)
SUPP_TIDE_SITES = (
    'Friday Harbor', 'Halfmoon Bay', 'Patricia Bay', 'Port Renfrew',
    'Squamish', 'Boundary Bay', 'Sand Heads',
)
