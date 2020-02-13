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
import netCDF4 as nc
import f90nml
import os

def load_nml_bio(resDir,nmlname,bioRefName='namelist_smelt_ref',bioCfgName='namelist_smelt_cfg',namRefDir=None):
    """ extract parameter values from smelt namelists for nampisbio
    :arg str resDir: directory containing namelists associated with run; usually results diri
    :arg str nmlname name of namelist to load: eg, 'nampisprod'
    :arg str bioRefName: name of bio reference namelist (optional)
    :arg str bioCfgName: name of bio config namelist (optional)
    :arg str namRefDir: dir to get ref namelist from if not in results dir (optional)
    """
    if namRefDir==None:
        namRefDir=resDir
    nmlRef=f90nml.read(os.path.join(namRefDir,bioRefName))
    nmlCfg=f90nml.read(os.path.join(resDir,bioCfgName))
    nml=nmlRef[nmlname]
    for key in nmlCfg[nmlname]:
        nml[key]=nmlCfg[nmlname][key]
    return nml

def each_limiter(zz_I_par,zz_NO,zz_NH,zz_Si,tmask,
                 zz_rate_Iopt,zz_rate_gamma,zz_rate_K_Si,zz_rate_kapa,zz_rate_k):
    # Light
    zz_plank_growth_light = (1.0 - np.exp(-zz_I_par / (0.33 * zz_rate_Iopt)) ) * \
                           (np.exp(-zz_I_par / (30. * zz_rate_Iopt))) * 1.06
    zz_Uc = (1.0 - zz_rate_gamma) * zz_plank_growth_light
    ILim=zz_Uc
    # Si
    zz_Sc = np.where(np.logical_and(zz_Si>0.0,tmask>0),
                    zz_Si / (zz_rate_K_Si + zz_Si),0.0)
    SiLim=zz_Sc
    # Nitrate and Ammonium
    zz_Oup_cell = np.where(np.logical_and(zz_NO > 0.0,tmask>0), 
                zz_NO * zz_rate_kapa / (zz_rate_k + zz_NO * zz_rate_kapa + zz_NH),0.0)
    zz_Hup_cell = np.where(np.logical_and(zz_NH > 0.0,tmask>0), 
                zz_NH / (zz_rate_k + zz_NO * zz_rate_kapa + zz_NH),0.0)
    if (np.any(zz_Oup_cell < 0.)):
        raise ValueError('zz_Oup_cell<0')
    if (np.any(zz_Hup_cell < 0.)):
        raise ValueError('zz_Hup_cell<0')
    NLim=zz_Oup_cell+zz_Hup_cell
    # set flags
    limiter=-1*np.ones(zz_Si.shape)
    limiter=np.where(np.logical_and(ILim<=NLim,ILim<=SiLim),0,
                     np.where(NLim<=SiLim,2,np.where(SiLim<NLim,4,limiter)))
    limval=np.where(np.logical_and(ILim<=NLim,ILim<=SiLim),ILim,
                     np.where(NLim<=SiLim,NLim+2,np.where(SiLim<NLim,SiLim+4,limiter)))

    return ILim, NLim, SiLim, limiter,limval

def calc_nutLim_2(zz_NO,zz_NH,zz_Si,zz_rate_K_Si,zz_rate_kapa,zz_rate_k):
    # calculate nutrient (si, no3, or nh4) limitation only for calculating 
    # diatom sinking rates
    # Si
    zz_Sc = np.where(zz_Si>0.0,
                    zz_Si / (zz_rate_K_Si + zz_Si),0.0)
    SiLim=zz_Sc
    # Nitrate and Ammonium
    zz_Oup_cell = np.where(zz_NO > 0.0, 
                zz_NO * zz_rate_kapa / (zz_rate_k + zz_NO * zz_rate_kapa + zz_NH),0.0)
    zz_Hup_cell = np.where(zz_NH > 0.0, 
                zz_NH / (zz_rate_k + zz_NO * zz_rate_kapa + zz_NH),0.0)
    if (np.any(zz_Oup_cell < 0.)):
        raise ValueError('zz_Oup_cell<0')
    if (np.any(zz_Hup_cell < 0.)):
        raise ValueError('zz_Hup_cell<0')
    NLim=zz_Oup_cell+zz_Hup_cell
    nutLim=np.minimum(NLim,SiLim)
    return np.power(nutLim,0.2)

