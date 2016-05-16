# Copyright 2013-2016 The Salish Sea MEOPAR Contributors
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

"""SalishSeaCmd prepare sub-command plug-in unit tests
"""
import os
try:
    from unittest.mock import (
        call,
        Mock,
        patch,
    )
except ImportError:
    from mock import (
        call,
        Mock,
        patch,
    )

import cliff.app
import pytest

import salishsea_cmd.prepare


@pytest.fixture
def prepare_cmd():
    return salishsea_cmd.prepare.Prepare(Mock(spec=cliff.app.App), [])


class TestGetParser:
    """Unit tests for `salishsea prepare` sub-command command-line parser.
    """
    def test_get_parser(self, prepare_cmd):
        parser = prepare_cmd.get_parser('salishsea prepare')
        assert parser.prog == 'salishsea prepare'

    def test_parsed_args_defaults(self, prepare_cmd):
        parser = prepare_cmd.get_parser('salishsea prepare')
        parsed_args = parser.parse_args(['foo'])
        assert parsed_args.desc_file == 'foo'
        assert not parsed_args.nemo34
        assert not parsed_args.quiet

    @pytest.mark.parametrize('flag, attr', [
        ('--nemo3.4', 'nemo34'),
        ('-q', 'quiet'),
        ('--quiet', 'quiet'),
    ])
    def test_parsed_args_flags(self, flag, attr, prepare_cmd):
        parser = prepare_cmd.get_parser('salishsea prepare')
        parsed_args = parser.parse_args(['foo', flag])
        assert getattr(parsed_args, attr)


@patch.object(salishsea_cmd.prepare.lib, 'load_run_desc')
@patch.object(salishsea_cmd.prepare, '_check_nemo_exec')
@patch.object(salishsea_cmd.prepare, '_check_xios_exec')
@patch.object(salishsea_cmd.prepare.os.path, 'dirname')
@patch.object(salishsea_cmd.prepare, '_make_run_dir')
@patch.object(salishsea_cmd.prepare, '_make_namelists')
@patch.object(salishsea_cmd.prepare, '_copy_run_set_files')
@patch.object(salishsea_cmd.prepare, '_make_executable_links')
@patch.object(salishsea_cmd.prepare, '_make_grid_links')
@patch.object(salishsea_cmd.prepare, '_make_forcing_links')
class TestPrepare:
    """Unit tests for `salishsea prepare` prepare() function.
    """
    @pytest.mark.parametrize('nemo34, m_cne_return, m_cxe_return', [
        (True, ('repo', 'bin_dir'), (None, None)),
        (False, ('nemo_repo', 'nemo_bin_dir'), ('xios_repo', 'xios_bin_dir')),
    ])
    def test_prepare(
        self, m_mfl, m_mgl, m_mel, m_crsf, m_mnl, m_mrd, m_dirname, m_cxe, m_cne,
        m_lrd, nemo34, m_cne_return, m_cxe_return,
    ):
        m_cne.return_value = m_cne_return
        m_cxe.return_value = m_cxe_return
        run_dir = salishsea_cmd.prepare.prepare('SalishSea.yaml', nemo34)
        m_lrd.assert_called_once_with('SalishSea.yaml')
        m_cne.assert_called_once_with(m_lrd(), nemo34)
        if nemo34:
            assert not m_cxe.called
        else:
            m_cne.assert_called_once_with(m_lrd(), nemo34)
        m_dirname.assert_called_once_with(os.path.abspath('SalishSea.yaml'))
        m_mrd.assert_called_once_with(m_lrd())
        m_mnl.assert_called_once_with(
            m_dirname(), m_lrd(), m_mrd(), m_cne_return[0], nemo34)
        m_crsf.assert_called_once_with(
            m_lrd(), 'SalishSea.yaml', m_dirname(), m_mrd(), nemo34)
        m_mel.assert_called_once_with(
            m_cne_return[0], m_cne_return[1], m_mrd(), nemo34,
            m_cxe_return[0], m_cxe_return[1])
        m_mgl.assert_called_once_with(m_lrd(), m_mrd())
        m_mfl.assert_called_once_with(m_lrd(), m_mrd(), nemo34)
        assert run_dir == m_mrd()


