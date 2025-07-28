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
import os
from datetime import datetime

import numpy
import pandas
import pytest
import xarray

from salishsea_tools import evaltools


class TestReqdColsInDataFrame:
    """Unit tests for the _reqd_cols_in_data_frame() function."""

    def test_ferry_method_with_correct_columns(self):
        df = pandas.DataFrame({"dtUTC": [], "Lat": [], "Lon": []})
        reqd_cols = evaltools._reqd_cols_in_data_frame(
            df, match_method="ferry", n_spatial_dims=2, pre_indexed=False
        )
        assert reqd_cols == ["dtUTC", "Lat", "Lon"]

    def test_ferry_method_pre_indexed_with_correct_columns(self):
        df = pandas.DataFrame({"dtUTC": [], "i": [], "j": []})
        reqd_cols = evaltools._reqd_cols_in_data_frame(
            df, match_method="ferry", n_spatial_dims=2, pre_indexed=True
        )
        assert reqd_cols == ["dtUTC", "i", "j"]

    def test_vertNet_method_with_correct_columns(self):
        df = pandas.DataFrame(
            {"dtUTC": [], "Lat": [], "Lon": [], "Z_upper": [], "Z_lower": []}
        )
        reqd_cols = evaltools._reqd_cols_in_data_frame(
            df, match_method="vertNet", n_spatial_dims=3, pre_indexed=False
        )
        assert reqd_cols == ["dtUTC", "Lat", "Lon", "Z_upper", "Z_lower"]

    def test_vertNet_method_pre_indexed_with_correct_columns(self):
        df = pandas.DataFrame(
            {"dtUTC": [], "i": [], "j": [], "Z_upper": [], "Z_lower": []}
        )
        reqd_cols = evaltools._reqd_cols_in_data_frame(
            df, match_method="vertNet", n_spatial_dims=3, pre_indexed=True
        )
        assert reqd_cols == ["dtUTC", "i", "j", "Z_upper", "Z_lower"]

    def test_other_method_with_correct_columns(self):
        df = pandas.DataFrame({"dtUTC": [], "Lat": [], "Lon": [], "Z": []})
        reqd_cols = evaltools._reqd_cols_in_data_frame(
            df, match_method="other", n_spatial_dims=3, pre_indexed=False
        )
        assert reqd_cols == ["dtUTC", "Lat", "Lon", "Z"]

    def test_other_method_pre_indexed_with_correct_columns(self):
        df = pandas.DataFrame({"dtUTC": [], "i": [], "j": [], "k": []})
        reqd_cols = evaltools._reqd_cols_in_data_frame(
            df, match_method="other", n_spatial_dims=3, pre_indexed=True
        )
        assert reqd_cols == ["dtUTC", "i", "j", "k"]

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
        file_types = evaltools._calc_file_types(
            model_file_hours_res, model_var_file_types
        )
        assert file_types == expected

    def test_unused_file_types_removed(self):
        model_file_hours_res = {"grid_T": 1, "biol_T": 24, "chem_T": 1}
        model_var_file_types = {"vosaline": "grid_T"}
        expected = ["grid_T"]
        file_types = evaltools._calc_file_types(
            model_file_hours_res, model_var_file_types
        )
        assert file_types == expected

    def test_missing_file_types_error(self):
        model_file_hours_res = {"grid_T": 1}
        model_var_file_types = {"vosaline": "grid_T", "nitrate": "biol_T"}
        with pytest.raises(
            KeyError, match=r"^\"Error: file type\(s\) missing .*: {\'biol_T\'}"
        ):
            evaltools._calc_file_types(model_file_hours_res, model_var_file_types)

    def test_no_matching_file_types(self):
        model_file_hours_res = {"biol_T": 1, "chem_T": 1}
        model_var_file_types = {"vosaline": "grid_T"}
        expected = []
        with pytest.raises(
            KeyError, match=r"^\"Error: file type\(s\) missing .*: {\'grid_T\'}"
        ):
            evaltools._calc_file_types(model_file_hours_res, model_var_file_types)


class TestFileTypeModelVars:
    """Unit tests for the evaltools._calc_file_type_model_vars() function."""

    def test_empty_input(self):
        """Test with empty dictionaries and lists."""
        model_var_file_types = {}
        file_types = []
        expected = {}
        file_type_model_vars = evaltools._calc_file_type_model_vars(
            model_var_file_types, file_types
        )
        assert expected == file_type_model_vars

    def test_single_mapping(self):
        """Test with a single variable and a single file type."""
        model_var_file_types = {"votemper": "grid_T"}
        file_types = ["grid_T"]
        expected = {"grid_T": ["votemper"]}
        file_type_model_vars = evaltools._calc_file_type_model_vars(
            model_var_file_types, file_types
        )
        assert expected == file_type_model_vars

    def test_multiple_variables_one_type(self):
        """Test multiple variables associated with the same file type."""
        model_var_file_types = {"votemper": "grid_T", "vosaline": "grid_T"}
        file_types = ["grid_T"]
        expected = {"grid_T": ["votemper", "vosaline"]}
        file_type_model_vars = evaltools._calc_file_type_model_vars(
            model_var_file_types, file_types
        )
        assert expected == file_type_model_vars

    def test_multiple_types(self):
        """Test multiple file types with variables split across them."""
        model_var_file_types = {
            "votemper": "grid_T",
            "vosaline": "grid_T",
            "nitrate": "biol_T",
        }
        file_types = ["grid_T", "biol_T"]
        expected = {"grid_T": ["votemper", "vosaline"], "biol_T": ["nitrate"]}
        file_type_model_vars = evaltools._calc_file_type_model_vars(
            model_var_file_types, file_types
        )
        assert expected == file_type_model_vars

    def test_unused_file_type(self):
        """Test for a file type that is included in the list but not used."""
        model_var_file_types = {"votemper": "grid_T"}
        file_types = ["grid_T", "biol_T"]
        expected = {"grid_T": ["votemper"], "biol_T": []}
        file_type_model_vars = evaltools._calc_file_type_model_vars(
            model_var_file_types, file_types
        )
        assert expected == file_type_model_vars

    def test_no_match_file_types(self):
        """Test for file types with no variables in the mapping."""
        model_var_file_types = {"votemper": "grid_T", "total_alkalinity": "chem_T"}
        file_types = ["grid_T", "biol_T", "chem_T"]
        expected = {
            "grid_T": ["votemper"],
            "biol_T": [],
            "chem_T": ["total_alkalinity"],
        }
        file_type_model_vars = evaltools._calc_file_type_model_vars(
            model_var_file_types, file_types
        )
        assert expected == file_type_model_vars


