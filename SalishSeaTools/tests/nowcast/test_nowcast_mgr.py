# Copyright 2013-2014 The Salish Sea MEOPAR contributors
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

"""Unit tests for Salish Sea NEMO nowcast manager.
"""
from mock import (
    Mock,
    patch,
)
import pytest
import yaml


@pytest.fixture
def nowcast_mgr_module():
    from salishsea_tools.nowcast import nowcast_mgr
    return nowcast_mgr


@pytest.mark.use_fixtures(['nowcast_mgr_module'])
class TestParseMessage(object):
    """Unit tests for parse_message() function.
    """
    def test_undefined_msg_type_reply(self, nowcast_mgr_module):
        nowcast_mgr_module.mgr_name = 'nowcast_mgr'
        config = {
            'msg_types': {
                'worker': {
                    'the end': 'foo'
                }
            }
        }
        message = '{source: worker, msg_type: bar, payload: null}\n'
        reply, next_step, next_step_args = nowcast_mgr_module.parse_message(
            config, message)
        expected = {
            'source': 'nowcast_mgr',
            'msg_type': 'undefined msg',
            'payload': None,
        }
        assert yaml.safe_load(reply) == expected

    def test_undefined_msg_type_next_step(self, nowcast_mgr_module):
        config = {
            'msg_types': {
                'worker': {
                    'the end': 'foo'
                }
            }
        }
        message = '{source: worker, msg_type: bar, payload: null}\n'
        reply, next_step, next_step_args = nowcast_mgr_module.parse_message(
            config, message)
        assert next_step == nowcast_mgr_module.do_nothing

    def test_undefined_msg_type_next_step_args(self, nowcast_mgr_module):
        config = {
            'msg_types': {
                'worker': {
                    'the end': 'foo'
                }
            }
        }
        message = '{source: worker, msg_type: bar, payload: null}\n'
        reply, next_step, next_step_args = nowcast_mgr_module.parse_message(
            config, message)
        assert next_step_args == []

    @patch('salishsea_tools.nowcast.nowcast_mgr.logger.info')
    def test_valid_msg_type_logging(self, m_logger, nowcast_mgr_module):
        config = {
            'msg_types': {
                'worker': {
                    'the end': 'foo'
                }
            }
        }
        message = '{source: worker, msg_type: the end, payload: null}\n'
        nowcast_mgr_module.parse_message(config, message)
        m_logger.assert_any_call('received message from worker: (the end) foo')

    def test_valid_msg_reply(self, nowcast_mgr_module):
        nowcast_mgr_module.mgr_name = 'nowcast_mgr'
        config = {
            'msg_types': {
                'download_weather': {
                    'success 06': 'foo',
                },
            },
        }
        message = (
            '{source: download_weather, '
            'msg_type: success 06, payload: null}\n')
        reply, next_step, next_step_args = nowcast_mgr_module.parse_message(
            config, message)
        expected = {
            'source': 'nowcast_mgr',
            'msg_type': 'ack',
            'payload': None,
        }
        assert yaml.safe_load(reply) == expected

    def test_valid_msg_next_step(self, nowcast_mgr_module):
        config = {
            'msg_types': {
                'download_weather': {
                    'success 06': 'foo'
                }
            }
        }
        message = (
            '{source: download_weather, '
            'msg_type: success 06, payload: null}\n')
        reply, next_step, next_step_args = nowcast_mgr_module.parse_message(
            config, message)
        assert next_step == nowcast_mgr_module.do_nothing

    def test_valid_msg_next_step_args(self, nowcast_mgr_module):
        config = {
            'msg_types': {
                'download_weather': {
                    'success 06': 'foo'
                }
            }
        }
        message = (
            '{source: download_weather, '
            'msg_type: success 06, payload: null}\n')
        reply, next_step, next_step_args = nowcast_mgr_module.parse_message(
            config, message)
        assert next_step_args == []

    @patch('salishsea_tools.nowcast.nowcast_mgr.logger.info')
    def test_the_end_msg_logging(self, m_logger, nowcast_mgr_module):
        config = {
            'msg_types': {
                'worker': {
                    'the end': 'foo'
                }
            }
        }
        message = '{source: worker, msg_type: the end, payload: null}\n'
        nowcast_mgr_module.parse_message(config, message)
        m_logger.assert_any_call(
            'worker-automated parts of nowcast completed for today')

    def test_the_end_msg_reply(self, nowcast_mgr_module):
        nowcast_mgr_module.mgr_name = 'nowcast_mgr'
        config = {
            'msg_types': {
                'worker': {
                    'the end': 'foo',
                },
            },
        }
        message = '{source: worker, msg_type: the end, payload: null}\n'
        reply, next_step, next_step_args = nowcast_mgr_module.parse_message(
            config, message)
        expected = {
            'source': 'nowcast_mgr',
            'msg_type': 'ack',
            'payload': None,
        }
        assert yaml.safe_load(reply) == expected

    def test_the_end_msg_next_step(self, nowcast_mgr_module):
        config = {
            'msg_types': {
                'worker': {
                    'the end': 'foo'
                }
            }
        }
        message = '{source: worker, msg_type: the end, payload: null}\n'
        reply, next_step, next_step_args = nowcast_mgr_module.parse_message(
            config, message)
        assert next_step == nowcast_mgr_module.finish_automation

    def test_the_end_next_msg_step_args(self, nowcast_mgr_module):
        config = {
            'msg_types': {
                'worker': {
                    'the end': 'foo'
                }
            }
        }
        message = '{source: worker, msg_type: the end, payload: null}\n'
        reply, next_step, next_step_args = nowcast_mgr_module.parse_message(
            config, message)
        assert next_step_args == [config]


