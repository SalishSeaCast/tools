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

"""Unit tests for evaltools module data loader functions."""

import arrow
import pandas
import pytest

from salishsea_tools import evaltools


class TestLoadFerryERDDAP:
    """Unit tests for the evaltools.load_ferry_ERDDAP() function."""

    @pytest.fixture
    def mock_erddapy(self, monkeypatch):
        class MockERDDAP:
            def __init__(self, server, protocol):
                pass

            def to_pandas(self, *args, **kwargs):
                mock_data = pandas.DataFrame(
                    {
                        "time (UTC)": pandas.date_range(
                            "2025-07-01", periods=3, freq="D"
                        ),
                        "latitude (degrees_north)": [48.5, 48.6, 48.7],
                        "longitude (degrees_east)": [-123.5, -123.6, -123.7],
                        "o2_concentration_corrected (ml/l)": [1.0, 1.1, 1.2],
                        "salinity (g/kg)": [30.0, 31.0, 32.0],
                        "temperature (degrees_Celcius)": [10, 11, 12],
                        "chlorophyll (ug/l)": [0, 0.5, 1.1],
                        "turbidity (NTU)": [5, 7.3, 12.2],
                        "nemo_grid_j (count)": [1, 2, 3],
                        "nemo_grid_i (count)": [4, 5, 6],
                    }
                )
                mock_data.set_index(["time (UTC)"], inplace=True)
                return mock_data

        monkeypatch.setattr(evaltools.erddapy, "ERDDAP", MockERDDAP)

    def test_load_ferry_erddap_default_variables(self, mock_erddapy):
        """Test loading data with the default variable list."""
        datelims = (arrow.get("2025-07-01"), arrow.get("2025-07-03"))
        result = evaltools.load_ferry_ERDDAP(datelims)

        assert not result.empty
        assert "dtUTC" in result.columns
        assert "Lat" in result.columns
        assert "Lon" in result.columns
        assert "oxygen (uM)" in result.columns
        assert "conservative temperature (oC)" in result.columns
        assert "salinity (g/kg)" in result.columns
        assert "chlorophyll (ug/l)" in result.columns
        assert "turbidity (NTU)" in result.columns
        assert "j" in result.columns
        assert "i" in result.columns

    def test_load_ferry_erddap_data_processing(self, mock_erddapy):
        """Test that the data is processed correctly after loading."""
        datelims = (arrow.get("2025-07-01"), arrow.get("2025-07-03"))

        result = evaltools.load_ferry_ERDDAP(datelims)

        # Verify data types and values
        assert isinstance(result, pandas.DataFrame)
        pandas.testing.assert_series_equal(
            result["dtUTC"],
            pandas.Series(
                ["2025-07-01", "2025-07-02", "2025-07-03"],
                dtype="datetime64[ns]",
                name="dtUTC",
            ),
        )
        pandas.testing.assert_series_equal(
            result["Lat"], pandas.Series([48.5, 48.6, 48.7], name="Lat")
        )
        pandas.testing.assert_series_equal(
            result["Lon"], pandas.Series([-123.5, -123.6, -123.7], name="Lon")
        )
        pandas.testing.assert_series_equal(
            result["oxygen (uM)"],
            pandas.Series([44.661, 1.1 * 44.661, 1.2 * 44.661], name="oxygen (uM)"),
        )
        pandas.testing.assert_series_equal(
            result["conservative temperature (oC)"],
            pandas.Series(
                [10.083100, 11.070570, 12.055291], name="conservative temperature (oC)"
            ),
        )
        pandas.testing.assert_series_equal(
            result["salinity (g/kg)"],
            pandas.Series([30.0, 31.0, 32.0], name="salinity (g/kg)"),
        )
        pandas.testing.assert_series_equal(
            result["chlorophyll (ug/l)"],
            pandas.Series([0.0, 0.5, 1.1], name="chlorophyll (ug/l)"),
        )
        pandas.testing.assert_series_equal(
            result["turbidity (NTU)"],
            pandas.Series([5.0, 7.3, 12.2], name="turbidity (NTU)"),
        )
        pandas.testing.assert_series_equal(
            result["j"], pandas.Series([1, 2, 3], name="j")
        )
        pandas.testing.assert_series_equal(
            result["i"], pandas.Series([4, 5, 6], name="i")
        )

    def test_load_ferry_erddap_empty_date_range(self, monkeypatch):
        """Test loading data for a date range with no available data."""

        class MockERDDAP:
            def __init__(self, server, protocol):
                pass

            def to_pandas(self, *args, **kwargs):
                mock_data = pandas.DataFrame({})
                return mock_data

        monkeypatch.setattr(evaltools.erddapy, "ERDDAP", MockERDDAP)

        datelims = (arrow.get("2025-07-01"), arrow.get("2025-07-03"))
        with pytest.raises(ValueError):
            evaltools.load_ferry_ERDDAP(datelims)

    def test_load_ferry_erddap_invalid_date_lims(self, mock_erddapy):
        """Test loading data with invalid date limits."""
        datelims = tuple()
        with pytest.raises(IndexError):
            evaltools.load_ferry_ERDDAP(datelims)
