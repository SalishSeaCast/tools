"""Unit tests for hg_commands module.
"""
"""
Copyright 2013-2014 The Salish Sea MEOPAR contributors
and The University of British Columbia

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import subprocess
from mock import patch
from salishsea_tools import hg_commands as hg


@patch('salishsea_tools.hg_commands.subprocess.check_output')
def test_default_url(mock_chk_out):
    """default_url returns expected result
    """
    mock_chk_out.return_value = 'foo'
    url = hg.default_url()
    assert url == 'foo'


@patch('salishsea_tools.hg_commands.subprocess.check_output')
def test_default_url_with_repo(mock_chk_out):
    """default_url uses expected command when repo arg is provided
    """
    mock_chk_out.return_value = 'foo'
    hg.default_url('bar')
    mock_chk_out.assert_called_once_with('hg -R bar paths default'.split())


@patch('salishsea_tools.hg_commands.subprocess.check_output')
def test_default_url_no_repo(mock_chk_out):
    """default_url returns None when called on non-top level hg repo dir
    """
    mock_chk_out.side_effect = subprocess.CalledProcessError(1, 'cmd')
    url = hg.default_url('bar/baz')
    assert url is None


@patch('salishsea_tools.hg_commands.subprocess.check_output')
def test_heads_tip_rev(mock_chk_out):
    """heads uses expected command with default revs list
    """
    hg.heads('foo')
    mock_chk_out.assert_called_once_with('hg -R foo heads .'.split())


@patch('salishsea_tools.hg_commands.subprocess.check_output')
def test_heads_multiple_revs(mock_chk_out):
    """heads uses expected command with multiple revs
    """
    hg.heads('foo', revs=['bar', 'baz'])
    mock_chk_out.assert_called_once_with('hg -R foo heads bar baz'.split())
