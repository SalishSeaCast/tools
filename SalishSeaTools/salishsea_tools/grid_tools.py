# Copyright 2013-2016 The Salish Sea MEOPAR contributors
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

""" Functions for calculating time-dependent scale factors and depth in NEMO.
 NKS nsoontie@eos.ubc.ca 08-2016
"""

import numpy as np


def calculate_mu(e3t0, tmask):
    """Calculate the mu correction factor for variable volume in NEMO.
    e3t0 and tmask must be the same shape.
    See NEMO vvl manual appendix A.1 for details.

    :arg e3t0: initial vertical scale factors on T-grid.
               Dimensions: (depth, y, x).
    :type e3t0: numpy array

    :arg tmask: T-grid mask. Dimensions: (depth, y, x)
    :type tmask: numpy array

    :returns: the mu correction factor with dimensions (depth, y, x)

    """
    # Iterate over k to find v and inner sum
    vn = 0
    sum_matrix = np.zeros(e3t0.shape)
    for k in np.arange(e3t0.shape[0]):
        inner_sum = 0
        for n in np.arange(k, e3t0.shape[0]):
            inner_sum = inner_sum + e3t0[n, ...]*tmask[n, ...]
        sum_matrix[k, ...] = inner_sum
        vn = vn + e3t0[k, ...]*inner_sum*tmask[k, ...]

    mu = sum_matrix/vn
    mu = np.nan_to_num(mu)  # turn nans to zeros
    return mu


def calculate_adjustment_factor(mu, ssh):
    """Calculate the time=dependent adjustment factor for variable volume in
    NEMO. adj = (1+ssh*mu) and e3t_t = e3t_0*adj
    See NEMO vvl manual appendix A.1 for details.

    :arg mu: mu correction factor. Dimension: (depth, y, x)
    :type mu: numpy array

    :arg ssh: the model sea surface height. Dimensions: (time, y, x)
    :type ssh: numpy array

    :returns: the adjustment factor with dimensions (time, depth, y, x)
    """
    ssh = np.expand_dims(ssh, axis=1)   # Give ssh a depth dimension
    adj = (1 + ssh*mu)

    return adj


def calculate_vertical_grids(
    e3t0,
    tmask,
    ssh,
    return_vars=['e3t_t', 'e3w_t', 'gdept_t', 'gdepw_t']
):
    """ Calculate the time dependent vertical grids and scale factors for
    variable volume in NEMO. See NEMO vvl manual appendix A.1 for details.

    :arg e3t0: initial vertical scale factors on T-grid.
               Dimensions: (depth, y, x).
    :type e3t0: numpy array

    :arg tmask: T-grid mask. Dimensions: (depth, y, x)
    :type tmask: numpy array

    :arg ssh: the model sea surface height. Dimensions: (time, depth, y, x)
    :type ssh: numpy array

    :arg return_vars: List of scale factors and depth variables to return.
                      Options are gdept_t, gdepw_t, e3t_t, e3w_t. Default is
                      all of these.
    :type return_vars: list of strings

    :returns: A dictionary containing the desired time dependent vertical
              scale factors on t and w grids and depths on t and w grids.
              Dimensions of each: (time, depth, y, x)
    """
    # adjustment factors
    mu = calculate_mu(e3t0, tmask)
    adj = calculate_adjustment_factor(mu, ssh)
    # scale factors
    e3t_t = e3t0*adj
    # intiliaize for k=0
    e3w_t = np.copy(e3t_t)
    # overwrite k>0
    e3w_t[:, 1:, ...] = 0.5*(e3t_t[:, 1:, ...] + e3t_t[:, 0:-1, ...])
    # depths
    # initialize for k=0
    gdept_t = 0.5*e3t_t
    gdepw_t = np.zeros(gdept_t.shape)
    # overwrite k>0
    for k in np.arange(1, gdept_t.shape[1]):
        gdept_t[:, k, ...] = gdept_t[:, k-1, ...] + e3w_t[:, k, ...]
        gdepw_t[:, k, ...] = gdepw_t[:, k-1, ...] + e3t_t[:, k-1, ...]
    # Create dictionary to return
    all_vars = {'e3t_t': e3t_t,
                'e3w_t': e3w_t,
                'gdept_t': gdept_t,
                'gdepw_t': gdepw_t
                }
    for var in list(all_vars.keys()):
        if var not in return_vars:
            del all_vars[var]

    return all_vars
