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

import pytest


@pytest.fixture()
def viz_tools_module():
    from salishsea_tools import viz_tools
    return viz_tools


def test_set_aspect_defaults(viz_tools_module):
    axes = Mock()
    viz_tools_module.set_aspect(axes)
    axes.set_aspect.assert_called_once_with(5/4.4, adjustable='box-forced')


def test_set_aspect_args(viz_tools_module):
    axes = Mock()
    viz_tools_module.set_aspect(axes, 3/2, 'foo')
    axes.set_aspect.assert_called_once_with(3/2, adjustable='foo')
