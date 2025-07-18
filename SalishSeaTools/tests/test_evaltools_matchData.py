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

"""Unit tests for evaltools module matchData() function and its supporting functions."""

import pandas
import pytest

from salishsea_tools import evaltools


class TestReqdColsInDataFrame:
    """Unit tests for the _reqd_cols_in_data_frame() function."""

    def test_ferry_method_with_correct_columns(self):
        df = pandas.DataFrame({"dtUTC": [], "Lat": [], "Lon": []})
        result = evaltools._reqd_cols_in_data_frame(
            df, match_method="ferry", n_spatial_dims=2, pre_indexed=False
        )
        assert result == ["dtUTC", "Lat", "Lon"]

    def test_ferry_method_pre_indexed_with_correct_columns(self):
        df = pandas.DataFrame({"dtUTC": [], "i": [], "j": []})
        result = evaltools._reqd_cols_in_data_frame(
            df, match_method="ferry", n_spatial_dims=2, pre_indexed=True
        )
        assert result == ["dtUTC", "i", "j"]

    def test_vertNet_method_with_correct_columns(self):
        df = pandas.DataFrame(
            {"dtUTC": [], "Lat": [], "Lon": [], "Z_upper": [], "Z_lower": []}
        )
        result = evaltools._reqd_cols_in_data_frame(
            df, match_method="vertNet", n_spatial_dims=3, pre_indexed=False
        )
        assert result == ["dtUTC", "Lat", "Lon", "Z_upper", "Z_lower"]

    def test_vertNet_method_pre_indexed_with_correct_columns(self):
        df = pandas.DataFrame(
            {"dtUTC": [], "i": [], "j": [], "Z_upper": [], "Z_lower": []}
        )
        result = evaltools._reqd_cols_in_data_frame(
            df, match_method="vertNet", n_spatial_dims=3, pre_indexed=True
        )
        assert result == ["dtUTC", "i", "j", "Z_upper", "Z_lower"]

    def test_other_method_with_correct_columns(self):
        df = pandas.DataFrame({"dtUTC": [], "Lat": [], "Lon": [], "Z": []})
        result = evaltools._reqd_cols_in_data_frame(
            df, match_method="other", n_spatial_dims=3, pre_indexed=False
        )
        assert result == ["dtUTC", "Lat", "Lon", "Z"]

    def test_other_method_pre_indexed_with_correct_columns(self):
        df = pandas.DataFrame({"dtUTC": [], "i": [], "j": [], "k": []})
        result = evaltools._reqd_cols_in_data_frame(
            df, match_method="other", n_spatial_dims=3, pre_indexed=True
        )
        assert result == ["dtUTC", "i", "j", "k"]

    def test_missing_required_columns_raises_exception(self):
        df = pandas.DataFrame({"dtUTC": [], "Lat": []})  # Missing 'Lon'
        with pytest.raises(KeyError, match=r".*missing from data.*"):
            evaltools._reqd_cols_in_data_frame(
                df, match_method="ferry", n_spatial_dims=2, pre_indexed=False
            )


class TestCalcFileTypes:
    """Unit tests for the _calc_file_types() function."""

    def test_valid_file_types(self):
        model_file_hours_res = {"grid_T": 1, "biol_T": 24, "chem_T": 1}
        model_var_file_types = {"vosaline": "grid_T", "nitrate": "biol_T"}
        expected = ["grid_T", "biol_T"]
        result = evaltools._calc_file_types(model_file_hours_res, model_var_file_types)
        assert result == expected

    def test_unused_file_types_removed(self):
        model_file_hours_res = {"grid_T": 1, "biol_T": 24, "chem_T": 1}
        model_var_file_types = {"vosaline": "grid_T"}
        expected = ["grid_T"]
        result = evaltools._calc_file_types(model_file_hours_res, model_var_file_types)
        assert result == expected

    def test_missing_file_types_error(self):
        model_file_hours_res = {"grid_T": 1}
        model_var_file_types = {"vosaline": "grid_T", "nitrate": "biol_T"}
        expected = ["grid_T"]
        result = evaltools._calc_file_types(model_file_hours_res, model_var_file_types)
        assert result == expected

    def test_no_matching_file_types(self):
        model_file_hours_res = {"biol_T": 1, "chem_T": 1}
        model_var_file_types = {"vosaline": "grid_T"}
        expected = []
        result = evaltools._calc_file_types(model_file_hours_res, model_var_file_types)
        assert result == expected
