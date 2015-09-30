"""Unit tests for bathy_tools.
"""
from __future__ import division
"""
Copyright 2013-2015 The Salish Sea MEOPAR contributors
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
import numpy as np
import pytest

from salishsea_tools.nowcast import analyze


@pytest.fixture
def linear_depths():
    return np.arange(0, 40)


class TestDepthAverage:
    """Unit tests for depth_average() function.
    """

    # A couple of examples of translating notebook cells into unit test
    # methods
    def test_1d_zeros_array_n_1(self, linear_depths):
        """Cell 4 case
        """
        var = np.zeros((linear_depths.shape[0], 1))
        result = analyze.depth_average(var, linear_depths, depth_axis=0)
        assert result == np.zeros((1,))
        assert result.shape == (1,)

    def test_1d_zeros_array_n(self, linear_depths):
        """Cell 5 case
        """
        var = np.zeros((linear_depths.shape[0]))
        result = analyze.depth_average(var, linear_depths, depth_axis=0)
        assert result == 0


    # Parametrizing a single test method with a collection of inputs
    # and expected results.
    # It's a judgement call to decide whether this is more readable
    # than 6 separate test methods
    @pytest.mark.parametrize('var, depth_axis, expected', [
        # Cell 4 case
        (np.zeros((linear_depths().shape[0], 1)), 0, np.zeros((1,))),
        # Cell 5 case
        (np.zeros((linear_depths().shape[0])), 0, 0),
        # Cell 6 case
        (np.ones((linear_depths().shape[0], 1)), 0, 1),
        # Cell 7 case
        (np.ones((10, linear_depths().shape[0])), 1, np.ones((10,))),
        # Cell 8 case
        (np.ones((10, linear_depths().shape[0], 11)), 1, np.ones((10, 11))),
        # Cell 9 case
        (np.ones((1, linear_depths().shape[0], 2, 3)), 1, np.ones((1, 2, 3))),
    ])
    # Parametrization args go between self and fixture
    def test_1d_array(self, var, depth_axis, expected, linear_depths):
        result = analyze.depth_average(
            var, linear_depths, depth_axis=depth_axis)
        np.testing.assert_array_equal(result, expected)
