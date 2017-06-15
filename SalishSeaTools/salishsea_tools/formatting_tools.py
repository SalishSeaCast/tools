# Copyright 2013-2017 The Salish Sea MEOPAR contributors
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

"""Functions for formatting data output from datasets.
"""

#: String to LaTeX notation mapping for units
STR_LATEX_MAPPING = {
    'm/s': 'm/s',
    'm2/s': 'm$^2$ / s$',
    'degrees_east': '$^\circ$E',
    'degrees_north': '$^\circ$N',
    'degC': '$^\circ$C',
    'g kg-1': 'g / kg',
    'g/kg': 'g / kg',
    'mmol m-3': 'mmol / $m^{3}$',
    'mmol/m3': 'mmol / $m^{3}$',
    'm2/s3': 'm$^2$ / s$^3$'
}


def format_units(units):
    """Convert unit string to LaTeX notation.

    :arg str units: Unit to convert.

    :returns: Units in LaTeX notation.
    :rtype: str
    """
    try:
        return STR_LATEX_MAPPING[units]
    except KeyError:
        raise KeyError(
            'units not found in string to LaTeX mapping: {}'.format(units))
