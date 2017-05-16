.. _netCDF4FilesCreationAndConventions:

**************************************
netCDF4 Files Creation and Conventions
**************************************

The Salish Sea MEOPAR project uses netCDF4_ files as input for the NEMO model and for other purposes,
where appropriate.
This section documents the recommended way of creating netCDF4 files with compression of variables,
limitation of variables to appropriate precision,
and appropriate metadata attributes for the variables and the dataset as a whole.
The recommendations are based on the `NetCDF Climate and Forecast (CF) Metadata Conventions, Version 1.6, 5 December, 2011`_.
Use of the `netCDF4-python`_ library
(included in :ref:`AnacondaPythonDistro`)
is assumed.

.. _netCDF4: http://www.unidata.ucar.edu/software/netcdf/
.. _NetCDF Climate and Forecast (CF) Metadata Conventions, Version 1.6, 5 December, 2011: http://cfconventions.org/Data/cf-conventions/cf-conventions-1.6/build/cf-conventions.html
.. _netCDF4-python: http://unidata.github.io/netcdf4-python/

The :ref:`salishsea_tools.nc_tools` in the :ref:`SalishSeaToolsPackage` is a library of Python functions for exploring and managing the attributes of netCDF files.
The `PrepareTS.ipynb`_ notebook shows examples of the use of those functions.

.. _PrepareTS.ipynb: http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/Initial/PrepareTS.ipynb


Creating netCDF4 Files
======================

All of the following code examples assume that the `netcdf4-python`_ library has been imported and aliased to :kbd:`nc`:

.. code-block:: python

    import netCDF4 as nc


Datasets and Files
------------------

Create an "empty" netCDF4 dataset and store it on disk:

.. code-block:: python

    foo = nc.Dataset('foo.nc', 'w')
    foo.close()

The :py:class:`Dataset` constructor defaults to creating :kbd:`NETCDF4` format objects.
Other formats may be specified with the :kbd:`format` keyword argument
(see the `netCDF4-python`_ docs).

The first argument that :py:class:`Dataset` takes is the path and name of the netCDF4 file that will be created, updated, or read.
The second argument is the mode with which to access the file.
Use:

* :kbd:`w` (write mode) to create a new file,
  use :kbd:`clobber=True` to over-write and existing one
* :kbd:`r` (read mode) to open an existing file read-only
* :kbd:`r+` (append mode) to open an existing file and change its contents


Dimensions
----------

Create dimensions on a dataset with the :py:meth:`createDimension` method,
for example:

.. code-block:: python

    foo.createDimension('t', None)
    foo.createDimension('z', 40)
    foo.createDimension('y', 898)
    foo.createDimension('x', 398)

The first dimension is called :kbd:`t` with unlimited size
(i.e. variable values may be appended along the this dimension).
Unlimited size dimensions must be declared before
("to the left of")
other dimensions.
NEMO supports only a single unlimited size dimension that is used for time.

The other 3 dimensions are obviously spatial dimensions with sizes of 40,
898,
and 398,
respectively.

The recommended maximum number of dimensions is 4.
The recommended order of dimensions is :kbd:`t`,
:kbd:`z`,
:kbd:`y`,
:kbd:`x`.
Not all datasets are required to have all 4 dimensions.


.. _netCDF4-python-variables:

Variables
---------

Create variables on a dataset with the :py:meth:`createVariable` method,
for example:

.. code-block:: python

    lats = foo.createVariable('nav_lat', float, ('y', 'x'), zlib=True)
    lons = foo.createVariable('nav_lon', float, ('y', 'x'), zlib=True)
    depths = foo.createVariable('Bathymetry', float, ('y', 'x'), zlib=True, least_significant_digit=1, fill_value=0)

The first argument to :py:meth:`createVariable` is the variable name.
For files read by NEMO the variable names must be those that NEMO expects.

The second argument is the variable type.
There are many way of specifying type,
but Python built-in types work well in the absence of specific requirements.

The third argument is a tuple of previously defined dimension names.
As noted above,

* The recommended maximum number of dimensions is 4
* The recommended order of dimensions is :kbd:`t`,
  :kbd:`z`,
  :kbd:`y`,
  :kbd:`x`
* Not all variables are required to have all 4 dimensions

All variables should be created with the :kbd:`zlib=True` argument to enable data compression within the netCDF4 file.

When appropriate,
the :kbd:`least_significant_digit` argument should be used to improve compression and storage efficiency by quantizing the variable data to the specified precision.
In the example above the :kbd:`depths` data will be quantized such that a precision of 0.1 is retained.

