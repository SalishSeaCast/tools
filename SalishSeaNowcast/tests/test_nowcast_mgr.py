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

"""Unit tests for Salish Sea NEMO nowcast NowcastManager class.
"""
import logging
from unittest.mock import (
    Mock,
    mock_open,
    patch,
)

import pytest
import yaml
import zmq


@pytest.fixture
def mgr_module():
    from nowcast import nowcast_mgr
    return nowcast_mgr


@pytest.fixture
def mgr_class():
    from nowcast.nowcast_mgr import NowcastManager
    return NowcastManager


@pytest.fixture
def mgr(mgr_class):
    return mgr_class()


@patch.object(mgr_module(), 'NowcastManager')
def test_main(m_mgr, mgr_module):
    """Unit test for nowcast_mgr.main function.
    """
    mgr_module.main()
    assert m_mgr().run.called


class TestNowcastManagerConstructor:
    """Unit tests for NowcastManager.__init__ method.
    """
    def test_name(self):
        p_get_module_name = patch.object(
            mgr_module().lib, 'get_module_name', return_value='nowcast_mgr',
        )
        with p_get_module_name:
            mgr = mgr_class()()
        assert mgr.name == 'nowcast_mgr'

    def test_logger(self, mgr):
        p_get_module_name = patch.object(
            mgr_module().lib, 'get_module_name', return_value='nowcast_mgr',
        )
        with p_get_module_name:
            mgr = mgr_class()()
        assert mgr.logger.name == 'nowcast_mgr'

    def test_worker_loggers(self, mgr):
        assert mgr.worker_loggers == {}

    def test_context(self, mgr):
        assert isinstance(mgr.context, zmq.Context)

    def test_checklist(self, mgr):
        assert mgr.checklist == {}


@pytest.mark.parametrize('worker', [
    'download_weather',
    'get_NeahBay_ssh',
])
def test_after_actions(worker, mgr):
    """Unit tests for NowcastManager.acter_actions property.
    """
    assert worker in mgr.after_actions


class TestNowcastManagerRun:
    """Unit tests for NowcastManager.run method.
    """
    def test_parsed_args(self, mgr):
        mgr._cli = Mock(name='_cli')
        mgr._load_config = Mock(name='_load_config')
        mgr._prep_logging = Mock(name='_prep_logging')
        mgr._prep_messaging = Mock(name='_prep_messaging')
        mgr._process_messages = Mock(name='_process_messages')
        mgr.run()
        assert mgr.parsed_args == mgr._cli()

    def test_config(self, mgr):
        mgr._cli = Mock(name='_cli')
        mgr._load_config = Mock(name='_load_config')
        mgr._prep_logging = Mock(name='_prep_logging')
        mgr._prep_messaging = Mock(name='_prep_messaging')
        mgr._load_checklist = Mock(name='_load_checklist')
        mgr._process_messages = Mock(name='_process_messages')
        mgr.run()
        assert mgr.config == mgr._load_config()

    def test_prep_logging(self, mgr):
        mgr._cli = Mock(name='_cli')
        mgr._load_config = Mock(name='_load_config')
        mgr._prep_logging = Mock(name='_prep_logging')
        mgr._prep_messaging = Mock(name='_prep_messaging')
        mgr._load_checklist = Mock(name='_load_checklist')
        mgr._process_messages = Mock(name='_process_messages')
        mgr.run()
        assert mgr._prep_logging.called

    def test_install_signal_handlers(self, mgr):
        mgr._cli = Mock(name='_cli')
        mgr._load_config = Mock(name='_load_config')
        mgr._prep_logging = Mock(name='_prep_logging')
        mgr._prep_messaging = Mock(name='_prep_messaging')
        mgr._load_checklist = Mock(name='_load_checklist')
        mgr._install_signal_handlers = Mock(name='_install_signal_handlers')
        mgr._process_messages = Mock(name='_process_messages')
        mgr.run()
        assert mgr._install_signal_handlers.called

    def test_socket(self, mgr):
        mgr._cli = Mock(name='_cli')
        mgr._load_config = Mock(name='_load_config')
        mgr._prep_logging = Mock(name='_prep_logging')
        mgr._prep_messaging = Mock(name='_prep_messaging')
        mgr._load_checklist = Mock(name='_load_checklist')
        mgr._process_messages = Mock(name='_process_messages')
        mgr.run()
        assert mgr._socket == mgr._prep_messaging()

    def test_load_checklist(self, mgr):
        mgr._cli = Mock(name='_cli', return_value=Mock(ignore_checklist=False))
        mgr._load_config = Mock(name='_load_config')
        mgr._prep_logging = Mock(name='_prep_logging')
        mgr._prep_messaging = Mock(name='_prep_messaging')
        mgr._load_checklist = Mock(name='_load_checklist')
        mgr._process_messages = Mock(name='_process_messages')
        mgr.run()
        assert mgr._load_checklist.called

    def test_no_load_checklist(self, mgr):
        mgr._cli = Mock(name='_cli', return_value=Mock(ignore_checklist=True))
        mgr._load_config = Mock(name='_load_config')
        mgr._prep_logging = Mock(name='_prep_logging')
        mgr._prep_messaging = Mock(name='_prep_messaging')
        mgr._load_checklist = Mock(name='_load_checklist')
        mgr._process_messages = Mock(name='_process_messages')
        mgr.run()
        assert not mgr._load_checklist.called

    def test_process_messages(self, mgr):
        mgr._cli = Mock(name='_cli')
        mgr._load_config = Mock(name='_load_config')
        mgr._prep_logging = Mock(name='_prep_logging')
        mgr._prep_messaging = Mock(name='_prep_messaging')
        mgr._load_checklist = Mock(name='_load_checklist')
        mgr._process_messages = Mock(name='_process_messages')
        mgr.run()
        assert mgr._process_messages.called


