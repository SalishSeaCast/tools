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
class TestMessageProcesor(object):
    """Unit tests for message_processor() function.
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
        reply, next_steps = nowcast_mgr_module.message_processor(
            config, message)
        expected = {
            'source': 'nowcast_mgr',
            'msg_type': 'undefined msg',
            'payload': None,
        }
        assert yaml.safe_load(reply) == expected

    def test_undefined_msg_type_next_steps(self, nowcast_mgr_module):
        config = {
            'msg_types': {
                'worker': {
                    'the end': 'foo'
                }
            }
        }
        message = '{source: worker, msg_type: bar, payload: null}\n'
        reply, next_steps = nowcast_mgr_module.message_processor(
            config, message)
        assert next_steps is None

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
        nowcast_mgr_module.message_processor(config, message)
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
        reply, next_steps = nowcast_mgr_module.message_processor(
            config, message)
        expected = {
            'source': 'nowcast_mgr',
            'msg_type': 'ack',
            'payload': None,
        }
        assert yaml.safe_load(reply) == expected

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
        nowcast_mgr_module.message_processor(config, message)
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
        reply, next_steps = nowcast_mgr_module.message_processor(
            config, message)
        expected = {
            'source': 'nowcast_mgr',
            'msg_type': 'ack',
            'payload': None,
        }
        assert yaml.safe_load(reply) == expected

    def test_the_end_next_msg_steps(self, nowcast_mgr_module):
        config = {
            'msg_types': {
                'worker': {
                    'the end': 'foo'
                }
            }
        }
        message = '{source: worker, msg_type: the end, payload: null}\n'
        reply, next_steps = nowcast_mgr_module.message_processor(
            config, message)
        assert next_steps == [(nowcast_mgr_module.finish_automation, [config])]


@pytest.mark.use_fixtures(['nowcast_mgr_module'])
class TestAfterInitCloudSuccess(object):
    """Unit tests for after_init_cloud() function actions for success message.
    """
    def test_launch_n_nodes(self, nowcast_mgr_module):
        config = {
            'run':
                {'cloud host': 'west.cloud',
                 'west.cloud':
                    {'nodes': 3}}}
        payload = {}
        next_steps = nowcast_mgr_module.after_init_cloud(
            'init_cloud', 'success', payload, config)
        expected = [
            (nowcast_mgr_module.update_checklist,
             ['init_cloud', 'nodes', payload]),
        ]
        for i in range(3):
            node_name = 'nowcast{}'.format(i)
            expected.append(
                (nowcast_mgr_module.launch_worker,
                 ['create_compute_node', config, [node_name]]),
            )
        expected.append([nowcast_mgr_module.is_cloud_ready, [config]])
        assert next_steps == expected

    def test_launch_missing_0_node(self, nowcast_mgr_module):
        config = {
            'run':
                {'cloud host': 'west.cloud',
                 'west.cloud':
                    {'nodes': 3}}}
        payload = {
            'nowcast1': '192.168.0.10',
            'nowcast2': '192.168.0.11',
        }
        next_steps = nowcast_mgr_module.after_init_cloud(
            'init_cloud', 'success', payload, config)
        expected = [
            (nowcast_mgr_module.update_checklist,
             ['init_cloud', 'nodes', payload]),
            (nowcast_mgr_module.launch_worker,
             ['create_compute_node', config, ['nowcast0']]),
        ]
        expected.append([nowcast_mgr_module.is_cloud_ready, [config]])
        assert next_steps == expected

    def test_launch_missing_last_node(self, nowcast_mgr_module):
        config = {
            'run':
                {'cloud host': 'west.cloud',
                 'west.cloud':
                    {'nodes': 3}}}
        payload = {
            'nowcast0': '192.168.0.10',
            'nowcast1': '192.168.0.11',
        }
        next_steps = nowcast_mgr_module.after_init_cloud(
            'init_cloud', 'success', payload, config)
        expected = [
            (nowcast_mgr_module.update_checklist,
             ['init_cloud', 'nodes', payload]),
            (nowcast_mgr_module.launch_worker,
             ['create_compute_node', config, ['nowcast2']]),
        ]
        expected.append([nowcast_mgr_module.is_cloud_ready, [config]])
        assert next_steps == expected

    def test_launch_missing_misc_node(self, nowcast_mgr_module):
        config = {
            'run':
                {'cloud host': 'west.cloud',
                 'west.cloud':
                    {'nodes': 5}}}
        payload = {
            'nowcast0': '192.168.0.10',
            'nowcast1': '192.168.0.11',
            'nowcast3': '192.168.0.13',
            'nowcast4': '192.168.0.14',
        }
        next_steps = nowcast_mgr_module.after_init_cloud(
            'init_cloud', 'success', payload, config)
        expected = [
            (nowcast_mgr_module.update_checklist,
             ['init_cloud', 'nodes', payload]),
            (nowcast_mgr_module.launch_worker,
             ['create_compute_node', config, ['nowcast2']]),
        ]
        expected.append([nowcast_mgr_module.is_cloud_ready, [config]])
        assert next_steps == expected

    def test_launch_no_nodes(self, nowcast_mgr_module):
        config = {
            'run':
                {'cloud host': 'west.cloud',
                 'west.cloud':
                    {'nodes': 5}}}
        payload = {
            'nowcast0': '192.168.0.10',
            'nowcast1': '192.168.0.11',
            'nowcast2': '192.168.0.12',
            'nowcast3': '192.168.0.13',
            'nowcast4': '192.168.0.14',
        }
        next_steps = nowcast_mgr_module.after_init_cloud(
            'init_cloud', 'success', payload, config)
        expected = [
            (nowcast_mgr_module.update_checklist,
             ['init_cloud', 'nodes', payload]),
        ]
        expected.append([nowcast_mgr_module.is_cloud_ready, [config]])
        assert next_steps == expected


@pytest.mark.use_fixtures(['nowcast_mgr_module'])
class TestIsCloudReady(object):
    """Unit tests for is_cloud_ready() function.
    """
    def test_no_nowcast0(self, nowcast_mgr_module):
        config = {
            'run':
                {'cloud host': 'west.cloud',
                 'west.cloud':
                    {'nodes': 5}}}
        p_checklist = patch.dict(
            nowcast_mgr_module.checklist,
            {'nodes': {'nowcast1': '192.168.0.11'}})
        with p_checklist:
            nowcast_mgr_module.is_cloud_ready(config)
            assert 'cloud ready' not in nowcast_mgr_module.checklist

    def test_no_cloud_addr_sets_empty_addr(self, nowcast_mgr_module):
        config = {
            'run':
                {'cloud host': 'west.cloud',
                 'west.cloud':
                    {'nodes': 5}}}
        nowcast_mgr_module.launch_worker = Mock(name='launch_worker')
        p_checklist = patch.dict(
            nowcast_mgr_module.checklist,
            {'nodes': {'nowcast0': '192.168.0.10'}})
        with p_checklist:
            nowcast_mgr_module.is_cloud_ready(config)
            assert nowcast_mgr_module.checklist['cloud addr'] == ''

    def test_no_cloud_addr_launches_set_head_node_ip(self, nowcast_mgr_module):
        config = {
            'run':
                {'cloud host': 'west.cloud',
                 'west.cloud':
                    {'nodes': 5}}}
        nowcast_mgr_module.launch_worker = Mock(name='launch_worker')
        p_checklist = patch.dict(
            nowcast_mgr_module.checklist,
            {'nodes': {'nowcast0': '192.168.0.10'}})
        with p_checklist:
            nowcast_mgr_module.is_cloud_ready(config)
            nowcast_mgr_module.launch_worker.assert_called_once_with(
                'set_head_node_ip', config)

    def test_cloud_ready(self, nowcast_mgr_module):
        config = {
            'run':
                {'cloud host': 'west.cloud',
                 'west.cloud':
                    {'nodes': 2}}}
        nowcast_mgr_module.launch_worker = Mock(name='launch_worker')
        p_checklist = patch.dict(
            nowcast_mgr_module.checklist,
            {'nodes': {'nowcast0': '192.168.0.10',
                       'nowcast1': '192.168.0.11'}})
        with p_checklist:
            nowcast_mgr_module.is_cloud_ready(config)
            assert nowcast_mgr_module.checklist['cloud ready']

    def test_cloud_ready_launches_set_ssh_config(self, nowcast_mgr_module):
        config = {
            'run':
                {'cloud host': 'west.cloud',
                 'west.cloud':
                    {'nodes': 2}}}
        nowcast_mgr_module.launch_worker = Mock(name='launch_worker')
        p_checklist = patch.dict(
            nowcast_mgr_module.checklist,
            {'cloud addr': '206.12.48.112',
             'nodes': {'nowcast0': '192.168.0.10',
                       'nowcast1': '192.168.0.11'}})
        with p_checklist:
            nowcast_mgr_module.is_cloud_ready(config)
            nowcast_mgr_module.launch_worker.assert_called_once_with(
                'set_ssh_config', config)


def test_the_end_next_step(nowcast_mgr_module):
    config = Mock(name='config')
    next_steps = nowcast_mgr_module.the_end(config)
    assert next_steps == [(nowcast_mgr_module.finish_automation, [config])]


@pytest.mark.parametrize('worker, msg_type', [
    ('after_download_weather', 'failure 00'),
    ('after_download_weather', 'failure 06'),
    ('after_download_weather', 'failure 12'),
    ('after_download_weather', 'failure 18'),
    ('after_download_weather', 'crash'),
    ('after_get_NeahBay_ssh', 'failure'),
    ('after_get_NeahBay_ssh', 'crash'),
    ('after_make_runoff_file', 'failure'),
    ('after_make_runoff_file', 'crash'),
    ('after_grib_to_netcdf', 'failure nowcast+'),
    ('after_grib_to_netcdf', 'failure forecast2'),
    ('after_grib_to_netcdf', 'crash'),
    ('after_init_cloud', 'failure'),
    ('after_init_cloud', 'crash'),
    ('after_create_compute_node', 'failure'),
    ('after_create_compute_node', 'crash'),
    ('after_set_head_node_ip', 'failure'),
    ('after_set_head_node_ip', 'crash'),
    ('after_set_ssh_config', 'failure'),
    ('after_set_ssh_config', 'crash'),
    ('after_set_mpi_hosts', 'failure'),
    ('after_set_mpi_hosts', 'crash'),
    ('after_upload_forcing', 'failure'),
    ('after_upload_forcing', 'crash'),
    ('after_make_forcing_links', 'failure'),
    ('after_make_forcing_links', 'crash'),
    ('after_download_results', 'failure nowcast'),
    ('after_download_results', 'failure forecast'),
    ('after_download_results', 'crash'),
])
def test_after_worker_no_next_steps(
    worker, msg_type, nowcast_mgr_module,
):
    payload = {'orcinus': True}
    config = {'run': {'hpc host': 'orcinus'}}
    after_worker_func = getattr(nowcast_mgr_module, worker)
    next_steps = after_worker_func(worker, msg_type, payload, config)
    assert next_steps is None


@pytest.mark.parametrize('msg_type', [
    'success 00',
    'success 18',
])
def test_simple_download_weather_success_next_step_args(
    msg_type, nowcast_mgr_module,
):
    payload = Mock(name='payload')
    config = Mock(name='config')
    next_steps = nowcast_mgr_module.after_download_weather(
        'download_weather', msg_type, payload, config)
    expected = [
        (nowcast_mgr_module.update_checklist,
         ['download_weather', 'weather', payload]),
    ]
    assert next_steps == expected


def test_download_weather_success_06_next_step_args(nowcast_mgr_module):
    payload = Mock(name='payload')
    config = Mock(name='config')
    next_steps = nowcast_mgr_module.after_download_weather(
        'download_weather', 'success 06', payload, config)
    expected = [
        (nowcast_mgr_module.update_checklist,
         ['download_weather', 'weather', payload]),
        (nowcast_mgr_module.launch_worker, ['make_runoff_file', config]),
        (nowcast_mgr_module.launch_worker,
         ['grib_to_netcdf', config, ['forecast2']]),
    ]
    assert next_steps == expected


def test_download_weather_success_12_next_step_args(nowcast_mgr_module):
    payload = Mock(name='payload')
    config = Mock(name='config')
    next_steps = nowcast_mgr_module.after_download_weather(
        'download_weather', 'success 12', payload, config)
    expected = [
        (nowcast_mgr_module.update_checklist,
         ['download_weather', 'weather', payload]),
        (nowcast_mgr_module.launch_worker, ['get_NeahBay_ssh', config]),
        (nowcast_mgr_module.launch_worker,
         ['grib_to_netcdf', config, ['nowcast+']]),
    ]
    assert next_steps == expected


def test_get_NeahBay_ssh_success_next_step_args(nowcast_mgr_module):
    payload = Mock(name='payload')
    config = Mock(name='config')
    next_steps = nowcast_mgr_module.after_get_NeahBay_ssh(
        'get_NeahBay_ssh', 'success', payload, config)
    expected = [
        (nowcast_mgr_module.update_checklist,
         ['get_NeahBay_ssh', 'sshNeahBay', payload]),
    ]
    assert next_steps == expected


def test_make_runoff_file_success_next_steps(nowcast_mgr_module):
    payload = Mock(name='payload')
    config = Mock(name='config')
    next_steps = nowcast_mgr_module.after_make_runoff_file(
        'make_runoff_file', 'success', payload, config)
    expected = [
        (nowcast_mgr_module.update_checklist,
         ['make_runoff_file', 'rivers', payload]),
    ]
    assert next_steps == expected


def test_grib_to_netcdf_success_nowcast_next_steps(nowcast_mgr_module):
    payload = Mock(name='payload')
    config = {'run': {'hpc host': 'orcinus'}}
    next_steps = nowcast_mgr_module.after_grib_to_netcdf(
        'grib_to_netcdf', 'success nowcast+', payload, config)
    expected = [
        (nowcast_mgr_module.update_checklist,
         ['grib_to_netcdf', 'weather forcing', payload]),
        (nowcast_mgr_module.launch_worker,
         ['upload_forcing', config, ['orcinus']]),
        (nowcast_mgr_module.launch_worker, ['init_cloud', config]),
    ]
    assert next_steps == expected


def test_grib_to_netcdf_success_forecast2_next_steps(nowcast_mgr_module):
    payload = Mock(name='payload')
    config = {'run': {'hpc host': 'orcinus'}}
    next_steps = nowcast_mgr_module.after_grib_to_netcdf(
        'grib_to_netcdf', 'success forecast2', payload, config)
    expected = [
        (nowcast_mgr_module.update_checklist,
         ['grib_to_netcdf', 'weather forcing', payload]),
    ]
    assert next_steps == expected


def test_create_compute_node_success_next_steps(nowcast_mgr_module):
    payload = Mock(name='payload')
    config = Mock(name='config')
    next_steps = nowcast_mgr_module.after_create_compute_node(
        'create_compute_node', 'success', payload, config)
    expected = [
        (nowcast_mgr_module.update_checklist,
         ['create_compute_node', 'nodes', payload]),
        (nowcast_mgr_module.is_cloud_ready, [config]),
    ]
    assert next_steps == expected


def test_set_head_node_ip_success_next_steps(nowcast_mgr_module):
    payload = Mock(name='payload')
    config = Mock(name='config')
    next_steps = nowcast_mgr_module.after_set_head_node_ip(
        'set_head_node_ip', 'success', payload, config)
    expected = [
        (nowcast_mgr_module.update_checklist,
         ['set_head_node_ip', 'cloud addr', payload]),
    ]
    assert next_steps == expected


def test_set_ssh_config_success_next_steps(nowcast_mgr_module):
    payload = Mock(name='payload')
    config = Mock(name='config')
    next_steps = nowcast_mgr_module.after_set_ssh_config(
        'set_ssh_config', 'success', payload, config)
    expected = [
        (nowcast_mgr_module.update_checklist,
         ['set_ssh_config', 'ssh config', payload]),
        (nowcast_mgr_module.launch_worker, ['set_mpi_hosts', config]),
    ]
    assert next_steps == expected


def test_set_mpi_hosts_success_next_steps(nowcast_mgr_module):
    payload = Mock(name='payload')
    config = Mock(name='config')
    next_steps = nowcast_mgr_module.after_set_mpi_hosts(
        'set_mpi_hosts', 'success', payload, config)
    expected = [
        (nowcast_mgr_module.update_checklist,
         ['set_mpi_hosts', 'mpi_hosts', payload]),
        (nowcast_mgr_module.launch_worker, ['mount_sshfs', config]),
    ]
    assert next_steps == expected


def test_mount_sshfs_success_next_steps(nowcast_mgr_module):
    payload = Mock(name='payload')
    config = {'run': {'cloud host': 'west.cloud'}}
    next_steps = nowcast_mgr_module.after_mount_sshfs(
        'mount_sshfs', 'success', payload, config)
    expected = [
        (nowcast_mgr_module.update_checklist,
         ['mount_sshfs', 'sshfs mount', payload]),
        (nowcast_mgr_module.launch_worker,
         ['upload_forcing', config, ['west.cloud']])
    ]
    assert next_steps == expected


def test_upload_forcing_success_next_steps(nowcast_mgr_module):
    payload = {'west.cloud': True}
    config = Mock(name='config')
    next_steps = nowcast_mgr_module.after_upload_forcing(
        'upload_forcing', 'success', payload, config)
    expected = [
        (nowcast_mgr_module.update_checklist,
         ['upload_forcing', 'forcing upload', payload]),
        (nowcast_mgr_module.launch_worker,
         ['make_forcing_links', config, ['west.cloud']]),
    ]
    assert next_steps == expected


def test_make_forcing_links_success_next_steps(nowcast_mgr_module):
    payload = Mock(name='payload')
    config = Mock(name='config')
    next_steps = nowcast_mgr_module.after_make_forcing_links(
        'make_forcing_links', 'success', payload, config)
    expected = [
        (nowcast_mgr_module.update_checklist,
         ['make_forcing_links', 'forcing links', payload]),
    ]
    assert next_steps == expected


@pytest.mark.parametrize('msg_type', [
    'success nowcast',
    'success forecast',
])
def test_download_results_success_next_steps(msg_type, nowcast_mgr_module):
    payload = Mock(name='payload')
    config = Mock(name='config')
    next_steps = nowcast_mgr_module.after_download_results(
        'download_results', msg_type, payload, config)
    expected = [
        (nowcast_mgr_module.update_checklist,
         ['download_results', 'results files', payload]),
    ]
    assert next_steps == expected
