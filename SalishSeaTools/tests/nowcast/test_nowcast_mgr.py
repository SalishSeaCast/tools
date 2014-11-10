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
from mock import patch
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
    @patch('salishsea_tools.nowcast.nowcast_mgr.logger.info')
    def test_valid_msg_type(self, m_logger, nowcast_mgr_module):
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

    @pytest.mark.parametrize('worker, msg_type', [
        ('get_NeahBay_ssh', 'success'),
        ('download_weather', 'success 06'),
        ('download_weather', 'failure 06'),
        ('download_weather', 'success 18'),
        ('download_weather', 'failure 18'),
        ('download_weather', 'the end'),
    ])
    def test_reply(self, worker, msg_type, nowcast_mgr_module):
        nowcast_mgr_module.mgr_name = 'nowcast_mgr'
        config = {
            'msg_types': {
                worker: {
                    msg_type: 'foo',
                },
            },
        }
        message = (
            '{{source: {}, msg_type: {}, payload: null}}\n'
            .format(worker, msg_type))
        reply, next_step, next_step_args = nowcast_mgr_module.parse_message(
            config, message)
        expected = {
            'source': 'nowcast_mgr',
            'msg_type': 'ack',
            'payload': None,
        }
        assert yaml.safe_load(reply) == expected

    @pytest.mark.parametrize('msg_type', [
        'success 06',
        'failure 06',
        'success 18',
        'failure 18',
    ])
    def test_next_step(self, msg_type, nowcast_mgr_module):
        config = {
            'msg_types': {
                'worker': {
                    msg_type: 'foo'
                }
            }
        }
        message = (
            '{{source: worker, msg_type: {}, payload: null}}\n'
            .format(msg_type))
        reply, next_step, next_step_args = nowcast_mgr_module.parse_message(
            config, message)
        assert next_step == nowcast_mgr_module.do_nothing

    @pytest.mark.parametrize('msg_type', [
        'success 06',
        'failure 06',
        'success 18',
        'failure 18',
    ])
    def test_next_step_args(self, msg_type, nowcast_mgr_module):
        config = {
            'msg_types': {
                'worker': {
                    msg_type: 'foo'
                }
            }
        }
        message = (
            '{{source: worker, msg_type: {}, payload: null}}\n'
            .format(msg_type))
        reply, next_step, next_step_args = nowcast_mgr_module.parse_message(
            config, message)
        assert next_step_args == []

    def test_success_get_NeahBay_ssh_reply(self, nowcast_mgr_module):
        nowcast_mgr_module.mgr_name = 'nowcast_mgr'
        config = {
            'msg_types': {
                'get_NeahBay_ssh': {
                    'success': 'foo'
                }
            }
        }
        message = (
            '{source: get_NeahBay_ssh, msg_type: success, payload: null}\n')
        reply, next_step, next_step_args = nowcast_mgr_module.parse_message(
            config, message)
        expected = {
            'source': 'nowcast_mgr',
            'msg_type': 'ack',
            'payload': None,
        }
        assert yaml.safe_load(reply) == expected

    def test_get_NeahBay_ssh_next_step(self, nowcast_mgr_module):
        config = {
            'msg_types': {
                'get_NeahBay_ssh': {
                    'success': 'foo'
                }
            }
        }
        message = (
            '{source: get_NeahBay_ssh, msg_type: success, payload: null}\n')
        reply, next_step, next_step_args = nowcast_mgr_module.parse_message(
            config, message)
        assert next_step == nowcast_mgr_module.update_checklist

    def test_get_NeahBay_ssh_next_step_args(self, nowcast_mgr_module):
        config = {
            'msg_types': {
                'get_NeahBay_ssh': {
                    'success': 'foo'
                }
            }
        }
        message = (
            '{source: get_NeahBay_ssh, msg_type: success, '
            ' payload: {txt: sshNB_2014-11-10.txt}}\n')
        reply, next_step, next_step_args = nowcast_mgr_module.parse_message(
            config, message)
        expected = ['sshNeahBay', {'txt': 'sshNB_2014-11-10.txt'}]
        assert next_step_args == expected

    def test_the_end_next_step(self, nowcast_mgr_module):
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

    def test_the_end_next_step_args(self, nowcast_mgr_module):
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
        assert next_step_args == []