class TestLoadConfig:
    """Unit tests for NowcastManager._load_config method.
    """
    @patch.object(mgr_module().lib, 'load_config')
    def test_load_config(self, m_load_config, mgr):
        mgr.parsed_args = Mock(config_file='nowcast.yaml')
        mgr._load_config()
        m_load_config.assert_called_once_with('nowcast.yaml')

    @patch.object(mgr_module().lib, 'load_config')
    def test_load_config_console_logging(self, m_load_config, mgr):
        mgr.parsed_args = Mock(config_file='nowcast.yaml', debug=True)
        m_load_config.return_value = {'logging': {}}
        config = mgr._load_config()
        assert config['logging']['console']


class TestPrepLogging:
    """Unit tests for NowcastManager._prep_logging method.
    """
    @patch.object(mgr_module().lib, 'configure_logging')
    def test_prep_logging(self, m_config_logging, mgr):
        mgr.parsed_args = Mock(name='parsed_args')
        mgr.config = Mock(name='config')
        mgr._prep_logging()
        m_config_logging.assert_called_once_with(
            mgr.config, mgr.logger, mgr.parsed_args.debug)

    @patch.object(mgr_module().lib, 'configure_logging')
    def test_prep_logging_info_msgs(self, m_config_logging, mgr):
        mgr.parsed_args = Mock(name='parsed_args')
        mgr.config = Mock(name='config')
        mgr.logger = Mock(name='logger')
        mgr._prep_logging()
        assert mgr.logger.info.call_count == 1

    @patch.object(mgr_module().lib, 'configure_logging')
    def test_prep_logging_debug_msgs(self, m_config_logging, mgr):
        mgr.parsed_args = Mock(name='parsed_args')
        mgr.config = Mock(name='config')
        mgr.logger = Mock(name='logger')
        mgr._prep_logging()
        assert mgr.logger.debug.call_count == 1


def test_prep_messaging(mgr):
    """Unit test for NowcastManager._prep_messaging method.
    """
    mgr.config = {'zmq': {'ports': {'backend': 6665}}}
    mgr.context.socket = Mock(name='socket')
    socket = mgr._prep_messaging()
    socket.connect.assert_called_once_with('tcp://localhost:6665')


class TestLoadChecklist:
    """Unit tests for NowcastManager._load_checklist method.
    """
    def test_load_checklist(self, mgr):
        p_open = patch.object(mgr_module(), 'open', mock_open(), create=True)
        mgr.config = {'checklist file': 'nowcast_checklist.yaml'}
        with p_open as m_open:
            mgr._load_checklist()
        m_open.assert_called_once_with('nowcast_checklist.yaml', 'rt')

    def test_load_checklist_filenotfounderror(self, mgr):
        mgr.config = {'checklist file': 'nowcast_checklist.yaml'}
        mgr.logger = Mock(name='logger')
        mgr._load_checklist()
        mgr.logger.warning.assert_called_with('running with empty checklist')


class TestProcessMessages:
    """Unit tests for NowcastManager._process_messages method.
    """
    ## TODO: Need to figure out how to break out of a while True loop