class TestCheckNemoExec:
    """Unit tests for `salishsea prepare` _check_nemo_exec() function.
    """
    def test_nemo_code_repo_path(self, tmpdir):
        p_code = tmpdir.ensure_dir('NEMO-3.6-code')
        p_code.ensure(
            'NEMOGCM', 'CONFIG', 'SalishSea', 'BLD', 'bin', 'nemo.exe')
        run_desc = {
            'config_name': 'SalishSea',
            'paths': {'NEMO-code': str(p_code)},
        }
        nemo_code_repo, nemo_bin_dir = salishsea_cmd.prepare._check_nemo_exec(
            run_desc, nemo34=False)
        assert nemo_code_repo == p_code

    def test_nemo_bin_dir_path(self, tmpdir):
        p_code = tmpdir.ensure_dir('NEMO-3.6-code')
        run_desc = {
            'config_name': 'SalishSea',
            'paths': {'NEMO-code': str(p_code)},
        }
        p_bin_dir = p_code.ensure_dir(
            'NEMOGCM', 'CONFIG', 'SalishSea', 'BLD', 'bin')
        p_bin_dir.ensure('nemo.exe')
        nemo_code_repo, nemo_bin_dir = salishsea_cmd.prepare._check_nemo_exec(
            run_desc, nemo34=False)
        assert nemo_bin_dir == p_bin_dir

    def test_nemo_exec_not_found(self, tmpdir):
        p_code = tmpdir.ensure_dir('NEMO-3.6-code')
        run_desc = {
            'config_name': 'SalishSea',
            'paths': {'NEMO-code': str(p_code)},
        }
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._check_nemo_exec(run_desc, nemo34=False)

    @patch.object(salishsea_cmd.prepare, 'log')
    def test_iom_server_exec_not_found(self, m_log, tmpdir):
        p_code = tmpdir.ensure_dir('NEMO-3.6-code')
        run_desc = {
            'config_name': 'SalishSea',
            'paths': {'NEMO-code': str(p_code)},
        }
        p_bin_dir = p_code.ensure_dir(
            'NEMOGCM', 'CONFIG', 'SalishSea', 'BLD', 'bin')
        p_exists = patch.object(
            salishsea_cmd.prepare.os.path, 'exists', side_effect=[True, False])
        with p_exists:
            nemo_code_repo, nemo_bin_dir = salishsea_cmd.prepare._check_nemo_exec(
                run_desc, nemo34=True)
        m_log.warn.assert_called_once_with(
            '{}/server.exe not found - are you running without key_iomput?'
            .format(p_bin_dir))

    def test_nemo36_no_iom_server_check(self, tmpdir):
        p_code = tmpdir.ensure_dir('NEMO-3.6-code')
        run_desc = {
            'config_name': 'SalishSea',
            'paths': {'NEMO-code': str(p_code)},
        }
        p_code.ensure_dir(
            'NEMOGCM', 'CONFIG', 'SalishSea', 'BLD', 'bin')
        with patch.object(salishsea_cmd.prepare.os.path, 'exists') as m_exists:
            nemo_code_repo, nemo_bin_dir = salishsea_cmd.prepare._check_nemo_exec(
                run_desc, nemo34=False)
        assert m_exists.call_count == 1


class TestCheckXiosExec:
    """Unit tests for `salishsea prepare` _check_xios_exec() function.
    """
    def test_xios_bin_dir_path(self, tmpdir):
        p_xios = tmpdir.ensure_dir('XIOS')
        run_desc = {
            'paths': {'XIOS': str(p_xios)},
        }
        p_bin_dir = p_xios.ensure_dir('bin')
        p_bin_dir.ensure('xios_server.exe')
        xios_code_repo, xios_bin_dir = salishsea_cmd.prepare._check_xios_exec(
            run_desc)
        assert xios_code_repo == p_xios
        assert xios_bin_dir == p_bin_dir

    def test_xios_exec_not_found(self, tmpdir):
        p_xios = tmpdir.ensure_dir('XIOS')
        run_desc = {
            'paths': {'XIOS': str(p_xios)},
        }
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._check_xios_exec(run_desc)


class TestMakeRunDir:
    """Unit test for `salishsea prepare` _make_run_dir() function.
    """
    @patch.object(salishsea_cmd.prepare.uuid, 'uuid1', return_value='uuid')
    def test_make_run_dir(self, m_uuid1, tmpdir):
        """_make_run_dir() creates directory w/ UUID v1 name
        """
        p_runs_dir = tmpdir.ensure_dir('SalishSea')
        run_desc = {
            'paths': {'runs directory': str(p_runs_dir)},
        }
        run_dir = salishsea_cmd.prepare._make_run_dir(run_desc)
        assert run_dir == os.path.join(str(p_runs_dir), m_uuid1())