class TestLoadMeshMask:
    """Unit tests for the _load_mesh_mask() function."""

    @pytest.fixture
    def temp_mesh_mask_file(self, tmp_path):
        """Create a temporary NetCDF file with example mesh mask data."""
        mesh_mask_path = tmp_path / "mesh_mask.nc"
        data = xarray.Dataset(
            {
                "tmask": (("y", "x"), numpy.array([[1, 0], [1, 1]])),
                "lons": (("y", "x"), numpy.array([[123.0, 124.0], [125.0, 126.0]])),
                "lats": (("y", "x"), numpy.array([[47.0, 48.0], [49.0, 50.0]])),
                "e3t_0": (("z", "y", "x"), numpy.random.rand(1, 2, 2)),
            }
        )
        data.to_netcdf(mesh_mask_path)
        return os.fspath(mesh_mask_path)

    def test_load_tmask_with_pre_indexed(self, temp_mesh_mask_file):
        """Test loading the tmask variable when pre_indexed is True."""
        result = evaltools._load_mesh_mask(
            mesh_mask_path=temp_mesh_mask_file,
            mask_name="tmask",
            method="any",
            pre_indexed=True,
            lon_vars={"tmask": "lons"},
            lat_vars={"tmask": "lats"},
        )
        expected_tmask = numpy.array([[1, 0], [1, 1]])
        numpy.testing.assert_array_equal(result["mask"], expected_tmask)
        assert "lons" not in result
        assert "lats" not in result

    def test_load_tmask_without_pre_indexed(self, temp_mesh_mask_file):
        """Test loading the tmask variable when pre_indexed is False."""
        result = evaltools._load_mesh_mask(
            mesh_mask_path=temp_mesh_mask_file,
            mask_name="tmask",
            method="any",
            pre_indexed=False,
            lon_vars={"tmask": "lons"},
            lat_vars={"tmask": "lats"},
        )
        expected_tmask = numpy.array([[1, 0], [1, 1]])
        expected_lons = numpy.array([[123.0, 124.0], [125.0, 126.0]])
        expected_lats = numpy.array([[47.0, 48.0], [49.0, 50.0]])
        numpy.testing.assert_array_equal(result["mask"], expected_tmask)
        numpy.testing.assert_array_equal(result["lons"], expected_lons)
        numpy.testing.assert_array_equal(result["lats"], expected_lats)

    def test_load_for_vertnet_method(self, temp_mesh_mask_file):
        """Test loading with the vertNet method including thickness data."""
        result = evaltools._load_mesh_mask(
            mesh_mask_path=temp_mesh_mask_file,
            mask_name="tmask",
            method="vertNet",
            pre_indexed=False,
            lon_vars={"tmask": "lons"},
            lat_vars={"tmask": "lats"},
        )
        assert "e3t0" in result
        assert result["e3t0"].shape == (2, 2)  # Squeezed along the z-axis


class TestMatchData:
    """Unit tests for the matchData() function."""

    def test_input_data_with_missing_columns(self):
        data = pandas.DataFrame({"Lat": [48.5], "Lon": [-123.5], "Z": [5]})
        model_var_file_types = {"votemper": "grid_T"}
        model_file_hours_res = {"grid_T": 1}
        mesh_mask_path = "path/to/mesh_mask.nc"

        with pytest.raises(KeyError, match=r"\['dtUTC'] missing from data"):
            evaltools.matchData(
                data, model_var_file_types, model_file_hours_res, mesh_mask_path
            )

    def test_invalid_mask_name(self):
        data = pandas.DataFrame(
            {
                "dtUTC": [datetime(2025, 1, 1, 12)],
                "Lat": [48.5],
                "Lon": [-123.5],
                "Z": [5],
            }
        )
        model_var_file_types = {"salinity": "grid_T"}
        model_file_hours_res = {"grid_T": 1}
        mesh_mask_path = "path/to/mesh_mask.nc"

        with pytest.raises(
            ValueError,
            match="Data matching for atmospheric fields is not yet supported: maskName='ops'",
        ):
            evaltools.matchData(
                data,
                model_var_file_types,
                model_file_hours_res,
                mesh_mask_path,
                mask_name="ops",
            )