def test_do_nothing(nowcast_mgr_module):
    result = nowcast_mgr_module.do_nothing()
    assert result is None


def test_do_nothing_any_args(nowcast_mgr_module):
    result = nowcast_mgr_module.do_nothing('foo', 42)
    assert result is None


def test_undefined_message_next_step(nowcast_mgr_module):
    next_step, next_step_args = nowcast_mgr_module.undefined_message()
    assert next_step == nowcast_mgr_module.do_nothing


def test_undefined_message_next_step_args(nowcast_mgr_module):
    next_step, next_step_args = nowcast_mgr_module.undefined_message()
    assert next_step_args == []


def test_the_end_next_step(nowcast_mgr_module):
    config = Mock(name='config')
    next_step, next_step_args = nowcast_mgr_module.the_end(config)
    assert next_step == nowcast_mgr_module.finish_automation


def test_the_end_next_step_args(nowcast_mgr_module):
    config = Mock(name='config')
    next_step, next_step_args = nowcast_mgr_module.the_end(config)
    assert next_step_args == [config]


@pytest.mark.parametrize('worker, msg_type, exp_next_step', [
    ('after_download_weather', 'success 06', 'do_nothing'),
    ('after_download_weather', 'failure 06', 'do_nothing'),
    ('after_download_weather', 'success 18', 'launch_worker'),
    ('after_download_weather', 'failure 18', 'do_nothing'),
    ('after_get_NeahBay_ssh', 'success', 'update_checklist'),
    ('after_get_NeahBay_ssh', 'failure', 'do_nothing'),
    ('after_make_runoff_file', 'success', 'update_checklist'),
    ('after_make_runoff_file', 'failure', 'do_nothing'),
    ('after_grib_to_netcdf', 'success', 'update_checklist'),
    ('after_grib_to_netcdf', 'failure', 'do_nothing'),
])
def test_after_worker_next_step(
    worker, msg_type, exp_next_step, nowcast_mgr_module,
):
    payload = Mock(name='payload')
    config = Mock(name='config')
    after_worker_func = getattr(nowcast_mgr_module, worker)
    next_step, next_step_args = after_worker_func(
        worker, msg_type, payload, config)
    assert next_step == getattr(nowcast_mgr_module, exp_next_step)


@pytest.mark.parametrize('worker, msg_type, exp_next_step_args', [
    ('after_download_weather', 'success 06', []),
    ('after_download_weather', 'failure 06', []),
    ('after_download_weather', 'failure 18', []),
    ('after_get_NeahBay_ssh', 'failure', []),
    ('after_make_runoff_file', 'failure', []),
    ('after_grib_to_netcdf', 'failure', []),
])
def test_after_worker_do_nothing_next_step_args(
    worker, msg_type, exp_next_step_args, nowcast_mgr_module,
):
    payload = Mock(name='payload')
    config = Mock(name='config')
    after_worker_func = getattr(nowcast_mgr_module, worker)
    next_step, next_step_args = after_worker_func(
        worker, msg_type, payload, config)
    assert next_step_args == exp_next_step_args


def test_get_NeahBay_ssh_success_next_step_args(nowcast_mgr_module):
    payload = Mock(name='payload')
    config = Mock(name='config')
    next_step, next_step_args = nowcast_mgr_module.after_get_NeahBay_ssh(
        'get_NeahBay_ssh', 'success', payload, config)
    assert next_step_args == ['get_NeahBay_ssh', 'sshNeahBay', payload]


def test_make_runoff_file_success_next_step_args(nowcast_mgr_module):
    payload = Mock(name='payload')
    config = Mock(name='config')
    next_step, next_step_args = nowcast_mgr_module.after_make_runoff_file(
        'make_runoff_file', 'success', payload, config)
    assert next_step_args == ['make_runoff_file', 'rivers', payload]


def test_grib_to_netcdf_success_next_step_args(nowcast_mgr_module):
    payload = Mock(name='payload')
    config = Mock(name='config')
    next_step, next_step_args = nowcast_mgr_module.after_grib_to_netcdf(
        'grib_to_netcdf', 'success', payload, config)
    assert next_step_args == ['grib_to_netcdf', 'weather forcing', payload]
