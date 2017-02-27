.. _io:

.. currentmodule:: pandas

.. ipython:: python
   :suppress:

   import os
   import csv
   from pandas.compat import StringIO, BytesIO
   import pandas as pd
   ExcelWriter = pd.ExcelWriter

   import numpy as np
   np.random.seed(123456)
   randn = np.random.randn
   np.set_printoptions(precision=4, suppress=True)

   import matplotlib.pyplot as plt
   plt.close('all')

   import pandas.util.testing as tm
   pd.options.display.max_rows=15
   clipdf = pd.DataFrame({'A':[1,2,3],'B':[4,5,6],'C':['p','q','r']},
                         index=['x','y','z'])

===============================
IO Tools (Text, CSV, HDF5, ...)
===============================

The pandas I/O API is a set of top level ``reader`` functions accessed like ``pd.read_csv()`` that generally return a ``pandas``
object.

    * :ref:`read_csv<io.read_csv_table>`
    * :ref:`read_excel<io.excel_reader>`
    * :ref:`read_hdf<io.hdf5>`
    * :ref:`read_sql<io.sql>`
    * :ref:`read_json<io.json_reader>`
    * :ref:`read_msgpack<io.msgpack>` (experimental)
    * :ref:`read_html<io.read_html>`
    * :ref:`read_gbq<io.bigquery_reader>` (experimental)
    * :ref:`read_stata<io.stata_reader>`
    * :ref:`read_sas<io.sas_reader>`
    * :ref:`read_clipboard<io.clipboard>`
    * :ref:`read_pickle<io.pickle>`

The corresponding ``writer`` functions are object methods that are accessed like ``df.to_csv()``

    * :ref:`to_csv<io.store_in_csv>`
    * :ref:`to_excel<io.excel_writer>`
    * :ref:`to_hdf<io.hdf5>`
    * :ref:`to_sql<io.sql>`
    * :ref:`to_json<io.json_writer>`
    * :ref:`to_msgpack<io.msgpack>` (experimental)
    * :ref:`to_html<io.html>`
    * :ref:`to_gbq<io.bigquery_writer>` (experimental)
    * :ref:`to_stata<io.stata_writer>`
    * :ref:`to_clipboard<io.clipboard>`
    * :ref:`to_pickle<io.pickle>`

:ref:`Here <io.perf>` is an informal performance comparison for some of these IO methods.

.. note::
   For examples that use the ``StringIO`` class, make sure you import it
   according to your Python version, i.e. ``from StringIO import StringIO`` for
   Python 2 and ``from io import StringIO`` for Python 3.

.. _io.read_csv_table:

CSV & Text files
----------------

The two workhorse functions for reading text files (a.k.a. flat files) are
:func:`read_csv` and :func:`read_table`. They both use the same parsing code to
intelligently convert tabular data into a DataFrame object. See the
:ref:`cookbook<cookbook.csv>` for some advanced strategies.

Parsing options
'''''''''''''''

:func:`read_csv` and :func:`read_table` accept the following arguments:

Basic
+++++

filepath_or_buffer : various
  Either a path to a file (a :class:`python:str`, :class:`python:pathlib.Path`,
  or :class:`py:py._path.local.LocalPath`), URL (including http, ftp, and S3
  locations), or any object with a ``read()`` method (such as an open file or
  :class:`~python:io.StringIO`).
sep : str, defaults to ``','`` for :func:`read_csv`, ``\t`` for :func:`read_table`
  Delimiter to use. If sep is ``None``,
  will try to automatically determine this. Separators longer than 1 character
  and different from ``'\s+'`` will be interpreted as regular expressions, will
  force use of the python parsing engine and will ignore quotes in the data.
  Regex example: ``'\\r\\t'``.
delimiter : str, default ``None``
  Alternative argument name for sep.
delim_whitespace : boolean, default False
  Specifies whether or not whitespace (e.g. ``' '`` or ``'\t'``)
  will be used as the delimiter. Equivalent to setting ``sep='\s+'``.
  If this option is set to True, nothing should be passed in for the
  ``delimiter`` parameter.

  .. versionadded:: 0.18.1 support for the Python parser.

Column and Index Locations and Names
++++++++++++++++++++++++++++++++++++

header : int or list of ints, default ``'infer'``
  Row number(s) to use as the column names, and the start of the data. Default
  behavior is as if ``header=0`` if no ``names`` passed, otherwise as if
  ``header=None``. Explicitly pass ``header=0`` to be able to replace existing
  names. The header can be a list of ints that specify row locations for a
  multi-index on the columns e.g. ``[0,1,3]``. Intervening rows that are not
  specified will be skipped (e.g. 2 in this example is skipped). Note that
  this parameter ignores commented lines and empty lines if
  ``skip_blank_lines=True``, so header=0 denotes the first line of data
  rather than the first line of the file.
names : array-like, default ``None``
  List of column names to use. If file contains no header row, then you should
  explicitly pass ``header=None``. Duplicates in this list are not allowed unless
  ``mangle_dupe_cols=True``, which is the default.
index_col :  int or sequence or ``False``, default ``None``
  Column to use as the row labels of the DataFrame. If a sequence is given, a
  MultiIndex is used. If you have a malformed file with delimiters at the end of
  each line, you might consider ``index_col=False`` to force pandas to *not* use
  the first column as the index (row names).
usecols : array-like, default ``None``
  Return a subset of the columns. All elements in this array must either
  be positional (i.e. integer indices into the document columns) or strings
  that correspond to column names provided either by the user in `names` or
  inferred from the document header row(s). For example, a valid `usecols`
  parameter would be [0, 1, 2] or ['foo', 'bar', 'baz']. Using this parameter
  results in much faster parsing time and lower memory usage.
as_recarray : boolean, default ``False``
  DEPRECATED: this argument will be removed in a future version. Please call
  ``pd.read_csv(...).to_records()`` instead.

  Return a NumPy recarray instead of a DataFrame after parsing the data. If
  set to ``True``, this option takes precedence over the ``squeeze`` parameter.
  In addition, as row indices are not available in such a format, the ``index_col``
  parameter will be ignored.
squeeze : boolean, default ``False``
  If the parsed data only contains one column then return a Series.
prefix : str, default ``None``
  Prefix to add to column numbers when no header, e.g. 'X' for X0, X1, ...
mangle_dupe_cols : boolean, default ``True``
  Duplicate columns will be specified as 'X.0'...'X.N', rather than 'X'...'X'.
  Passing in False will cause data to be overwritten if there are duplicate
  names in the columns.

General Parsing Configuration
+++++++++++++++++++++++++++++

dtype : Type name or dict of column -> type, default ``None``
  Data type for data or columns. E.g. ``{'a': np.float64, 'b': np.int32}``
  (unsupported with ``engine='python'``). Use `str` or `object` to preserve and
  not interpret dtype.
engine : {``'c'``, ``'python'``}
  Parser engine to use. The C engine is faster while the python engine is
  currently more feature-complete.
converters : dict, default ``None``
  Dict of functions for converting values in certain columns. Keys can either be
  integers or column labels.
true_values : list, default ``None``
  Values to consider as ``True``.
false_values : list, default ``None``
  Values to consider as ``False``.
skipinitialspace : boolean, default ``False``
  Skip spaces after delimiter.
skiprows : list-like or integer, default ``None``
  Line numbers to skip (0-indexed) or number of lines to skip (int) at the start
  of the file.
skipfooter : int, default ``0``
  Number of lines at bottom of file to skip (unsupported with engine='c').
skip_footer : int, default ``0``
  DEPRECATED: use the ``skipfooter`` parameter instead, as they are identical
nrows : int, default ``None``
  Number of rows of file to read. Useful for reading pieces of large files.
low_memory : boolean, default ``True``
  Internally process the file in chunks, resulting in lower memory use
  while parsing, but possibly mixed type inference.  To ensure no mixed
  types either set ``False``, or specify the type with the ``dtype`` parameter.
  Note that the entire file is read into a single DataFrame regardless,
  use the ``chunksize`` or ``iterator`` parameter to return the data in chunks.
  (Only valid with C parser)
buffer_lines : int, default None
    DEPRECATED: this argument will be removed in a future version because its
    value is not respected by the parser
compact_ints : boolean, default False
  DEPRECATED: this argument will be removed in a future version

  If ``compact_ints`` is ``True``, then for any column that is of integer dtype, the
  parser will attempt to cast it as the smallest integer ``dtype`` possible, either
  signed or unsigned depending on the specification from the ``use_unsigned`` parameter.
use_unsigned : boolean, default False
  DEPRECATED: this argument will be removed in a future version

  If integer columns are being compacted (i.e. ``compact_ints=True``), specify whether
  the column should be compacted to the smallest signed or unsigned integer dtype.
memory_map : boolean, default False
  If a filepath is provided for ``filepath_or_buffer``, map the file object
  directly onto memory and access the data directly from there. Using this
  option can improve performance because there is no longer any I/O overhead.

NA and Missing Data Handling
++++++++++++++++++++++++++++

na_values : scalar, str, list-like, or dict, default ``None``
  Additional strings to recognize as NA/NaN. If dict passed, specific per-column
  NA values. By default the following values are interpreted as NaN:
  ``'-1.#IND', '1.#QNAN', '1.#IND', '-1.#QNAN', '#N/A N/A', '#N/A', 'N/A', 'NA',
  '#NA', 'NULL', 'NaN', '-NaN', 'nan', '-nan', ''``.
keep_default_na : boolean, default ``True``
  If na_values are specified and keep_default_na is ``False`` the default NaN
  values are overridden, otherwise they're appended to.
na_filter : boolean, default ``True``
  Detect missing value markers (empty strings and the value of na_values). In
  data without any NAs, passing ``na_filter=False`` can improve the performance
  of reading a large file.
verbose : boolean, default ``False``
  Indicate number of NA values placed in non-numeric columns.
skip_blank_lines : boolean, default ``True``
  If ``True``, skip over blank lines rather than interpreting as NaN values.

Datetime Handling
+++++++++++++++++

parse_dates : boolean or list of ints or names or list of lists or dict, default ``False``.
  - If ``True`` -> try parsing the index.
  - If ``[1, 2, 3]`` ->  try parsing columns 1, 2, 3 each as a separate date
    column.
  - If ``[[1, 3]]`` -> combine columns 1 and 3 and parse as a single date
    column.
  - If ``{'foo' : [1, 3]}`` -> parse columns 1, 3 as date and call result 'foo'.
    A fast-path exists for iso8601-formatted dates.
infer_datetime_format : boolean, default ``False``
  If ``True`` and parse_dates is enabled for a column, attempt to infer the
  datetime format to speed up the processing.
keep_date_col : boolean, default ``False``
  If ``True`` and parse_dates specifies combining multiple columns then keep the
  original columns.
date_parser : function, default ``None``
  Function to use for converting a sequence of string columns to an array of
  datetime instances. The default uses ``dateutil.parser.parser`` to do the
  conversion. Pandas will try to call date_parser in three different ways,
  advancing to the next if an exception occurs: 1) Pass one or more arrays (as
  defined by parse_dates) as arguments; 2) concatenate (row-wise) the string
  values from the columns defined by parse_dates into a single array and pass
  that; and 3) call date_parser once for each row using one or more strings
  (corresponding to the columns defined by parse_dates) as arguments.
dayfirst : boolean, default ``False``
  DD/MM format dates, international and European format.

Iteration
+++++++++

iterator : boolean, default ``False``
  Return `TextFileReader` object for iteration or getting chunks with
  ``get_chunk()``.
chunksize : int, default ``None``
  Return `TextFileReader` object for iteration. See :ref:`iterating and chunking
  <io.chunking>` below.

Quoting, Compression, and File Format
+++++++++++++++++++++++++++++++++++++

compression : {``'infer'``, ``'gzip'``, ``'bz2'``, ``'zip'``, ``'xz'``, ``None``}, default ``'infer'``
  For on-the-fly decompression of on-disk data. If 'infer', then use gzip,
  bz2, zip, or xz if filepath_or_buffer is a string ending in '.gz', '.bz2',
  '.zip', or '.xz', respectively, and no decompression otherwise. If using 'zip',
  the ZIP file must contain only one data file to be read in.
  Set to ``None`` for no decompression.

  .. versionadded:: 0.18.1 support for 'zip' and 'xz' compression.

thousands : str, default ``None``
  Thousands separator.
decimal : str, default ``'.'``
  Character to recognize as decimal point. E.g. use ``','`` for European data.
float_precision : string, default None
  Specifies which converter the C engine should use for floating-point values.
  The options are ``None`` for the ordinary converter, ``high`` for the
  high-precision converter, and ``round_trip`` for the round-trip converter.
lineterminator : str (length 1), default ``None``
  Character to break file into lines. Only valid with C parser.
quotechar : str (length 1)
  The character used to denote the start and end of a quoted item. Quoted items
  can include the delimiter and it will be ignored.
quoting : int or ``csv.QUOTE_*`` instance, default ``0``
  Control field quoting behavior per ``csv.QUOTE_*`` constants. Use one of
  ``QUOTE_MINIMAL`` (0), ``QUOTE_ALL`` (1), ``QUOTE_NONNUMERIC`` (2) or
  ``QUOTE_NONE`` (3).
doublequote : boolean, default ``True``
   When ``quotechar`` is specified and ``quoting`` is not ``QUOTE_NONE``,
   indicate whether or not to interpret two consecutive ``quotechar`` elements
   **inside** a field as a single ``quotechar`` element.
escapechar : str (length 1), default ``None``
  One-character string used to escape delimiter when quoting is ``QUOTE_NONE``.
comment : str, default ``None``
  Indicates remainder of line should not be parsed. If found at the beginning of
  a line, the line will be ignored altogether. This parameter must be a single
  character. Like empty lines (as long as ``skip_blank_lines=True``), fully
  commented lines are ignored by the parameter `header` but not by `skiprows`.
  For example, if ``comment='#'``, parsing '#empty\\na,b,c\\n1,2,3' with
  `header=0` will result in 'a,b,c' being treated as the header.
encoding : str, default ``None``
  Encoding to use for UTF when reading/writing (e.g. ``'utf-8'``). `List of
  Python standard encodings
  <https://docs.python.org/3/library/codecs.html#standard-encodings>`_.
dialect : str or :class:`python:csv.Dialect` instance, default ``None``
  If ``None`` defaults to Excel dialect. Ignored if sep longer than 1 char. See
  :class:`python:csv.Dialect` documentation for more details.
tupleize_cols : boolean, default ``False``
  Leave a list of tuples on columns as is (default is to convert to a MultiIndex
  on the columns).

Error Handling
++++++++++++++

error_bad_lines : boolean, default ``True``
  Lines with too many fields (e.g. a csv line with too many commas) will by
  default cause an exception to be raised, and no DataFrame will be returned. If
  ``False``, then these "bad lines" will dropped from the DataFrame that is
  returned (only valid with C parser). See :ref:`bad lines <io.bad_lines>`
  below.
warn_bad_lines : boolean, default ``True``
  If error_bad_lines is ``False``, and warn_bad_lines is ``True``, a warning for
  each "bad line" will be output (only valid with C parser).

.. ipython:: python
   :suppress:

   f = open('foo.csv','w')
   f.write('date,A,B,C\n20090101,a,1,2\n20090102,b,3,4\n20090103,c,4,5')
   f.close()

Consider a typical CSV file containing, in this case, some time series data:

.. ipython:: python

   print(open('foo.csv').read())

The default for `read_csv` is to create a DataFrame with simple numbered rows:

.. ipython:: python

   pd.read_csv('foo.csv')

In the case of indexed data, you can pass the column number or column name you
wish to use as the index:

.. ipython:: python

   pd.read_csv('foo.csv', index_col=0)

.. ipython:: python

   pd.read_csv('foo.csv', index_col='date')

You can also use a list of columns to create a hierarchical index:

.. ipython:: python

   pd.read_csv('foo.csv', index_col=[0, 'A'])

.. _io.dialect:

The ``dialect`` keyword gives greater flexibility in specifying the file format.
By default it uses the Excel dialect but you can specify either the dialect name
or a :class:`python:csv.Dialect` instance.

.. ipython:: python
   :suppress:

   data = ('label1,label2,label3\n'
           'index1,"a,c,e\n'
           'index2,b,d,f')

Suppose you had data with unenclosed quotes:

.. ipython:: python

   print(data)

By default, ``read_csv`` uses the Excel dialect and treats the double quote as
the quote character, which causes it to fail when it finds a newline before it
finds the closing double quote.

We can get around this using ``dialect``

.. ipython:: python

   dia = csv.excel()
   dia.quoting = csv.QUOTE_NONE
   pd.read_csv(StringIO(data), dialect=dia)

All of the dialect options can be specified separately by keyword arguments:

.. ipython:: python

    data = 'a,b,c~1,2,3~4,5,6'
    pd.read_csv(StringIO(data), lineterminator='~')

Another common dialect option is ``skipinitialspace``, to skip any whitespace
after a delimiter:

.. ipython:: python

   data = 'a, b, c\n1, 2, 3\n4, 5, 6'
   print(data)
   pd.read_csv(StringIO(data), skipinitialspace=True)

The parsers make every attempt to "do the right thing" and not be very
fragile. Type inference is a pretty big deal. So if a column can be coerced to
integer dtype without altering the contents, it will do so. Any non-numeric
columns will come through as object dtype as with the rest of pandas objects.

.. _io.dtypes:

Specifying column data types
''''''''''''''''''''''''''''

Starting with v0.10, you can indicate the data type for the whole DataFrame or
individual columns:

.. ipython:: python

    data = 'a,b,c\n1,2,3\n4,5,6\n7,8,9'
    print(data)

    df = pd.read_csv(StringIO(data), dtype=object)
    df
    df['a'][0]
    df = pd.read_csv(StringIO(data), dtype={'b': object, 'c': np.float64})
    df.dtypes

Fortunately, ``pandas`` offers more than one way to ensure that your column(s)
contain only one ``dtype``. If you're unfamiliar with these concepts, you can
see :ref:`here<basics.dtypes>` to learn more about dtypes, and
:ref:`here<basics.object_conversion>` to learn more about ``object`` conversion in
``pandas``.


For instance, you can use the ``converters`` argument
of :func:`~pandas.read_csv`:

.. ipython:: python

    data = "col_1\n1\n2\n'A'\n4.22"
    df = pd.read_csv(StringIO(data), converters={'col_1':str})
    df
    df['col_1'].apply(type).value_counts()

Or you can use the :func:`~pandas.to_numeric` function to coerce the
dtypes after reading in the data,

.. ipython:: python

    df2 = pd.read_csv(StringIO(data))
    df2['col_1'] = pd.to_numeric(df2['col_1'], errors='coerce')
    df2
    df2['col_1'].apply(type).value_counts()

which would convert all valid parsing to floats, leaving the invalid parsing
as ``NaN``.

Ultimately, how you deal with reading in columns containing mixed dtypes
depends on your specific needs. In the case above, if you wanted to ``NaN`` out
the data anomalies, then :func:`~pandas.to_numeric` is probably your best option.
However, if you wanted for all the data to be coerced, no matter the type, then
using the ``converters`` argument of :func:`~pandas.read_csv` would certainly be
worth trying.

.. note::
    The ``dtype`` option is currently only supported by the C engine.
    Specifying ``dtype`` with ``engine`` other than 'c' raises a
    ``ValueError``.

.. note::
   In some cases, reading in abnormal data with columns containing mixed dtypes
   will result in an inconsistent dataset. If you rely on pandas to infer the
   dtypes of your columns, the parsing engine will go and infer the dtypes for
   different chunks of the data, rather than the whole dataset at once. Consequently,
   you can end up with column(s) with mixed dtypes. For example,

   .. ipython:: python
        :okwarning:

        df = pd.DataFrame({'col_1':range(500000) + ['a', 'b'] + range(500000)})
        df.to_csv('foo')
        mixed_df = pd.read_csv('foo')
        mixed_df['col_1'].apply(type).value_counts()
        mixed_df['col_1'].dtype

   will result with `mixed_df` containing an ``int`` dtype for certain chunks
   of the column, and ``str`` for others due to the mixed dtypes from the
   data that was read in. It is important to note that the overall column will be
   marked with a ``dtype`` of ``object``, which is used for columns with mixed dtypes.

