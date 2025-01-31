# Copyright 2013 – present by the SalishSeaCast contributors
# and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for SalishSeaTools stormtools module.
"""
import os
from unittest.mock import Mock

from dateutil import tz
import pandas
import pytest

from salishsea_tools import stormtools


class TestStormSurgeRiskLevel:
    """Unit tests for storm_surge_risk_level() function."""

    def test_places_key_error(self):
        m_ttide = Mock(name="ttide", pred_all=[42])
        with pytest.raises(KeyError):
            stormtools.storm_surge_risk_level("foo", 42.24, m_ttide)

    @pytest.mark.parametrize(
        "max_ssh, expected",
        [
            (4.9, None),
            (5.1, "moderate risk"),
            (5.4, "extreme risk"),
        ],
    )
    def test_risk_level(self, max_ssh, expected):
        m_ttide = Mock(name="ttide", pred_all=[2])
        risk_level = stormtools.storm_surge_risk_level(
            "Point Atkinson", max_ssh, m_ttide
        )
        assert risk_level == expected


class TestLoadTidalPredictions:
    """Unit tests for load_tidal_predictions() function."""

    @staticmethod
    @pytest.fixture
    def tmp_csv_file(tmp_path):
        """Create a temporary CSV file for testing."""
        desc_line = (
            "Harmonics from,/home/sallen/MEOPAR/tidal_constituents/tide_data/07786const.wlev,"
            "Time zone,PST,''"
        )
        msl_line = "Mean (m),3.090000,Z0 constituent,''"
        lat_line = "Latitude,'',''"
        test_data = (
            "time , pred_8 , pred_all , pred_noshallow \n"
            "30-Dec-2006 00:05:00 , 0.078625, -0.049689, -0.075132\n"
            "30-Dec-2006 00:15:00 , 0.162499, 0.038772, 0.011968\n"
            "30-Dec-2006 00:25:00 , 0.242253, 0.123667, 0.095479\n"
        )
        filename = tmp_path / "test_tidal_predictions.csv"
        content = f"{desc_line}\n{msl_line}\n{lat_line}\n{test_data}"
        filename.write_text(content)
        return filename

    def test_load_tidal_predictions_returns_dataframe_and_msl(self, tmp_csv_file):
        ttide, msl = stormtools.load_tidal_predictions(os.fspath(tmp_csv_file))

        # Verify mean sea level
        assert msl == 3.09

        # Verify DataFrame contents
        expected_data = {
            "time": pandas.to_datetime(
                ["2006-12-30 00:05:00", "2006-12-30 00:15:00", "2006-12-30 00:25:00"]
            )
            .tz_localize(tz.tzoffset("PST", -8 * 60 * 60))
            .tz_convert("UTC"),
            "pred_8": [0.078625, 0.162499, 0.242253],
            "pred_all": [-0.049689, 0.038772, 0.123667],
            "pred_noshallow": [-0.075132, 0.011968, 0.095479],
        }
        expected_df = pandas.DataFrame(expected_data)
        pandas.testing.assert_frame_equal(ttide.reset_index(drop=True), expected_df)

    def test_load_tidal_predictions_raises_file_not_found_error(self):
        with pytest.raises(FileNotFoundError):
            stormtools.load_tidal_predictions("non_existent_file.csv")

    def test_load_tidal_predictions_invalid_file_format(self, tmp_path):
        invalid_file = tmp_path / "invalid_data.csv"
        invalid_file.write_text("Invalid Header Line\nWrong Data Format\n")

        with pytest.raises(IndexError):
            stormtools.load_tidal_predictions(os.fspath(invalid_file))
