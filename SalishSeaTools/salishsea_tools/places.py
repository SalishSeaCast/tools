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
        # j is the longitude direction, i is the latitude direction
        'wind grid ji': (190, 102),
    },
    'Cherry Point': {
        'lon lat': (-122.766667, 48.866667),
        'stn number': 9449424,
        'mean sea lvl': 3.543,
        'hist max sea lvl': 5.846,
        'wind grid ji': (122, 166),
    },
    'Nanaimo': {
        'lon lat': (-123.93, 49.16),
        'mean sea lvl': 3.08,
        'hist max sea lvl': 5.47,
        'wind grid ji': (142, 133),
    },
    'Point Atkinson': {
        'lon lat': (-123.25, 49.33),
        'stn number': 7795,
        'mean sea lvl': 3.09,
        'hist max sea lvl': 5.61,
        'wind grid ji': (146, 155),
    },
    'Victoria': {
        'lon lat': (-123.36, 48.41),
        'stn number': 7120,
        'mean sea lvl': 1.8810,
        'hist max sea lvl': 3.76,
        'wind grid ji': (104, 144),
    },

    # Ferry terminals
    'Tsawwassen': {
        'lon lat': (-123.1281, 49.0084)
    },
    'Duke Pt.': {
        'lon lat': (-123.8909, 49.1632)
    },
    'Horseshoe Bay': {
        'lon lat': (-123.2728, 49.3742)
    },
    'Departure Bay': {
        'lon lat': (-123.8909, 49.1632)
    },
    'Swartz Bay': {
        'lon lat': (-123.4102, 48.6882),
    },

    # Cities
    'Vancouver': {
        'lon lat': (-123.1207, 49.2827)
    },
}
