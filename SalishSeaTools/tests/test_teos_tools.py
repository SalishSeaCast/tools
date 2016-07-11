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

"""Unit tests for the teos_tools module.
"""
from __future__ import division

import numpy as np
import pytest

from salishsea_tools import teos_tools


def test_PSU_TEOS_constant_value():
    expected = 35.16504 / 35
    np.testing.assert_allclose(teos_tools.PSU_TEOS, expected)


def test_TEOS_PSU_constant_value():
    expected = 35 / 35.16504
    np.testing.assert_allclose(teos_tools.TEOS_PSU, expected)


@pytest.mark.parametrize('psu, expected', [
    (0, 0),
    (35, 35.16504),
    (30, 30.14146),
    (70, 70.33008),
])
def test_psu_teos(psu, expected):
    np.testing.assert_allclose(teos_tools.psu_teos(psu), expected)


@pytest.mark.parametrize('psu, expected', [
    (np.array([0, 30, 35, 70]), np.array([0, 30.14146, 35.16504, 70.33008])),
    ([0, 30, 35, 70], np.array([0, 30.14146, 35.16504, 70.33008])),
    ((0, 30, 35, 70), np.array([0, 30.14146, 35.16504, 70.33008])),
])
def test_psu_teos_polymorphic_sequence(psu, expected):
    teos = teos_tools.psu_teos(psu)
    np.testing.assert_allclose(teos, expected)


@pytest.mark.parametrize('teos, expected', [
    (0, 0),
    (35.16504, 35),
    (30.14146, 30),
    (70.33008, 70),
])
def test_teos_psu(teos, expected):
    np.testing.assert_allclose(teos_tools.teos_psu(teos), expected)

@pytest.mark.parametrize('teos, expected', [
    (np.array([0, 30.14146, 35.16504, 70.33008]), np.array([0, 30, 35, 70])),
    ([0, 30.14146, 35.16504, 70.33008], np.array([0, 30, 35, 70])),
    ((0, 30.14146, 35.16504, 70.33008), np.array([0, 30, 35, 70])),
])
def test_teos_psu_polymorphic_sequence(teos, expected):
    psu = teos_tools.teos_psu(teos)
    np.testing.assert_allclose(psu, expected)
