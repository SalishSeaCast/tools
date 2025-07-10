# Copyright 2013 – present by the SalishSeaCast contributors
# and The University of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for SalishSeaTools formatting_tools module."""

import pytest

from salishsea_tools.formatting_tools import format_units


class TestFormatUnits:
    """Unit tests for the format_units() function."""

    @pytest.mark.parametrize(
        "units, expected_output",
        [
            ("m/s", "m/s"),
            ("m2/s", "m$^2$ / s$"),
            ("degrees_east", "$^\\circ$E"),
            ("degrees_north", "$^\\circ$N"),
            ("degC", "$^\\circ$C"),
            ("g kg-1", "g / kg"),
            ("g/kg", "g / kg"),
            ("mmol m-3", "mmol / $m^{3}$"),
            ("mmol/m3", "mmol / $m^{3}$"),
            ("m2/s3", "m$^2$ / s$^3$"),
        ],
    )
    def test_format_units_valid(self, units, expected_output):
        """Test valid unit conversion to LaTeX notation."""
        assert format_units(units) == expected_output

    @pytest.mark.parametrize(
        "invalid_units",
        [
            "invalid_unit",
            "",
            None,
        ],
    )
    def test_format_units_invalid(self, invalid_units):
        """Test invalid unit conversion raises KeyError."""
        with pytest.raises(
            KeyError, match=r"units not found in string to LaTeX mapping"
        ):
            format_units(invalid_units)
