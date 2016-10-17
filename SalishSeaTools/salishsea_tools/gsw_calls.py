# Module to call matlab gsw functions from python.
# You need to have a matlab gsw wrappers for each function.
# These functions and wrappers are all so similar. Auto-create?
# The function generic_gsw_caller can handle calling any of the matlab
# wrappers. This function replaces the call_... python functions.

import numpy as np

import os
import subprocess as sp


def generic_gsw_caller(matlab_wrapper_name, input_vars,
                       matlab_wrapper_dir=('/data/nsoontie/MEOPAR/tools/'
                                           'SalishSeaTools/salishsea_tools/'
                                           'teos-10_matlab_wrappers')):
    """ A generic function for calling matlab wrappers of gsw functions.

    :arg str matlab_wrapper_name: The name of the matlab wrapper.
                                  e.g. mw_gsw_p_from_z.m
    :arg input_vars: A list of the input variables in the same order as
                     expected from the gsw matlab function.
    :type input_vars: list of numpy arrays

    :arg str matlab_wrapper_dir: The directory where the matlab wrappers are
                                 saved. Also a script called startup.m, which
                                 adds the gsw paths to the matlab path, must be
                                 in this directory.
    :returns: A numpy array containing the output from cliing the gsw function.
    """
    # link matlab wrapper script and startup script
    os.symlink(os.path.join(matlab_wrapper_dir, 'startup.m'), 'startup.m')
    os.symlink(os.path.join(matlab_wrapper_dir, matlab_wrapper_name),
               matlab_wrapper_name)
    # save inputs to a file for reading into matlab
    tmp_files = []
    for count, var_data in enumerate(input_vars):
        tmp_fname = 'input{}.txt'.format(count)
        tmp_files.append(tmp_fname)
        np.savetxt(tmp_fname, var_data.flatten(), delimiter=',')
    shape = input_vars[0].shape
    # create string of input arguments
    output = 'output_file'
    arg_strings = "('{}'".format(output)
    for tmp_fname in tmp_files:
        arg_strings += ",'{}'".format(tmp_fname)
    arg_strings += ');exit'
    # create string for calling matlab
    functioncall = '{}{}'.format(matlab_wrapper_name[:-2], arg_strings)
    cmd = ["matlab", "-nodesktop", "-nodisplay", "-r", functioncall]
    sp.call(cmd)
    # load output from matlab
    output_data = np.loadtxt(output, delimiter=',')
    # remove tmp files
    for f in tmp_files:
        os.remove(f)
    os.remove(output)
    # remove symbolic links
    os.unlink('startup.m')
    os.unlink(matlab_wrapper_name)
    return output_data.reshape(shape)


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
    for f in [fname, zfile, latfile]:
        os.remove(f[1:-1])
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
    for f in [fname, SPfile, ]:
        os.remove(f[1:-1])
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

    for f in [fname, SPfile, pfile,
              longfile, latfile]:
        os.remove(f[1:-1])

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

    for f in [fname, SAfile, PTfile]:
        os.remove(f[1:-1])

    return CT.reshape(shape)
