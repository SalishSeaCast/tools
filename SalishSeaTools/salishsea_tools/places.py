# Copyright 2013-2015 The Salish Sea MEOPAR contributors
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
    'Point Atkinson': {
        # deg N, deg E
        'lat lon': (49.33, -123.25),
        # Canadian Hydrographic Service (CHS)
        'stn number': 7795,
        # m above chart datum
        'mean sea lvl': 3.09,
        # m above chart datum
        'hist max sea lvl': 5.61,
        # indices of nearest weather forcing grid point
        # j is the longitue direction, i is the latitude direction
        'wind grid ji': (146, 155),
    },
}
