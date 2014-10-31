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

"""Unit tests for the nowcast.run_NEMO module.
"""
from __future__ import division

from datetime import (
    date,
    timedelta,
)
import os

import pytest


@pytest.fixture()
def run_NEMO_module():
    from salishsea_tools.nowcast import run_NEMO
    return run_NEMO


def test_get_namelist_value(run_NEMO_module):
    lines = ['  nn_it000 = 8641  ! first time step\n']
    line_index, value = run_NEMO_module.get_namelist_value('nn_it000', lines)
    assert line_index == 0
    assert value == str(8641)


def test_get_namelist_value_last_occurrence(run_NEMO_module):
    lines = [
        '  nn_it000 = 8641  ! first time step\n',
        '  nn_it000 = 8642  ! first time step\n',
    ]
    line_index, value = run_NEMO_module.get_namelist_value('nn_it000', lines)
    assert line_index == 1
    assert value == str(8642)


def test_run_description_init_conditions(run_NEMO_module):
    today = date(2014, 10, 28)
    run_desc = run_NEMO_module.run_description('foo', today, 42)
    expected = os.path.join(
        'SalishSea/nowcast/',
        (today - timedelta(days=1)).strftime('%d%b%y').lower(),
        'SalishSea_00000042_restart.nc',
    )
    assert run_desc['forcing']['initial conditions'].endswith(expected)
