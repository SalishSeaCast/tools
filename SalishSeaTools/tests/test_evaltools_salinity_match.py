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

"""Unit tests for evaltools module _salinity_match() function."""

import numpy
import pandas
import pytest
import xarray

from salishsea_tools import evaltools


class TestSalinityMatch:
    @staticmethod
    @pytest.fixture
    def sample_data():
        data = pandas.DataFrame(
            {
                "dtUTC": pandas.to_datetime(["2025-09-15 12:00"]),
                "Sal (g kg-1)": [30.0],
                "j": [10],
                "i": [20],
            }
        )
        return data

    @staticmethod
    @pytest.fixture
    def sample_flist():
        return {
            "grid_T": pandas.DataFrame(
                {
                    "fname": ["file1.nc"],
                    "start": [pandas.Timestamp("2025-09-15 00:00")],
                    "end": [pandas.Timestamp("2025-09-16 00:00")],
                }
            )
        }

    @staticmethod
    @pytest.fixture
    def sample_ftypes():
        return ["grid_T"]

    @staticmethod
    @pytest.fixture
    def sample_filemap_r():
        return {"grid_T": ["salinity"]}

    @staticmethod
    @pytest.fixture
    def sample_omask():
        return None

    @staticmethod
    @pytest.fixture
    def sample_fdict():
        return {}

    def test_no_salinity_variable(
        self,
        sample_data,
        sample_flist,
        sample_ftypes,
        sample_filemap_r,
        sample_omask,
        sample_fdict,
    ):
        filemap_r_no_sal = {"grid_T": ["temperature"]}

        with pytest.raises(
            ValueError, match="No salinity variable found in filemap_r."
        ):
            evaltools._salinity_match(
                sample_data,
                sample_flist,
                sample_ftypes,
                filemap_r_no_sal,
                sample_omask,
                sample_fdict,
            )

    def test_matching_salinity(
        self,
        sample_data,
        sample_flist,
        sample_ftypes,
        sample_filemap_r,
        sample_omask,
        sample_fdict,
        monkeypatch,
    ):
        class MockSalinityProfile:
            def __getitem__(self, *indices):
                return xarray.DataArray(
                    data=numpy.array([29.5, 30.0, 30.5]),
                    coords={
                        "deptht": numpy.array([0.5, 1.5, 2.5]),
                    },
                    dims=("deptht",),
                )

        class MockDataArray:
            def sel(self, time_counter, method):
                return MockSalinityProfile()

        class MockDataset:
            def __getitem__(self, key):
                return MockDataArray()

            def close(self):
                pass

        def mock_open_dataset(path):
            return MockDataset()

        monkeypatch.setattr(evaltools.xr, "open_dataset", mock_open_dataset)

        result = evaltools._salinity_match(
            sample_data,
            sample_flist,
            sample_ftypes,
            sample_filemap_r,
            sample_omask,
            sample_fdict,
        )

        assert "matched_salinity" in result
        numpy.testing.assert_array_almost_equal(
            result["matched_salinity"], numpy.array([30.0])
        )

    def test_no_matching_salinity(
        self,
        sample_data,
        sample_flist,
        sample_ftypes,
        sample_filemap_r,
        sample_omask,
        sample_fdict,
        monkeypatch,
    ):
        class MockSalinityProfile:
            def __getitem__(self, *indices):
                return xarray.DataArray(
                    data=numpy.array([numpy.nan, numpy.nan, numpy.nan]),
                    coords={
                        "deptht": numpy.array([0.5, 1.5, 2.5]),
                    },
                    dims=("deptht",),
                )

        class MockDataArray:
            def sel(self, time_counter, method):
                return MockSalinityProfile()

        class MockDataset:
            def __getitem__(self, key):
                return MockDataArray()

            def close(self):
                pass

        def mock_open_dataset(path):
            return MockDataset()

        monkeypatch.setattr(evaltools.xr, "open_dataset", mock_open_dataset)

        result = evaltools._salinity_match(
            sample_data,
            sample_flist,
            sample_ftypes,
            sample_filemap_r,
            sample_omask,
            sample_fdict,
        )

        assert "matched_salinity" in result
        numpy.testing.assert_array_almost_equal(
            result["matched_salinity"], numpy.array([numpy.nan])
        )
