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
    with nc_tools.scDataset(files) as f: #merging files
        nt,nz,ny,nx = f.variables['vozocrtx'].shape
        ubdx = np.zeros((nz,ny,nx))
        for n in range(nt):
            u = np.abs(f.variables['vozocrtx'][n,:,:,:] / delta_x)
            ubdx = np.maximum(u,ubdx)    #taking maximum over time
        new_u = np.zeros((ny,nx))
        for m in range(nz):
            u = ubdx[m,:,:]
            new_u = np.maximum(u,new_u)  #taking maximum over depth

    umask = meshmask['umask'][0,0,...]
    return ma.masked_array(new_u, mask = 1-umask)

def pcourantv(files,meshmask):
    """Given a list of V filenames and a mesh mask, returns an array with the unscaled Courant numbers.

    :arg files: list of V filenames

    :arg meshmask: mesh mask 
    :type meshmask: :py:class:`netCDF4.Dataset`

    :returns: Numpy MaskedArray with unscaled Courant numbers.
    :rtype: :py:class: `numpy.ma.core.MaskedArray`
    """

    delta_y = meshmask['e2v'][:]
    with nc_tools.scDataset(files) as f: #merging files
        nt,nz,ny,nx = f.variables['vomecrty'].shape
        vbdx = np.zeros((nz,ny,nx))
        for n in range(nt):
            v = np.abs(f.variables['vomecrty'][n,:,:,:] / delta_y)
            vbdx = np.maximum(v,vbdx)    #taking maximum over time
        new_v = np.zeros((ny,nx))
        for m in range(nz):
            v = vbdx[m,:,:]
            new_v = np.maximum(v,new_v)  #taking maximum over deptht

    vmask = meshmask['vmask'][0,0,...]
    return ma.masked_array(new_v, mask = 1-vmask)

def pcourantw(files,meshmask):
    """Given a list of W filenames and a mesh mask, returns an array with the unscaled Courant numbers.

    :arg files: list of W filenames

    :arg meshmask: mesh mask 
    :type meshmask: :py:class:`netCDF4.Dataset`

    :returns: Numpy MaskedArray with unscaled Courant numbers.
    :rtype: :py:class: `numpy.ma.core.MaskedArray`
    """

    with nc_tools.scDataset(files) as f: #merging files
        nt,nz,ny,nx = f.variables['vovecrtz'].shape
        wbdx = np.zeros((nz,ny,nx))
        delta_z = meshmask['e3w_1d'][0,...]
        delta_z = delta_z[:,np.newaxis,np.newaxis]

        for n in range(nt):
            w = np.abs(f.variables['vovecrtz'][n,:,:,:] / delta_z)
            wbdx = np.maximum(w,wbdx)    #taking maximum over time
        new_w = np.zeros((ny,nx))
        for m in range(nz):
            w = wbdx[m,:,:]
            new_w = np.maximum(w,new_w)  #taking maximum over deptht

    tmask = meshmask['tmask'][0,0,...]
    return ma.masked_array(new_w, mask = 1-tmask)