.. _io.categorical:

Specifying Categorical dtype
''''''''''''''''''''''''''''

.. versionadded:: 0.19.0

``Categorical`` columns can be parsed directly by specifying ``dtype='category'``

.. ipython:: python

   data = 'col1,col2,col3\na,b,1\na,b,2\nc,d,3'

   pd.read_csv(StringIO(data))
   pd.read_csv(StringIO(data)).dtypes
   pd.read_csv(StringIO(data), dtype='category').dtypes

Individual columns can be parsed as a ``Categorical`` using a dict specification

.. ipython:: python

   pd.read_csv(StringIO(data), dtype={'col1': 'category'}).dtypes

.. note::

   The resulting categories will always be parsed as strings (object dtype).
   If the categories are numeric they can be converted using the
   :func:`to_numeric` function, or as appropriate, another converter
   such as :func:`to_datetime`.

   .. ipython:: python

      df = pd.read_csv(StringIO(data), dtype='category')
      df.dtypes
      df['col3']
      df['col3'].cat.categories = pd.to_numeric(df['col3'].cat.categories)
      df['col3']


Naming and Using Columns
''''''''''''''''''''''''

.. _io.headers:

Handling column names
+++++++++++++++++++++

A file may or may not have a header row. pandas assumes the first row should be
used as the column names:

.. ipython:: python

    data = 'a,b,c\n1,2,3\n4,5,6\n7,8,9'
    print(data)
    pd.read_csv(StringIO(data))

By specifying the ``names`` argument in conjunction with ``header`` you can
indicate other names to use and whether or not to throw away the header row (if
any):

.. ipython:: python

    print(data)
    pd.read_csv(StringIO(data), names=['foo', 'bar', 'baz'], header=0)
    pd.read_csv(StringIO(data), names=['foo', 'bar', 'baz'], header=None)

If the header is in a row other than the first, pass the row number to
``header``. This will skip the preceding rows:

.. ipython:: python

    data = 'skip this skip it\na,b,c\n1,2,3\n4,5,6\n7,8,9'
    pd.read_csv(StringIO(data), header=1)

.. _io.dupe_names:

Duplicate names parsing
'''''''''''''''''''''''

If the file or header contains duplicate names, pandas by default will deduplicate
these names so as to prevent data overwrite:

.. ipython :: python

   data = 'a,b,a\n0,1,2\n3,4,5'
   pd.read_csv(StringIO(data))

There is no more duplicate data because ``mangle_dupe_cols=True`` by default, which modifies
a series of duplicate columns 'X'...'X' to become 'X.0'...'X.N'.  If ``mangle_dupe_cols
=False``, duplicate data can arise:

.. code-block :: python

   In [2]: data = 'a,b,a\n0,1,2\n3,4,5'
   In [3]: pd.read_csv(StringIO(data), mangle_dupe_cols=False)
   Out[3]:
      a  b  a
   0  2  1  2
   1  5  4  5

To prevent users from encountering this problem with duplicate data, a ``ValueError``
exception is raised if ``mangle_dupe_cols != True``:

.. code-block :: python

   In [2]: data = 'a,b,a\n0,1,2\n3,4,5'
   In [3]: pd.read_csv(StringIO(data), mangle_dupe_cols=False)
   ...
   ValueError: Setting mangle_dupe_cols=False is not supported yet

.. _io.usecols:

Filtering columns (``usecols``)
+++++++++++++++++++++++++++++++

The ``usecols`` argument allows you to select any subset of the columns in a
file, either using the column names or position numbers:

.. ipython:: python

    data = 'a,b,c,d\n1,2,3,foo\n4,5,6,bar\n7,8,9,baz'
    pd.read_csv(StringIO(data))
    pd.read_csv(StringIO(data), usecols=['b', 'd'])
    pd.read_csv(StringIO(data), usecols=[0, 2, 3])

Comments and Empty Lines
''''''''''''''''''''''''

.. _io.skiplines:

Ignoring line comments and empty lines
++++++++++++++++++++++++++++++++++++++

If the ``comment`` parameter is specified, then completely commented lines will
be ignored. By default, completely blank lines will be ignored as well. Both of
these are API changes introduced in version 0.15.

.. ipython:: python

   data = '\na,b,c\n  \n# commented line\n1,2,3\n\n4,5,6'
   print(data)
   pd.read_csv(StringIO(data), comment='#')

If ``skip_blank_lines=False``, then ``read_csv`` will not ignore blank lines:

.. ipython:: python

   data = 'a,b,c\n\n1,2,3\n\n\n4,5,6'
   pd.read_csv(StringIO(data), skip_blank_lines=False)

.. warning::

   The presence of ignored lines might create ambiguities involving line numbers;
   the parameter ``header`` uses row numbers (ignoring commented/empty
   lines), while ``skiprows`` uses line numbers (including commented/empty lines):

   .. ipython:: python

      data = '#comment\na,b,c\nA,B,C\n1,2,3'
      pd.read_csv(StringIO(data), comment='#', header=1)
      data = 'A,B,C\n#comment\na,b,c\n1,2,3'
      pd.read_csv(StringIO(data), comment='#', skiprows=2)

   If both ``header`` and ``skiprows`` are specified, ``header`` will be
   relative to the end of ``skiprows``. For example:

   .. ipython:: python

      data = '# empty\n# second empty line\n# third empty' \
                'line\nX,Y,Z\n1,2,3\nA,B,C\n1,2.,4.\n5.,NaN,10.0'
      print(data)
      pd.read_csv(StringIO(data), comment='#', skiprows=4, header=1)

.. _io.comments:

Comments
++++++++

Sometimes comments or meta data may be included in a file:

.. ipython:: python
   :suppress:

   data =  ("ID,level,category\n"
            "Patient1,123000,x # really unpleasant\n"
            "Patient2,23000,y # wouldn't take his medicine\n"
            "Patient3,1234018,z # awesome")

   with open('tmp.csv', 'w') as fh:
       fh.write(data)

.. ipython:: python

   print(open('tmp.csv').read())

By default, the parser includes the comments in the output:

.. ipython:: python

   df = pd.read_csv('tmp.csv')
   df

We can suppress the comments using the ``comment`` keyword:

.. ipython:: python

   df = pd.read_csv('tmp.csv', comment='#')
   df

.. ipython:: python
   :suppress:

   os.remove('tmp.csv')

.. _io.unicode:

Dealing with Unicode Data
'''''''''''''''''''''''''

The ``encoding`` argument should be used for encoded unicode data, which will
result in byte strings being decoded to unicode in the result:

.. ipython:: python

   data = b'word,length\nTr\xc3\xa4umen,7\nGr\xc3\xbc\xc3\x9fe,5'.decode('utf8').encode('latin-1')
   df = pd.read_csv(BytesIO(data), encoding='latin-1')
   df
   df['word'][1]

Some formats which encode all characters as multiple bytes, like UTF-16, won't
parse correctly at all without specifying the encoding. `Full list of Python
standard encodings
<https://docs.python.org/3/library/codecs.html#standard-encodings>`_

.. _io.index_col:

Index columns and trailing delimiters
'''''''''''''''''''''''''''''''''''''

If a file has one more column of data than the number of column names, the
first column will be used as the DataFrame's row names:

.. ipython:: python

    data = 'a,b,c\n4,apple,bat,5.7\n8,orange,cow,10'
    pd.read_csv(StringIO(data))

.. ipython:: python

    data = 'index,a,b,c\n4,apple,bat,5.7\n8,orange,cow,10'
    pd.read_csv(StringIO(data), index_col=0)

Ordinarily, you can achieve this behavior using the ``index_col`` option.

There are some exception cases when a file has been prepared with delimiters at
the end of each data line, confusing the parser. To explicitly disable the
index column inference and discard the last column, pass ``index_col=False``:

.. ipython:: python

    data = 'a,b,c\n4,apple,bat,\n8,orange,cow,'
    print(data)
    pd.read_csv(StringIO(data))
    pd.read_csv(StringIO(data), index_col=False)

.. _io.parse_dates:

Date Handling
'''''''''''''

Specifying Date Columns
+++++++++++++++++++++++

To better facilitate working with datetime data, :func:`read_csv` and
:func:`read_table` use the keyword arguments ``parse_dates`` and ``date_parser``
to allow users to specify a variety of columns and date/time formats to turn the
input text data into ``datetime`` objects.

The simplest case is to just pass in ``parse_dates=True``:

.. ipython:: python

   # Use a column as an index, and parse it as dates.
   df = pd.read_csv('foo.csv', index_col=0, parse_dates=True)
   df

   # These are python datetime objects
   df.index

It is often the case that we may want to store date and time data separately,
or store various date fields separately. the ``parse_dates`` keyword can be
used to specify a combination of columns to parse the dates and/or times from.

You can specify a list of column lists to ``parse_dates``, the resulting date
columns will be prepended to the output (so as to not affect the existing column
order) and the new column names will be the concatenation of the component
column names:

.. ipython:: python
   :suppress:

   data =  ("KORD,19990127, 19:00:00, 18:56:00, 0.8100\n"
            "KORD,19990127, 20:00:00, 19:56:00, 0.0100\n"
            "KORD,19990127, 21:00:00, 20:56:00, -0.5900\n"
            "KORD,19990127, 21:00:00, 21:18:00, -0.9900\n"
            "KORD,19990127, 22:00:00, 21:56:00, -0.5900\n"
            "KORD,19990127, 23:00:00, 22:56:00, -0.5900")

   with open('tmp.csv', 'w') as fh:
       fh.write(data)

.. ipython:: python

    print(open('tmp.csv').read())
    df = pd.read_csv('tmp.csv', header=None, parse_dates=[[1, 2], [1, 3]])
    df

By default the parser removes the component date columns, but you can choose
to retain them via the ``keep_date_col`` keyword:

.. ipython:: python

   df = pd.read_csv('tmp.csv', header=None, parse_dates=[[1, 2], [1, 3]],
                    keep_date_col=True)
   df

Note that if you wish to combine multiple columns into a single date column, a
nested list must be used. In other words, ``parse_dates=[1, 2]`` indicates that
the second and third columns should each be parsed as separate date columns
while ``parse_dates=[[1, 2]]`` means the two columns should be parsed into a
single column.

You can also use a dict to specify custom name columns:

.. ipython:: python

   date_spec = {'nominal': [1, 2], 'actual': [1, 3]}
   df = pd.read_csv('tmp.csv', header=None, parse_dates=date_spec)
   df

It is important to remember that if multiple text columns are to be parsed into
a single date column, then a new column is prepended to the data. The `index_col`
specification is based off of this new set of columns rather than the original
data columns:


.. ipython:: python

   date_spec = {'nominal': [1, 2], 'actual': [1, 3]}
   df = pd.read_csv('tmp.csv', header=None, parse_dates=date_spec,
                    index_col=0) #index is the nominal column
   df

.. note::
   read_csv has a fast_path for parsing datetime strings in iso8601 format,
   e.g "2000-01-01T00:01:02+00:00" and similar variations. If you can arrange
   for your data to store datetimes in this format, load times will be
   significantly faster, ~20x has been observed.


.. note::

   When passing a dict as the `parse_dates` argument, the order of
   the columns prepended is not guaranteed, because `dict` objects do not impose
   an ordering on their keys. On Python 2.7+ you may use `collections.OrderedDict`
   instead of a regular `dict` if this matters to you. Because of this, when using a
   dict for 'parse_dates' in conjunction with the `index_col` argument, it's best to
   specify `index_col` as a column label rather then as an index on the resulting frame.


Date Parsing Functions
++++++++++++++++++++++

Finally, the parser allows you to specify a custom ``date_parser`` function to
take full advantage of the flexibility of the date parsing API:

.. ipython:: python

   import pandas.io.date_converters as conv
   df = pd.read_csv('tmp.csv', header=None, parse_dates=date_spec,
                    date_parser=conv.parse_date_time)
   df

Pandas will try to call the ``date_parser`` function in three different ways. If
an exception is raised, the next one is tried:

1. ``date_parser`` is first called with one or more arrays as arguments,
   as defined using `parse_dates` (e.g., ``date_parser(['2013', '2013'], ['1', '2'])``)

2. If #1 fails, ``date_parser`` is called with all the columns
   concatenated row-wise into a single array (e.g., ``date_parser(['2013 1', '2013 2'])``)

3. If #2 fails, ``date_parser`` is called once for every row with one or more
   string arguments from the columns indicated with `parse_dates`
   (e.g., ``date_parser('2013', '1')`` for the first row, ``date_parser('2013', '2')``
   for the second, etc.)

Note that performance-wise, you should try these methods of parsing dates in order:

1. Try to infer the format using ``infer_datetime_format=True`` (see section below)

2. If you know the format, use ``pd.to_datetime()``:
   ``date_parser=lambda x: pd.to_datetime(x, format=...)``

3. If you have a really non-standard format, use a custom ``date_parser`` function.
   For optimal performance, this should be vectorized, i.e., it should accept arrays
   as arguments.

You can explore the date parsing functionality in ``date_converters.py`` and
add your own. We would love to turn this module into a community supported set
of date/time parsers. To get you started, ``date_converters.py`` contains
functions to parse dual date and time columns, year/month/day columns,
and year/month/day/hour/minute/second columns. It also contains a
``generic_parser`` function so you can curry it with a function that deals with
a single date rather than the entire array.

.. ipython:: python
   :suppress:

   os.remove('tmp.csv')

.. _io.dayfirst:


Inferring Datetime Format
+++++++++++++++++++++++++

If you have ``parse_dates`` enabled for some or all of your columns, and your
datetime strings are all formatted the same way, you may get a large speed
up by setting ``infer_datetime_format=True``.  If set, pandas will attempt
to guess the format of your datetime strings, and then use a faster means
of parsing the strings.  5-10x parsing speeds have been observed.  pandas
will fallback to the usual parsing if either the format cannot be guessed
or the format that was guessed cannot properly parse the entire column
of strings.  So in general, ``infer_datetime_format`` should not have any
negative consequences if enabled.

Here are some examples of datetime strings that can be guessed (All
representing December 30th, 2011 at 00:00:00)

- "20111230"
- "2011/12/30"
- "20111230 00:00:00"
- "12/30/2011 00:00:00"
- "30/Dec/2011 00:00:00"
- "30/December/2011 00:00:00"

``infer_datetime_format`` is sensitive to ``dayfirst``.  With
``dayfirst=True``, it will guess "01/12/2011" to be December 1st. With
``dayfirst=False`` (default) it will guess "01/12/2011" to be January 12th.

.. ipython:: python

   # Try to infer the format for the index column
   df = pd.read_csv('foo.csv', index_col=0, parse_dates=True,
                    infer_datetime_format=True)
   df

.. ipython:: python
   :suppress:

   os.remove('foo.csv')

International Date Formats
++++++++++++++++++++++++++

While US date formats tend to be MM/DD/YYYY, many international formats use
DD/MM/YYYY instead. For convenience, a ``dayfirst`` keyword is provided:

.. ipython:: python
   :suppress:

   data = "date,value,cat\n1/6/2000,5,a\n2/6/2000,10,b\n3/6/2000,15,c"
   with open('tmp.csv', 'w') as fh:
        fh.write(data)

.. ipython:: python

   print(open('tmp.csv').read())

   pd.read_csv('tmp.csv', parse_dates=[0])
   pd.read_csv('tmp.csv', dayfirst=True, parse_dates=[0])

.. _io.float_precision:

Specifying method for floating-point conversion
'''''''''''''''''''''''''''''''''''''''''''''''

The parameter ``float_precision`` can be specified in order to use
a specific floating-point converter during parsing with the C engine.
The options are the ordinary converter, the high-precision converter, and
the round-trip converter (which is guaranteed to round-trip values after
writing to a file). For example:

.. ipython:: python

   val = '0.3066101993807095471566981359501369297504425048828125'
   data = 'a,b,c\n1,2,{0}'.format(val)
   abs(pd.read_csv(StringIO(data), engine='c', float_precision=None)['c'][0] - float(val))
   abs(pd.read_csv(StringIO(data), engine='c', float_precision='high')['c'][0] - float(val))
   abs(pd.read_csv(StringIO(data), engine='c', float_precision='round_trip')['c'][0] - float(val))


.. _io.thousands:

Thousand Separators
'''''''''''''''''''

For large numbers that have been written with a thousands separator, you can
set the ``thousands`` keyword to a string of length 1 so that integers will be parsed
correctly:

.. ipython:: python
   :suppress:

   data =  ("ID|level|category\n"
            "Patient1|123,000|x\n"
            "Patient2|23,000|y\n"
            "Patient3|1,234,018|z")

   with open('tmp.csv', 'w') as fh:
       fh.write(data)

By default, numbers with a thousands separator will be parsed as strings

.. ipython:: python

    print(open('tmp.csv').read())
    df = pd.read_csv('tmp.csv', sep='|')
    df

    df.level.dtype

The ``thousands`` keyword allows integers to be parsed correctly

.. ipython:: python

    print(open('tmp.csv').read())
    df = pd.read_csv('tmp.csv', sep='|', thousands=',')
    df

    df.level.dtype

.. ipython:: python
   :suppress:

   os.remove('tmp.csv')

.. _io.na_values:

NA Values
'''''''''