class TestMessageHandler:
    """Unit tests for NowcastManager._message_handler method.
    """
    def test_handle_undefined_msg(self, mgr):
        mgr.config = {'msg_types': {'worker': {}}}
        mgr._handle_undefined_msg = Mock(name='_handle_undefined_msg')
        mgr._log_received_msg = Mock(name='_log_received_msg')
        message = {'source': 'worker', 'msg_type': 'foo', 'payload': ''}
        reply, next_steps = mgr._message_handler(yaml.dump(message))
        mgr._handle_undefined_msg.assert_called_once_with('worker', 'foo')
        assert reply == mgr._handle_undefined_msg()
        assert next_steps is None
        assert not mgr._log_received_msg.called

    def test_need_msg(self, mgr):
        mgr.config = {'msg_types': {'worker': {'need': ''}}}
        mgr._handle_need_msg = Mock(name='_handle_need_msg')
        mgr._log_received_msg = Mock(name='_log_received_msg')
        message = {'source': 'worker', 'msg_type': 'need', 'payload': 'bar'}
        reply, next_steps = mgr._message_handler(yaml.dump(message))
        mgr._log_received_msg.assert_called_once_with('worker', 'need')
        mgr._handle_need_msg.assert_called_once_with('bar')
        assert reply == mgr._handle_need_msg()
        assert next_steps is None

    def test_log_msg(self, mgr):
        mgr.config = {'msg_types': {'worker': {'log': ''}}}
        mgr._handle_log_msg = Mock(name='_handle_log_msg')
        mgr._log_received_msg = Mock(name='_log_received_msg')
        message = {'source': 'worker', 'msg_type': 'log', 'payload': 'bar'}
        reply, next_steps = mgr._message_handler(yaml.dump(message))
        mgr._log_received_msg.assert_called_once_with('worker', 'log')
        mgr._handle_log_msg.assert_called_once_with('worker', 'log', 'bar')
        assert reply == mgr._handle_log_msg()
        assert next_steps is None

    def test_action_msg(self, mgr):
        mgr.config = {'msg_types': {'worker': {'foo': ''}}}
        mgr._handle_action_msg = Mock(
            name='_handle_action_msg', return_value=('reply', ['actions']))
        mgr._log_received_msg = Mock(name='_log_received_msg')
        message = {'source': 'worker', 'msg_type': 'foo', 'payload': 'bar'}
        reply, next_steps = mgr._message_handler(yaml.dump(message))
        mgr._log_received_msg.assert_called_once_with('worker', 'foo')
        mgr._handle_action_msg.assert_called_once_with('worker', 'foo', 'bar')
        assert reply, next_steps == ('reply', ['actions'])


def test_handle_undefined_msg(mgr):
    """Unit test for NowcastManager._handle_undefined_msg method.
    """
    mgr.name = 'nowcast_mgr'
    mgr.logger = Mock(name='logger')
    reply = mgr._handle_undefined_msg('worker', 'foo')
    assert mgr.logger.warning.call_count == 1
    expected = yaml.dump({
        'source': 'nowcast_mgr', 'msg_type': 'undefined msg', 'payload': None,
    })
    assert reply == expected


def test_log_received_msg(mgr):
    """Unit test for NowcastManager._log_received_msg method.
    """
    mgr.config = {'msg_types': {'worker': {'foo': 'bar'}}}
    mgr.logger = Mock(name='logger')
    mgr._log_received_msg('worker', 'foo')
    assert mgr.logger.debug.call_count == 1


def test_handle_need_msg(mgr):
    """Unit test for NowcastManager._handle_need_msg method.
    """
    mgr.name = 'nowcast_mgr'
    mgr.checklist = {'foo': 'bar'}
    reply = mgr._handle_need_msg('foo')
    expected = yaml.dump({
        'source': 'nowcast_mgr', 'msg_type': 'ack', 'payload': 'bar',
    })
    assert reply == expected


def test_handle_log_msg(mgr):
    """Unit test for NowcastManager._handle_log_msg method.
    """
    mgr.name = 'nowcast_mgr'
    mgr.worker_loggers = {'worker': Mock(name='worker_logger')}
    reply = mgr._handle_log_msg('worker', 'log.info', 'foo')
    mgr.worker_loggers['worker'].log.assert_called_once_with(
        logging.INFO, 'foo')
    expected = yaml.dump({
        'source': 'nowcast_mgr', 'msg_type': 'ack', 'payload': None,
        })
    assert reply == expected


class TestHandleActionMsg:
    """Unit tests for NowcastManager._handle_action_msg method.
    """
    def test_handle_action_msg_reply(self, mgr):
        mgr.name = 'nowcast_mgr'
        mgr._after_download_weather = Mock(name='_after_download_weather')
        reply, next_steps = mgr._handle_action_msg(
            'download_weather', 'success 00', True)
        expected = yaml.dump({
            'source': 'nowcast_mgr', 'msg_type': 'ack', 'payload': None,
            })
        assert reply == expected

    def test_handle_action_msg_next_steps(self, mgr):
        mgr.name = 'nowcast_mgr'
        mgr._after_download_weather = Mock(name='_after_download_weather')
        reply, next_steps = mgr._handle_action_msg(
            'download_weather', 'success 00', True)
        mgr._after_download_weather.assert_called_once_with(
            'download_weather', 'success 00', True)
        assert next_steps == mgr._after_download_weather()


