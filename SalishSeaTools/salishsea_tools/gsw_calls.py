# Module to call matlab gsw functions from python..
# The function generic_gsw_caller can handle calling any single variable output
# gsw functions.
# The _call_... python functions have been replaced by generic_gsw_caller()
import logging
import os
import shlex
import subprocess as sp

import numpy as np


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def generic_gsw_caller(
    gsw_function_name, input_vars,
    matlab_gsw_dir='/ocean/rich/home/matlab/gsw3',
):
    """ A generic function for calling matlab gsw functions. Only works with
    gsw functions that have a single variable as output.

    :arg str gsw_function_name: The name of the matlab gsw function.
                                e.g. gsw_p_from_z.m
    :arg input_vars: A list of the input variables in the same order as
                     expected from the gsw matlab function.
    :type input_vars: list of numpy arrays

    :arg str matlab_gsw_dir: The directory where the matlab gsw scripts are
                             stored.
    :returns: A numpy array containing the output from call to gsw function.
    """
    # save inputs to a file for reading into matlab
    tmp_files = []
    for count, var_data in enumerate(input_vars):
        tmp_fname = 'input{}'.format(count)
        tmp_files.append(tmp_fname)
        np.savetxt(tmp_fname, var_data.flatten(), delimiter=',')
    shape = input_vars[0].shape
    # create matlab wrapper
    gsw_function_name = (
        gsw_function_name if gsw_function_name.endswith('.m')
        else '{}.m'.format(gsw_function_name))
    output = 'output_file'
    matlab_wrapper_name = _create_matlab_wrapper(gsw_function_name,
                                                 output,
                                                 tmp_files,
                                                 matlab_gsw_dir)
    # create string of input arguments
    arg_strings = "('{}'".format(output)
    for tmp_fname in tmp_files:
        arg_strings += ",'{}'".format(tmp_fname)
    arg_strings += ');exit'
    # create string for calling matlab
    functioncall = '{}{}'.format(matlab_wrapper_name[:-2], arg_strings)
    _run_matlab(functioncall)
    # load output from matlab
    output_data = np.loadtxt(output, delimiter=',')
    # remove tmp files
    for f in tmp_files:
        os.remove(f)
    os.remove(output)
    os.remove(matlab_wrapper_name)
    return output_data.reshape(shape)


def _create_matlab_wrapper(
    gsw_function_name, outfile, input_files, matlab_gsw_dir,
):
    # Create a matlab wrapper file
    wrapper_file_name = 'mw_{}'.format(gsw_function_name)
    f = open(wrapper_file_name, 'w')
    header = 'function [] = {}({},'.format(wrapper_file_name[:-2], outfile)
    for input_file in input_files:
        header += "{},".format(input_file)
    header = header[:-1] + ')\n'
    f.write(header)
    # Add directories to matlab path
    f.write('addpath {}\n'.format(matlab_gsw_dir))
    for subdir in ['html', 'library', 'thermodynamics_from_t', 'pdf']:
        f.write('addpath {}\n'.format(os.path.join(matlab_gsw_dir, subdir)))
    # reading input files
    input_args = ''
    for count, input_file in enumerate(input_files):
        f.write("in{} = dlmread({},',');\n".format(count, input_file))
        input_args += 'in{},'.format(count)
    # call matlab gsw function
    f.write('y = {}({});\n'.format(gsw_function_name[:-2], input_args[:-1]))
    f.write("dlmwrite({},y,',');\n".format(outfile))
    return wrapper_file_name


def _run_matlab(functioncall):
    cmd = shlex.split('matlab -nosplash -nodesktop -nodisplay -nojvm -r')
    cmd.append(functioncall)
    logger.debug('executing {}'.format(cmd))
    try:
        cmd_output = sp.check_output(
            cmd, stderr=sp.STDOUT, universal_newlines=True)
    except sp.CalledProcessError as e:
        logger.error(
            'matlab command failed with return code {.returncode}'.format(e))
        cmd_output = e.output
    finally:
        for line in cmd_output.splitlines():
            line = line.strip()
            if line:
                logger.debug(line)


def _call_p_from_z(z, lat):
    fname = "'pout'"
    zfile = "'zfile'"
    latfile = "'latfile'"
    for f, var in zip([zfile, latfile], [z, lat]):
        np.savetxt(f[1:-1], var.flatten(), delimiter=',')
    shape = z.shape

    functioncall = 'mw_gsw_p_from_z({},{},{});exit'.format(fname,
                                                           zfile,
                                                           latfile)
    _run_matlab(functioncall)
    pressure = np.loadtxt(fname[1:-1], delimiter=',')
    for f in [fname, zfile, latfile]:
        os.remove(f[1:-1])
    return pressure.reshape(shape)


def _call_SR_from_SP(SP):
    fname = "'SRout'"
    SPfile = "'SPfile'"
    for f, var in zip([SPfile, ], [SP, ]):
        np.savetxt(f[1:-1], var.flatten(), delimiter=',')
    shape = SP.shape

    functioncall = 'mw_gsw_SR_from_SP({},{});exit'.format(fname,
                                                          SPfile,)
    _run_matlab(functioncall)
    sal_ref = np.loadtxt(fname[1:-1], delimiter=',')
    for f in [fname, SPfile, ]:
        os.remove(f[1:-1])
    return sal_ref.reshape(shape)


def _call_SA_from_SP(SP, p, long, lat):
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
    _run_matlab(functioncall)
    SA = np.loadtxt(fname[1:-1], delimiter=',')

    for f in [fname, SPfile, pfile,
              longfile, latfile]:
        os.remove(f[1:-1])

    return SA.reshape(shape)


def _call_CT_from_PT(SA, PT):
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
    _run_matlab(functioncall)
    CT = np.loadtxt(fname[1:-1], delimiter=',')

    for f in [fname, SAfile, PTfile]:
        os.remove(f[1:-1])

    return CT.reshape(shape)
