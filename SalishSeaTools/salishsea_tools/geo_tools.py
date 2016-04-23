# Copyright 2013-2016 The Salish Sea NEMO Project and
# The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Functions for working with geographical data and model results.
"""
import numpy as np

from salishsea_tools import tidetools


def distance_along_curve(lons, lats):
    """Calculate cumulative distance in km between points in lons, lats

    :arg lons: 1D array of longitude points.
    :type lons: :py:class:`numpy.ndarray`

    :arg lats: 1D array of latitude points.
    :type lats: :py:class:`numpy.ndarray`

    :returns: Cummulative point-by-point distance along track in km.
    :rtype: :py:class:`numpy.ndarray`
    """
    dist = [0]
    for i in np.arange(1, lons.shape[0]):
        newdist = dist[i-1] + tidetools.haversine(lons[i], lats[i],
                                                  lons[i-1], lats[i-1])
        dist.append(newdist)
    dist = np.array(dist)
    return dist
