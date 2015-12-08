# Copyright 2013-2015 The Salish Sea MEOPAR Contributors
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

"""Constants and functions for working with TEOS-10 salinity in the
Salish Sea NEMO model.

TEOS-10 is the Thermodynamic Equation of Seawater (2010).
See http://www.teos-10.org/.
"""
from __future__ import division


#: Conversion factor from practical salinity units (psu)
#: to TEOS-10 reference salinity
PSU_TEOS = 35.16504 / 35  # g/kg
#: Conversion factor from TEOS-10 reference salinity
#: to practical salinity units (psu)
TEOS_PSU = 35 / 35.16504  # kg/g


def psu_teos(psu):
    """Convert salinity in practical salinity units (psu) to TEOS-10
    reference salinity in g/kg.

    :arg float psu: Practical salinity units (psu) value to convert.

    :returns: TEOS-10 reference salinity in g/kg.
    :rtype: float
    """
    return psu * PSU_TEOS


def teos_psu(teos):
    """Convert TEOS-10 reference salinity in g/kg to salinity in
    practical salinity units (psu).

    :arg float psu: TEOS-10 reference salinity value [g/kg] to convert.

    :returns: Practical salinity units (psu) value.
    :rtype: float
    """
    return teos * TEOS_PSU