When appropriate,
the :kbd:`fill_value` argument can be used to specify the value that the variable gets filled with before any data is written to it.
Doing so overrides the default netCDF :kbd:`_FillValue`
(which depends on the type of the variable).
If :kbd:`fill_value` is set to False, then the variable is not pre-filled.
In the example above the :kbd:`depths` data will be initialized to zero,
the appropriate value for grid points that are on land.


Writing and Retrieving Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Variable data in netCDF4 datasets are stored in NumPy_ array_ or `masked array`_ objects.

.. _NumPy: http://docs.scipy.org/doc/numpy/reference/index.html
.. _array: http://docs.scipy.org/doc/numpy/reference/arrays.html
.. _masked array: http://docs.scipy.org/doc/numpy/reference/maskedarray.html

An appropriately sized and shaped NumPy array can be loaded into a dataset variable by assigning it to a slice that span the variable:

.. code-block:: python

    import numpy as np

    d[:] = np.arange(48, 51.1, 0.1)

and values can be retrieved using most of the usual NumPy indexing and slicing techniques.

There are differences between the NumPy and netCDF variable slicing rules;
see the `netCDF4-python`_ docs for details.


netCDF4 File Conventions
========================

The `NetCDF Climate and Forecast (CF) Metadata Conventions, Version 1.6, 5 December, 2011`_ has the following stated goal::

  The NetCDF library is designed to read and write data that has been structured according to well-defined rules and is easily ported across various computer platforms.
  The netCDF interface enables but does not require the creation of self-describing datasets.
  The purpose of the CF conventions is to require conforming datasets to contain sufficient metadata that they are self-describing in the sense that each variable in the file has an associated description of what it represents,
  including physical units if appropriate,
  and that each value can be located in space
  (relative to earth-based coordinates)
  and time.

Datasets created by the Salish Sea MEOPAR project shall conform to `CF-1.6`_.
NEMO results nominally conform to an ealier version,
`CF-1.1`_.

.. _CF-1.1: http://cfconventions.org/Data/cf-conventions/cf-conventions-1.1/build/cf-conventions.html
.. _CF-1.6: http://cfconventions.org/Data/cf-conventions/cf-conventions-1.6/build/cf-conventions.html


Global Attributes
-----------------

Global attributes are on the dataset.
The can be access individually as attributes using dotted notation:

.. code-block:: python

    foo.Conventions = 'CF-1.6'

or in code using the methods on a :py:class:`Dataset` object.

Required
~~~~~~~~

All datasets should have values for the following attributes unless there is a *very* good reason not to.

The following are defined in `CF-1.6`_.
See that documentation for more details of the intent behind these attributes.

:kbd:`Conventions`
  Identification of conventions.

  Example:

  .. code-block:: python

      foo.Conventions = 'CF-1.6'

:kbd:`title`
  A succinct description of what is in the dataset.

  Example:

  .. code-block:: python

      foo.title = 'Salish Sea NEMO Bathymetry'

:kbd:`institution`
  Specifies where the dataset was produced.

  Example:

  .. code-block:: python

      foo.institution = 'Dept of Earth, Ocean & Atmospheric Sciences, University of British Columbia'

:kbd:`source`
  The method of production of the original dataset.
  For datasets created via IPython Notebooks or code modules this should be the URL of the source code in the :ref:`tools-repo` on Bitbucket.

  Example:

  .. code-block:: python

      foo.source = 'https://bitbucket.org/salishsea/tools/src/tip/bathymetry/netCDF4bathy.ipynb'

:kbd:`references`
  Published or web-based references that describe the dataset or methods used to produce it.
  This should include the URL of the dataset in the appropriate repo
  (typically :ref:`NEMO-forcing-repo`)
  on Bitbucket.

  Example:

  .. code-block:: python

      foo.references = 'https://bitbucket.org/salishsea/nemo-forcing/src/tip/grid/bathy_meter_SalishSea.nc'

:kbd:`history`
  Provides an audit trail for modifications to the original dataset.
  Each line should begin with a timestamp indicating the date and time of day when the modification was done.

  Example:

  .. code-block:: python

      foo.history = """
          [2013-10-30 13:18] Created netCDF4 zlib=True dataset.
          [2013-10-30 15:22] Set depths between 0 and 4m to 4m and those >428m to 428m.
          [2013-10-31 17:10] Algorithmic smoothing.
      """

:kbd:`comment`
  Miscellaneous information about the dataset or methods used to produce it.

  Example:

  .. code-block:: python

      foo.comment = 'Based on 1_bathymetry_seagrid_WestCoast.nc file from 2-Oct-2013 WCSD_PREP tarball provided by J-P Paquin.'


Variable Attributes
-------------------

Variable attributes are on particular variables in the dataset.
The can be access individually as attributes using dotted notation:

.. code-block:: python

    depths.units = 'm'