To control which values are parsed as missing values (which are signified by ``NaN``), specifiy a
string in ``na_values``. If you specify a list of strings, then all values in
it are considered to be missing values. If you specify a number (a ``float``, like ``5.0`` or an ``integer`` like ``5``),
the corresponding equivalent values will also imply a missing value (in this case effectively
``[5.0,5]`` are recognized as ``NaN``.

To completely override the default values that are recognized as missing, specify ``keep_default_na=False``.
The default ``NaN`` recognized values are ``['-1.#IND', '1.#QNAN', '1.#IND', '-1.#QNAN', '#N/A','N/A', 'NA',
'#NA', 'NULL', 'NaN', '-NaN', 'nan', '-nan']``. Although a 0-length string
``''`` is not included in the default ``NaN`` values list, it is still treated
as a missing value.

.. code-block:: python

   read_csv(path, na_values=[5])

the default values, in addition to ``5`` , ``5.0`` when interpreted as numbers are recognized as ``NaN``

.. code-block:: python

   read_csv(path, keep_default_na=False, na_values=[""])

only an empty field will be ``NaN``

.. code-block:: python

   read_csv(path, keep_default_na=False, na_values=["NA", "0"])

only ``NA`` and ``0`` as strings are ``NaN``

.. code-block:: python

   read_csv(path, na_values=["Nope"])

the default values, in addition to the string ``"Nope"`` are recognized as ``NaN``

.. _io.infinity:

Infinity
''''''''

``inf`` like values will be parsed as ``np.inf`` (positive infinity), and ``-inf`` as ``-np.inf`` (negative infinity).
These will ignore the case of the value, meaning ``Inf``, will also be parsed as ``np.inf``.


Returning Series
''''''''''''''''

Using the ``squeeze`` keyword, the parser will return output with a single column
as a ``Series``:

.. ipython:: python
   :suppress:

   data =  ("level\n"
            "Patient1,123000\n"
            "Patient2,23000\n"
            "Patient3,1234018")

   with open('tmp.csv', 'w') as fh:
       fh.write(data)

.. ipython:: python

   print(open('tmp.csv').read())

   output =  pd.read_csv('tmp.csv', squeeze=True)
   output

   type(output)

.. ipython:: python
   :suppress:

   os.remove('tmp.csv')

.. _io.boolean:

Boolean values
''''''''''''''

The common values ``True``, ``False``, ``TRUE``, and ``FALSE`` are all
recognized as boolean. Sometime you would want to recognize some other values
as being boolean. To do this use the ``true_values`` and ``false_values``
options:

.. ipython:: python

    data= 'a,b,c\n1,Yes,2\n3,No,4'
    print(data)
    pd.read_csv(StringIO(data))
    pd.read_csv(StringIO(data), true_values=['Yes'], false_values=['No'])

.. _io.bad_lines:

Handling "bad" lines
''''''''''''''''''''

Some files may have malformed lines with too few fields or too many. Lines with
too few fields will have NA values filled in the trailing fields. Lines with
too many will cause an error by default:

.. ipython:: python
   :suppress:

    data = 'a,b,c\n1,2,3\n4,5,6,7\n8,9,10'

.. code-block:: ipython

    In [27]: data = 'a,b,c\n1,2,3\n4,5,6,7\n8,9,10'

    In [28]: pd.read_csv(StringIO(data))
    ---------------------------------------------------------------------------
    CParserError                              Traceback (most recent call last)
    CParserError: Error tokenizing data. C error: Expected 3 fields in line 3, saw 4

You can elect to skip bad lines:

.. code-block:: ipython

    In [29]: pd.read_csv(StringIO(data), error_bad_lines=False)
    Skipping line 3: expected 3 fields, saw 4

    Out[29]:
       a  b   c
    0  1  2   3
    1  8  9  10

.. _io.quoting:

Quoting and Escape Characters
'''''''''''''''''''''''''''''

Quotes (and other escape characters) in embedded fields can be handled in any
number of ways. One way is to use backslashes; to properly parse this data, you
should pass the ``escapechar`` option:

.. ipython:: python

   data = 'a,b\n"hello, \\"Bob\\", nice to see you",5'
   print(data)
   pd.read_csv(StringIO(data), escapechar='\\')

.. _io.fwf:

Files with Fixed Width Columns
''''''''''''''''''''''''''''''

While ``read_csv`` reads delimited data, the :func:`read_fwf` function works
with data files that have known and fixed column widths. The function parameters
to ``read_fwf`` are largely the same as `read_csv` with two extra parameters:

  - ``colspecs``: A list of pairs (tuples) giving the extents of the
    fixed-width fields of each line as half-open intervals (i.e.,  [from, to[ ).
    String value 'infer' can be used to instruct the parser to try detecting
    the column specifications from the first 100 rows of the data. Default
    behaviour, if not specified, is to infer.
  - ``widths``: A list of field widths which can be used instead of 'colspecs'
    if the intervals are contiguous.

.. ipython:: python
   :suppress:

   f = open('bar.csv', 'w')
   data1 = ("id8141    360.242940   149.910199   11950.7\n"
            "id1594    444.953632   166.985655   11788.4\n"
            "id1849    364.136849   183.628767   11806.2\n"
            "id1230    413.836124   184.375703   11916.8\n"
            "id1948    502.953953   173.237159   12468.3")
   f.write(data1)
   f.close()

Consider a typical fixed-width data file:

.. ipython:: python

   print(open('bar.csv').read())

In order to parse this file into a DataFrame, we simply need to supply the
column specifications to the `read_fwf` function along with the file name:

.. ipython:: python

   #Column specifications are a list of half-intervals
   colspecs = [(0, 6), (8, 20), (21, 33), (34, 43)]
   df = pd.read_fwf('bar.csv', colspecs=colspecs, header=None, index_col=0)
   df

Note how the parser automatically picks column names X.<column number> when
``header=None`` argument is specified. Alternatively, you can supply just the
column widths for contiguous columns:

.. ipython:: python

   #Widths are a list of integers
   widths = [6, 14, 13, 10]
   df = pd.read_fwf('bar.csv', widths=widths, header=None)
   df

The parser will take care of extra white spaces around the columns
so it's ok to have extra separation between the columns in the file.

.. versionadded:: 0.13.0

By default, ``read_fwf`` will try to infer the file's ``colspecs`` by using the
first 100 rows of the file. It can do it only in cases when the columns are
aligned and correctly separated by the provided ``delimiter`` (default delimiter
is whitespace).

.. ipython:: python

   df = pd.read_fwf('bar.csv', header=None, index_col=0)
   df

.. ipython:: python
   :suppress:

   os.remove('bar.csv')

Indexes
'''''''

Files with an "implicit" index column
+++++++++++++++++++++++++++++++++++++

.. ipython:: python
   :suppress:

   f = open('foo.csv', 'w')
   f.write('A,B,C\n20090101,a,1,2\n20090102,b,3,4\n20090103,c,4,5')
   f.close()

Consider a file with one less entry in the header than the number of data
column:

.. ipython:: python

   print(open('foo.csv').read())

In this special case, ``read_csv`` assumes that the first column is to be used
as the index of the DataFrame:

.. ipython:: python

   pd.read_csv('foo.csv')

Note that the dates weren't automatically parsed. In that case you would need
to do as before:

.. ipython:: python

   df = pd.read_csv('foo.csv', parse_dates=True)
   df.index

.. ipython:: python
   :suppress:

   os.remove('foo.csv')


Reading an index with a ``MultiIndex``
++++++++++++++++++++++++++++++++++++++

.. _io.csv_multiindex:

Suppose you have data indexed by two columns:

.. ipython:: python

   print(open('data/mindex_ex.csv').read())

The ``index_col`` argument to ``read_csv`` and ``read_table`` can take a list of
column numbers to turn multiple columns into a ``MultiIndex`` for the index of the
returned object:

.. ipython:: python

   df = pd.read_csv("data/mindex_ex.csv", index_col=[0,1])
   df
   df.ix[1978]

.. _io.multi_index_columns:

Reading columns with a ``MultiIndex``
+++++++++++++++++++++++++++++++++++++

By specifying list of row locations for the ``header`` argument, you
can read in a ``MultiIndex`` for the columns. Specifying non-consecutive
rows will skip the intervening rows. In order to have the pre-0.13 behavior
of tupleizing columns, specify ``tupleize_cols=True``.

.. ipython:: python

   from pandas.util.testing import makeCustomDataframe as mkdf
   df = mkdf(5,3,r_idx_nlevels=2,c_idx_nlevels=4)
   df.to_csv('mi.csv')
   print(open('mi.csv').read())
   pd.read_csv('mi.csv',header=[0,1,2,3],index_col=[0,1])

Starting in 0.13.0, ``read_csv`` will be able to interpret a more common format
of multi-columns indices.

.. ipython:: python
   :suppress:

   data = ",a,a,a,b,c,c\n,q,r,s,t,u,v\none,1,2,3,4,5,6\ntwo,7,8,9,10,11,12"
   fh = open('mi2.csv','w')
   fh.write(data)
   fh.close()

.. ipython:: python

   print(open('mi2.csv').read())
   pd.read_csv('mi2.csv',header=[0,1],index_col=0)

Note: If an ``index_col`` is not specified (e.g. you don't have an index, or wrote it
with ``df.to_csv(..., index=False``), then any ``names`` on the columns index will be *lost*.

.. ipython:: python
   :suppress:

   import os
   os.remove('mi.csv')
   os.remove('mi2.csv')

.. _io.sniff:

Automatically "sniffing" the delimiter
''''''''''''''''''''''''''''''''''''''

``read_csv`` is capable of inferring delimited (not necessarily
comma-separated) files, as pandas uses the :class:`python:csv.Sniffer`
class of the csv module. For this, you have to specify ``sep=None``.

.. ipython:: python
   :suppress:

   df = pd.DataFrame(np.random.randn(10, 4))
   df.to_csv('tmp.sv', sep='|')
   df.to_csv('tmp2.sv', sep=':')

.. ipython:: python

    print(open('tmp2.sv').read())
    pd.read_csv('tmp2.sv', sep=None, engine='python')

.. _io.chunking:

Iterating through files chunk by chunk
''''''''''''''''''''''''''''''''''''''

Suppose you wish to iterate through a (potentially very large) file lazily
rather than reading the entire file into memory, such as the following:


.. ipython:: python

   print(open('tmp.sv').read())
   table = pd.read_table('tmp.sv', sep='|')
   table


By specifying a ``chunksize`` to ``read_csv`` or ``read_table``, the return
value will be an iterable object of type ``TextFileReader``:

.. ipython:: python

   reader = pd.read_table('tmp.sv', sep='|', chunksize=4)
   reader

   for chunk in reader:
       print(chunk)


Specifying ``iterator=True`` will also return the ``TextFileReader`` object:

.. ipython:: python

   reader = pd.read_table('tmp.sv', sep='|', iterator=True)
   reader.get_chunk(5)

.. ipython:: python
   :suppress:

   os.remove('tmp.sv')
   os.remove('tmp2.sv')

Specifying the parser engine
''''''''''''''''''''''''''''

Under the hood pandas uses a fast and efficient parser implemented in C as well
as a python implementation which is currently more feature-complete. Where
possible pandas uses the C parser (specified as ``engine='c'``), but may fall
back to python if C-unsupported options are specified. Currently, C-unsupported
options include:

- ``sep`` other than a single character (e.g. regex separators)
- ``skipfooter``
- ``sep=None`` with ``delim_whitespace=False``

Specifying any of the above options will produce a ``ParserWarning`` unless the
python engine is selected explicitly using ``engine='python'``.

Writing out Data
''''''''''''''''

.. _io.store_in_csv:

Writing to CSV format
+++++++++++++++++++++

The Series and DataFrame objects have an instance method ``to_csv`` which
allows storing the contents of the object as a comma-separated-values file. The
function takes a number of arguments. Only the first is required.

  - ``path_or_buf``: A string path to the file to write or a StringIO
  - ``sep`` : Field delimiter for the output file (default ",")
  - ``na_rep``: A string representation of a missing value (default '')
  - ``float_format``: Format string for floating point numbers
  - ``cols``: Columns to write (default None)
  - ``header``: Whether to write out the column names (default True)
  - ``index``: whether to write row (index) names (default True)
  - ``index_label``: Column label(s) for index column(s) if desired. If None
    (default), and `header` and `index` are True, then the index names are
    used. (A sequence should be given if the DataFrame uses MultiIndex).
  - ``mode`` : Python write mode, default 'w'
  - ``encoding``: a string representing the encoding to use if the contents are
    non-ASCII, for python versions prior to 3
  - ``line_terminator``: Character sequence denoting line end (default '\\n')
  - ``quoting``: Set quoting rules as in csv module (default csv.QUOTE_MINIMAL)
  - ``quotechar``: Character used to quote fields (default '"')
  - ``doublequote``: Control quoting of ``quotechar`` in fields (default True)
  - ``escapechar``: Character used to escape ``sep`` and ``quotechar`` when
    appropriate (default None)
  - ``chunksize``: Number of rows to write at a time
  - ``tupleize_cols``: If False (default), write as a list of tuples, otherwise
    write in an expanded line format suitable for ``read_csv``
  - ``date_format``: Format string for datetime objects

Writing a formatted string
++++++++++++++++++++++++++

.. _io.formatting:

The DataFrame object has an instance method ``to_string`` which allows control
over the string representation of the object. All arguments are optional:

  - ``buf`` default None, for example a StringIO object
  - ``columns`` default None, which columns to write
  - ``col_space`` default None, minimum width of each column.
  - ``na_rep`` default ``NaN``, representation of NA value
  - ``formatters`` default None, a dictionary (by column) of functions each of
    which takes a single argument and returns a formatted string
  - ``float_format`` default None, a function which takes a single (float)
    argument and returns a formatted string; to be applied to floats in the
    DataFrame.
  - ``sparsify`` default True, set to False for a DataFrame with a hierarchical
    index to print every multiindex key at each row.
  - ``index_names`` default True, will print the names of the indices
  - ``index`` default True, will print the index (ie, row labels)
  - ``header`` default True, will print the column labels
  - ``justify`` default ``left``, will print column headers left- or
    right-justified

The Series object also has a ``to_string`` method, but with only the ``buf``,
``na_rep``, ``float_format`` arguments. There is also a ``length`` argument
which, if set to ``True``, will additionally output the length of the Series.

.. _io.json:

JSON
----

Read and write ``JSON`` format files and strings.

.. _io.json_writer:

Writing JSON
''''''''''''

A ``Series`` or ``DataFrame`` can be converted to a valid JSON string. Use ``to_json``
with optional parameters:

- ``path_or_buf`` : the pathname or buffer to write the output
  This can be ``None`` in which case a JSON string is returned
- ``orient`` :

  Series :
      - default is ``index``
      - allowed values are {``split``, ``records``, ``index``}

  DataFrame
      - default is ``columns``
      - allowed values are {``split``, ``records``, ``index``, ``columns``, ``values``}

  The format of the JSON string

  .. csv-table::
     :widths: 20, 150
     :delim: ;

     ``split``; dict like {index -> [index], columns -> [columns], data -> [values]}
     ``records``; list like [{column -> value}, ... , {column -> value}]
     ``index``; dict like {index -> {column -> value}}
     ``columns``; dict like {column -> {index -> value}}
     ``values``; just the values array

- ``date_format`` : string, type of date conversion, 'epoch' for timestamp, 'iso' for ISO8601.
- ``double_precision`` : The number of decimal places to use when encoding floating point values, default 10.
- ``force_ascii`` : force encoded string to be ASCII, default True.
- ``date_unit`` : The time unit to encode to, governs timestamp and ISO8601 precision. One of 's', 'ms', 'us' or 'ns' for seconds, milliseconds, microseconds and nanoseconds respectively. Default 'ms'.
- ``default_handler`` : The handler to call if an object cannot otherwise be converted to a suitable format for JSON. Takes a single argument, which is the object to convert, and returns a serializable object.
- ``lines`` : If ``records`` orient, then will write each record per line as json.

Note ``NaN``'s, ``NaT``'s and ``None`` will be converted to ``null`` and ``datetime`` objects will be converted based on the ``date_format`` and ``date_unit`` parameters.

.. ipython:: python

   dfj = pd.DataFrame(randn(5, 2), columns=list('AB'))
   json = dfj.to_json()
   json

Orient Options
++++++++++++++

There are a number of different options for the format of the resulting JSON
file / string. Consider the following DataFrame and Series:

.. ipython:: python

  dfjo = pd.DataFrame(dict(A=range(1, 4), B=range(4, 7), C=range(7, 10)),
                      columns=list('ABC'), index=list('xyz'))
  dfjo
  sjo = pd.Series(dict(x=15, y=16, z=17), name='D')
  sjo

**Column oriented** (the default for ``DataFrame``) serializes the data as
nested JSON objects with column labels acting as the primary index:

.. ipython:: python

  dfjo.to_json(orient="columns")
  # Not available for Series

**Index oriented** (the default for ``Series``) similar to column oriented
but the index labels are now primary:

.. ipython:: python

  dfjo.to_json(orient="index")
  sjo.to_json(orient="index")

**Record oriented** serializes the data to a JSON array of column -> value records,
index labels are not included. This is useful for passing DataFrame data to plotting
libraries, for example the JavaScript library d3.js:

.. ipython:: python

  dfjo.to_json(orient="records")
  sjo.to_json(orient="records")

**Value oriented** is a bare-bones option which serializes to nested JSON arrays of
values only, column and index labels are not included:

.. ipython:: python

  dfjo.to_json(orient="values")
  # Not available for Series

**Split oriented** serializes to a JSON object containing separate entries for
values, index and columns. Name is also included for ``Series``:

.. ipython:: python

  dfjo.to_json(orient="split")
  sjo.to_json(orient="split")

.. note::

  Any orient option that encodes to a JSON object will not preserve the ordering of
  index and column labels during round-trip serialization. If you wish to preserve
  label ordering use the `split` option as it uses ordered containers.

Date Handling
+++++++++++++

Writing in ISO date format

.. ipython:: python

   dfd = pd.DataFrame(randn(5, 2), columns=list('AB'))
   dfd['date'] = pd.Timestamp('20130101')
   dfd = dfd.sort_index(1, ascending=False)
   json = dfd.to_json(date_format='iso')
   json

Writing in ISO date format, with microseconds

.. ipython:: python

   json = dfd.to_json(date_format='iso', date_unit='us')
   json

Epoch timestamps, in seconds

.. ipython:: python

   json = dfd.to_json(date_format='epoch', date_unit='s')
   json

Writing to a file, with a date index and a date column

.. ipython:: python

   dfj2 = dfj.copy()
   dfj2['date'] = pd.Timestamp('20130101')
   dfj2['ints'] = list(range(5))
   dfj2['bools'] = True
   dfj2.index = pd.date_range('20130101', periods=5)
   dfj2.to_json('test.json')
   open('test.json').read()

Fallback Behavior
+++++++++++++++++

If the JSON serializer cannot handle the container contents directly it will fallback in the following manner:

- if the dtype is unsupported (e.g. ``np.complex``) then the ``default_handler``, if provided, will be called
  for each value, otherwise an exception is raised.

- if an object is unsupported it will attempt the following:


  * check if the object has defined a ``toDict`` method and call it.
    A ``toDict`` method should return a ``dict`` which will then be JSON serialized.

  * invoke the ``default_handler`` if one was provided.

  * convert the object to a ``dict`` by traversing its contents. However this will often fail
    with an ``OverflowError`` or give unexpected results.

In general the best approach for unsupported objects or dtypes is to provide a ``default_handler``.
For example:

.. code-block:: python

  DataFrame([1.0, 2.0, complex(1.0, 2.0)]).to_json()  # raises

  RuntimeError: Unhandled numpy dtype 15

can be dealt with by specifying a simple ``default_handler``:

.. ipython:: python

   pd.DataFrame([1.0, 2.0, complex(1.0, 2.0)]).to_json(default_handler=str)

.. _io.json_reader:

Reading JSON
''''''''''''

Reading a JSON string to pandas object can take a number of parameters.
The parser will try to parse a ``DataFrame`` if ``typ`` is not supplied or
is ``None``. To explicitly force ``Series`` parsing, pass ``typ=series``

- ``filepath_or_buffer`` : a **VALID** JSON string or file handle / StringIO. The string could be
  a URL. Valid URL schemes include http, ftp, S3, and file. For file URLs, a host
  is expected. For instance, a local file could be
  file ://localhost/path/to/table.json
- ``typ``    : type of object to recover (series or frame), default 'frame'
- ``orient`` :

  Series :
      - default is ``index``
      - allowed values are {``split``, ``records``, ``index``}

  DataFrame
      - default is ``columns``
      - allowed values are {``split``, ``records``, ``index``, ``columns``, ``values``}

  The format of the JSON string

  .. csv-table::
     :widths: 20, 150
     :delim: ;

     ``split``; dict like {index -> [index], columns -> [columns], data -> [values]}
     ``records``; list like [{column -> value}, ... , {column -> value}]
     ``index``; dict like {index -> {column -> value}}
     ``columns``; dict like {column -> {index -> value}}
     ``values``; just the values array

- ``dtype`` : if True, infer dtypes, if a dict of column to dtype, then use those, if False, then don't infer dtypes at all, default is True, apply only to the data
- ``convert_axes`` : boolean, try to convert the axes to the proper dtypes, default is True
- ``convert_dates`` : a list of columns to parse for dates; If True, then try to parse date-like columns, default is True
- ``keep_default_dates`` : boolean, default True. If parsing dates, then parse the default date-like columns
- ``numpy`` : direct decoding to numpy arrays. default is False;
  Supports numeric data only, although labels may be non-numeric. Also note that the JSON ordering **MUST** be the same for each term if ``numpy=True``
- ``precise_float`` : boolean, default ``False``. Set to enable usage of higher precision (strtod) function when decoding string to double values. Default (``False``) is to use fast but less precise builtin functionality
- ``date_unit`` : string, the timestamp unit to detect if converting dates. Default
  None. By default the timestamp precision will be detected, if this is not desired
  then pass one of 's', 'ms', 'us' or 'ns' to force timestamp precision to
  seconds, milliseconds, microseconds or nanoseconds respectively.
- ``lines`` : reads file as one json object per line.
- ``encoding`` : The encoding to use to decode py3 bytes.

The parser will raise one of ``ValueError/TypeError/AssertionError`` if the JSON is not parseable.

If a non-default ``orient`` was used when encoding to JSON be sure to pass the same
option here so that decoding produces sensible results, see `Orient Options`_ for an
overview.

Data Conversion
+++++++++++++++

The default of ``convert_axes=True``, ``dtype=True``, and ``convert_dates=True`` will try to parse the axes, and all of the data
into appropriate types, including dates. If you need to override specific dtypes, pass a dict to ``dtype``. ``convert_axes`` should only
be set to ``False`` if you need to preserve string-like numbers (e.g. '1', '2') in an axes.

.. note::

  Large integer values may be converted to dates if ``convert_dates=True`` and the data and / or column labels appear 'date-like'. The exact threshold depends on the ``date_unit`` specified. 'date-like' means that the column label meets one of the following criteria:

     * it ends with ``'_at'``
     * it ends with ``'_time'``
     * it begins with ``'timestamp'``
     * it is ``'modified'``
     * it is ``'date'``

.. warning::

   When reading JSON data, automatic coercing into dtypes has some quirks:

     * an index can be reconstructed in a different order from serialization, that is, the returned order is not guaranteed to be the same as before serialization
     * a column that was ``float`` data will be converted to ``integer`` if it can be done safely, e.g. a column of ``1.``
     * bool columns will be converted to ``integer`` on reconstruction

   Thus there are times where you may want to specify specific dtypes via the ``dtype`` keyword argument.

Reading from a JSON string:

.. ipython:: python

   pd.read_json(json)

Reading from a file:

.. ipython:: python

   pd.read_json('test.json')

Don't convert any data (but still convert axes and dates):

.. ipython:: python

   pd.read_json('test.json', dtype=object).dtypes

Specify dtypes for conversion:

.. ipython:: python

   pd.read_json('test.json', dtype={'A' : 'float32', 'bools' : 'int8'}).dtypes

Preserve string indices:

.. ipython:: python

   si = pd.DataFrame(np.zeros((4, 4)),
            columns=list(range(4)),
            index=[str(i) for i in range(4)])
   si
   si.index
   si.columns
   json = si.to_json()

   sij = pd.read_json(json, convert_axes=False)
   sij
   sij.index
   sij.columns

Dates written in nanoseconds need to be read back in nanoseconds:

.. ipython:: python

   json = dfj2.to_json(date_unit='ns')

   # Try to parse timestamps as millseconds -> Won't Work
   dfju = pd.read_json(json, date_unit='ms')
   dfju

   # Let pandas detect the correct precision
   dfju = pd.read_json(json)
   dfju

   # Or specify that all timestamps are in nanoseconds
   dfju = pd.read_json(json, date_unit='ns')
   dfju

The Numpy Parameter
+++++++++++++++++++

.. note::
  This supports numeric data only. Index and columns labels may be non-numeric, e.g. strings, dates etc.

If ``numpy=True`` is passed to ``read_json`` an attempt will be made to sniff
an appropriate dtype during deserialization and to subsequently decode directly
to numpy arrays, bypassing the need for intermediate Python objects.

This can provide speedups if you are deserialising a large amount of numeric
data:

.. ipython:: python

   randfloats = np.random.uniform(-100, 1000, 10000)
   randfloats.shape = (1000, 10)
   dffloats = pd.DataFrame(randfloats, columns=list('ABCDEFGHIJ'))

   jsonfloats = dffloats.to_json()

.. ipython:: python

   timeit pd.read_json(jsonfloats)

.. ipython:: python

   timeit pd.read_json(jsonfloats, numpy=True)

The speedup is less noticeable for smaller datasets:

.. ipython:: python

   jsonfloats = dffloats.head(100).to_json()

.. ipython:: python

   timeit pd.read_json(jsonfloats)

.. ipython:: python

   timeit pd.read_json(jsonfloats, numpy=True)

.. warning::

   Direct numpy decoding makes a number of assumptions and may fail or produce
   unexpected output if these assumptions are not satisfied:

    - data is numeric.

    - data is uniform. The dtype is sniffed from the first value decoded.
      A ``ValueError`` may be raised, or incorrect output may be produced
      if this condition is not satisfied.

    - labels are ordered. Labels are only read from the first container, it is assumed
      that each subsequent row / column has been encoded in the same order. This should be satisfied if the
      data was encoded using ``to_json`` but may not be the case if the JSON
      is from another source.

.. ipython:: python
   :suppress:

   import os
   os.remove('test.json')

.. _io.json_normalize:

Normalization
'''''''''''''

.. versionadded:: 0.13.0

pandas provides a utility function to take a dict or list of dicts and *normalize* this semi-structured data
into a flat table.

.. ipython:: python

   from pandas.io.json import json_normalize
   data = [{'state': 'Florida',
             'shortname': 'FL',
             'info': {
                  'governor': 'Rick Scott'
             },
             'counties': [{'name': 'Dade', 'population': 12345},
                         {'name': 'Broward', 'population': 40000},
                         {'name': 'Palm Beach', 'population': 60000}]},
            {'state': 'Ohio',
             'shortname': 'OH',
             'info': {
                  'governor': 'John Kasich'
             },
             'counties': [{'name': 'Summit', 'population': 1234},
                          {'name': 'Cuyahoga', 'population': 1337}]}]

   json_normalize(data, 'counties', ['state', 'shortname', ['info', 'governor']])

.. _io.jsonl:

Line delimited json
'''''''''''''''''''

.. versionadded:: 0.19.0

pandas is able to read and write line-delimited json files that are common in data processing pipelines
using Hadoop or Spark.

.. ipython:: python

  jsonl = '''
      {"a":1,"b":2}
      {"a":3,"b":4}
  '''
  df = pd.read_json(jsonl, lines=True)
  df
  df.to_json(orient='records', lines=True)

HTML
----

.. _io.read_html:

Reading HTML Content
''''''''''''''''''''''

.. warning::

   We **highly encourage** you to read the :ref:`HTML parsing gotchas
   <html-gotchas>` regarding the issues surrounding the
   BeautifulSoup4/html5lib/lxml parsers.

.. versionadded:: 0.12.0

The top-level :func:`~pandas.io.html.read_html` function can accept an HTML
string/file/URL and will parse HTML tables into list of pandas DataFrames.
Let's look at a few examples.

.. note::

   ``read_html`` returns a ``list`` of ``DataFrame`` objects, even if there is
   only a single table contained in the HTML content

Read a URL with no options

.. ipython:: python

   url = 'http://www.fdic.gov/bank/individual/failed/banklist.html'
   dfs = pd.read_html(url)
   dfs

.. note::

   The data from the above URL changes every Monday so the resulting data above
   and the data below may be slightly different.

Read in the content of the file from the above URL and pass it to ``read_html``
as a string

.. ipython:: python
   :suppress:

   import os
   file_path = os.path.abspath(os.path.join('source', '_static', 'banklist.html'))

.. ipython:: python

   with open(file_path, 'r') as f:
       dfs = pd.read_html(f.read())
   dfs

You can even pass in an instance of ``StringIO`` if you so desire

.. ipython:: python

   with open(file_path, 'r') as f:
       sio = StringIO(f.read())

   dfs = pd.read_html(sio)
   dfs

.. note::

   The following examples are not run by the IPython evaluator due to the fact
   that having so many network-accessing functions slows down the documentation
   build. If you spot an error or an example that doesn't run, please do not
   hesitate to report it over on `pandas GitHub issues page
   <http://www.github.com/pydata/pandas/issues>`__.


Read a URL and match a table that contains specific text

.. code-block:: python

   match = 'Metcalf Bank'
   df_list = pd.read_html(url, match=match)

Specify a header row (by default ``<th>`` elements are used to form the column
index); if specified, the header row is taken from the data minus the parsed
header elements (``<th>`` elements).

.. code-block:: python

   dfs = pd.read_html(url, header=0)

Specify an index column

.. code-block:: python

   dfs = pd.read_html(url, index_col=0)

Specify a number of rows to skip

.. code-block:: python

   dfs = pd.read_html(url, skiprows=0)

Specify a number of rows to skip using a list (``xrange`` (Python 2 only) works
as well)

.. code-block:: python

   dfs = pd.read_html(url, skiprows=range(2))

Specify an HTML attribute

.. code-block:: python

   dfs1 = pd.read_html(url, attrs={'id': 'table'})
   dfs2 = pd.read_html(url, attrs={'class': 'sortable'})
   print(np.array_equal(dfs1[0], dfs2[0]))  # Should be True

Specify values that should be converted to NaN

.. code-block:: python

   dfs = pd.read_html(url, na_values=['No Acquirer'])

.. versionadded:: 0.19

Specify whether to keep the default set of NaN values

.. code-block:: python

   dfs = pd.read_html(url, keep_default_na=False)

.. versionadded:: 0.19

Specify converters for columns. This is useful for numerical text data that has
leading zeros.  By default columns that are numerical are cast to numeric
types and the leading zeros are lost.  To avoid this, we can convert these
columns to strings.

.. code-block:: python

   url_mcc = 'https://en.wikipedia.org/wiki/Mobile_country_code'
   dfs = pd.read_html(url_mcc, match='Telekom Albania', header=0, converters={'MNC':
   str})

.. versionadded:: 0.19

Use some combination of the above

.. code-block:: python

   dfs = pd.read_html(url, match='Metcalf Bank', index_col=0)

Read in pandas ``to_html`` output (with some loss of floating point precision)

.. code-block:: python

   df = pd.DataFrame(randn(2, 2))
   s = df.to_html(float_format='{0:.40g}'.format)
   dfin = pd.read_html(s, index_col=0)

The ``lxml`` backend will raise an error on a failed parse if that is the only
parser you provide (if you only have a single parser you can provide just a
string, but it is considered good practice to pass a list with one string if,
for example, the function expects a sequence of strings)

.. code-block:: python

   dfs = pd.read_html(url, 'Metcalf Bank', index_col=0, flavor=['lxml'])

or

.. code-block:: python

   dfs = pd.read_html(url, 'Metcalf Bank', index_col=0, flavor='lxml')

However, if you have bs4 and html5lib installed and pass ``None`` or ``['lxml',
'bs4']`` then the parse will most likely succeed. Note that *as soon as a parse
succeeds, the function will return*.

.. code-block:: python

   dfs = pd.read_html(url, 'Metcalf Bank', index_col=0, flavor=['lxml', 'bs4'])


.. _io.html:

Writing to HTML files
''''''''''''''''''''''

``DataFrame`` objects have an instance method ``to_html`` which renders the
contents of the ``DataFrame`` as an HTML table. The function arguments are as
in the method ``to_string`` described above.

.. note::

   Not all of the possible options for ``DataFrame.to_html`` are shown here for
   brevity's sake. See :func:`~pandas.core.frame.DataFrame.to_html` for the
   full set of options.

.. ipython:: python
   :suppress:

   def write_html(df, filename, *args, **kwargs):
       static = os.path.abspath(os.path.join('source', '_static'))
       with open(os.path.join(static, filename + '.html'), 'w') as f:
           df.to_html(f, *args, **kwargs)

.. ipython:: python

   df = pd.DataFrame(randn(2, 2))
   df
   print(df.to_html())  # raw html

.. ipython:: python
   :suppress:

   write_html(df, 'basic')

HTML:

.. raw:: html
   :file: _static/basic.html

The ``columns`` argument will limit the columns shown

.. ipython:: python

   print(df.to_html(columns=[0]))

.. ipython:: python
   :suppress:

   write_html(df, 'columns', columns=[0])

HTML:

.. raw:: html
   :file: _static/columns.html

``float_format`` takes a Python callable to control the precision of floating
point values

.. ipython:: python

   print(df.to_html(float_format='{0:.10f}'.format))

.. ipython:: python
   :suppress:

   write_html(df, 'float_format', float_format='{0:.10f}'.format)

HTML:

.. raw:: html
   :file: _static/float_format.html

``bold_rows`` will make the row labels bold by default, but you can turn that
off

.. ipython:: python

   print(df.to_html(bold_rows=False))

.. ipython:: python
   :suppress:

   write_html(df, 'nobold', bold_rows=False)

.. raw:: html
   :file: _static/nobold.html

The ``classes`` argument provides the ability to give the resulting HTML
table CSS classes. Note that these classes are *appended* to the existing
``'dataframe'`` class.

.. ipython:: python

   print(df.to_html(classes=['awesome_table_class', 'even_more_awesome_class']))

Finally, the ``escape`` argument allows you to control whether the
"<", ">" and "&" characters escaped in the resulting HTML (by default it is
``True``). So to get the HTML without escaped characters pass ``escape=False``

.. ipython:: python

   df = pd.DataFrame({'a': list('&<>'), 'b': randn(3)})


.. ipython:: python
   :suppress:

   write_html(df, 'escape')
   write_html(df, 'noescape', escape=False)

Escaped:

.. ipython:: python

   print(df.to_html())

.. raw:: html
   :file: _static/escape.html

Not escaped:

.. ipython:: python

   print(df.to_html(escape=False))

.. raw:: html
   :file: _static/noescape.html

.. note::

   Some browsers may not show a difference in the rendering of the previous two
   HTML tables.

.. _io.excel:

Excel files
-----------

The :func:`~pandas.read_excel` method can read Excel 2003 (``.xls``) and
Excel 2007+ (``.xlsx``) files using the ``xlrd`` Python
module.  The :meth:`~DataFrame.to_excel` instance method is used for
saving a ``DataFrame`` to Excel.  Generally the semantics are
similar to working with :ref:`csv<io.read_csv_table>` data.  See the :ref:`cookbook<cookbook.excel>` for some
advanced strategies

.. _io.excel_reader:

Reading Excel Files
'''''''''''''''''''

In the most basic use-case, ``read_excel`` takes a path to an Excel
file, and the ``sheetname`` indicating which sheet to parse.

.. code-block:: python

   # Returns a DataFrame
   read_excel('path_to_file.xls', sheetname='Sheet1')


.. _io.excel.excelfile_class:

``ExcelFile`` class
+++++++++++++++++++

To facilitate working with multiple sheets from the same file, the ``ExcelFile``
class can be used to wrap the file and can be be passed into ``read_excel``
There will be a performance benefit for reading multiple sheets as the file is
read into memory only once.

.. code-block:: python

   xlsx = pd.ExcelFile('path_to_file.xls)
   df = pd.read_excel(xlsx, 'Sheet1')

The ``ExcelFile`` class can also be used as a context manager.

.. code-block:: python

   with pd.ExcelFile('path_to_file.xls') as xls:
       df1 = pd.read_excel(xls, 'Sheet1')
       df2 = pd.read_excel(xls, 'Sheet2')

The ``sheet_names`` property will generate
a list of the sheet names in the file.

The primary use-case for an ``ExcelFile`` is parsing multiple sheets with
different parameters

.. code-block:: python

    data = {}
    # For when Sheet1's format differs from Sheet2
    with pd.ExcelFile('path_to_file.xls') as xls:
        data['Sheet1'] = pd.read_excel(xls, 'Sheet1', index_col=None, na_values=['NA'])
        data['Sheet2'] = pd.read_excel(xls, 'Sheet2', index_col=1)

Note that if the same parsing parameters are used for all sheets, a list
of sheet names can simply be passed to ``read_excel`` with no loss in performance.

.. code-block:: python

    # using the ExcelFile class
    data = {}
    with pd.ExcelFile('path_to_file.xls') as xls:
        data['Sheet1'] = read_excel(xls, 'Sheet1', index_col=None, na_values=['NA'])
        data['Sheet2'] = read_excel(xls, 'Sheet2', index_col=None, na_values=['NA'])

    # equivalent using the read_excel function
    data = read_excel('path_to_file.xls', ['Sheet1', 'Sheet2'], index_col=None, na_values=['NA'])

.. versionadded:: 0.12

``ExcelFile`` has been moved to the top level namespace.

.. versionadded:: 0.17

``read_excel`` can take an ``ExcelFile`` object as input


.. _io.excel.specifying_sheets:

Specifying Sheets
+++++++++++++++++

.. note :: The second argument is ``sheetname``, not to be confused with ``ExcelFile.sheet_names``

.. note :: An ExcelFile's attribute ``sheet_names`` provides access to a list of sheets.

- The arguments ``sheetname`` allows specifying the sheet or sheets to read.
- The default value for ``sheetname`` is 0, indicating to read the first sheet
- Pass a string to refer to the name of a particular sheet in the workbook.
- Pass an integer to refer to the index of a sheet. Indices follow Python
  convention, beginning at 0.
- Pass a list of either strings or integers, to return a dictionary of specified sheets.
- Pass a ``None`` to return a dictionary of all available sheets.

.. code-block:: python

   # Returns a DataFrame
   read_excel('path_to_file.xls', 'Sheet1', index_col=None, na_values=['NA'])

Using the sheet index:

.. code-block:: python

   # Returns a DataFrame
   read_excel('path_to_file.xls', 0, index_col=None, na_values=['NA'])

Using all default values:

.. code-block:: python

   # Returns a DataFrame
   read_excel('path_to_file.xls')

Using None to get all sheets:

.. code-block:: python

   # Returns a dictionary of DataFrames
   read_excel('path_to_file.xls',sheetname=None)

Using a list to get multiple sheets:

.. code-block:: python

   # Returns the 1st and 4th sheet, as a dictionary of DataFrames.
   read_excel('path_to_file.xls',sheetname=['Sheet1',3])

.. versionadded:: 0.16

``read_excel`` can read more than one sheet, by setting ``sheetname`` to either
a list of sheet names, a list of sheet positions, or ``None`` to read all sheets.

.. versionadded:: 0.13

Sheets can be specified by sheet index or sheet name, using an integer or string,
respectively.

.. _io.excel.reading_multiindex:

Reading a ``MultiIndex``
++++++++++++++++++++++++

.. versionadded:: 0.17

``read_excel`` can read a ``MultiIndex`` index, by passing a list of columns to ``index_col``
and a ``MultiIndex`` column by passing a list of rows to ``header``.  If either the ``index``
or ``columns`` have serialized level names those will be read in as well by specifying
the rows/columns that make up the levels.

For example, to read in a ``MultiIndex`` index without names:

.. ipython:: python

   df = pd.DataFrame({'a':[1,2,3,4], 'b':[5,6,7,8]},
                     index=pd.MultiIndex.from_product([['a','b'],['c','d']]))
   df.to_excel('path_to_file.xlsx')
   df = pd.read_excel('path_to_file.xlsx', index_col=[0,1])
   df

If the index has level names, they will parsed as well, using the same
parameters.

.. ipython:: python

   df.index = df.index.set_names(['lvl1', 'lvl2'])
   df.to_excel('path_to_file.xlsx')
   df = pd.read_excel('path_to_file.xlsx', index_col=[0,1])
   df


If the source file has both ``MultiIndex`` index and columns, lists specifying each
should be passed to ``index_col`` and ``header``

.. ipython:: python

   df.columns = pd.MultiIndex.from_product([['a'],['b', 'd']], names=['c1', 'c2'])
   df.to_excel('path_to_file.xlsx')
   df = pd.read_excel('path_to_file.xlsx',
                       index_col=[0,1], header=[0,1])
   df

.. ipython:: python
   :suppress:

   import os
   os.remove('path_to_file.xlsx')

.. warning::

   Excel files saved in version 0.16.2 or prior that had index names will still able to be read in,
   but the ``has_index_names`` argument must specified to ``True``.


Parsing Specific Columns
++++++++++++++++++++++++

It is often the case that users will insert columns to do temporary computations
in Excel and you may not want to read in those columns. `read_excel` takes
a `parse_cols` keyword to allow you to specify a subset of columns to parse.

If `parse_cols` is an integer, then it is assumed to indicate the last column
to be parsed.

.. code-block:: python

   read_excel('path_to_file.xls', 'Sheet1', parse_cols=2)

If `parse_cols` is a list of integers, then it is assumed to be the file column
indices to be parsed.

.. code-block:: python

   read_excel('path_to_file.xls', 'Sheet1', parse_cols=[0, 2, 3])

Cell Converters
+++++++++++++++

It is possible to transform the contents of Excel cells via the `converters`
option. For instance, to convert a column to boolean:

.. code-block:: python

   read_excel('path_to_file.xls', 'Sheet1', converters={'MyBools': bool})

This options handles missing values and treats exceptions in the converters
as missing data. Transformations are applied cell by cell rather than to the
column as a whole, so the array dtype is not guaranteed. For instance, a
column of integers with missing values cannot be transformed to an array
with integer dtype, because NaN is strictly a float. You can manually mask
missing data to recover integer dtype:

.. code-block:: python

   cfun = lambda x: int(x) if x else -1
   read_excel('path_to_file.xls', 'Sheet1', converters={'MyInts': cfun})

.. _io.excel_writer:

Writing Excel Files
'''''''''''''''''''

Writing Excel Files to Disk
+++++++++++++++++++++++++++

To write a DataFrame object to a sheet of an Excel file, you can use the
``to_excel`` instance method.  The arguments are largely the same as ``to_csv``
described above, the first argument being the name of the excel file, and the
optional second argument the name of the sheet to which the DataFrame should be
written.  For example:

.. code-block:: python

   df.to_excel('path_to_file.xlsx', sheet_name='Sheet1')

Files with a ``.xls`` extension will be written using ``xlwt`` and those with a
``.xlsx`` extension will be written using ``xlsxwriter`` (if available) or
``openpyxl``.

The DataFrame will be written in a way that tries to mimic the REPL output. One
difference from 0.12.0 is that the ``index_label`` will be placed in the second
row instead of the first. You can get the previous behaviour by setting the
``merge_cells`` option in ``to_excel()`` to ``False``:

.. code-block:: python

   df.to_excel('path_to_file.xlsx', index_label='label', merge_cells=False)

The Panel class also has a ``to_excel`` instance method,
which writes each DataFrame in the Panel to a separate sheet.

In order to write separate DataFrames to separate sheets in a single Excel file,
one can pass an :class:`~pandas.io.excel.ExcelWriter`.

.. code-block:: python

   with ExcelWriter('path_to_file.xlsx') as writer:
       df1.to_excel(writer, sheet_name='Sheet1')
       df2.to_excel(writer, sheet_name='Sheet2')

.. note::

    Wringing a little more performance out of ``read_excel``
    Internally, Excel stores all numeric data as floats. Because this can
    produce unexpected behavior when reading in data, pandas defaults to trying
    to convert integers to floats if it doesn't lose information (``1.0 -->
    1``).  You can pass ``convert_float=False`` to disable this behavior, which
    may give a slight performance improvement.

.. _io.excel_writing_buffer:

Writing Excel Files to Memory
+++++++++++++++++++++++++++++

.. versionadded:: 0.17

Pandas supports writing Excel files to buffer-like objects such as ``StringIO`` or
``BytesIO`` using :class:`~pandas.io.excel.ExcelWriter`.

.. versionadded:: 0.17

Added support for Openpyxl >= 2.2

.. code-block:: python

   # Safe import for either Python 2.x or 3.x
   try:
       from io import BytesIO
   except ImportError:
       from cStringIO import StringIO as BytesIO

   bio = BytesIO()

   # By setting the 'engine' in the ExcelWriter constructor.
   writer = ExcelWriter(bio, engine='xlsxwriter')
   df.to_excel(writer, sheet_name='Sheet1')

   # Save the workbook
   writer.save()

   # Seek to the beginning and read to copy the workbook to a variable in memory
   bio.seek(0)
   workbook = bio.read()

.. note::

    ``engine`` is optional but recommended.  Setting the engine determines
    the version of workbook produced. Setting ``engine='xlrd'`` will produce an
    Excel 2003-format workbook (xls).  Using either ``'openpyxl'`` or
    ``'xlsxwriter'`` will produce an Excel 2007-format workbook (xlsx). If
    omitted, an Excel 2007-formatted workbook is produced.

.. _io.excel.writers:

Excel writer engines
''''''''''''''''''''

.. versionadded:: 0.13

``pandas`` chooses an Excel writer via two methods:

1. the ``engine`` keyword argument
2. the filename extension (via the default specified in config options)

By default, ``pandas`` uses the `XlsxWriter`_  for ``.xlsx`` and `openpyxl`_
for ``.xlsm`` files and `xlwt`_ for ``.xls`` files.  If you have multiple
engines installed, you can set the default engine through :ref:`setting the
config options <options>` ``io.excel.xlsx.writer`` and
``io.excel.xls.writer``. pandas will fall back on `openpyxl`_ for ``.xlsx``
files if `Xlsxwriter`_ is not available.

.. _XlsxWriter: http://xlsxwriter.readthedocs.org
.. _openpyxl: http://openpyxl.readthedocs.org/
.. _xlwt: http://www.python-excel.org

To specify which writer you want to use, you can pass an engine keyword
argument to ``to_excel`` and to ``ExcelWriter``. The built-in engines are:

- ``openpyxl``: This includes stable support for Openpyxl from 1.6.1. However,
  it is advised to use version 2.2 and higher, especially when working with
  styles.
- ``xlsxwriter``
- ``xlwt``

.. code-block:: python

   # By setting the 'engine' in the DataFrame and Panel 'to_excel()' methods.
   df.to_excel('path_to_file.xlsx', sheet_name='Sheet1', engine='xlsxwriter')

   # By setting the 'engine' in the ExcelWriter constructor.
   writer = ExcelWriter('path_to_file.xlsx', engine='xlsxwriter')

   # Or via pandas configuration.
   from pandas import options
   options.io.excel.xlsx.writer = 'xlsxwriter'

   df.to_excel('path_to_file.xlsx', sheet_name='Sheet1')

.. _io.clipboard:

Clipboard
---------

A handy way to grab data is to use the ``read_clipboard`` method, which takes
the contents of the clipboard buffer and passes them to the ``read_table``
method. For instance, you can copy the following
text to the clipboard (CTRL-C on many operating systems):

.. code-block:: python

     A B C
   x 1 4 p
   y 2 5 q
   z 3 6 r

And then import the data directly to a DataFrame by calling:

.. code-block:: python

   clipdf = pd.read_clipboard()

.. ipython:: python

   clipdf

The ``to_clipboard`` method can be used to write the contents of a DataFrame to
the clipboard. Following which you can paste the clipboard contents into other
applications (CTRL-V on many operating systems). Here we illustrate writing a
DataFrame into clipboard and reading it back.

.. ipython:: python

    df = pd.DataFrame(randn(5,3))
    df
    df.to_clipboard()
    pd.read_clipboard()

We can see that we got the same content back, which we had earlier written to the clipboard.

.. note::

   You may need to install xclip or xsel (with gtk or PyQt4 modules) on Linux to use these methods.

.. _io.pickle:

Pickling
--------

All pandas objects are equipped with ``to_pickle`` methods which use Python's
``cPickle`` module to save data structures to disk using the pickle format.

.. ipython:: python

   df
   df.to_pickle('foo.pkl')

The ``read_pickle`` function in the ``pandas`` namespace can be used to load
any pickled pandas object (or any other pickled object) from file:


.. ipython:: python

   pd.read_pickle('foo.pkl')

.. ipython:: python
   :suppress:

   import os
   os.remove('foo.pkl')

.. warning::

   Loading pickled data received from untrusted sources can be unsafe.

   See: http://docs.python.org/2.7/library/pickle.html

.. warning::

   Several internal refactorings, 0.13 (:ref:`Series Refactoring <whatsnew_0130.refactoring>`), and 0.15 (:ref:`Index Refactoring <whatsnew_0150.refactoring>`),
   preserve compatibility with pickles created prior to these versions. However, these must
   be read with ``pd.read_pickle``, rather than the default python ``pickle.load``.
   See `this question <http://stackoverflow.com/questions/20444593/pandas-compiled-from-source-default-pickle-behavior-changed>`__
   for a detailed explanation.

.. note::

    These methods were previously ``pd.save`` and ``pd.load``, prior to 0.12.0, and are now deprecated.

.. _io.msgpack:

msgpack (experimental)
----------------------

.. versionadded:: 0.13.0

Starting in 0.13.0, pandas is supporting the ``msgpack`` format for
object serialization. This is a lightweight portable binary format, similar
to binary JSON, that is highly space efficient, and provides good performance
both on the writing (serialization), and reading (deserialization).

.. warning::

   This is a very new feature of pandas. We intend to provide certain
   optimizations in the io of the ``msgpack`` data. Since this is marked
   as an EXPERIMENTAL LIBRARY, the storage format may not be stable until a future release.

   As a result of writing format changes and other issues:
   +----------------------+------------------------+
   | Packed with          | Can be unpacked with   |
   +======================+========================+
   | pre-0.17 / Python 2  | any                    |
   +----------------------+------------------------+
   | pre-0.17 / Python 3  | any                    |
   +----------------------+------------------------+
   | 0.17 / Python 2      | - 0.17 / Python 2      |
   |                      | - >=0.18 / any Python  |
   +----------------------+------------------------+
   | 0.17 / Python 3      | >=0.18 / any Python    |
   +----------------------+------------------------+
   | 0.18                 | >= 0.18                |
   +======================+========================+

   Reading (files packed by older versions) is backward-compatibile, except for files packed with 0.17 in Python 2, in which case only they can only be unpacked in Python 2.

.. ipython:: python

   df = pd.DataFrame(np.random.rand(5,2),columns=list('AB'))
   df.to_msgpack('foo.msg')
   pd.read_msgpack('foo.msg')
   s = pd.Series(np.random.rand(5),index=pd.date_range('20130101',periods=5))

You can pass a list of objects and you will receive them back on deserialization.

.. ipython:: python

   pd.to_msgpack('foo.msg', df, 'foo', np.array([1,2,3]), s)
   pd.read_msgpack('foo.msg')

You can pass ``iterator=True`` to iterate over the unpacked results

.. ipython:: python

   for o in pd.read_msgpack('foo.msg',iterator=True):
       print o

You can pass ``append=True`` to the writer to append to an existing pack

.. ipython:: python

   df.to_msgpack('foo.msg',append=True)
   pd.read_msgpack('foo.msg')

Unlike other io methods, ``to_msgpack`` is available on both a per-object basis,
``df.to_msgpack()`` and using the top-level ``pd.to_msgpack(...)`` where you
can pack arbitrary collections of python lists, dicts, scalars, while intermixing
pandas objects.

.. ipython:: python

   pd.to_msgpack('foo2.msg', { 'dict' : [ { 'df' : df }, { 'string' : 'foo' }, { 'scalar' : 1. }, { 's' : s } ] })
   pd.read_msgpack('foo2.msg')

.. ipython:: python
   :suppress:
   :okexcept:

   os.remove('foo.msg')
   os.remove('foo2.msg')

Read/Write API
''''''''''''''

Msgpacks can also be read from and written to strings.

.. ipython:: python

   df.to_msgpack()

Furthermore you can concatenate the strings to produce a list of the original objects.

.. ipython:: python

  pd.read_msgpack(df.to_msgpack() + s.to_msgpack())

.. _io.hdf5:

HDF5 (PyTables)
---------------

``HDFStore`` is a dict-like object which reads and writes pandas using
the high performance HDF5 format using the excellent `PyTables
<http://www.pytables.org/>`__ library. See the :ref:`cookbook <cookbook.hdf>`
for some advanced strategies

.. warning::

   As of version 0.15.0, pandas requires ``PyTables`` >= 3.0.0. Stores written with prior versions of pandas / ``PyTables`` >= 2.3 are fully compatible (this was the previous minimum ``PyTables`` required version).

.. warning::

   There is a ``PyTables`` indexing bug which may appear when querying stores using an index.  If you see a subset of results being returned, upgrade to ``PyTables`` >= 3.2.  Stores created previously will need to be rewritten using the updated version.

.. warning::

   As of version 0.17.0, ``HDFStore`` will not drop rows that have all missing values by default. Previously, if all values (except the index) were missing, ``HDFStore`` would not write those rows to disk.

.. ipython:: python
   :suppress:
   :okexcept:

   os.remove('store.h5')

.. ipython:: python

   store = pd.HDFStore('store.h5')
   print(store)

Objects can be written to the file just like adding key-value pairs to a
dict:

.. ipython:: python

   np.random.seed(1234)
   index = pd.date_range('1/1/2000', periods=8)
   s = pd.Series(randn(5), index=['a', 'b', 'c', 'd', 'e'])
   df = pd.DataFrame(randn(8, 3), index=index,
                     columns=['A', 'B', 'C'])
   wp = pd.Panel(randn(2, 5, 4), items=['Item1', 'Item2'],
                 major_axis=pd.date_range('1/1/2000', periods=5),
                 minor_axis=['A', 'B', 'C', 'D'])

   # store.put('s', s) is an equivalent method
   store['s'] = s

   store['df'] = df

   store['wp'] = wp

   # the type of stored data
   store.root.wp._v_attrs.pandas_type

   store

In a current or later Python session, you can retrieve stored objects:

.. ipython:: python

   # store.get('df') is an equivalent method
   store['df']

   # dotted (attribute) access provides get as well
   store.df

Deletion of the object specified by the key

.. ipython:: python

   # store.remove('wp') is an equivalent method
   del store['wp']

   store

Closing a Store, Context Manager

.. ipython:: python

   store.close()
   store
   store.is_open

   # Working with, and automatically closing the store with the context
   # manager
   with pd.HDFStore('store.h5') as store:
       store.keys()

.. ipython:: python
   :suppress:

   store.close()
   import os
   os.remove('store.h5')



Read/Write API
''''''''''''''

``HDFStore`` supports an top-level API using  ``read_hdf`` for reading and ``to_hdf`` for writing,
similar to how ``read_csv`` and ``to_csv`` work. (new in 0.11.0)

.. ipython:: python

   df_tl = pd.DataFrame(dict(A=list(range(5)), B=list(range(5))))
   df_tl.to_hdf('store_tl.h5','table',append=True)
   pd.read_hdf('store_tl.h5', 'table', where = ['index>2'])

.. ipython:: python
   :suppress:
   :okexcept:

   os.remove('store_tl.h5')


As of version 0.17.0, HDFStore will no longer drop rows that are all missing by default. This behavior can be enabled by setting ``dropna=True``.

.. ipython:: python
   :suppress:

   import os

.. ipython:: python

   df_with_missing = pd.DataFrame({'col1':[0, np.nan, 2],
                                   'col2':[1, np.nan, np.nan]})
   df_with_missing

   df_with_missing.to_hdf('file.h5', 'df_with_missing',
                           format = 'table', mode='w')

   pd.read_hdf('file.h5', 'df_with_missing')

   df_with_missing.to_hdf('file.h5', 'df_with_missing',
                           format = 'table', mode='w', dropna=True)
   pd.read_hdf('file.h5', 'df_with_missing')


.. ipython:: python
   :suppress:

   os.remove('file.h5')

This is also true for the major axis of a ``Panel``:

.. ipython:: python

   matrix = [[[np.nan, np.nan, np.nan],[1,np.nan,np.nan]],
          [[np.nan, np.nan, np.nan], [np.nan,5,6]],
          [[np.nan, np.nan, np.nan],[np.nan,3,np.nan]]]

   panel_with_major_axis_all_missing = pd.Panel(matrix,
           items=['Item1', 'Item2','Item3'],
           major_axis=[1,2],
           minor_axis=['A', 'B', 'C'])

   panel_with_major_axis_all_missing

   panel_with_major_axis_all_missing.to_hdf('file.h5', 'panel',
                                           dropna = True,
                                           format='table',
                                           mode='w')
   reloaded = pd.read_hdf('file.h5', 'panel')
   reloaded


.. ipython:: python
   :suppress:

   os.remove('file.h5')



.. _io.hdf5-fixed:

Fixed Format
''''''''''''

.. note::

   This was prior to 0.13.0 the ``Storer`` format.

The examples above show storing using ``put``, which write the HDF5 to ``PyTables`` in a fixed array format, called
the ``fixed`` format. These types of stores are are **not** appendable once written (though you can simply
remove them and rewrite). Nor are they **queryable**; they must be
retrieved in their entirety. They also do not support dataframes with non-unique column names.
The ``fixed`` format stores offer very fast writing and slightly faster reading than ``table`` stores.
This format is specified by default when using ``put`` or ``to_hdf`` or by ``format='fixed'`` or ``format='f'``

.. warning::

   A ``fixed`` format will raise a ``TypeError`` if you try to retrieve using a ``where`` .

   .. code-block:: python

       pd.DataFrame(randn(10,2)).to_hdf('test_fixed.h5','df')

       pd.read_hdf('test_fixed.h5','df',where='index>5')
       TypeError: cannot pass a where specification when reading a fixed format.
                  this store must be selected in its entirety


.. _io.hdf5-table:

Table Format
''''''''''''

``HDFStore`` supports another ``PyTables`` format on disk, the ``table``
format. Conceptually a ``table`` is shaped very much like a DataFrame,
with rows and columns. A ``table`` may be appended to in the same or
other sessions.  In addition, delete & query type operations are
supported. This format is specified by ``format='table'`` or ``format='t'``
to ``append`` or ``put`` or ``to_hdf``

.. versionadded:: 0.13

This format can be set as an option as well ``pd.set_option('io.hdf.default_format','table')`` to
enable ``put/append/to_hdf`` to by default store in the ``table`` format.

.. ipython:: python
   :suppress:
   :okexcept:

   os.remove('store.h5')

.. ipython:: python

   store = pd.HDFStore('store.h5')
   df1 = df[0:4]
   df2 = df[4:]

   # append data (creates a table automatically)
   store.append('df', df1)
   store.append('df', df2)
   store

   # select the entire object
   store.select('df')

   # the type of stored data
   store.root.df._v_attrs.pandas_type

.. note::

   You can also create a ``table`` by passing ``format='table'`` or ``format='t'`` to a ``put`` operation.

.. _io.hdf5-keys:

Hierarchical Keys
'''''''''''''''''

Keys to a store can be specified as a string. These can be in a
hierarchical path-name like format (e.g. ``foo/bar/bah``), which will
generate a hierarchy of sub-stores (or ``Groups`` in PyTables
parlance). Keys can be specified with out the leading '/' and are ALWAYS
absolute (e.g. 'foo' refers to '/foo'). Removal operations can remove
everything in the sub-store and BELOW, so be *careful*.

.. ipython:: python

   store.put('foo/bar/bah', df)
   store.append('food/orange', df)
   store.append('food/apple',  df)
   store

   # a list of keys are returned
   store.keys()

   # remove all nodes under this level
   store.remove('food')
   store

.. warning::

    Hierarchical keys cannot be retrieved as dotted (attribute) access as described above for items stored under the root node.

    .. code-block:: python

       In [8]: store.foo.bar.bah
       AttributeError: 'HDFStore' object has no attribute 'foo'

       # you can directly access the actual PyTables node but using the root node
       In [9]: store.root.foo.bar.bah
       Out[9]:
       /foo/bar/bah (Group) ''
         children := ['block0_items' (Array), 'block0_values' (Array), 'axis0' (Array), 'axis1' (Array)]

    Instead, use explicit string based keys

    .. ipython:: python

       store['foo/bar/bah']


.. _io.hdf5-types:

Storing Types
'''''''''''''

Storing Mixed Types in a Table
++++++++++++++++++++++++++++++

Storing mixed-dtype data is supported. Strings are stored as a
fixed-width using the maximum size of the appended column. Subsequent attempts
at appending longer strings will raise a ``ValueError``.

Passing ``min_itemsize={`values`: size}`` as a parameter to append
will set a larger minimum for the string columns. Storing ``floats,
strings, ints, bools, datetime64`` are currently supported. For string
columns, passing ``nan_rep = 'nan'`` to append will change the default
nan representation on disk (which converts to/from `np.nan`), this
defaults to `nan`.

.. ipython:: python

    df_mixed = pd.DataFrame({ 'A' : randn(8),
                              'B' : randn(8),
                              'C' : np.array(randn(8),dtype='float32'),
                              'string' :'string',
                              'int' : 1,
                              'bool' : True,
                              'datetime64' : pd.Timestamp('20010102')},
                            index=list(range(8)))
    df_mixed.ix[3:5,['A', 'B', 'string', 'datetime64']] = np.nan

    store.append('df_mixed', df_mixed, min_itemsize = {'values': 50})
    df_mixed1 = store.select('df_mixed')
    df_mixed1
    df_mixed1.get_dtype_counts()

    # we have provided a minimum string column size
    store.root.df_mixed.table

Storing Multi-Index DataFrames
++++++++++++++++++++++++++++++

Storing multi-index dataframes as tables is very similar to
storing/selecting from homogeneous index DataFrames.

.. ipython:: python

        index = pd.MultiIndex(levels=[['foo', 'bar', 'baz', 'qux'],
                                      ['one', 'two', 'three']],
                              labels=[[0, 0, 0, 1, 1, 2, 2, 3, 3, 3],
                                      [0, 1, 2, 0, 1, 1, 2, 0, 1, 2]],
                              names=['foo', 'bar'])
        df_mi = pd.DataFrame(np.random.randn(10, 3), index=index,
                             columns=['A', 'B', 'C'])
        df_mi

        store.append('df_mi',df_mi)
        store.select('df_mi')

        # the levels are automatically included as data columns
        store.select('df_mi', 'foo=bar')


.. _io.hdf5-query:

Querying
''''''''

Querying a Table
++++++++++++++++

.. warning::

   This query capabilities have changed substantially starting in ``0.13.0``.
   Queries from prior version are accepted (with a ``DeprecationWarning``) printed
   if its not string-like.

``select`` and ``delete`` operations have an optional criterion that can
be specified to select/delete only a subset of the data. This allows one
to have a very large on-disk table and retrieve only a portion of the
data.

A query is specified using the ``Term`` class under the hood, as a boolean expression.

- ``index`` and ``columns`` are supported indexers of a DataFrame
- ``major_axis``, ``minor_axis``, and ``items`` are supported indexers of
  the Panel
- if ``data_columns`` are specified, these can be used as additional indexers

Valid comparison operators are:

``=, ==, !=, >, >=, <, <=``

Valid boolean expressions are combined with:

- ``|`` : or
- ``&`` : and
- ``(`` and ``)`` : for grouping

These rules are similar to how boolean expressions are used in pandas for indexing.

.. note::

   - ``=`` will be automatically expanded to the comparison operator ``==``
   - ``~`` is the not operator, but can only be used in very limited
     circumstances
   - If a list/tuple of expressions is passed they will be combined via ``&``

The following are valid expressions:

- ``'index>=date'``
- ``"columns=['A', 'D']"``
- ``"columns in ['A', 'D']"``
- ``'columns=A'``
- ``'columns==A'``
- ``"~(columns=['A','B'])"``
- ``'index>df.index[3] & string="bar"'``
- ``'(index>df.index[3] & index<=df.index[6]) | string="bar"'``
- ``"ts>=Timestamp('2012-02-01')"``
- ``"major_axis>=20130101"``

The ``indexers`` are on the left-hand side of the sub-expression:

``columns``, ``major_axis``, ``ts``

The right-hand side of the sub-expression (after a comparison operator) can be:

- functions that will be evaluated, e.g. ``Timestamp('2012-02-01')``
- strings, e.g. ``"bar"``
- date-like, e.g. ``20130101``, or ``"20130101"``
- lists, e.g. ``"['A','B']"``
- variables that are defined in the local names space, e.g. ``date``

.. note::

   Passing a string to a query by interpolating it into the query
   expression is not recommended. Simply assign the string of interest to a
   variable and use that variable in an expression. For example, do this

   .. code-block:: python

      string = "HolyMoly'"
      store.select('df', 'index == string')

   instead of this

   .. code-block:: python

      string = "HolyMoly'"
      store.select('df',  'index == %s' % string)

   The latter will **not** work and will raise a ``SyntaxError``.Note that
   there's a single quote followed by a double quote in the ``string``
   variable.

   If you *must* interpolate, use the ``'%r'`` format specifier

   .. code-block:: python

      store.select('df', 'index == %r' % string)

   which will quote ``string``.


Here are some examples:

.. ipython:: python

    dfq = pd.DataFrame(randn(10,4),columns=list('ABCD'),index=pd.date_range('20130101',periods=10))
    store.append('dfq',dfq,format='table',data_columns=True)

Use boolean expressions, with in-line function evaluation.

.. ipython:: python

    store.select('dfq',"index>pd.Timestamp('20130104') & columns=['A', 'B']")

Use and inline column reference

.. ipython:: python

   store.select('dfq',where="A>0 or C>0")

Works with a Panel as well.

.. ipython:: python

   store.append('wp',wp)
   store
   store.select('wp', "major_axis>pd.Timestamp('20000102') & minor_axis=['A', 'B']")

The ``columns`` keyword can be supplied to select a list of columns to be
returned, this is equivalent to passing a
``'columns=list_of_columns_to_filter'``:

.. ipython:: python

   store.select('df', "columns=['A', 'B']")

``start`` and ``stop`` parameters can be specified to limit the total search
space. These are in terms of the total number of rows in a table.

.. ipython:: python

   # this is effectively what the storage of a Panel looks like
   wp.to_frame()

   # limiting the search
   store.select('wp',"major_axis>20000102 & minor_axis=['A','B']",
                start=0, stop=10)

.. note::

   ``select`` will raise a ``ValueError`` if the query expression has an unknown
   variable reference. Usually this means that you are trying to select on a column
   that is **not** a data_column.

   ``select`` will raise a ``SyntaxError`` if the query expression is not valid.


.. _io.hdf5-timedelta:

Using timedelta64[ns]
+++++++++++++++++++++

.. versionadded:: 0.13

Beginning in 0.13.0, you can store and query using the ``timedelta64[ns]`` type. Terms can be
specified in the format: ``<float>(<unit>)``, where float may be signed (and fractional), and unit can be
``D,s,ms,us,ns`` for the timedelta. Here's an example:

.. ipython:: python

   from datetime import timedelta
   dftd = pd.DataFrame(dict(A = pd.Timestamp('20130101'), B = [ pd.Timestamp('20130101') + timedelta(days=i,seconds=10) for i in range(10) ]))
   dftd['C'] = dftd['A']-dftd['B']
   dftd
   store.append('dftd',dftd,data_columns=True)
   store.select('dftd',"C<'-3.5D'")

Indexing
++++++++

You can create/modify an index for a table with ``create_table_index``
after data is already in the table (after and ``append/put``
operation). Creating a table index is **highly** encouraged. This will
speed your queries a great deal when you use a ``select`` with the
indexed dimension as the ``where``.

.. note::

   Indexes are automagically created (starting ``0.10.1``) on the indexables
   and any data columns you specify. This behavior can be turned off by passing
   ``index=False`` to ``append``.

.. ipython:: python

   # we have automagically already created an index (in the first section)
   i = store.root.df.table.cols.index.index
   i.optlevel, i.kind

   # change an index by passing new parameters
   store.create_table_index('df', optlevel=9, kind='full')
   i = store.root.df.table.cols.index.index
   i.optlevel, i.kind

Oftentimes when appending large amounts of data to a store, it is useful to turn off index creation for each append, then recreate at the end.

.. ipython:: python

   df_1 = pd.DataFrame(randn(10,2),columns=list('AB'))
   df_2 = pd.DataFrame(randn(10,2),columns=list('AB'))

   st = pd.HDFStore('appends.h5',mode='w')
   st.append('df', df_1, data_columns=['B'], index=False)
   st.append('df', df_2, data_columns=['B'], index=False)
   st.get_storer('df').table

Then create the index when finished appending.

.. ipython:: python

   st.create_table_index('df', columns=['B'], optlevel=9, kind='full')
   st.get_storer('df').table

   st.close()

.. ipython:: python
   :suppress:
   :okexcept:

   os.remove('appends.h5')

See `here <http://stackoverflow.com/questions/17893370/ptrepack-sortby-needs-full-index>`__ for how to create a completely-sorted-index (CSI) on an existing store.

Query via Data Columns
++++++++++++++++++++++

You can designate (and index) certain columns that you want to be able
to perform queries (other than the `indexable` columns, which you can
always query). For instance say you want to perform this common
operation, on-disk, and return just the frame that matches this
query. You can specify ``data_columns = True`` to force all columns to
be data_columns

.. ipython:: python

   df_dc = df.copy()
   df_dc['string'] = 'foo'
   df_dc.ix[4:6,'string'] = np.nan
   df_dc.ix[7:9,'string'] = 'bar'
   df_dc['string2'] = 'cool'
   df_dc.ix[1:3,['B','C']] = 1.0
   df_dc

   # on-disk operations
   store.append('df_dc', df_dc, data_columns = ['B', 'C', 'string', 'string2'])
   store.select('df_dc', [ pd.Term('B>0') ])

   # getting creative
   store.select('df_dc', 'B > 0 & C > 0 & string == foo')

   # this is in-memory version of this type of selection
   df_dc[(df_dc.B > 0) & (df_dc.C > 0) & (df_dc.string == 'foo')]

   # we have automagically created this index and the B/C/string/string2
   # columns are stored separately as ``PyTables`` columns
   store.root.df_dc.table

There is some performance degradation by making lots of columns into
`data columns`, so it is up to the user to designate these. In addition,
you cannot change data columns (nor indexables) after the first
append/put operation (Of course you can simply read in the data and
create a new table!)

Iterator
++++++++

Starting in ``0.11.0``, you can pass, ``iterator=True`` or ``chunksize=number_in_a_chunk``
to ``select`` and ``select_as_multiple`` to return an iterator on the results.
The default is 50,000 rows returned in a chunk.

.. ipython:: python

   for df in store.select('df', chunksize=3):
      print(df)

.. note::

   .. versionadded:: 0.12.0

   You can also use the iterator with ``read_hdf`` which will open, then
   automatically close the store when finished iterating.

   .. code-block:: python

      for df in pd.read_hdf('store.h5','df', chunksize=3):
          print(df)

Note, that the chunksize keyword applies to the **source** rows. So if you
are doing a query, then the chunksize will subdivide the total rows in the table
and the query applied, returning an iterator on potentially unequal sized chunks.

Here is a recipe for generating a query and using it to create equal sized return
chunks.

.. ipython:: python

   dfeq = pd.DataFrame({'number': np.arange(1,11)})
   dfeq

   store.append('dfeq', dfeq, data_columns=['number'])

   def chunks(l, n):
        return [l[i:i+n] for i in range(0, len(l), n)]

   evens = [2,4,6,8,10]
   coordinates = store.select_as_coordinates('dfeq','number=evens')
   for c in chunks(coordinates, 2):
        print store.select('dfeq',where=c)

Advanced Queries
++++++++++++++++

Select a Single Column
^^^^^^^^^^^^^^^^^^^^^^

To retrieve a single indexable or data column, use the
method ``select_column``. This will, for example, enable you to get the index
very quickly. These return a ``Series`` of the result, indexed by the row number.
These do not currently accept the ``where`` selector.

.. ipython:: python

   store.select_column('df_dc', 'index')
   store.select_column('df_dc', 'string')

.. _io.hdf5-selecting_coordinates:

Selecting coordinates
^^^^^^^^^^^^^^^^^^^^^

Sometimes you want to get the coordinates (a.k.a the index locations) of your query. This returns an
``Int64Index`` of the resulting locations. These coordinates can also be passed to subsequent
``where`` operations.

.. ipython:: python

   df_coord = pd.DataFrame(np.random.randn(1000,2),index=pd.date_range('20000101',periods=1000))
   store.append('df_coord',df_coord)
   c = store.select_as_coordinates('df_coord','index>20020101')
   c.summary()
   store.select('df_coord',where=c)

.. _io.hdf5-where_mask:

Selecting using a where mask
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometime your query can involve creating a list of rows to select. Usually this ``mask`` would
be a resulting ``index`` from an indexing operation. This example selects the months of
a datetimeindex which are 5.

.. ipython:: python

   df_mask = pd.DataFrame(np.random.randn(1000,2),index=pd.date_range('20000101',periods=1000))
   store.append('df_mask',df_mask)
   c = store.select_column('df_mask','index')
   where = c[pd.DatetimeIndex(c).month==5].index
   store.select('df_mask',where=where)

Storer Object
^^^^^^^^^^^^^

If you want to inspect the stored object, retrieve via
``get_storer``. You could use this programmatically to say get the number
of rows in an object.

.. ipython:: python

   store.get_storer('df_dc').nrows


Multiple Table Queries
++++++++++++++++++++++

New in 0.10.1 are the methods ``append_to_multiple`` and
``select_as_multiple``, that can perform appending/selecting from
multiple tables at once. The idea is to have one table (call it the
selector table) that you index most/all of the columns, and perform your
queries. The other table(s) are data tables with an index matching the
selector table's index. You can then perform a very fast query
on the selector table, yet get lots of data back. This method is similar to
having a very wide table, but enables more efficient queries.

The ``append_to_multiple`` method splits a given single DataFrame
into multiple tables according to ``d``, a dictionary that maps the
table names to a list of 'columns' you want in that table. If `None`
is used in place of a list, that table will have the remaining
unspecified columns of the given DataFrame. The argument ``selector``
defines which table is the selector table (which you can make queries from).
The argument ``dropna`` will drop rows from the input DataFrame to ensure
tables are synchronized.  This means that if a row for one of the tables
being written to is entirely ``np.NaN``, that row will be dropped from all tables.

If ``dropna`` is False, **THE USER IS RESPONSIBLE FOR SYNCHRONIZING THE TABLES**.
Remember that entirely ``np.Nan`` rows are not written to the HDFStore, so if
you choose to call ``dropna=False``, some tables may have more rows than others,
and therefore ``select_as_multiple`` may not work or it may return unexpected
results.

.. ipython:: python

   df_mt = pd.DataFrame(randn(8, 6), index=pd.date_range('1/1/2000', periods=8),
                                     columns=['A', 'B', 'C', 'D', 'E', 'F'])
   df_mt['foo'] = 'bar'
   df_mt.ix[1, ('A', 'B')] = np.nan

   # you can also create the tables individually
   store.append_to_multiple({'df1_mt': ['A', 'B'], 'df2_mt': None },
                             df_mt, selector='df1_mt')
   store

   # individual tables were created
   store.select('df1_mt')
   store.select('df2_mt')

   # as a multiple
   store.select_as_multiple(['df1_mt', 'df2_mt'], where=['A>0', 'B>0'],
                             selector = 'df1_mt')


Delete from a Table
'''''''''''''''''''

You can delete from a table selectively by specifying a ``where``. In
deleting rows, it is important to understand the ``PyTables`` deletes
rows by erasing the rows, then **moving** the following data. Thus
deleting can potentially be a very expensive operation depending on the
orientation of your data. This is especially true in higher dimensional
objects (``Panel`` and ``Panel4D``). To get optimal performance, it's
worthwhile to have the dimension you are deleting be the first of the
``indexables``.

Data is ordered (on the disk) in terms of the ``indexables``. Here's a
simple use case. You store panel-type data, with dates in the
``major_axis`` and ids in the ``minor_axis``. The data is then
interleaved like this:

- date_1
  - id_1
  - id_2
  -  .
  - id_n
- date_2
  - id_1
  -  .
  - id_n

It should be clear that a delete operation on the ``major_axis`` will be
fairly quick, as one chunk is removed, then the following data moved. On
the other hand a delete operation on the ``minor_axis`` will be very
expensive. In this case it would almost certainly be faster to rewrite
the table using a ``where`` that selects all but the missing data.

.. ipython:: python

   # returns the number of rows deleted
   store.remove('wp', 'major_axis>20000102' )
   store.select('wp')

.. warning::

   Please note that HDF5 **DOES NOT RECLAIM SPACE** in the h5 files
   automatically. Thus, repeatedly deleting (or removing nodes) and adding
   again, **WILL TEND TO INCREASE THE FILE SIZE**.

   To *repack and clean* the file, use :ref:`ptrepack <io.hdf5-ptrepack>`

.. _io.hdf5-notes:

Notes & Caveats
'''''''''''''''


Compression
+++++++++++

``PyTables`` allows the stored data to be compressed. This applies to
all kinds of stores, not just tables.

- Pass ``complevel=int`` for a compression level (1-9, with 0 being no
  compression, and the default)
- Pass ``complib=lib`` where lib is any of ``zlib, bzip2, lzo, blosc`` for
  whichever compression library you prefer.

``HDFStore`` will use the file based compression scheme if no overriding
``complib`` or ``complevel`` options are provided. ``blosc`` offers very
fast compression, and is my most used. Note that ``lzo`` and ``bzip2``
may not be installed (by Python) by default.

Compression for all objects within the file

.. code-block:: python

   store_compressed = pd.HDFStore('store_compressed.h5', complevel=9, complib='blosc')

Or on-the-fly compression (this only applies to tables). You can turn
off file compression for a specific table by passing ``complevel=0``

.. code-block:: python

   store.append('df', df, complib='zlib', complevel=5)

.. _io.hdf5-ptrepack:

ptrepack
++++++++

``PyTables`` offers better write performance when tables are compressed after
they are written, as opposed to turning on compression at the very
beginning. You can use the supplied ``PyTables`` utility
``ptrepack``. In addition, ``ptrepack`` can change compression levels
after the fact.

.. code-block:: console

   ptrepack --chunkshape=auto --propindexes --complevel=9 --complib=blosc in.h5 out.h5

Furthermore ``ptrepack in.h5 out.h5`` will *repack* the file to allow
you to reuse previously deleted space. Alternatively, one can simply
remove the file and write again, or use the ``copy`` method.

.. _io.hdf5-caveats:

Caveats
+++++++

.. warning::

   ``HDFStore`` is **not-threadsafe for writing**. The underlying
   ``PyTables`` only supports concurrent reads (via threading or
   processes). If you need reading and writing *at the same time*, you
   need to serialize these operations in a single thread in a single
   process. You will corrupt your data otherwise. See the (:issue:`2397`) for more information.

- If you use locks to manage write access between multiple processes, you
  may want to use :py:func:`~os.fsync` before releasing write locks. For
  convenience you can use ``store.flush(fsync=True)`` to do this for you.
- Once a ``table`` is created its items (Panel) / columns (DataFrame)
  are fixed; only exactly the same columns can be appended
- Be aware that timezones (e.g., ``pytz.timezone('US/Eastern')``)
  are not necessarily equal across timezone versions.  So if data is
  localized to a specific timezone in the HDFStore using one version
  of a timezone library and that data is updated with another version, the data
  will be converted to UTC since these timezones are not considered
  equal.  Either use the same version of timezone library or use ``tz_convert`` with
  the updated timezone definition.

.. warning::

   ``PyTables`` will show a ``NaturalNameWarning`` if a  column name
   cannot be used as an attribute selector.
   *Natural* identifiers contain only letters, numbers, and underscores,
   and may not begin with a number.
   Other identifiers cannot be used in a ``where`` clause
   and are generally a bad idea.

.. _io.hdf5-data_types:

DataTypes
'''''''''

``HDFStore`` will map an object dtype to the ``PyTables`` underlying
dtype. This means the following types are known to work:

======================================================  =========================
Type                                                    Represents missing values
======================================================  =========================
floating : ``float64, float32, float16``                ``np.nan``
integer : ``int64, int32, int8, uint64,uint32, uint8``
boolean
``datetime64[ns]``                                      ``NaT``
``timedelta64[ns]``                                     ``NaT``
categorical : see the section below
object : ``strings``                                    ``np.nan``
======================================================  =========================

``unicode`` columns are not supported, and **WILL FAIL**.

.. _io.hdf5-categorical:

Categorical Data
++++++++++++++++

.. versionadded:: 0.15.2

Writing data to a ``HDFStore`` that contains a ``category`` dtype was implemented
in 0.15.2. Queries work the same as if it was an object array. However, the ``category`` dtyped data is
stored in a more efficient manner.

.. ipython:: python

   dfcat = pd.DataFrame({ 'A' : pd.Series(list('aabbcdba')).astype('category'),
                          'B' : np.random.randn(8) })
   dfcat
   dfcat.dtypes
   cstore = pd.HDFStore('cats.h5', mode='w')
   cstore.append('dfcat', dfcat, format='table', data_columns=['A'])
   result = cstore.select('dfcat', where="A in ['b','c']")
   result
   result.dtypes

.. warning::

   The format of the ``Categorical`` is readable by prior versions of pandas (< 0.15.2), but will retrieve
   the data as an integer based column (e.g. the ``codes``). However, the ``categories`` *can* be retrieved
   but require the user to select them manually using the explicit meta path.

   The data is stored like so:

   .. ipython:: python

      cstore

      # to get the categories
      cstore.select('dfcat/meta/A/meta')

.. ipython:: python
   :suppress:
   :okexcept:

   cstore.close()
   import os
   os.remove('cats.h5')


String Columns
++++++++++++++

**min_itemsize**

The underlying implementation of ``HDFStore`` uses a fixed column width (itemsize) for string columns.
A string column itemsize is calculated as the maximum of the
length of data (for that column) that is passed to the ``HDFStore``, **in the first append**. Subsequent appends,
may introduce a string for a column **larger** than the column can hold, an Exception will be raised (otherwise you
could have a silent truncation of these columns, leading to loss of information). In the future we may relax this and
allow a user-specified truncation to occur.

Pass ``min_itemsize`` on the first table creation to a-priori specify the minimum length of a particular string column.
``min_itemsize`` can be an integer, or a dict mapping a column name to an integer. You can pass ``values`` as a key to
allow all *indexables* or *data_columns* to have this min_itemsize.

Starting in 0.11.0, passing a ``min_itemsize`` dict will cause all passed columns to be created as *data_columns* automatically.

.. note::

   If you are not passing any ``data_columns``, then the ``min_itemsize`` will be the maximum of the length of any string passed

.. ipython:: python

   dfs = pd.DataFrame(dict(A = 'foo', B = 'bar'),index=list(range(5)))
   dfs

   # A and B have a size of 30
   store.append('dfs', dfs, min_itemsize = 30)
   store.get_storer('dfs').table

   # A is created as a data_column with a size of 30
   # B is size is calculated
   store.append('dfs2', dfs, min_itemsize = { 'A' : 30 })
   store.get_storer('dfs2').table

**nan_rep**

String columns will serialize a ``np.nan`` (a missing value) with the ``nan_rep`` string representation. This defaults to the string value ``nan``.
You could inadvertently turn an actual ``nan`` value into a missing value.

.. ipython:: python

   dfss = pd.DataFrame(dict(A = ['foo','bar','nan']))
   dfss

   store.append('dfss', dfss)
   store.select('dfss')

   # here you need to specify a different nan rep
   store.append('dfss2', dfss, nan_rep='_nan_')
   store.select('dfss2')

.. _io.external_compatibility:

External Compatibility
''''''''''''''''''''''

``HDFStore`` writes ``table`` format objects in specific formats suitable for
producing loss-less round trips to pandas objects. For external
compatibility, ``HDFStore`` can read native ``PyTables`` format
tables.

It is possible to write an ``HDFStore`` object that can easily be imported into ``R`` using the
``rhdf5`` library (`Package website`_). Create a table format store like this:

.. _package website: http://www.bioconductor.org/packages/release/bioc/html/rhdf5.html

.. ipython:: python

   np.random.seed(1)
   df_for_r = pd.DataFrame({"first": np.random.rand(100),
                            "second": np.random.rand(100),
                            "class": np.random.randint(0, 2, (100,))},
                            index=range(100))
   df_for_r.head()

   store_export = pd.HDFStore('export.h5')
   store_export.append('df_for_r', df_for_r, data_columns=df_dc.columns)
   store_export

.. ipython:: python
   :suppress:

   store_export.close()
   import os
   os.remove('export.h5')

In R this file can be read into a ``data.frame`` object using the ``rhdf5``
library. The following example function reads the corresponding column names
and data values from the values and assembles them into a ``data.frame``:

.. code-block:: R

   # Load values and column names for all datasets from corresponding nodes and
   # insert them into one data.frame object.

   library(rhdf5)

   loadhdf5data <- function(h5File) {

   listing <- h5ls(h5File)
   # Find all data nodes, values are stored in *_values and corresponding column
   # titles in *_items
   data_nodes <- grep("_values", listing$name)
   name_nodes <- grep("_items", listing$name)
   data_paths = paste(listing$group[data_nodes], listing$name[data_nodes], sep = "/")
   name_paths = paste(listing$group[name_nodes], listing$name[name_nodes], sep = "/")
   columns = list()
   for (idx in seq(data_paths)) {
     # NOTE: matrices returned by h5read have to be transposed to to obtain
     # required Fortran order!
     data <- data.frame(t(h5read(h5File, data_paths[idx])))
     names <- t(h5read(h5File, name_paths[idx]))
     entry <- data.frame(data)
     colnames(entry) <- names
     columns <- append(columns, entry)
   }

   data <- data.frame(columns)

   return(data)
   }

Now you can import the ``DataFrame`` into R:

.. code-block:: R

   > data = loadhdf5data("transfer.hdf5")
   > head(data)
            first    second class
   1 0.4170220047 0.3266449     0
   2 0.7203244934 0.5270581     0
   3 0.0001143748 0.8859421     1
   4 0.3023325726 0.3572698     1
   5 0.1467558908 0.9085352     1
   6 0.0923385948 0.6233601     1

.. note::
   The R function lists the entire HDF5 file's contents and assembles the
   ``data.frame`` object from all matching nodes, so use this only as a
   starting point if you have stored multiple ``DataFrame`` objects to a
   single HDF5 file.

Backwards Compatibility
'''''''''''''''''''''''

0.10.1 of ``HDFStore`` can read tables created in a prior version of pandas,
however query terms using the
prior (undocumented) methodology are unsupported. ``HDFStore`` will
issue a warning if you try to use a legacy-format file. You must
read in the entire file and write it out using the new format, using the
method ``copy`` to take advantage of the updates. The group attribute
``pandas_version`` contains the version information. ``copy`` takes a
number of options, please see the docstring.


.. ipython:: python
   :suppress:

   import os
   legacy_file_path = os.path.abspath('source/_static/legacy_0.10.h5')

.. ipython:: python
   :okwarning:

   # a legacy store
   legacy_store = pd.HDFStore(legacy_file_path,'r')
   legacy_store

   # copy (and return the new handle)
   new_store = legacy_store.copy('store_new.h5')
   new_store
   new_store.close()

.. ipython:: python
   :suppress:

   legacy_store.close()
   import os
   os.remove('store_new.h5')


Performance
'''''''''''

- ``tables`` format come with a writing performance penalty as compared to
  ``fixed`` stores. The benefit is the ability to append/delete and
  query (potentially very large amounts of data).  Write times are
  generally longer as compared with regular stores. Query times can
  be quite fast, especially on an indexed axis.
- You can pass ``chunksize=<int>`` to ``append``, specifying the
  write chunksize (default is 50000). This will significantly lower
  your memory usage on writing.
- You can pass ``expectedrows=<int>`` to the first ``append``,
  to set the TOTAL number of expected rows that ``PyTables`` will
  expected. This will optimize read/write performance.
- Duplicate rows can be written to tables, but are filtered out in
  selection (with the last items being selected; thus a table is
  unique on major, minor pairs)
- A ``PerformanceWarning`` will be raised if you are attempting to
  store types that will be pickled by PyTables (rather than stored as
  endemic types). See
  `Here <http://stackoverflow.com/questions/14355151/how-to-make-pandas-hdfstore-put-operation-faster/14370190#14370190>`__
  for more information and some solutions.

Experimental
''''''''''''

HDFStore supports ``Panel4D`` storage.

.. ipython:: python
   :okwarning:

   p4d = pd.Panel4D({ 'l1' : wp })
   p4d
   store.append('p4d', p4d)
   store

These, by default, index the three axes ``items, major_axis,
minor_axis``. On an ``AppendableTable`` it is possible to setup with the
first append a different indexing scheme, depending on how you want to
store your data. Pass the ``axes`` keyword with a list of dimensions
(currently must by exactly 1 less than the total dimensions of the
object). This cannot be changed after table creation.

.. ipython:: python
   :okwarning:

   store.append('p4d2', p4d, axes=['labels', 'major_axis', 'minor_axis'])
   store
   store.select('p4d2', [ pd.Term('labels=l1'), pd.Term('items=Item1'), pd.Term('minor_axis=A_big_strings') ])

.. ipython:: python
   :suppress:

   store.close()
   import os
   os.remove('store.h5')


.. _io.sql:

SQL Queries
-----------

The :mod:`pandas.io.sql` module provides a collection of query wrappers to both
facilitate data retrieval and to reduce dependency on DB-specific API. Database abstraction
is provided by SQLAlchemy if installed. In addition you will need a driver library for
your database. Examples of such drivers are `psycopg2 <http://initd.org/psycopg/>`__
for PostgreSQL or `pymysql <https://github.com/PyMySQL/PyMySQL>`__ for MySQL.
For `SQLite <https://docs.python.org/3.5/library/sqlite3.html>`__ this is
included in Python's standard library by default.
You can find an overview of supported drivers for each SQL dialect in the
`SQLAlchemy docs <http://docs.sqlalchemy.org/en/latest/dialects/index.html>`__.

.. versionadded:: 0.14.0

If SQLAlchemy is not installed, a fallback is only provided for sqlite (and
for mysql for backwards compatibility, but this is deprecated and will be
removed in a future version).
This mode requires a Python database adapter which respect the `Python
DB-API <http://www.python.org/dev/peps/pep-0249/>`__.

See also some :ref:`cookbook examples <cookbook.sql>` for some advanced strategies.

The key functions are:

.. autosummary::
    :toctree: generated/

    read_sql_table
    read_sql_query
    read_sql
    DataFrame.to_sql

.. note::

    The function :func:`~pandas.read_sql` is a convenience wrapper around
    :func:`~pandas.read_sql_table` and :func:`~pandas.read_sql_query` (and for
    backward compatibility) and will delegate to specific function depending on
    the provided input (database table name or sql query).
    Table names do not need to be quoted if they have special characters.

In the following example, we use the `SQlite <http://www.sqlite.org/>`__ SQL database
engine. You can use a temporary SQLite database where data are stored in
"memory".

To connect with SQLAlchemy you use the :func:`create_engine` function to create an engine
object from database URI. You only need to create the engine once per database you are
connecting to.
For more information on :func:`create_engine` and the URI formatting, see the examples
below and the SQLAlchemy `documentation <http://docs.sqlalchemy.org/en/latest/core/engines.html>`__

.. ipython:: python

   from sqlalchemy import create_engine
   # Create your engine.
   engine = create_engine('sqlite:///:memory:')

If you want to manage your own connections you can pass one of those instead:

.. code-block:: python

   with engine.connect() as conn, conn.begin():
       data = pd.read_sql_table('data', conn)

Writing DataFrames
''''''''''''''''''

Assuming the following data is in a DataFrame ``data``, we can insert it into
the database using :func:`~pandas.DataFrame.to_sql`.

+-----+------------+-------+-------+-------+
| id  |    Date    | Col_1 | Col_2 | Col_3 |
+=====+============+=======+=======+=======+
| 26  | 2012-10-18 |   X   |  25.7 | True  |
+-----+------------+-------+-------+-------+
| 42  | 2012-10-19 |   Y   | -12.4 | False |
+-----+------------+-------+-------+-------+
| 63  | 2012-10-20 |   Z   |  5.73 | True  |
+-----+------------+-------+-------+-------+


.. ipython:: python
   :suppress:

   import datetime
   c = ['id', 'Date', 'Col_1', 'Col_2', 'Col_3']
   d = [(26, datetime.datetime(2010,10,18), 'X', 27.5, True),
   (42, datetime.datetime(2010,10,19), 'Y', -12.5, False),
   (63, datetime.datetime(2010,10,20), 'Z', 5.73, True)]

   data  = pd.DataFrame(d, columns=c)

.. ipython:: python

    data.to_sql('data', engine)

With some databases, writing large DataFrames can result in errors due to
packet size limitations being exceeded. This can be avoided by setting the
``chunksize`` parameter when calling ``to_sql``.  For example, the following
writes ``data`` to the database in batches of 1000 rows at a time:

.. ipython:: python

    data.to_sql('data_chunked', engine, chunksize=1000)

SQL data types
++++++++++++++

:func:`~pandas.DataFrame.to_sql` will try to map your data to an appropriate
SQL data type based on the dtype of the data. When you have columns of dtype
``object``, pandas will try to infer the data type.

You can always override the default type by specifying the desired SQL type of
any of the columns by using the ``dtype`` argument. This argument needs a
dictionary mapping column names to SQLAlchemy types (or strings for the sqlite3
fallback mode).
For example, specifying to use the sqlalchemy ``String`` type instead of the
default ``Text`` type for string columns:

.. ipython:: python

    from sqlalchemy.types import String
    data.to_sql('data_dtype', engine, dtype={'Col_1': String})

.. note::

    Due to the limited support for timedelta's in the different database
    flavors, columns with type ``timedelta64`` will be written as integer
    values as nanoseconds to the database and a warning will be raised.

.. note::

    Columns of ``category`` dtype will be converted to the dense representation
    as you would get with ``np.asarray(categorical)`` (e.g. for string categories
    this gives an array of strings).
    Because of this, reading the database table back in does **not** generate
    a categorical.

Reading Tables
''''''''''''''

:func:`~pandas.read_sql_table` will read a database table given the
table name and optionally a subset of columns to read.

.. note::

    In order to use :func:`~pandas.read_sql_table`, you **must** have the
    SQLAlchemy optional dependency installed.

.. ipython:: python

   pd.read_sql_table('data', engine)

You can also specify the name of the column as the DataFrame index,
and specify a subset of columns to be read.

.. ipython:: python

   pd.read_sql_table('data', engine, index_col='id')
   pd.read_sql_table('data', engine, columns=['Col_1', 'Col_2'])

And you can explicitly force columns to be parsed as dates:

.. ipython:: python

   pd.read_sql_table('data', engine, parse_dates=['Date'])

If needed you can explicitly specify a format string, or a dict of arguments
to pass to :func:`pandas.to_datetime`:

.. code-block:: python

   pd.read_sql_table('data', engine, parse_dates={'Date': '%Y-%m-%d'})
   pd.read_sql_table('data', engine, parse_dates={'Date': {'format': '%Y-%m-%d %H:%M:%S'}})


You can check if a table exists using :func:`~pandas.io.sql.has_table`

Schema support
''''''''''''''

.. versionadded:: 0.15.0

Reading from and writing to different schema's is supported through the ``schema``
keyword in the :func:`~pandas.read_sql_table` and :func:`~pandas.DataFrame.to_sql`
functions. Note however that this depends on the database flavor (sqlite does not
have schema's). For example:

.. code-block:: python

   df.to_sql('table', engine, schema='other_schema')
   pd.read_sql_table('table', engine, schema='other_schema')

Querying
''''''''

You can query using raw SQL in the :func:`~pandas.read_sql_query` function.
In this case you must use the SQL variant appropriate for your database.
When using SQLAlchemy, you can also pass SQLAlchemy Expression language constructs,
which are database-agnostic.

.. ipython:: python

   pd.read_sql_query('SELECT * FROM data', engine)

Of course, you can specify a more "complex" query.

.. ipython:: python

   pd.read_sql_query("SELECT id, Col_1, Col_2 FROM data WHERE id = 42;", engine)

The :func:`~pandas.read_sql_query` function supports a ``chunksize`` argument.
Specifying this will return an iterator through chunks of the query result:

.. ipython:: python

    df = pd.DataFrame(np.random.randn(20, 3), columns=list('abc'))
    df.to_sql('data_chunks', engine, index=False)

.. ipython:: python

    for chunk in pd.read_sql_query("SELECT * FROM data_chunks", engine, chunksize=5):
        print(chunk)

You can also run a plain query without creating a dataframe with
:func:`~pandas.io.sql.execute`. This is useful for queries that don't return values,
such as INSERT. This is functionally equivalent to calling ``execute`` on the
SQLAlchemy engine or db connection object. Again, you must use the SQL syntax
variant appropriate for your database.

.. code-block:: python

   from pandas.io import sql
   sql.execute('SELECT * FROM table_name', engine)
   sql.execute('INSERT INTO table_name VALUES(?, ?, ?)', engine, params=[('id', 1, 12.2, True)])


Engine connection examples
''''''''''''''''''''''''''

To connect with SQLAlchemy you use the :func:`create_engine` function to create an engine
object from database URI. You only need to create the engine once per database you are
connecting to.

.. code-block:: python

   from sqlalchemy import create_engine

   engine = create_engine('postgresql://scott:tiger@localhost:5432/mydatabase')

   engine = create_engine('mysql+mysqldb://scott:tiger@localhost/foo')

   engine = create_engine('oracle://scott:tiger@127.0.0.1:1521/sidname')

   engine = create_engine('mssql+pyodbc://mydsn')

   # sqlite://<nohostname>/<path>
   # where <path> is relative:
   engine = create_engine('sqlite:///foo.db')

   # or absolute, starting with a slash:
   engine = create_engine('sqlite:////absolute/path/to/foo.db')

For more information see the examples the SQLAlchemy `documentation <http://docs.sqlalchemy.org/en/latest/core/engines.html>`__


Advanced SQLAlchemy queries
'''''''''''''''''''''''''''

You can use SQLAlchemy constructs to describe your query.

Use :func:`sqlalchemy.text` to specify query parameters in a backend-neutral way

.. ipython:: python

   import sqlalchemy as sa
   pd.read_sql(sa.text('SELECT * FROM data where Col_1=:col1'), engine, params={'col1': 'X'})

If you have an SQLAlchemy description of your database you can express where conditions using SQLAlchemy expressions

.. ipython:: python

   metadata = sa.MetaData()
   data_table = sa.Table('data', metadata,
       sa.Column('index', sa.Integer),
       sa.Column('Date', sa.DateTime),
       sa.Column('Col_1', sa.String),
       sa.Column('Col_2', sa.Float),
       sa.Column('Col_3', sa.Boolean),
   )

   pd.read_sql(sa.select([data_table]).where(data_table.c.Col_3 == True), engine)

You can combine SQLAlchemy expressions with parameters passed to :func:`read_sql` using :func:`sqlalchemy.bindparam`

.. ipython:: python

    import datetime as dt
    expr = sa.select([data_table]).where(data_table.c.Date > sa.bindparam('date'))
    pd.read_sql(expr, engine, params={'date': dt.datetime(2010, 10, 18)})


Sqlite fallback
'''''''''''''''

The use of sqlite is supported without using SQLAlchemy.
This mode requires a Python database adapter which respect the `Python
DB-API <http://www.python.org/dev/peps/pep-0249/>`__.

You can create connections like so:

.. code-block:: python

   import sqlite3
   con = sqlite3.connect(':memory:')

And then issue the following queries:

.. code-block:: python

   data.to_sql('data', cnx)
   pd.read_sql_query("SELECT * FROM data", con)


.. _io.bigquery:

Google BigQuery (Experimental)
------------------------------

.. versionadded:: 0.13.0

The :mod:`pandas.io.gbq` module provides a wrapper for Google's BigQuery
analytics web service to simplify retrieving results from BigQuery tables
using SQL-like queries. Result sets are parsed into a pandas
DataFrame with a shape and data types derived from the source table.
Additionally, DataFrames can be inserted into new BigQuery tables or appended
to existing tables.

You will need to install some additional dependencies:

- Google's `python-gflags <https://github.com/google/python-gflags/>`__
- `httplib2 <http://pypi.python.org/pypi/httplib2>`__
- `google-api-python-client <http://github.com/google/google-api-python-client>`__

.. warning::

   To use this module, you will need a valid BigQuery account. Refer to the
   `BigQuery Documentation <https://cloud.google.com/bigquery/what-is-bigquery>`__ for details on the service itself.

The key functions are:

.. currentmodule:: pandas.io.gbq

.. autosummary::
   :toctree: generated/

   read_gbq
   to_gbq

.. currentmodule:: pandas

.. _io.bigquery_reader:

.. _io.bigquery_authentication:

Authentication
''''''''''''''

.. versionadded:: 0.18.0

Authentication to the Google ``BigQuery`` service is via ``OAuth 2.0``.
Is possible to authenticate with either user account credentials or service account credentials.

Authenticating with user account credentials is as simple as following the prompts in a browser window
which will be automatically opened for you. You will be authenticated to the specified
``BigQuery`` account using the product name ``pandas GBQ``. It is only possible on local host.
The remote authentication using user account credentials is not currently supported in Pandas.
Additional information on the authentication mechanism can be found
`here <https://developers.google.com/identity/protocols/OAuth2#clientside/>`__.

Authentication with service account credentials is possible via the `'private_key'` parameter. This method
is particularly useful when working on remote servers (eg. jupyter iPython notebook on remote host).
Additional information on service accounts can be found
`here <https://developers.google.com/identity/protocols/OAuth2#serviceaccount>`__.

You will need to install an additional dependency: `oauth2client <https://github.com/google/oauth2client>`__.

Authentication via ``application default credentials`` is also possible. This is only valid
if the parameter ``private_key`` is not provided. This method also requires that
the credentials can be fetched from the environment the code is running in.
Otherwise, the OAuth2 client-side authentication is used.
Additional information on
`application default credentials <https://developers.google.com/identity/protocols/application-default-credentials>`__.

.. versionadded:: 0.19.0

.. note::

   The `'private_key'` parameter can be set to either the file path of the service account key
   in JSON format, or key contents of the service account key in JSON format.

.. note::

   A private key can be obtained from the Google developers console by clicking
   `here <https://console.developers.google.com/permissions/serviceaccounts>`__. Use JSON key type.


Querying
''''''''

Suppose you want to load all data from an existing BigQuery table : `test_dataset.test_table`
into a DataFrame using the :func:`~pandas.io.gbq.read_gbq` function.

.. code-block:: python

   # Insert your BigQuery Project ID Here
   # Can be found in the Google web console
   projectid = "xxxxxxxx"

   data_frame = pd.read_gbq('SELECT * FROM test_dataset.test_table', projectid)


You can define which column from BigQuery to use as an index in the
destination DataFrame as well as a preferred column order as follows:

.. code-block:: python

   data_frame = pd.read_gbq('SELECT * FROM test_dataset.test_table',
                             index_col='index_column_name',
                             col_order=['col1', 'col2', 'col3'], projectid)

.. note::

   You can find your project id in the `Google developers console <https://console.developers.google.com>`__.


.. note::

   You can toggle the verbose output via the ``verbose`` flag which defaults to ``True``.

.. note::

    The ``dialect`` argument can be used to indicate whether to use BigQuery's ``'legacy'`` SQL
    or BigQuery's ``'standard'`` SQL (beta). The default value is ``'legacy'``. For more information
    on BigQuery's standard SQL, see `BigQuery SQL Reference
    <https://cloud.google.com/bigquery/sql-reference/>`__

.. _io.bigquery_writer:


Writing DataFrames
''''''''''''''''''

Assume we want to write a DataFrame ``df`` into a BigQuery table using :func:`~pandas.DataFrame.to_gbq`.

.. ipython:: python

   df = pd.DataFrame({'my_string': list('abc'),
                      'my_int64': list(range(1, 4)),
                      'my_float64': np.arange(4.0, 7.0),
                      'my_bool1': [True, False, True],
                      'my_bool2': [False, True, False],
                      'my_dates': pd.date_range('now', periods=3)})

   df
   df.dtypes

.. code-block:: python

   df.to_gbq('my_dataset.my_table', projectid)

.. note::

   The destination table and destination dataset will automatically be created if they do not already exist.

The ``if_exists`` argument can be used to dictate whether to ``'fail'``, ``'replace'``
or ``'append'`` if the destination table already exists. The default value is ``'fail'``.

For example, assume that ``if_exists`` is set to ``'fail'``. The following snippet will raise
a ``TableCreationError`` if the destination table already exists.

.. code-block:: python

   df.to_gbq('my_dataset.my_table', projectid, if_exists='fail')

.. note::

   If the ``if_exists`` argument is set to ``'append'``, the destination dataframe will
   be written to the table using the defined table schema and column types. The
   dataframe must match the destination table in column order, structure, and
   data types.
   If the ``if_exists`` argument is set to ``'replace'``, and the existing table has a
   different schema, a delay of 2 minutes will be forced to ensure that the new schema
   has propagated in the Google environment. See
   `Google BigQuery issue 191 <https://code.google.com/p/google-bigquery/issues/detail?id=191>`__.

Writing large DataFrames can result in errors due to size limitations being exceeded.
This can be avoided by setting the ``chunksize`` argument when calling :func:`~pandas.DataFrame.to_gbq`.
For example, the following writes ``df`` to a BigQuery table in batches of 10000 rows at a time:

.. code-block:: python

   df.to_gbq('my_dataset.my_table', projectid, chunksize=10000)

You can also see the progress of your post via the ``verbose`` flag which defaults to ``True``.
For example:

.. code-block:: python

   In [8]: df.to_gbq('my_dataset.my_table', projectid, chunksize=10000, verbose=True)

           Streaming Insert is 10% Complete
           Streaming Insert is 20% Complete
           Streaming Insert is 30% Complete
           Streaming Insert is 40% Complete
           Streaming Insert is 50% Complete
           Streaming Insert is 60% Complete
           Streaming Insert is 70% Complete
           Streaming Insert is 80% Complete
           Streaming Insert is 90% Complete
           Streaming Insert is 100% Complete

.. note::

   If an error occurs while streaming data to BigQuery, see
   `Troubleshooting BigQuery Errors <https://cloud.google.com/bigquery/troubleshooting-errors>`__.

.. note::

   The BigQuery SQL query language has some oddities, see the
   `BigQuery Query Reference Documentation <https://cloud.google.com/bigquery/query-reference>`__.

.. note::

   While BigQuery uses SQL-like syntax, it has some important differences from traditional
   databases both in functionality, API limitations (size and quantity of queries or uploads),
   and how Google charges for use of the service. You should refer to `Google BigQuery documentation <https://cloud.google.com/bigquery/what-is-bigquery>`__
   often as the service seems to be changing and evolving. BiqQuery is best for analyzing large
   sets of data quickly, but it is not a direct replacement for a transactional database.

Creating BigQuery Tables
''''''''''''''''''''''''

.. warning::

   As of 0.17, the function :func:`~pandas.io.gbq.generate_bq_schema` has been deprecated and will be
   removed in a future version.

As of 0.15.2, the gbq module has a function :func:`~pandas.io.gbq.generate_bq_schema` which will
produce the dictionary representation schema of the specified pandas DataFrame.

.. code-block:: ipython

   In [10]: gbq.generate_bq_schema(df, default_type='STRING')

   Out[10]: {'fields': [{'name': 'my_bool1', 'type': 'BOOLEAN'},
            {'name': 'my_bool2', 'type': 'BOOLEAN'},
            {'name': 'my_dates', 'type': 'TIMESTAMP'},
            {'name': 'my_float64', 'type': 'FLOAT'},
            {'name': 'my_int64', 'type': 'INTEGER'},
            {'name': 'my_string', 'type': 'STRING'}]}

.. note::

   If you delete and re-create a BigQuery table with the same name, but different table schema,
   you must wait 2 minutes before streaming data into the table. As a workaround, consider creating
   the new table with a different name. Refer to
   `Google BigQuery issue 191 <https://code.google.com/p/google-bigquery/issues/detail?id=191>`__.

.. _io.stata:

Stata Format
------------

.. versionadded:: 0.12.0

.. _io.stata_writer:

Writing to Stata format
'''''''''''''''''''''''

The method :func:`~pandas.core.frame.DataFrame.to_stata` will write a DataFrame
into a .dta file. The format version of this file is always 115 (Stata 12).

.. ipython:: python

   df = pd.DataFrame(randn(10, 2), columns=list('AB'))
   df.to_stata('stata.dta')

*Stata* data files have limited data type support; only strings with
244 or fewer characters, ``int8``, ``int16``, ``int32``, ``float32``
and ``float64`` can be stored in ``.dta`` files.  Additionally,
*Stata* reserves certain values to represent missing data. Exporting a
non-missing value that is outside of the permitted range in Stata for
a particular data type will retype the variable to the next larger
size.  For example, ``int8`` values are restricted to lie between -127
and 100 in Stata, and so variables with values above 100 will trigger
a conversion to ``int16``. ``nan`` values in floating points data
types are stored as the basic missing data type (``.`` in *Stata*).

.. note::

    It is not possible to export missing data values for integer data types.


The *Stata* writer gracefully handles other data types including ``int64``,
``bool``, ``uint8``, ``uint16``, ``uint32`` by casting to
the smallest supported type that can represent the data.  For example, data
with a type of ``uint8`` will be cast to ``int8`` if all values are less than
100 (the upper bound for non-missing ``int8`` data in *Stata*), or, if values are
outside of this range, the variable is cast to ``int16``.


.. warning::

   Conversion from ``int64`` to ``float64`` may result in a loss of precision
   if ``int64`` values are larger than 2**53.

.. warning::

  :class:`~pandas.io.stata.StataWriter` and
  :func:`~pandas.core.frame.DataFrame.to_stata` only support fixed width
  strings containing up to 244 characters, a limitation imposed by the version
  115 dta file format. Attempting to write *Stata* dta files with strings
  longer than 244 characters raises a ``ValueError``.

.. _io.stata_reader:

Reading from Stata format
'''''''''''''''''''''''''

The top-level function ``read_stata`` will read a dta file and return
either a DataFrame or a :class:`~pandas.io.stata.StataReader` that can
be used to read the file incrementally.

.. ipython:: python

   pd.read_stata('stata.dta')

.. versionadded:: 0.16.0

Specifying a ``chunksize`` yields a
:class:`~pandas.io.stata.StataReader` instance that can be used to
read ``chunksize`` lines from the file at a time.  The ``StataReader``
object can be used as an iterator.

.. ipython:: python

  reader = pd.read_stata('stata.dta', chunksize=3)
  for df in reader:
      print(df.shape)

For more fine-grained control, use ``iterator=True`` and specify
``chunksize`` with each call to
:func:`~pandas.io.stata.StataReader.read`.

.. ipython:: python

  reader = pd.read_stata('stata.dta', iterator=True)
  chunk1 = reader.read(5)
  chunk2 = reader.read(5)

Currently the ``index`` is retrieved as a column.

The parameter ``convert_categoricals`` indicates whether value labels should be
read and used to create a ``Categorical`` variable from them. Value labels can
also be retrieved by the function ``value_labels``, which requires :func:`~pandas.io.stata.StataReader.read`
to be called before use.

The parameter ``convert_missing`` indicates whether missing value
representations in Stata should be preserved.  If ``False`` (the default),
missing values are represented as ``np.nan``.  If ``True``, missing values are
represented using ``StataMissingValue`` objects, and columns containing missing
values will have ``object`` data type.

.. note::

   :func:`~pandas.read_stata` and
   :class:`~pandas.io.stata.StataReader` support .dta formats 113-115
   (Stata 10-12), 117 (Stata 13), and 118 (Stata 14).

.. note::

   Setting ``preserve_dtypes=False`` will upcast to the standard pandas data types:
   ``int64`` for all integer types and ``float64`` for floating point data.  By default,
   the Stata data types are preserved when importing.

.. ipython:: python
   :suppress:

   import os
   os.remove('stata.dta')

.. _io.stata-categorical:

Categorical Data
++++++++++++++++

.. versionadded:: 0.15.2

``Categorical`` data can be exported to *Stata* data files as value labeled data.
The exported data consists of the underlying category codes as integer data values
and the categories as value labels.  *Stata* does not have an explicit equivalent
to a ``Categorical`` and information about *whether* the variable is ordered
is lost when exporting.

.. warning::

    *Stata* only supports string value labels, and so ``str`` is called on the
    categories when exporting data.  Exporting ``Categorical`` variables with
    non-string categories produces a warning, and can result a loss of
    information if the ``str`` representations of the categories are not unique.

Labeled data can similarly be imported from *Stata* data files as ``Categorical``
variables using the keyword argument ``convert_categoricals`` (``True`` by default).
The keyword argument ``order_categoricals`` (``True`` by default) determines
whether imported ``Categorical`` variables are ordered.

.. note::

    When importing categorical data, the values of the variables in the *Stata*
    data file are not preserved since ``Categorical`` variables always
    use integer data types between ``-1`` and ``n-1`` where ``n`` is the number
    of categories. If the original values in the *Stata* data file are required,
    these can be imported by setting ``convert_categoricals=False``, which will
    import original data (but not the variable labels). The original values can
    be matched to the imported categorical data since there is a simple mapping
    between the original *Stata* data values and the category codes of imported
    Categorical variables: missing values are assigned code ``-1``, and the
    smallest original value is assigned ``0``, the second smallest is assigned
    ``1`` and so on until the largest original value is assigned the code ``n-1``.

.. note::

    *Stata* supports partially labeled series.  These series have value labels for
    some but not all data values. Importing a partially labeled series will produce
    a ``Categorical`` with string categories for the values that are labeled and
    numeric categories for values with no label.

.. _io.sas:

.. _io.sas_reader:

SAS Formats
-----------

.. versionadded:: 0.17.0

The top-level function :func:`read_sas` can read (but not write) SAS
`xport` (.XPT) and `SAS7BDAT` (.sas7bdat) format files were added in *v0.18.0*.

SAS files only contain two value types: ASCII text and floating point
values (usually 8 bytes but sometimes truncated).  For xport files,
there is no automatic type conversion to integers, dates, or
categoricals.  For SAS7BDAT files, the format codes may allow date
variables to be automatically converted to dates.  By default the
whole file is read and returned as a ``DataFrame``.

Specify a ``chunksize`` or use ``iterator=True`` to obtain reader
objects (``XportReader`` or ``SAS7BDATReader``) for incrementally
reading the file.  The reader objects also have attributes that
contain additional information about the file and its variables.

Read a SAS7BDAT file:

.. code-block:: python

    df = pd.read_sas('sas_data.sas7bdat')

Obtain an iterator and read an XPORT file 100,000 lines at a time:

.. code-block:: python

    rdr = pd.read_sas('sas_xport.xpt', chunk=100000)
    for chunk in rdr:
        do_something(chunk)

The specification_ for the xport file format is available from the SAS
web site.

.. _specification: https://support.sas.com/techsup/technote/ts140.pdf

No official documentation is available for the SAS7BDAT format.

.. _io.other:

Other file formats
------------------

pandas itself only supports IO with a limited set of file formats that map
cleanly to its tabular data model. For reading and writing other file formats
into and from pandas, we recommend these packages from the broader community.

netCDF
''''''

xarray_ provides data structures inspired by the pandas DataFrame for working
with multi-dimensional datasets, with a focus on the netCDF file format and
easy conversion to and from pandas.

.. _xarray: http://xarray.pydata.org/

.. _io.perf:

Performance Considerations
--------------------------

This is an informal comparison of various IO methods, using pandas 0.13.1.

.. code-block:: ipython

   In [1]: df = pd.DataFrame(randn(1000000,2),columns=list('AB'))

   In [2]: df.info()
   <class 'pandas.core.frame.DataFrame'>
   Int64Index: 1000000 entries, 0 to 999999
   Data columns (total 2 columns):
   A    1000000 non-null float64
   B    1000000 non-null float64
   dtypes: float64(2)
   memory usage: 22.9 MB

Writing

.. code-block:: ipython

   In [14]: %timeit test_sql_write(df)
   1 loops, best of 3: 6.24 s per loop

   In [15]: %timeit test_hdf_fixed_write(df)
   1 loops, best of 3: 237 ms per loop

   In [26]: %timeit test_hdf_fixed_write_compress(df)
   1 loops, best of 3: 245 ms per loop

   In [16]: %timeit test_hdf_table_write(df)
   1 loops, best of 3: 901 ms per loop

   In [27]: %timeit test_hdf_table_write_compress(df)
   1 loops, best of 3: 952 ms per loop

   In [17]: %timeit test_csv_write(df)
   1 loops, best of 3: 3.44 s per loop

Reading

.. code-block:: ipython

   In [18]: %timeit test_sql_read()
   1 loops, best of 3: 766 ms per loop

   In [19]: %timeit test_hdf_fixed_read()
   10 loops, best of 3: 19.1 ms per loop

   In [28]: %timeit test_hdf_fixed_read_compress()
   10 loops, best of 3: 36.3 ms per loop

   In [20]: %timeit test_hdf_table_read()
   10 loops, best of 3: 39 ms per loop

   In [29]: %timeit test_hdf_table_read_compress()
   10 loops, best of 3: 60.6 ms per loop

   In [22]: %timeit test_csv_read()
   1 loops, best of 3: 620 ms per loop

Space on disk (in bytes)

.. code-block:: none

    25843712 Apr  8 14:11 test.sql
    24007368 Apr  8 14:11 test_fixed.hdf
    15580682 Apr  8 14:11 test_fixed_compress.hdf
    24458444 Apr  8 14:11 test_table.hdf
    16797283 Apr  8 14:11 test_table_compress.hdf
    46152810 Apr  8 14:11 test.csv

And here's the code

.. code-block:: python

   import sqlite3
   import os
   from pandas.io import sql

   df = pd.DataFrame(randn(1000000,2),columns=list('AB'))

   def test_sql_write(df):
       if os.path.exists('test.sql'):
           os.remove('test.sql')
       sql_db = sqlite3.connect('test.sql')
       df.to_sql(name='test_table', con=sql_db)
       sql_db.close()

   def test_sql_read():
       sql_db = sqlite3.connect('test.sql')
       pd.read_sql_query("select * from test_table", sql_db)
       sql_db.close()

   def test_hdf_fixed_write(df):
       df.to_hdf('test_fixed.hdf','test',mode='w')

   def test_hdf_fixed_read():
       pd.read_hdf('test_fixed.hdf','test')

   def test_hdf_fixed_write_compress(df):
       df.to_hdf('test_fixed_compress.hdf','test',mode='w',complib='blosc')

   def test_hdf_fixed_read_compress():
       pd.read_hdf('test_fixed_compress.hdf','test')

   def test_hdf_table_write(df):
       df.to_hdf('test_table.hdf','test',mode='w',format='table')

   def test_hdf_table_read():
       pd.read_hdf('test_table.hdf','test')

   def test_hdf_table_write_compress(df):
       df.to_hdf('test_table_compress.hdf','test',mode='w',complib='blosc',format='table')

   def test_hdf_table_read_compress():
       pd.read_hdf('test_table_compress.hdf','test')

   def test_csv_write(df):
       df.to_csv('test.csv',mode='w')

   def test_csv_read():
       pd.read_csv('test.csv',index_col=0)
