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

"""Unit tests for Salish Sea NEMO nowcast get_NeahBay_ssh worker.
"""
import datetime
from unittest.mock import (
    Mock,
    patch,
)

import pytest
import pytz


@pytest.fixture
def worker_module():
    from salishsea_tools.nowcast.workers import get_NeahBay_ssh
    return get_NeahBay_ssh


@patch.object(worker_module(), 'NowcastWorker')
class TestMain:
    """Unit tests for main() function.
    """
    @patch.object(worker_module(), 'worker_name')
    def test_instantiate_worker(self, m_name, m_worker, worker_module):
        worker_module.main()
        args, kwargs = m_worker.call_args
        assert args == (m_name,)
        assert list(kwargs.keys()) == ['description']

    def test_add_run_type_arg(self, m_worker, worker_module):
        worker_module.main()
        args, kwargs = m_worker().arg_parser.add_argument.call_args_list[0]
        assert args == ('run_type',)
        assert kwargs['choices'] == set(('nowcast', 'forecast', 'forecast2'))
        assert 'help' in kwargs

    def test_run_worker(self, m_worker, worker_module):
        worker_module.main()
        args, kwargs = m_worker().run.call_args
        assert args == (
            worker_module.get_NeahBay_ssh,
            worker_module.success,
            worker_module.failure,
        )


class TestSuccess:
    """Unit tests for success() function.
    """
    def test_success_log_info(self, worker_module):
        parsed_args = Mock(run_type='nowcast')
        with patch.object(worker_module.logger, 'info') as m_logger:
            worker_module.success(parsed_args)
        assert m_logger.called

    def test_success_msg_type(self, worker_module):
        parsed_args = Mock(run_type='forecast')
        msg_type = worker_module.success(parsed_args)
        assert msg_type == 'success forecast'


class TestFailure:
    """Unit tests for failure() function.
    """
    def test_failure_log_error(self, worker_module):
        parsed_args = Mock(run_type='forecast2')
        with patch.object(worker_module.logger, 'error') as m_logger:
            worker_module.failure(parsed_args)
        assert m_logger.called

    def test_failure_msg_type(self, worker_module):
        parsed_args = Mock(run_type='nowcast')
        msg_type = worker_module.failure(parsed_args)
        assert msg_type == 'failure nowcast'


class TestUTCNowToRunDate(object):
    """Unit tests for _utc_now_to_run_date() function.
    """
    def test_nowcast(self, worker_module):
        utc_now = datetime.datetime(
            2014, 12, 25, 17, 52, 42, tzinfo=pytz.timezone('UTC'))
        run_day = worker_module._utc_now_to_run_date(
            utc_now, 'nowcast')
        assert run_day == datetime.date(2014, 12, 25)

    def test_forecast(self, worker_module):
        utc_now = datetime.datetime(
            2014, 12, 25, 19, 54, 42, tzinfo=pytz.timezone('UTC'))
        run_day = worker_module._utc_now_to_run_date(
            utc_now, 'forecast')
        assert run_day == datetime.date(2014, 12, 25)

    def test_forecast2(self, worker_module):
        utc_now = datetime.datetime(
            2014, 12, 26, 12, 53, 42, tzinfo=pytz.timezone('UTC'))
        run_day = worker_module._utc_now_to_run_date(
            utc_now, 'forecast2')
        assert run_day == datetime.date(2014, 12, 25)
