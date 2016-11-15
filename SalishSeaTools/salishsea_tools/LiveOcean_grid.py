# Tools for getting grid information from Live Ocean results
# Adapted from Parker MacCready's code

# Nancy Soontiens 2016

import netCDF4 as nc
import numpy as np


def get_basic_info(fn, getG=True, getS=True, getT=True):
    """
    Gets grid, vertical coordinate, and time info from a ROMS NetCDF
    history file with full name 'fn'

    Input: the filename (with path if needed)

    Output: dicts G, S, and T

    Example calls:

    for more than one the dout list is unpacked automatically
    G, S, T = zfun.get_basic_info(fn)

    for getting just one use [] to just get the dict
    [T] = zfun.get_basic_info(fn, getG=False, getS=False)

    """

    ds = nc.Dataset(fn, 'r')

    dout = []  # initialize an output list

    if getG:
        # get grid and bathymetry info
        g_varlist = ['h', 'lon_rho', 'lat_rho', 'lon_u', 'lat_u', 'lon_v',
                     'lat_v', 'mask_rho', 'mask_u', 'mask_v', 'pm', 'pn', ]
        G = dict()
        for vv in g_varlist:
            G[vv] = ds.variables[vv][:]
        G['DX'] = 1/G['pm']
        G['DY'] = 1/G['pn']
        G['M'], G['L'] = np.shape(G['lon_rho'])  # M = rows, L = columns
        # make the masks boolean
        G['mask_rho'] = G['mask_rho'] == 1
        G['mask_u'] = G['mask_u'] == 1
        G['mask_v'] = G['mask_v'] == 1
        dout.append(G)

    if getS:
        # get vertical sigma-coordinate info (vectors are bottom to top)
        s_varlist = ['s_rho', 'hc', 'Cs_r', 'Vtransform']
        S = dict()
        for vv in s_varlist:
            S[vv] = ds.variables[vv][:]
        S['N'] = len(S['s_rho'])  # number of vertical levels
        dout.append(S)

    if getT:
        # get time info
        t_varlist = ['ocean_time']
        T = dict()
        for vv in t_varlist:
            T[vv] = ds.variables[vv][:]
        T_units = ds.variables['ocean_time'].units
        tt = nc.num2date(T['ocean_time'][:], T_units)
        T['time'] = tt
        dout.append(T)

    return dout


def get_z(h, zeta, S):
    """
    Used to calculate the z position of fields in a ROMS history file. Only for
    rho levels

    Input: arrays h (bathymetry depth) and zeta (sea surface height)
    which must be the same size, and dict S created by get_basic_info()

    Output: 3-D arrays of z_rho

    NOTE: one foible is that if you input arrays of h and zeta that are
    vectors of length VL, the output array (e.g. z_rho) will have size (N, VL)
    (i.e. it will never return an array with size (N, VL, 1), even if (VL, 1)
    was the input shape).  This is a result of the initial and final squeeze
    calls.
    """

    # input error checking (seems clumsy)
    if (
        (type(h) != np.ndarray)
        or (type(zeta) not in [np.ndarray, np.ma.core.MaskedArray])
        or (type(S) != dict)
    ):
        print('WARNING from get_z(): Inputs must be numpy arrays')

    # number of vertical levels
    N = S['N']

    # remove singleton dimensions
    h = h.squeeze()
    zeta = zeta.squeeze()
    # ensure that we have enough dimensions
    h = np.atleast_2d(h)
    zeta = np.atleast_2d(zeta)
    # check that the dimensions are the same
    if h.shape != zeta.shape:
        print('WARNING from get_z(): h and zeta must be the same shape')
    M, L = h.shape

    # rho
    # create some useful arrays
    csr = S['Cs_r']
    csrr = csr.reshape(N, 1, 1).copy()
    Cs_r = np.tile(csrr, [1, M, L])
    H_r = np.tile(h.reshape(1, M, L).copy(), [N, 1, 1])
    Zeta_r = np.tile(zeta.reshape(1, M, L).copy(), [N, 1, 1])
    if S['hc'] == 0:  # if hc = 0 the transform is simpler (and faster)
        z_rho = H_r*Cs_r + Zeta_r + Zeta_r*Cs_r
    elif S['hc'] != 0:  # need to calculate a few more useful arrays
        sr = S['s_rho']
        srr = sr.reshape(N, 1, 1).copy()
        S_rho = np.tile(srr, [1, M, L])
        Hc_r = np.tile(S['hc'], [N, M, L])
        if S['Vtransform'] == 1:
            zr0 = (S_rho - Cs_r) * Hc_r + Cs_r*H_r
            z_rho = zr0 + Zeta_r * (1 + zr0/H_r)
        elif S['Vtransform'] == 2:
            zr0 = (S_rho*Hc_r + Cs_r*H_r) / (Hc_r + H_r)
            z_rho = Zeta_r + (Zeta_r + H_r)*zr0
    z_rho = z_rho.squeeze()

    return z_rho