class TestAfterDownloadWeather:
    """Unit tests for the NowcastManager._after_download_weather method.
    """
    @pytest.mark.parametrize('msg_type', [
        'crash',
        'failure 00',
        'failure 06',
        'failure 12',
        'failure 18',
    ])
    def test_no_action_msg_types(self, msg_type, mgr):
        mgr.config = {'run_types': []}
        actions = mgr._after_download_weather(
            'download_weather', msg_type, 'payload')
        assert actions is None

    @pytest.mark.parametrize('msg_type', [
        'success 00',
        'success 06',
        'success 12',
        'success 18',
    ])
    def test_update_checklist_on_success(self, msg_type, mgr):
        mgr.config = {'run_types': []}
        actions = mgr._after_download_weather(
            'download_weather', msg_type, 'payload')
        expected = (
            mgr._update_checklist, ['download_weather', 'weather', 'payload'],
        )
        assert actions[0] == expected

    def test_success_06_launch_make_runoff_file_worker(self, mgr):
        mgr.config = {'run_types': []}
        actions = mgr._after_download_weather(
            'download_weather', 'success 06', 'payload')
        expected = (
            mgr._launch_worker, ['make_runoff_file', mgr.config],
        )
        assert actions[1] == expected

    @pytest.mark.parametrize('index, worker, worker_args', [
        (1, 'get_NeahBay_ssh', 'nowcast'),
        (2, 'grib_to_netcdf', 'nowcast+'),
    ])
    def test_success_12_launch_workers(self, index, worker, worker_args, mgr):
        mgr.config = {'run_types': ['nowcast']}
        actions = mgr._after_download_weather(
            'download_weather', 'success 12', 'payload')
        expected = (mgr._launch_worker, [worker, [worker_args]],)
        assert actions[index] == expected

    @pytest.mark.parametrize('index, worker, worker_args', [
        (2, 'get_NeahBay_ssh', 'forecast2'),
        (3, 'grib_to_netcdf', 'forecast2'),
    ])
    def test_success_06_launch_workers(self, index, worker, worker_args, mgr):
        mgr.config = {'run_types': ['forecast2']}
        actions = mgr._after_download_weather(
            'download_weather', 'success 06', 'payload')
        expected = (mgr._launch_worker, [worker, [worker_args]],)
        assert actions[index] == expected


class TestAfterGetNeahBaySSH:
    """Unit tests for the NowcastManager._after_get_NeahBay_ssh method.
    """
    @pytest.mark.parametrize('msg_type', [
        'crash',
        'failure nowcast',
        'failure forecast',
        'failure forecast2',
    ])
    def test_no_action_msg_types(self, msg_type, mgr):
        mgr.config = {'run_types': [], 'run': []}
        actions = mgr._after_get_NeahBay_ssh(
            'get_NeahBay_ssh', msg_type, 'payload')
        assert actions is None

    @pytest.mark.parametrize('msg_type', [
        'success nowcast',
        'success forecast',
        'success forecast2',
    ])
    def test_update_checklist_on_success(self, msg_type, mgr):
        mgr.config = {'run_types': [], 'run': []}
        actions = mgr._after_get_NeahBay_ssh(
            'get_NeahBay_ssh', msg_type, 'payload')
        expected = (
            mgr._update_checklist,
            ['get_NeahBay_ssh', 'Neah Bay ssh', 'payload'],
        )
        assert actions[0] == expected

    @pytest.mark.parametrize('host_type, host_name', [
        ('hpc host', 'orcinus-nowcast'),
        ('cloud host', 'west.cloud-nowcast'),
    ])
    def test_success_forecast_launch_upload_forcing_worker(
        self, host_type, host_name, mgr,
    ):
        mgr.config = {'run_types': ['forecast'], 'run': {host_type: host_name}}
        actions = mgr._after_get_NeahBay_ssh(
            'get_NeahBay_ssh', 'success forecast', 'payload')
        expected = (
            mgr._launch_worker, ['upload_forcing', [host_name, 'ssh']],
        )
        assert actions[1] == expected


class TestUpdateChecklist:
    """Unit tests for the NowcastManager._update_checklist method.
    """
    def test_update_existing_value(self, mgr):
        mgr.config = {'checklist file': 'nowcast_checklist.yaml'}
        mgr.checklist = {'foo': 'bar'}
        with patch.object(mgr_module(), 'open', mock_open()):
            mgr._update_checklist('worker', 'foo', 'baz')
        assert mgr.checklist['foo'] == 'baz'

    def test_keyerror_adds_key_and_value(self, mgr):
        pass

    def test_valueerror_adds_key_and_value(self, mgr):
        pass

    def test_attributeerror_adds_key_and_value(self, mgr):
        pass

    def test_log_info_msg(self, mgr):
        pass

    def test_yaml_dump_checklist_to_disk(self, mgr):
        pass