def calc_diat_sink(zz_w_sink_Pmicro_min,zz_w_sink_Pmicro_max,diatNutLim):
    # enter min and max rates in m/day as in namelist
    # use calc_nutLim_2 to estimate diatNutLim, which is to power 0.2
    wsink= zz_w_sink_Pmicro_min*diatNutLim+zz_w_sink_Pmicro_max*(1.0-diatNutLim)
    return wsink/(24*3600) # diatom sinking rates are converted to m/s during namelist read

def calc_p_limiters(I,NO,NH,Si,tmask,nampisprod):
    """ calculates limiting factor: I, Si, or N based on SMELT output
    arg I: np.array slice of PAR from dia file
    arg NO: " nitrate
    arg NH: " ammonia
    arg Si: " silicate
    arg tmask: np.array containing appropriate tmask sliced to same size
    arg nampisprod: namelist dict loaded using load_nml_bio with 
        argument nampisprod 
    """
    ILimDiat, NLimDiat, SiLimDiat, limiterDiat, limvalDiat=each_limiter(I,NO,NH,Si,tmask,nampisprod['zz_rate_Iopt_diat'],
                                        nampisprod['zz_rate_gamma_diat'],nampisprod['zz_rate_k_Si_diat'],
                                        nampisprod['zz_rate_kapa_diat'],nampisprod['zz_rate_k_diat'])
    
    ILimMyri, NLimMyri, SiLimMyri, limiterMyri, limvalMyri=each_limiter(I,NO,NH,Si,tmask,nampisprod['zz_rate_Iopt_myri'],
                                        nampisprod['zz_rate_gamma_myri'],nampisprod['zz_rate_k_Si_myri'],
                                        nampisprod['zz_rate_kapa_myri'],nampisprod['zz_rate_k_myri'])
    
    ILimNano, NLimNano, SiLimNano, limiterNano, limvalNano=each_limiter(I,NO,NH,Si,tmask,nampisprod['zz_rate_Iopt_nano'],
                                        nampisprod['zz_rate_gamma_nano'],nampisprod['zz_rate_k_Si_nano'],
                                        nampisprod['zz_rate_kapa_nano'],nampisprod['zz_rate_k_nano'])
    Diat={'ILim':ILimDiat,'NLim':NLimDiat,'SiLim':SiLimDiat,'limiter':limiterDiat,'limval':limvalDiat}
    Myri={'ILim':ILimMyri,'NLim':NLimMyri,'SiLim':SiLimMyri,'limiter':limiterMyri,'limval':limvalMyri}
    Nano={'ILim':ILimNano,'NLim':NLimNano,'SiLim':SiLimNano,'limiter':limiterNano,'limval':limvalNano}
    return Diat, Myri, Nano

#def calc_limiter(resDir,fnameDia=None,fnamePtrc=None):
#    :arg str resDir: path to results directory where output and namelist files are stored
#    :arg str fnameDia: (optional) diagnostic file to get output from; 
#        if none suplied assumes there is only one possibility in resDir
#    :arg str fnamePtrc: (optional) ptrc file to get output from; 
#        if None assumes only 1 possible
#    """
#    
#    fDia=nc.Dataset(os.path.join(resDir,fnameDia))
#    fPtrc=nc.Dataset(os.path.join(resDir,fname
#

#def find_closest_model_point(
#    lon, lat, model_lons, model_lats, grid='NEMO', land_mask=None,
#    tols={
#        'NEMO': {'tol_lon': 0.0104, 'tol_lat': 0.00388},
#        'GEM2.5': {'tol_lon': 0.016, 'tol_lat': 0.012},
#        }
#):
#    """Returns the grid coordinates of the closest model point
#    to a specified lon/lat. If land_mask is provided, returns the closest
#    water point.
#
#    Example:
#
#    .. code-block:: python
#
#        j, i = find_closest_model_point(
#                   -125.5,49.2,model_lons,model_lats,land_mask=bathy.mask)
#
#    where bathy, model_lons and model_lats are returned from
#    :py:func:`salishsea_tools.tidetools.get_bathy_data`.
#
#    j is the y-index(latitude), i is the x-index(longitude)
#
#    :arg float lon: longitude to find closest grid point to
#
#    :arg float lat: latitude to find closest grid point to
#
#    :arg model_lons: specified model longitude grid
#    :type model_lons: :py:obj:`numpy.ndarray`
#
#    :arg model_lats: specified model latitude grid
#    :type model_lats: :py:obj:`numpy.ndarray`
#
#    :arg grid: specify which default lon/lat tolerances
#    :type grid: string
#
#    :arg land_mask: describes which grid coordinates are land
#    :type land_mask: numpy array
#
#    :arg tols: stored default tols for different grid types
#    :type tols: dict
#
#    :returns: yind, xind
#    """

