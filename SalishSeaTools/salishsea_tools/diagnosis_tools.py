# Copyright 2013-2017 The Salish Sea MEOPAR contributors
# and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
"""

import numpy as np
import numpy.ma as ma
import netCDF4 as nc
from salishsea_tools import nc_tools


__all__ = [
    'pcourantu', 'pcourantv','pcourantw'
]

def pcourantu(files,meshmask):
    """Given a list of U filenames and a mesh mask, returns an array with the unscaled Courant numbers.

    :arg files: list of U filenames

    :arg meshmask: mesh mask
    :type meshmask: :py:class:`netCDF4.Dataset`

    :returns: Numpy MaskedArray with unscaled Courant numbers.
    :rtype: :py:class: `numpy.ma.core.MaskedArray`
    """

    delta_x = meshmask['e1u'][:]
    with nc_tools.scDataset(files) as f:             #merging files
        nt,nz,ny,nx = f.variables['vozocrtx'].shape
        umax = np.zeros((nz,ny,nx))
        for n in range(nt):
            utmp = np.abs(f.variables['vozocrtx'][n,:,:,:])
            umax = np.maximum(utmp,umax)             #taking maximum over time
        ubdxmax = np.zeros((ny,nx))
        for m in range(nz):
            ubdxtmp = umax[m,...] / delta_x[0,...]
            ubdxmax = np.maximum(ubdxtmp,ubdxmax)    #taking maximum over depth

    umask = meshmask['umask'][0,0,...]
    return ma.masked_array(ubdxmax, mask = 1-umask)

def pcourantv(files,meshmask):
    """Given a list of V filenames and a mesh mask, returns an array with the unscaled Courant numbers.

    :arg files: list of V filenames

    :arg meshmask: mesh mask
    :type meshmask: :py:class:`netCDF4.Dataset`

    :returns: Numpy MaskedArray with unscaled Courant numbers.
    :rtype: :py:class: `numpy.ma.core.MaskedArray`
    """

    delta_y = meshmask['e2v'][:]
    with nc_tools.scDataset(files) as f:             #merging files
        nt,nz,ny,nx = f.variables['vomecrty'].shape
        vmax = np.zeros((nz,ny,nx))
        for n in range(nt):
            vtmp = np.abs(f.variables['vomecrty'][n,:,:,:])
            vmax = np.maximum(vtmp,vmax)             #taking maximum over time
        vbdymax = np.zeros((ny,nx))
        for m in range(nz):
            vbdytmp = vmax[m,...] / delta_y[0,...]
            vbdymax = np.maximum(vbdytmp,vbdymax)    #taking maximum over depth

    vmask = meshmask['vmask'][0,0,...]
    return ma.masked_array(vbdymax, mask = 1-vmask)

def pcourantw(files,meshmask):
    """Given a list of W filenames and a mesh mask, returns an array with the unscaled Courant numbers.

    :arg files: list of W filenames

    :arg meshmask: mesh mask
    :type meshmask: :py:class:`netCDF4.Dataset`

    :returns: Numpy MaskedArray with unscaled Courant numbers.
    :rtype: :py:class: `numpy.ma.core.MaskedArray`
    """

    with nc_tools.scDataset(files) as f:             #merging files
        nt,nz,ny,nx = f.variables['vovecrtz'].shape
        delta_z = meshmask['e3w_1d'][0,...]
        delta_z = delta_z[:,np.newaxis,np.newaxis]

        wmax = np.zeros((nz,ny,nx))
        for n in range(nt):
            wtmp = np.abs(f.variables['vovecrtz'][n,:,:,:])
            wmax = np.maximum(wtmp,wmax)             #taking maximum over time
        wbdz = wmax / delta_z

        wbdzmax = np.zeros((ny,nx))
        for m in range(nz):
            wbdztmp = wbdz[m,...]
            wbdzmax = np.maximum(wbdztmp,wbdzmax)    #taking maximum over depth

    tmask = meshmask['tmask'][0,0,...]
    return ma.masked_array(wbdzmax, mask = 1-tmask)