class TestRemoveRunDir:
    """Unit tests for `salishsea prepare` _remove_run_dir() function.
    """
    def test_remove_run_dir(self, tmpdir):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        salishsea_cmd.prepare._remove_run_dir(str(p_run_dir))
        assert not p_run_dir.check()

    def test_remove_run_dir_file(self, tmpdir):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        p_run_dir.ensure('namelist')
        salishsea_cmd.prepare._remove_run_dir(str(p_run_dir))
        assert not p_run_dir.join('namelist').check()
        assert not p_run_dir.check()

    @patch.object(salishsea_cmd.prepare.os, 'rmdir')
    def test_remove_run_dir_no_run_dir(self, m_rmdir):
        salishsea_cmd.prepare._remove_run_dir('run_dir')
        assert not m_rmdir.called


class TestMakeNamelists:
    """Unit tests for `salishsea prepare` _make_namelists() function.
    """
    def test_nemo34(self):
        with patch.object(salishsea_cmd.prepare, '_make_namelist_nemo34') as m_mn34:
            salishsea_cmd.prepare._make_namelists(
                'run_set_dir', 'run_desc', 'run_dir', 'nemo_code_repo',
                nemo34=True)
        m_mn34.assert_called_once_with('run_set_dir', 'run_desc', 'run_dir')

    def test_nemo36(self):
        with patch.object(salishsea_cmd.prepare, '_make_namelists_nemo36') as m_mn36:
            salishsea_cmd.prepare._make_namelists(
                'run_set_dir', 'run_desc', 'run_dir', 'nemo_code_repo',
                nemo34=False)
        m_mn36.assert_called_once_with(
            'run_set_dir', 'run_desc', 'run_dir', 'nemo_code_repo')


