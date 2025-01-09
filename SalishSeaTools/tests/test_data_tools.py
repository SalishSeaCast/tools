# Copyright 2013 – present The Salish Sea NEMO Project and
# The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Uni tests for salishsea_tools.data_tools module.
"""
import json
import json as stdlib_json
import logging
from datetime import datetime

import arrow
import numpy
import pandas
import pytest

from salishsea_tools import data_tools, teos_tools


class TestOncDatetime:
    """Unit tests for onc_datetime() function."""

    @pytest.mark.parametrize(
        "date_time",
        [
            "2016-06-27 16:49:42",
            datetime(2016, 6, 27, 16, 49, 42),
            arrow.get("2016-06-27 16:49:42"),
        ],
    )
    def test_onc_datetime_str(self, date_time):
        result = data_tools.onc_datetime(date_time)
        assert result == "2016-06-27T23:49:42.000Z"

    @pytest.mark.parametrize(
        "date_time, timezone",
        [
            ("2016-06-27 23:49:42", "utc"),
            (datetime(2016, 6, 27, 23, 49, 42), "utc"),
            (arrow.get("2016-06-27 23:49:42"), "utc"),
            ("2016-06-27 19:49:42", "Canada/Eastern"),
            (datetime(2016, 6, 28, 11, 49, 42), "Pacific/Auckland"),
            (arrow.get("2016-06-27 21:19:42"), "Canada/Newfoundland"),
        ],
    )
    def test_onc_datetime_timzone(self, date_time, timezone):
        result = data_tools.onc_datetime(date_time, timezone)
        assert result == "2016-06-27T23:49:42.000Z"


class TestOncJsonToDataset:
    """Unit tests for onc_json_to_dataset() function."""

    def test_onc_json_to_dataset_teos_10_salinity(self):
        onc_json = json.loads(
            """\
            {
              "citations": [
                "Ocean Networks Canada Society. 2023. Strait of Georgia East Conductivity Temperature Depth Deployed 2023-03-17. Ocean Networks Canada Society. https://doi.org/10.34943/9e6cf493-892f-4da0-9eb4-16254e7da48c."
              ],
              "parameters": {
                "dateFrom": "2023-12-12T00:00:00.000Z",
                "dateTo": "2023-12-12T00:00:10.000Z",
                "deviceCategoryCode": "CTD",
                "locationCode": "SEVIP",
                "sensorCategoryCodes": [
                  "salinity",
                  "temperature"
                ],
                "sensorsToInclude": "original"
              },
              "sensorData": [
                {
                  "actualSamples": 2,
                  "data": {
                    "qaqcFlags": [ 1, 1 ],
                    "sampleTimes": [
                      "2023-12-12T00:00:01.013Z",
                      "2023-12-12T00:00:02.006Z"
                    ],
                    "values": [ 30.9339, 30.9338 ]
                  },
                  "outputFormat": "array",
                  "sensorCategoryCode": "salinity",
                  "sensorCode": "salinity",
                  "sensorName": "Practical Salinity",
                  "unitOfMeasure": "psu"
                },
                {
                  "actualSamples": 2,
                  "data": {
                    "qaqcFlags": [ 1, 1 ],
                    "sampleTimes": [
                      "2023-12-12T00:00:01.013Z",
                      "2023-12-12T00:00:02.006Z"
                    ],
                    "values": [ 9.5185, 9.5185 ]
                  },
                  "outputFormat": "array",
                  "sensorCategoryCode": "temperature",
                  "sensorCode": "Temperature",
                  "sensorName": "Temperature",
                  "unitOfMeasure": "C"
                }
              ]
            }
            """
        )
        ds = data_tools.onc_json_to_dataset(onc_json)
        assert ds.attrs["station"] == "SEVIP"

        assert "salinity" in ds.data_vars
        assert ds.salinity.name == "salinity"
        expected = [teos_tools.psu_teos(d) for d in [30.9339, 30.9338]]
        numpy.testing.assert_array_equal(ds.salinity.data, expected)
        expected = numpy.array(
            [
                arrow.get(t).naive
                for t in ["2023-12-12T00:00:01.013Z", "2023-12-12T00:00:02.006Z"]
            ],
            dtype="datetime64[ns]",
        )
        numpy.testing.assert_array_equal(ds.salinity.coords["sampleTime"], expected)
        assert ds.salinity.dims == ("sampleTime",)
        numpy.testing.assert_array_equal(
            ds.salinity.attrs["qaqcFlag"], numpy.array([1, 1])
        )
        assert ds.salinity.attrs["sensorName"] == "Reference Salinity"
        assert ds.salinity.attrs["unitOfMeasure"] == "g/kg"
        assert ds.salinity.attrs["actualSamples"] == 2

        assert "temperature" in ds.data_vars
        assert ds.temperature.name == "temperature"
        numpy.testing.assert_array_equal(ds.temperature.data, [9.5185, 9.5185])
        expected = numpy.array(
            [
                arrow.get(t).naive
                for t in ["2023-12-12T00:00:01.013Z", "2023-12-12T00:00:02.006Z"]
            ],
            dtype="datetime64[ns]",
        )
        numpy.testing.assert_array_equal(ds.temperature.coords["sampleTime"], expected)
        assert ds.temperature.dims == ("sampleTime",)
        numpy.testing.assert_array_equal(
            ds.temperature.attrs["qaqcFlag"], numpy.array([1, 1])
        )
        assert ds.temperature.attrs["sensorName"] == "Temperature"
        assert ds.temperature.attrs["unitOfMeasure"] == "C"
        assert ds.temperature.attrs["actualSamples"] == 2

    def test_onc_json_to_dataset_psu_salinity(self):
        onc_json = json.loads(
            """\
            {
              "citations": [
                "Ocean Networks Canada Society. 2023. Strait of Georgia East Conductivity Temperature Depth Deployed 2023-03-17. Ocean Networks Canada Society. https://doi.org/10.34943/9e6cf493-892f-4da0-9eb4-16254e7da48c."
              ],
              "parameters": {
                "dateFrom": "2023-12-12T00:00:00.000Z",
                "dateTo": "2023-12-12T00:00:10.000Z",
                "deviceCategoryCode": "CTD",
                "locationCode": "SEVIP",
                "sensorCategoryCodes": [
                  "salinity",
                  "temperature"
                ],
                "sensorsToInclude": "original"
              },
              "sensorData": [
                {
                  "actualSamples": 2,
                  "data": {
                    "qaqcFlags": [ 1, 1 ],
                    "sampleTimes": [
                      "2023-12-12T00:00:01.013Z",
                      "2023-12-12T00:00:02.006Z"
                    ],
                    "values": [ 30.9339, 30.9338 ]
                  },
                  "outputFormat": "array",
                  "sensorCategoryCode": "salinity",
                  "sensorCode": "salinity",
                  "sensorName": "Practical Salinity",
                  "unitOfMeasure": "psu"
                }
              ]
            }
            """
        )
        ds = data_tools.onc_json_to_dataset(onc_json, teos=False)
        assert ds.attrs["station"] == "SEVIP"

        assert "salinity" in ds.data_vars
        assert ds.salinity.name == "salinity"
        numpy.testing.assert_array_equal(ds.salinity.data, [30.9339, 30.9338])
        expected = numpy.array(
            [
                arrow.get(t).naive
                for t in ["2023-12-12T00:00:01.013Z", "2023-12-12T00:00:02.006Z"]
            ],
            dtype="datetime64[ns]",
        )
        numpy.testing.assert_array_equal(ds.salinity.coords["sampleTime"], expected)
        assert ds.salinity.dims == ("sampleTime",)
        numpy.testing.assert_array_equal(
            ds.salinity.attrs["qaqcFlag"], numpy.array([1, 1])
        )
        assert ds.salinity.attrs["sensorName"] == "Practical Salinity"
        assert ds.salinity.attrs["unitOfMeasure"] == "psu"
        assert ds.salinity.attrs["actualSamples"] == 2


class TestResolveCHSTideStn:
    """Unit tests for resolve_chs_tide_stn() function."""

    def test_stn_number(self):
        stn_code = data_tools.resolve_chs_tide_stn(8074)

        assert stn_code == "08074"

    def test_stn_name(self):
        stn_code = data_tools.resolve_chs_tide_stn("Campbell River")

        assert stn_code == "08074"

    def test_stn_name_not_found(self, caplog):
        caplog.set_level(logging.DEBUG)

        stn_code = data_tools.resolve_chs_tide_stn("Rimouski")

        assert caplog.records[0].levelname == "ERROR"
        expected = "station name not found in places.PLACES: Rimouski; maybe try an integer station number?"
        assert caplog.messages[0] == expected
        assert stn_code is None

    def test_invalid_stn_nunmber(self, caplog):
        caplog.set_level(logging.DEBUG)

        stn_code = data_tools.resolve_chs_tide_stn("Boundary Bay")

        assert caplog.records[0].levelname == "WARNING"
        expected = "invalid station number for Boundary Bay station: None"
        assert caplog.messages[0] == expected
        assert stn_code is None


class TestGetCHSTideStnId:
    """Unit tests for get_chs_tide_stn_id() function."""

    def test_stn_name_not_found(self, caplog):
        caplog.set_level(logging.DEBUG)

        stn_id = data_tools.get_chs_tide_stn_id("Rimouski")

        assert caplog.records[0].levelname == "ERROR"
        expected = "station name not found in places.PLACES: Rimouski; maybe try an integer station number?"
        assert caplog.messages[0] == expected
        assert stn_id is None

    def test_no_valid_stn_code(self, caplog):
        caplog.set_level(logging.DEBUG)

        stn_id = data_tools.get_chs_tide_stn_id("Boundary Bay")

        assert caplog.records[1].levelname == "WARNING"
        expected = "can't resolve a valid CHS station code for Boundary Bay"
        assert caplog.messages[1] == expected
        assert stn_id is None

    def test_no_stn_info(self, monkeypatch):
        def mock_do_chs_iwls_api_request(endpoint, query_params, retry_args):
            class MockResponse:
                def json(self):
                    return stdlib_json.loads("[]")

            return MockResponse()

        monkeypatch.setattr(
            data_tools, "_do_chs_iwls_api_request", mock_do_chs_iwls_api_request
        )

        stn_id = data_tools.get_chs_tide_stn_id(9449880)  # Friday Harbor

        assert stn_id is None

    def test_get_chs_tide_stn_id(self, monkeypatch):
        def mock_do_chs_iwls_api_request(endpoint, query_params, retry_args):
            class MockResponse:
                def json(self):
                    return stdlib_json.loads(
                        """\
                        [
                          {
                            "id": "5cebf1de3d0f4a073c4bb996",
                            "code": "08074",
                            "officialName": "Campbell River",
                            "operating": true,
                            "latitude": 50.042,
                            "longitude": -125.247,
                            "type": "PERMANENT",
                            "timeSeries": []
                          }
                       ]
                        """
                    )

            return MockResponse()

        monkeypatch.setattr(
            data_tools, "_do_chs_iwls_api_request", mock_do_chs_iwls_api_request
        )

        stn_id = data_tools.get_chs_tide_stn_id(8074)

        assert stn_id == "5cebf1de3d0f4a073c4bb996"


class TestGetCHSTides:
    """Unit tests for get_chs_tides() function."""

    @pytest.mark.parametrize("data_type", ("obs", "pred"))
    def test_stn_name_not_found(self, data_type, monkeypatch):
        def mock_get_chs_tide_stn_id(stn):
            return None

        monkeypatch.setattr(data_tools, "get_chs_tide_stn_id", mock_get_chs_tide_stn_id)

        with pytest.raises(KeyError):
            data_tools.get_chs_tides(
                data_type, "Rimouski", begin="2021-03-18 00:00", end="2021-03-18 23:59"
            )

    def test_invalid_data_type(self, monkeypatch):
        def mock_get_chs_tide_stn_id(stn):
            return "5cebf1de3d0f4a073c4bb996"

        monkeypatch.setattr(data_tools, "get_chs_tide_stn_id", mock_get_chs_tide_stn_id)

        with pytest.raises(ValueError):
            data_tools.get_chs_tides(
                "foo",
                "Campbell River",
                begin="2021-03-18 00:00",
                end="2021-03-18 23:59",
            )

    @pytest.mark.parametrize("data_type", ("obs", "pred"))
    def test_invalid_start_date_time(self, data_type, caplog, monkeypatch):
        def mock_get_chs_tide_stn_id(stn):
            return "5cebf1de3d0f4a073c4bb996"

        monkeypatch.setattr(data_tools, "get_chs_tide_stn_id", mock_get_chs_tide_stn_id)
        caplog.set_level(logging.DEBUG)

        time_series = data_tools.get_chs_tides(
            data_type,
            "Campbell River",
            begin="2021-18-03",
            end="2021-03-18 23:59",
        )

        assert caplog.records[0].levelname == "ERROR"
        assert caplog.messages[0] == "invalid start date/time: 2021-18-03"
        assert time_series is None

    @pytest.mark.parametrize("data_type", ("obs", "pred"))
    def test_invalid_end_date_time(self, data_type, caplog, monkeypatch):
        def mock_get_chs_tide_stn_id(stn):
            return "5cebf1de3d0f4a073c4bb996"

        monkeypatch.setattr(data_tools, "get_chs_tide_stn_id", mock_get_chs_tide_stn_id)
        caplog.set_level(logging.DEBUG)

        time_series = data_tools.get_chs_tides(
            data_type,
            "Campbell River",
            begin="2021-03-18",
            end="2021-18-03 23:59",
        )

        assert caplog.records[0].levelname == "ERROR"
        assert caplog.messages[0] == "invalid end date/time: 2021-18-03 23:59"
        assert time_series is None

    def test_get_chs_tides_obs(self, caplog, monkeypatch):
        def mock_get_chs_tide_stn_id(stn):
            return "5cebf1de3d0f4a073c4bb996"

        monkeypatch.setattr(data_tools, "get_chs_tide_stn_id", mock_get_chs_tide_stn_id)

        def mock_do_chs_iwls_api_request(endpoint, query_params, retry_args):
            class MockResponse:
                @staticmethod
                def json():
                    return stdlib_json.loads(
                        """\
                        [
                          {
                            "eventDate": "2021-03-18T00:00:00Z",
                            "qcFlagCode": "1",
                            "value": 1.871,
                            "timeSeriesId": "5cebf1de3d0f4a073c4bb993"
                          },
                          {
                            "eventDate": "2021-03-18T00:01:00Z",
                            "qcFlagCode": "1",
                            "value": 1.885,
                            "timeSeriesId": "5cebf1de3d0f4a073c4bb993"
                          },
                          {
                            "eventDate": "2021-03-18T00:02:00Z",
                            "qcFlagCode": "1",
                            "value": 1.898,
                            "timeSeriesId": "5cebf1de3d0f4a073c4bb993"
                          },
                          {
                            "eventDate": "2021-03-18T00:03:00Z",
                            "qcFlagCode": "1",
                            "value": 1.91,
                            "timeSeriesId": "5cebf1de3d0f4a073c4bb993"
                          }
                        ]
                        """
                    )

            return MockResponse()

        monkeypatch.setattr(
            data_tools, "_do_chs_iwls_api_request", mock_do_chs_iwls_api_request
        )
        caplog.set_level(logging.DEBUG)

        time_series = data_tools.get_chs_tides(
            "obs",
            "Campbell River",
            begin="2021-03-18 00:00",
            end="2021-03-18 00:03",
        )

        assert caplog.records[0].levelname == "INFO"
        expected = (
            "retrieving obs water level data from "
            "https://api-iwls.dfo-mpo.gc.ca/api/v1/stations/5cebf1de3d0f4a073c4bb996/data "
            "for station 08074 Campbell River from 2021-03-18 00:00:00Z to 2021-03-18 00:03:00Z"
        )
        assert caplog.messages[0] == expected
        expected = pandas.Series(
            data=[1.871, 1.885, 1.898, 1.91],
            index=pandas.to_datetime(
                [
                    "2021-03-18T00:00:00",
                    "2021-03-18T00:01:00",
                    "2021-03-18T00:02:00",
                    "2021-03-18T00:03:00",
                ]
            ),
            name="08074 Campbell River water levels",
        )
        pandas.testing.assert_series_equal(time_series, expected)

    def test_get_chs_tides_pred(self, caplog, monkeypatch):
        def mock_get_chs_tide_stn_id(stn):
            return "5cebf1de3d0f4a073c4bb996"

        monkeypatch.setattr(data_tools, "get_chs_tide_stn_id", mock_get_chs_tide_stn_id)

        def mock_do_chs_iwls_api_request(endpoint, query_params, retry_args):
            class MockResponse:
                @staticmethod
                def json():
                    return stdlib_json.loads(
                        """\
                        [
                          {
                            "eventDate": "2021-03-19T00:00:00Z",
                            "qcFlagCode": "2",
                            "value": 1.757,
                            "timeSeriesId": "5cebf1de3d0f4a073c4bb991"
                          },
                          {
                            "eventDate": "2021-03-19T00:15:00Z",
                            "qcFlagCode": "2",
                            "value": 1.811,
                            "timeSeriesId": "5cebf1de3d0f4a073c4bb991"
                          },
                          {
                            "eventDate": "2021-03-19T00:30:00Z",
                            "qcFlagCode": "2",
                            "value": 1.878,
                            "timeSeriesId": "5cebf1de3d0f4a073c4bb991"
                          },
                          {
                            "eventDate": "2021-03-19T00:45:00Z",
                            "qcFlagCode": "2",
                            "value": 1.959,
                            "timeSeriesId": "5cebf1de3d0f4a073c4bb991"
                          },
                          {
                            "eventDate": "2021-03-19T01:00:00Z",
                            "qcFlagCode": "2",
                            "value": 2.053,
                            "timeSeriesId": "5cebf1de3d0f4a073c4bb991"
                          }
                        ]
                        """
                    )

            return MockResponse()

        monkeypatch.setattr(
            data_tools, "_do_chs_iwls_api_request", mock_do_chs_iwls_api_request
        )
        caplog.set_level(logging.DEBUG)

        time_series = data_tools.get_chs_tides(
            "obs",
            "Campbell River",
            begin="2021-03-18 00:00",
            end="2021-03-18 00:03",
        )

        assert caplog.records[0].levelname == "INFO"
        expected = (
            "retrieving obs water level data from "
            "https://api-iwls.dfo-mpo.gc.ca/api/v1/stations/5cebf1de3d0f4a073c4bb996/data "
            "for station 08074 Campbell River from 2021-03-18 00:00:00Z to 2021-03-18 00:03:00Z"
        )
        assert caplog.messages[0] == expected
        expected = pandas.Series(
            data=[1.757, 1.811, 1.878, 1.959, 2.053],
            index=pandas.to_datetime(
                [
                    "2021-03-19T00:00:00",
                    "2021-03-19T00:15:00",
                    "2021-03-19T00:30:00",
                    "2021-03-19T00:45:00",
                    "2021-03-19T01:00:00",
                ]
            ),
            name="08074 Campbell River water levels",
        )
        pandas.testing.assert_series_equal(time_series, expected)
