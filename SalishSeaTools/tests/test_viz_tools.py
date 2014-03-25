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

"""Unit tests for the viz_tools module.
"""
from __future__ import division

from mock import Mock

import numpy as np
import pytest


@pytest.fixture()
def viz_tools_module():
    from salishsea_tools import viz_tools
    return viz_tools


def test_set_aspect_defaults(viz_tools_module):
    axes = Mock()
    aspect = viz_tools_module.set_aspect(axes)
    axes.set_aspect.assert_called_once_with(5/4.4, adjustable='box-forced')
    assert aspect == 5/4.4


def test_set_aspect_args(viz_tools_module):
    axes = Mock()
    aspect = viz_tools_module.set_aspect(axes, 3/2, adjustable='foo')
    axes.set_aspect.assert_called_once_with(3/2, adjustable='foo')
    assert aspect == 3/2


def test_set_aspect_map_lats(viz_tools_module):
    axes = Mock()
    lats = np.array([42.0])
    lats_aspect = 1 / np.cos(42 * np.pi / 180)
    aspect = viz_tools_module.set_aspect(axes, coords='map', lats=lats)
    axes.set_aspect.assert_called_once_with(
        lats_aspect, adjustable='box-forced')
    assert aspect == lats_aspect


def test_set_aspect_map_explicit(viz_tools_module):
    axes = Mock()
    aspect = viz_tools_module.set_aspect(axes, 2/3, coords='map')
    axes.set_aspect.assert_called_once_with(2/3, adjustable='box-forced')
    assert aspect == 2/3