class TestMakeNamelistNEMO34:
    """Unit tests for `salishsea prepare` _make_namelist_nemo34() function.
    """
    def test_make_namelist_nemo34(self, tmpdir):
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('namelist.time').write('&namrun\n&end\n')
        run_desc = {
            'namelists': [
                str(p_run_set_dir.join('namelist.time')),
            ],
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        with patch.object(salishsea_cmd.prepare, '_set_mpi_decomposition'):
            salishsea_cmd.prepare._make_namelist_nemo34(
                str(p_run_set_dir), run_desc, str(p_run_dir))
        assert p_run_dir.join('namelist').check()

    def test_make_file_not_found_error(self, tmpdir):
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        run_desc = {
            'namelists': [
                str(p_run_set_dir.join('namelist.time')),
            ],
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_namelist_nemo34(
                str(p_run_set_dir), run_desc, str(p_run_dir))

    def test_namelist_ends_with_empty_namelists(
        self, tmpdir,
    ):
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('namelist.time').write('&namrun\n&end\n')
        run_desc = {
            'namelists': [
                str(p_run_set_dir.join('namelist.time')),
            ],
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        with patch.object(salishsea_cmd.prepare, '_set_mpi_decomposition'):
            salishsea_cmd.prepare._make_namelist_nemo34(
                str(p_run_set_dir), run_desc, str(p_run_dir))
        namelist = p_run_dir.join('namelist').read()
        assert namelist.endswith(salishsea_cmd.prepare.EMPTY_NAMELISTS)


class TestMakeNamelistNEMO36:
    """Unit tests for `salishsea prepare` _make_namelist_nemo36() function.
    """
    def test_make_namelists_nemo36(self, tmpdir):
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('namelist.time').write('&namrun\n&end\n')
        p_run_set_dir.join('namelist_top').write('&namtrc\n&end\n')
        p_run_set_dir.join('namelist_pisces').write('&nampisbio\n&end\n')
        run_desc = {
            'namelists': {
                'namelist_cfg': [
                    str(p_run_set_dir.join('namelist.time')),
                ],
                'namelist_top_cfg': [
                    str(p_run_set_dir.join('namelist_top')),
                ],
                'namelist_pisces_cfg': [
                    str(p_run_set_dir.join('namelist_pisces')),
                ],
            }
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        with patch.object(salishsea_cmd.prepare, '_set_mpi_decomposition'):
            salishsea_cmd.prepare._make_namelists_nemo36(
                str(p_run_set_dir), run_desc, str(p_run_dir), 'NEMO-code')
        assert p_run_dir.join('namelist_cfg').check()
        assert p_run_dir.join('namelist_top_cfg').check()
        assert p_run_dir.join('namelist_pisces_cfg').check()

    def test_file_not_found_error(self, tmpdir):
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        run_desc = {
            'namelists': {
                'namelist_cfg': [
                    str(p_run_set_dir.join('namelist.time')),
                ],
            }
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_namelists_nemo36(
                str(p_run_set_dir), run_desc, str(p_run_dir), 'NEMO-code')

    def test_namelist_ref_symlinks(self, tmpdir):
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('namelist.time').write('&namrun\n&end\n')
        p_run_set_dir.join('namelist_top').write('&namtrc\n&end\n')
        p_run_set_dir.join('namelist_pisces').write('&nampisbio\n&end\n')
        run_desc = {
            'namelists': {
                'namelist_cfg': [
                    str(p_run_set_dir.join('namelist.time')),
                ],
                'namelist_top_cfg': [
                    str(p_run_set_dir.join('namelist_top')),
                ],
                'namelist_pisces_cfg': [
                    str(p_run_set_dir.join('namelist_pisces')),
                ],
            }
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        p_code = tmpdir.ensure_dir('NEMO-3.6-code')
        p_code.ensure('NEMOGCM/CONFIG/SHARED/namelist_ref')
        p_code.ensure('NEMOGCM/CONFIG/SHARED/namelist_top_ref')
        p_code.ensure('NEMOGCM/CONFIG/SHARED/namelist_pisces_ref')
        with patch.object(salishsea_cmd.prepare, '_set_mpi_decomposition'):
            salishsea_cmd.prepare._make_namelists_nemo36(
                str(p_run_set_dir), run_desc, str(p_run_dir), str(p_code))
        assert p_run_dir.join('namelist_ref').check(file=True, link=True)
        assert p_run_dir.join('namelist_top_ref').check(file=True, link=True)
        assert p_run_dir.join('namelist_pisces_ref').check(
            file=True, link=True)

    def test_namelist_cfg_set_mpi_decomposition(self, tmpdir):
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('namelist.time').write('&namrun\n&end\n')
        p_run_set_dir.join('namelist_top').write('&namtrc\n&end\n')
        run_desc = {
            'namelists': {
                'namelist_cfg': [
                    str(p_run_set_dir.join('namelist.time')),
                ],
                'namelist_top_cfg': [
                    str(p_run_set_dir.join('namelist_top')),
                ],
            }
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        with patch.object(salishsea_cmd.prepare, '_set_mpi_decomposition') as m_smd:
            salishsea_cmd.prepare._make_namelists_nemo36(
                str(p_run_set_dir), run_desc, str(p_run_dir), 'NEMO-code')
        m_smd.assert_called_once_with('namelist_cfg', run_desc, str(p_run_dir))

    def test_no_namelist_cfg_error(self, tmpdir):
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('namelist_top').write('&namtrc\n&end\n')
        run_desc = {
            'namelists': {
                'namelist_top_cfg': [
                    str(p_run_set_dir.join('namelist_top')),
                ],
            }
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_namelists_nemo36(
                str(p_run_set_dir), run_desc, str(p_run_dir), 'NEMO-code')


class TestCopyRunSetFiles:
    """Unit tests for `salishsea prepare` _copy_run_set_files() function.
    """
    @patch.object(salishsea_cmd.prepare.shutil, 'copy2')
    @patch.object(salishsea_cmd.prepare, '_set_xios_server_mode')
    def test_nemo34_copy_run_set_files_no_path(
        self, m_sxsm, m_copy,
    ):
        """_copy_run_set_files creates correct symlink for source w/o path
        """
        run_desc = {'output': {'files': 'iodef.xml'}}
        desc_file = 'foo.yaml'
        pwd = os.getcwd()
        with patch('salishsea_cmd.prepare.os.chdir'):
            salishsea_cmd.prepare._copy_run_set_files(
                run_desc, desc_file, pwd, 'run_dir', nemo34=True)
        expected = [
            call(os.path.join(pwd, 'iodef.xml'), 'iodef.xml'),
            call(os.path.join(pwd, 'foo.yaml'), 'foo.yaml'),
            call(os.path.join(pwd, 'xmlio_server.def'), 'xmlio_server.def'),
        ]
        assert m_copy.call_args_list == expected

    @patch.object(salishsea_cmd.prepare.shutil, 'copy2')
    @patch.object(salishsea_cmd.prepare, '_set_xios_server_mode')
    def test_nemo36_copy_run_set_files_no_path(
        self, m_sxsm, m_copy,
    ):
        """_copy_run_set_files creates correct symlink for source w/o path
        """
        run_desc = {
            'output': {
                'files': 'iodef.xml',
                'domain': 'domain_def.xml',
                'fields': 'field_def.xml',
            },
        }
        desc_file = 'foo.yaml'
        pwd = os.getcwd()
        with patch('salishsea_cmd.prepare.os.chdir'):
            salishsea_cmd.prepare._copy_run_set_files(
                run_desc, desc_file, pwd, 'run_dir', nemo34=False)
        expected = [
            call(os.path.join(pwd, 'iodef.xml'), 'iodef.xml'),
            call(os.path.join(pwd, 'foo.yaml'), 'foo.yaml'),
            call(os.path.join(pwd, 'domain_def.xml'), 'domain_def.xml'),
            call(os.path.join(pwd, 'field_def.xml'), 'field_def.xml'),
        ]
        assert m_copy.call_args_list == expected

    @patch.object(salishsea_cmd.prepare.shutil, 'copy2')
    @patch.object(salishsea_cmd.prepare, '_set_xios_server_mode')
    def test_nemo34_copy_run_set_files_relative_path(
        self, m_sxsm, m_copy,
    ):
        """_copy_run_set_files creates correct symlink for relative path source
        """
        run_desc = {'output': {'files': '../iodef.xml'}}
        desc_file = 'foo.yaml'
        pwd = os.getcwd()
        with patch.object(salishsea_cmd.prepare.os, 'chdir'):
            salishsea_cmd.prepare._copy_run_set_files(
                run_desc, desc_file, pwd, 'run_dir', nemo34=True)
        expected = [
            call(os.path.join(os.path.dirname(pwd), 'iodef.xml'), 'iodef.xml'),
            call(os.path.join(pwd, 'foo.yaml'), 'foo.yaml'),
            call(os.path.join(pwd, 'xmlio_server.def'), 'xmlio_server.def'),
        ]
        assert m_copy.call_args_list == expected

    @patch.object(salishsea_cmd.prepare.shutil, 'copy2')
    @patch.object(salishsea_cmd.prepare, '_set_xios_server_mode')
    def test_nemo36_copy_run_set_files_relative_path(
        self, m_sxsm, m_copy,
    ):
        """_copy_run_set_files creates correct symlink for relative path source
        """
        run_desc = {
            'output': {
                'files': '../iodef.xml',
                'domain': '../domain_def.xml',
                'fields': '../field_def.xml',
            },
        }
        desc_file = 'foo.yaml'
        pwd = os.getcwd()
        with patch.object(salishsea_cmd.prepare.os, 'chdir'):
            salishsea_cmd.prepare._copy_run_set_files(
                run_desc, desc_file, pwd, 'run_dir', nemo34=False)
        expected = [
            call(os.path.join(os.path.dirname(pwd), 'iodef.xml'), 'iodef.xml'),
            call(os.path.join(pwd, 'foo.yaml'), 'foo.yaml'),
            call(
                os.path.join(os.path.dirname(pwd), 'domain_def.xml'),
                'domain_def.xml'),
            call(
                os.path.join(os.path.dirname(pwd), 'field_def.xml'),
                'field_def.xml'),
        ]
        assert m_copy.call_args_list == expected


class TestMakeExecutableLinks:
    """Unit tests for `salishsea prepare` _make_executable_links() function.
    """
    @pytest.mark.parametrize('nemo34', [True, False])
    def test_nemo_exe_symlink(self, nemo34, tmpdir):
        p_nemo_bin_dir = tmpdir.ensure_dir(
            'NEMO-code/NEMOGCM/CONFIG/SalishSea/BLD/bin')
        p_nemo_bin_dir.ensure('nemo.exe')
        p_xios_bin_dir = tmpdir.ensure_dir('XIOS/bin')
        p_run_dir = tmpdir.ensure_dir('run_dir')
        with patch.object(salishsea_cmd.prepare.hg, 'parents'):
            salishsea_cmd.prepare._make_executable_links(
                'nemo_code_repo', str(p_nemo_bin_dir), str(p_run_dir),
                nemo34, 'xios_code_repo', str(p_xios_bin_dir))
        assert p_run_dir.join('nemo.exe').check(file=True, link=True)

    @pytest.mark.parametrize('nemo34', [True, False])
    def test_server_exe_symlink(self, nemo34, tmpdir):
        p_nemo_bin_dir = tmpdir.ensure_dir(
            'NEMO-code/NEMOGCM/CONFIG/SalishSea/BLD/bin')
        p_nemo_bin_dir.ensure('nemo.exe')
        p_xios_bin_dir = tmpdir.ensure_dir('XIOS/bin')
        if nemo34:
            p_nemo_bin_dir.ensure('server.exe')
        p_run_dir = tmpdir.ensure_dir('run_dir')
        with patch.object(salishsea_cmd.prepare.hg, 'parents'):
            salishsea_cmd.prepare._make_executable_links(
                'nemo_code_repo', str(p_nemo_bin_dir), str(p_run_dir),
                nemo34, 'xios_code_repo', str(p_xios_bin_dir))
        assert p_run_dir.join('nemo.exe').check(file=True, link=True)
        if nemo34:
            assert p_run_dir.join('server.exe').check(file=True, link=True)
        else:
            assert not p_run_dir.join('server.exe').check(file=True, link=True)

    @pytest.mark.parametrize('nemo34, xios_code_repo', [
        (True, None),
        (False, 'xios_code_repo'),
    ])
    def test_xios_server_exe_symlink(
        self, nemo34, xios_code_repo, tmpdir,
    ):
        p_nemo_bin_dir = tmpdir.ensure_dir(
            'NEMO-code/NEMOGCM/CONFIG/SalishSea/BLD/bin')
        p_nemo_bin_dir.ensure('nemo.exe')
        p_xios_bin_dir = tmpdir.ensure_dir('XIOS/bin')
        if not nemo34:
            p_xios_bin_dir.ensure('xios_server.exe')
        p_run_dir = tmpdir.ensure_dir('run_dir')
        with patch.object(salishsea_cmd.prepare.hg, 'parents'):
            salishsea_cmd.prepare._make_executable_links(
                'nemo_code_repo', str(p_nemo_bin_dir), str(p_run_dir),
                nemo34, xios_code_repo, str(p_xios_bin_dir))
        if nemo34:
            assert not p_run_dir.join('xios_server.exe').check(
                file=True, link=True)
        else:
            assert p_run_dir.join('xios_server.exe').check(
                file=True, link=True)

    @pytest.mark.parametrize('nemo34', [True, False])
    def test_nemo_code_rev_file(self, nemo34, tmpdir):
        p_nemo_bin_dir = tmpdir.ensure_dir(
            'NEMO-code/NEMOGCM/CONFIG/SalishSea/BLD/bin')
        p_nemo_bin_dir.ensure('nemo.exe')
        p_xios_bin_dir = tmpdir.ensure_dir('XIOS/bin')
        p_run_dir = tmpdir.ensure_dir('run_dir')
        with patch.object(salishsea_cmd.prepare.hg, 'parents'):
            salishsea_cmd.prepare._make_executable_links(
                'nemo_code_repo', str(p_nemo_bin_dir), str(p_run_dir),
                nemo34, 'xios_code_repo', str(p_xios_bin_dir))
        assert p_run_dir.join('NEMO-code_rev.txt').check(file=True)

    @pytest.mark.parametrize('nemo34, xios_code_repo', [
        (True, None),
        (False, 'xios_code_repo'),
    ])
    def test_xios_code_rev_file(
        self, nemo34, xios_code_repo, tmpdir,
    ):
        p_nemo_bin_dir = tmpdir.ensure_dir(
            'NEMO-code/NEMOGCM/CONFIG/SalishSea/BLD/bin')
        p_nemo_bin_dir.ensure('nemo.exe')
        p_xios_bin_dir = tmpdir.ensure_dir('XIOS/bin')
        if not nemo34:
            p_xios_bin_dir.ensure('xios_server.exe')
        p_run_dir = tmpdir.ensure_dir('run_dir')
        with patch.object(salishsea_cmd.prepare.hg, 'parents'):
            salishsea_cmd.prepare._make_executable_links(
                'nemo_code_repo', str(p_nemo_bin_dir), str(p_run_dir),
                nemo34, xios_code_repo, str(p_xios_bin_dir))
        if nemo34:
            assert not p_run_dir.join('XIOS-code_rev.txt').check(file=True)
        else:
            assert p_run_dir.join('XIOS-code_rev.txt').check(file=True)


class TestMakeGridLinks:
    @patch.object(salishsea_cmd.prepare, 'log')
    def test_no_forcing_dir(self, m_log):
        run_desc = {
            'paths': {
                'forcing': 'foo',
            },
        }
        salishsea_cmd.prepare._remove_run_dir = Mock()
        p_exists = patch.object(
            salishsea_cmd.prepare.os.path, 'exists', return_value=False)
        p_abspath = patch.object(
            salishsea_cmd.prepare.os.path, 'abspath', side_effect=lambda path: path)
        with pytest.raises(SystemExit), p_exists, p_abspath:
            salishsea_cmd.prepare._make_grid_links(run_desc, 'run_dir')
        m_log.error.assert_called_once_with(
            'foo not found; cannot create symlinks - '
            'please check the forcing path in your run description file')
        salishsea_cmd.prepare._remove_run_dir.assert_called_once_with('run_dir')

    @patch.object(salishsea_cmd.prepare, 'log')
    def test_no_link_path(self, m_log):
        run_desc = {
            'paths': {
                'forcing': 'foo',
            },
            'grid': {
                'coordinates': 'coordinates.nc',
                'bathymetry': 'bathy.nc',
            },
        }
        salishsea_cmd.prepare._remove_run_dir = Mock()
        p_exists = patch.object(
            salishsea_cmd.prepare.os.path, 'exists', side_effect=[True, False])
        p_abspath = patch.object(
            salishsea_cmd.prepare.os.path, 'abspath', side_effect=lambda path: path)
        p_chdir = patch.object(salishsea_cmd.prepare.os, 'chdir')
        with pytest.raises(SystemExit), p_exists, p_abspath, p_chdir:
            salishsea_cmd.prepare._make_grid_links(run_desc, 'run_dir')
        m_log.error.assert_called_once_with(
            'foo/grid/coordinates.nc not found; cannot create symlink - '
            'please check the forcing path and grid file names '
            'in your run description file')
        salishsea_cmd.prepare._remove_run_dir.assert_called_once_with('run_dir')


class TestMakeForcingLinks:
    """Unit tests for `salishsea prepare` _make_forcing_links() function.
    """
    def test_nemo34(self, tmpdir):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        run_desc = {'paths': {'forcing': 'nemo_forcing_dir'}}
        patch_exists = patch.object(
            salishsea_cmd.prepare.os.path, 'exists', return_value=True)
        patch_mfl34 = patch.object(
            salishsea_cmd.prepare, '_make_forcing_links_nemo34')
        patch_hgp = patch.object(salishsea_cmd.prepare.hg, 'parents')
        with patch_exists, patch_hgp, patch_mfl34 as m_mfl34:
            salishsea_cmd.prepare._make_forcing_links(
                run_desc, str(p_run_dir), nemo34=True)
        m_mfl34.assert_called_once_with(run_desc, str(p_run_dir))

    def test_nemo36(self, tmpdir):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        run_desc = {'paths': {'forcing': 'nemo_forcing_dir'}}
        patch_exists = patch.object(
            salishsea_cmd.prepare.os.path, 'exists', return_value=True)
        patch_mfl36 = patch.object(
            salishsea_cmd.prepare, '_make_forcing_links_nemo36')
        patch_hgp = patch.object(salishsea_cmd.prepare.hg, 'parents')
        with patch_exists, patch_hgp, patch_mfl36 as m_mfl36:
            salishsea_cmd.prepare._make_forcing_links(
                run_desc, str(p_run_dir), nemo34=False)
        m_mfl36.assert_called_once_with(run_desc, str(p_run_dir))

    @pytest.mark.parametrize('nemo34', [True, False])
    @patch.object(salishsea_cmd.prepare, 'log')
    def test_make_forcing_links_no_forcing_dir(
        self, m_log, nemo34, tmpdir,
    ):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        run_desc = {
            'paths': {
                'forcing': 'foo',
            },
        }
        salishsea_cmd.prepare._remove_run_dir = Mock()
        p_exists = patch.object(
            salishsea_cmd.prepare.os.path, 'exists', return_value=False)
        p_abspath = patch.object(
            salishsea_cmd.prepare.os.path, 'abspath', side_effect=lambda path: path)
        with pytest.raises(SystemExit), p_exists, p_abspath:
            salishsea_cmd.prepare._make_forcing_links(
                run_desc, str(p_run_dir), nemo34)
        m_log.error.assert_called_once_with(
            'foo not found; cannot create symlinks - '
            'please check the forcing path in your run description file')
        salishsea_cmd.prepare._remove_run_dir.assert_called_once_with(str(p_run_dir))


class TestMakeForcingLinksNEMO34:
    """Unit tests for `salishsea prepare` _make_forcing_links_nemo34() function.
    """
    @pytest.mark.parametrize(
        'link_path, expected',
        [
            ('SalishSea_00475200_restart.nc', 'SalishSea_00475200_restart.nc'),
            ('initial_strat/', 'foo/initial_strat/'),
        ],
    )
    @patch.object(salishsea_cmd.prepare, '_check_atmos_files')
    @patch.object(salishsea_cmd.prepare, 'log')
    def test_make_forcing_links_no_restart_path(
        self, m_log, m_caf, link_path, expected,
    ):
        run_desc = {
            'paths': {
                'forcing': 'foo',
            },
            'forcing': {
                'atmospheric': 'bar',
                'initial conditions': link_path,
                'open boundaries': 'open_boundaries/',
                'rivers': 'rivers/',
            },
        }
        salishsea_cmd.prepare._remove_run_dir = Mock()
        p_exists = patch.object(
            salishsea_cmd.prepare.os.path, 'exists', return_value=False)
        p_abspath = patch.object(
            salishsea_cmd.prepare.os.path, 'abspath', side_effect=lambda path: path)
        p_chdir = patch.object(salishsea_cmd.prepare.os, 'chdir')
        with pytest.raises(SystemExit), p_exists, p_abspath, p_chdir:
            salishsea_cmd.prepare._make_forcing_links_nemo34(run_desc, 'run_dir')
        m_log.error.assert_called_once_with(
            '{} not found; cannot create symlink - '
            'please check the forcing path and initial conditions file names '
            'in your run description file'.format(expected))
        salishsea_cmd.prepare._remove_run_dir.assert_called_once_with('run_dir')

    @patch.object(salishsea_cmd.prepare, '_check_atmos_files')
    @patch.object(salishsea_cmd.prepare, 'log')
    def test_make_forcing_links_no_forcing_path(
        self, m_log, m_caf,
    ):
        run_desc = {
            'paths': {
                'forcing': 'foo',
            },
            'forcing': {
                'atmospheric': 'bar',
                'initial conditions': 'initial_strat/',
                'open boundaries': 'open_boundaries/',
                'rivers': 'rivers/',
            },
        }
        salishsea_cmd.prepare._remove_run_dir = Mock()
        p_exists = patch.object(
            salishsea_cmd.prepare.os.path, 'exists', side_effect=[True, False])
        p_abspath = patch.object(
            salishsea_cmd.prepare.os.path, 'abspath', side_effect=lambda path: path)
        p_chdir = patch.object(salishsea_cmd.prepare.os, 'chdir')
        p_symlink = patch.object(salishsea_cmd.prepare.os, 'symlink')
        with pytest.raises(SystemExit), p_exists, p_abspath, p_chdir:
            with p_symlink:
                salishsea_cmd.prepare._make_forcing_links_nemo34(
                    run_desc, 'run_dir')
        m_log.error.assert_called_once_with(
            'foo/bar not found; cannot create symlink - '
            'please check the forcing paths and file names '
            'in your run description file')
        salishsea_cmd.prepare._remove_run_dir.assert_called_once_with('run_dir')


class TestMakeForcingLinksNEMO36:
    """Unit tests for `salishsea prepare` _make_forcing_links_nemo36() function.
    """
    def test_abs_path_link(self, tmpdir):
        p_nemo_forcing = tmpdir.ensure_dir('NEMO-forcing')
        p_atmos_ops = tmpdir.ensure_dir(
            'results/forcing/atmospheric/GEM2.5/operational')
        run_desc = {
            'paths': {
                'forcing': str(p_nemo_forcing),
            },
            'forcing': {
                'NEMO-atmos': {
                    'link to': str(p_atmos_ops),
                }}}
        patch_symlink = patch.object(salishsea_cmd.prepare.os, 'symlink')
        with patch_symlink as m_symlink:
            salishsea_cmd.prepare._make_forcing_links_nemo36(run_desc, 'run_dir')
        m_symlink.assert_called_once_with(p_atmos_ops, 'run_dir/NEMO-atmos')

    def test_rel_path_link(self, tmpdir):
        p_nemo_forcing = tmpdir.ensure_dir('NEMO-forcing')
        p_nemo_forcing.ensure_dir('rivers')
        run_desc = {
            'paths': {
                'forcing': str(p_nemo_forcing),
            },
            'forcing': {
                'rivers': {
                    'link to': 'rivers',
                }}}
        patch_symlink = patch.object(salishsea_cmd.prepare.os, 'symlink')
        with patch_symlink as m_symlink:
            salishsea_cmd.prepare._make_forcing_links_nemo36(run_desc, 'run_dir')
        m_symlink.assert_called_once_with(
            p_nemo_forcing.join('rivers'), 'run_dir/rivers')

    @patch.object(salishsea_cmd.prepare, 'log')
    def test_no_link_path(self, m_log, tmpdir):
        p_nemo_forcing = tmpdir.ensure_dir('NEMO-forcing')
        run_desc = {
            'paths': {
                'forcing': str(p_nemo_forcing),
            },
            'forcing': {
                'rivers': {
                    'link to': 'rivers',
                }}}
        salishsea_cmd.prepare._remove_run_dir = Mock()
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_forcing_links_nemo36(run_desc, 'run_dir')
        m_log.error.assert_called_once_with(
            '{} not found; cannot create symlink - '
            'please check the forcing paths and file names '
            'in your run description file'
            .format(p_nemo_forcing.join('rivers')))
        salishsea_cmd.prepare._remove_run_dir.assert_called_once_with('run_dir')