or in code using the methods on a :py:class:`Variable` object.


Required
~~~~~~~~

All variables should have values for the following attributes unless there is a *very* good reason not to.

The following are defined in `CF-1.6`_.
See that documentation for more details of the intent behind these attributes.

:kbd:`units`
  Required for all variables that represent dimensional quantities.
  The value of the units attribute is a string that can be recognized by UNIDATA's `Udunits package`_,
  with a few exceptions.

  .. _Udunits package: http://www.unidata.ucar.edu/software/udunits/

  Example:

  .. code-block:: python

      depths.units = 'm'

  Exceptions and special cases:

  * For latitude use ``units = 'degrees_north'``
  * For longitude use ``units = 'degrees_east'``
  * For time use ``units = `seconds since yyyy-mm-dd HH:MM:SS'`` with an actual date/time
  * For practical salinity use ``units = 1`` and ``long_name = 'Practical Salinity'``

:kbd:`long_name`
  A long descriptive name which may, for example, be used for labeling plots.

  Example:

  .. code-block:: python

      depths.long_name = 'Depth'


As Applicable
~~~~~~~~~~~~~

:kbd:`calendar`
  The calendar to use on a time axis to calculate a new date and time given a base date,
  base time and a time increment.

  Example:

  .. code-block:: python

      time.calendar = 'gregorian'

:kbd:`positive`
  The direction of positive
  (i.e., the direction in which the coordinate values are increasing)
  for a vertical coordinate.
  For Salish Sea MEOPAR files this is applicable to depths and a value of :kbd:`down` is used,
  indicating that the depth of the surface is 0 and depth values increase downward.

  Example:

  .. code-block:: python

      depths.positive = 'down'

:kbd:`valid_range`
  Smallest and largest valid values of a variable.
  If valid minimum and maximum values for a variable can be stated,
  use this instead of :kbd:`valid_min` and :kbd:`valid_max`.

  Example:

  .. code-block:: python

      depths.valid_range = np.array((0.0, 428.0))

:kbd:`valid_min`
  Smallest valid value of a variable.
  Use this only if there is no value for :kbd:`valid_max`,
  otherwise,
  use :kbd:`valid_range`.

  Example:

  .. code-block:: python

      sal.valid_min = 0

:kbd:`valid_max`
  Largest valid value of a variable.
  Use this only if there is no value for :kbd:`valid_min`,
  otherwise,
  use :kbd:`valid_range`.

  Example:

  .. code-block:: python

      foo.valid_max = 42

:kbd:`_FillValue`
  The value that a variable gets filled with before any data is loaded into it.
  Each data type has a default for :kbd:`_FillValue`,
  but a variable-specific value can be specified in the :py:meth:`createVariable` method
  (see :ref:`netCDF4-python-variables`).

:kbd:`standard_name`
  A name used to identify the physical quantity.
  A standard name contains no whitespace and is case sensitive.
  The :kbd:`standard_name` attribute is typically used where a descriptive,
  code-friendly alternative to the :kbd:`long_name` or the variable name itself is needed.

  Example:

  .. code-block:: python

      sal.standard_name = 'practical_salinity'


Applying netCDF4 Variable-Level Compression
===========================================

NEMO-3.4 produces netCDF files that use the :kbd:`64-bit offset` format.
The size on disk of those files can be reduced by up to 90%
(depending on the contents of the file)
by converting them to :kbd:`netCDF-4` format and applying Lempel-Ziv compression to each variable.
The :command:`ncks` tool from the `NCO package`_ can be used to accomplish that:

.. code-block:: bash

    $ ncks -4 -L4 -O SalishSea_1d_grid_T.nc SalishSea_1d_grid_T.nc

.. note:: The above command replaces the original version of the file with its netCDF4 compressed version.

.. _NCO package: http://nco.sourceforge.net/

The :kbd:`-4` argument tells :command:`ncks` to produce a :kbd:`netCDF-4` format file.

The :kbd:`-L4` argument causes level 4 compression to be used.
Level 4 is a good compromise between the amount of compression that is achieved and the amount of processing time required to do the compression.

The :kbd:`-O` argument tells :command:`ncks` to over-write existing file without asking for confirmation.

The file names are the input and output files,
respectively.

NEMO-3.6 produces netCDF files that use the :kbd:`netCDF-4` format with level 1 Lempel-Ziv compression applied to each variable.
As above,
the size of those files on disk can be reduced by up to 90%
(depending on the contents of the file)
by increasing the compression level to 4.
The command to do so is the same:

.. code-block:: bash

    $ ncks -4 -L4 -O SalishSea_1d_grid_T.nc SalishSea_1d_grid_T.nc

.. note:: The above command replaces the original version of the file with its netCDF4 compressed version.
