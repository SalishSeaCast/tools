# Module to call matlab gsw functions from python.
# You need to have a matlab gsw wrappers for each function.
# These functions and wrappers are all so similar. Auto-create?

import numpy as np

import os
import subprocess as sp


def call_p_from_z(z, lat):

    fname = "'pout'"
    zfile = "'zfile'"
    latfile = "'latfile'"
    for f, var in zip([zfile, latfile], [z, lat]):
        np.savetxt(f[1:-1], var.flatten(), delimiter=',')
    shape = z.shape

    functioncall = 'mw_gsw_p_from_z({},{},{});exit'.format(fname,
                                                           zfile,
                                                           latfile)
    cmd = ["matlab", "-nodesktop", "-nodisplay", "-r", functioncall]
    sp.call(cmd)
    pressure = np.loadtxt(fname[1:-1], delimiter=',')
    for f in [fname[1:-1], zfile[1:-1], latfile[1:-1]]:
        os.remove(f)
    return pressure.reshape(shape)


def call_SR_from_SP(SP):

    fname = "'SRout'"
    SPfile = "'SPfile'"
    for f, var in zip([SPfile, ], [SP, ]):
        np.savetxt(f[1:-1], var.flatten(), delimiter=',')
    shape = SP.shape

    functioncall = 'mw_gsw_SR_from_SP({},{});exit'.format(fname,
                                                          SPfile,)
    cmd = ["matlab", "-nodesktop", "-nodisplay", "-r", functioncall]
    sp.call(cmd)
    sal_ref = np.loadtxt(fname[1:-1], delimiter=',')
    for f in [fname[1:-1], SPfile[1:-1], ]:
        os.remove(f)
    return sal_ref.reshape(shape)


def call_SA_from_SP(SP, p, long, lat):

    fname = "'SAout'"
    SPfile = "'SPfile'"
    pfile = "'pfile'"
    longfile = "'longfile'"
    latfile = "'latfile'"
    for f, var in zip([SPfile, pfile, longfile, latfile],
                      [SP, p, long, lat]):
        np.savetxt(f[1:-1], var.flatten(), delimiter=',')
    shape = SP.shape

    functioncall = 'mw_gsw_SA_from_SP({},{},{},{},{});exit'.format(fname,
                                                                   SPfile,
                                                                   pfile,
                                                                   longfile,
                                                                   latfile)
    cmd = ["matlab", "-nodesktop", "-nodisplay", "-r", functioncall]
    sp.call(cmd)
    SA = np.loadtxt(fname[1:-1], delimiter=',')

    for f in [fname[1:-1], SPfile[1:-1], pfile[1:-1],
              longfile[1:-1], latfile[1:-1]]:
        os.remove(f)

    return SA.reshape(shape)


def call_CT_from_PT(SA, PT):

    fname = "'CTout'"
    SAfile = "'SAfile'"
    PTfile = "'PTfile'"
    for f, var in zip([SAfile, PTfile],
                      [SA, PT]):
        np.savetxt(f[1:-1], var.flatten(), delimiter=',')
    shape = PT.shape

    functioncall = 'mw_gsw_CT_from_pt({},{},{});exit'.format(fname,
                                                             SAfile,
                                                             PTfile)
    cmd = ["matlab", "-nodesktop", "-nodisplay", "-r", functioncall]
    sp.call(cmd)
    CT = np.loadtxt(fname[1:-1], delimiter=',')

    for f in [fname[1:-1], SAfile[1:-1], PTfile[1:-1]]:
        os.remove(f)

    return CT.reshape(shape)
