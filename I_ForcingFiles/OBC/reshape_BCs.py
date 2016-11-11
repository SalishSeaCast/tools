import netCDF4 as nc
import datetime, sys

def reshape_BCs(infile, outfile):
    """
    This script rewrites an unstructured boundary condition file in
    structured format. The unstructured format has a singleton dimension for
    'yb' so the arrays have length (yb,xbT)=(1,10*nx), whereas the structured
    format has array lengths (yb,xbT)=(10,nx), for a sponge region width of 10.
    Also we drop variables nbidta, nbjdta, and nbrdta as they are not used.

    :arg str infile: unstructured nc file
    :arg str outfile: structured nc file

    Usage:
    python reshape_BCs.py SalishSea_north_TEOS10.nc SalishSea_north_TEOS10-structured.nc
    python reshape_BCs.py SalishSea_west_TEOS10.nc SalishSea_west_TEOS10-structured.nc
    """
    fin  = nc.Dataset(infile, 'r')
    fout = nc.Dataset(outfile, 'w')

    # Copy global attributes
    for attr in fin.ncattrs():
        fout.setncattr(attr, fin.getncattr(attr))

    # Copy depth and time dimensions
    dim = fin.dimensions['deptht']
    fout.createDimension(dim.name, dim.size)
    dim = fin.dimensions['time_counter']
    fout.createDimension(dim.name, None)

    # Adjust the yb and xbT dimensions
    dim = fin.dimensions['yb']
    fout.createDimension(dim.name, 10)
    dim = fin.dimensions['xbT']
    fout.createDimension(dim.name, dim.size/10)

    # Copy variables
    for k, v in fin.variables.items():
        # Skip nbidta, nbjdta, and nbrdta because they are not used
        if v.name in ['nbidta', 'nbjdta', 'nbrdta']:
            print("Skipping {} ...".format(v.name))
            continue
        # Create variables
        fout.createVariable(v.name, v.datatype, v.dimensions, zlib=True, complevel=4, shuffle=False)
        # Copy data (reshape implicit here)
        fout.variables[v.name][:] = fin.variables[v.name][:]
        # Copy attributes
        for attr in v.ncattrs():
            fout.variables[v.name].setncattr(attr, v.getncattr(attr))

    # Update notes
    fout.source += ("\n https://bitbucket.org/salishsea/"
                    "tools/I_ForcingFiles/OBC/reshape_BCs.py")

    fout.history += ("\n [{}] Reshaped to structured format and drop "
                     "variables nbidta, nbjdta, and nbrdta, with compression."
                     .format(datetime.datetime.today().strftime('%Y-%m-%d')))

    fin.close()
    fout.close()

if __name__ == "__main__":
    reshape_BCs(sys.argv[1], sys.argv[2])
