.. currentmodule:: pandas

.. ipython:: python
   :suppress:

   import numpy as np
   np.random.seed(123456)
   np.set_printoptions(precision=4, suppress=True)
   import pandas as pd
   import matplotlib
   matplotlib.style.use('ggplot')
   import matplotlib.pyplot as plt
   plt.close('all')
   pd.options.display.max_rows=15

.. _computation:

Computational tools
===================

Statistical Functions
---------------------

.. _computation.pct_change:

Percent Change
~~~~~~~~~~~~~~

``Series``, ``DataFrame``, and ``Panel`` all have a method ``pct_change`` to compute the
percent change over a given number of periods (using ``fill_method`` to fill
NA/null values *before* computing the percent change).

.. ipython:: python

   ser = pd.Series(np.random.randn(8))

   ser.pct_change()

.. ipython:: python

   df = pd.DataFrame(np.random.randn(10, 4))

   df.pct_change(periods=3)

.. _computation.covariance:

Covariance
~~~~~~~~~~

The ``Series`` object has a method ``cov`` to compute covariance between series
(excluding NA/null values).

.. ipython:: python

   s1 = pd.Series(np.random.randn(1000))
   s2 = pd.Series(np.random.randn(1000))
   s1.cov(s2)

Analogously, ``DataFrame`` has a method ``cov`` to compute pairwise covariances
among the series in the DataFrame, also excluding NA/null values.

.. _computation.covariance.caveats:

.. note::

    Assuming the missing data are missing at random this results in an estimate
    for the covariance matrix which is unbiased. However, for many applications
    this estimate may not be acceptable because the estimated covariance matrix
    is not guaranteed to be positive semi-definite. This could lead to
    estimated correlations having absolute values which are greater than one,
    and/or a non-invertible covariance matrix. See `Estimation of covariance
    matrices <http://en.wikipedia.org/w/index.php?title=Estimation_of_covariance_matrices>`_
    for more details.

.. ipython:: python

   frame = pd.DataFrame(np.random.randn(1000, 5), columns=['a', 'b', 'c', 'd', 'e'])
   frame.cov()

``DataFrame.cov`` also supports an optional ``min_periods`` keyword that
specifies the required minimum number of observations for each column pair
in order to have a valid result.

.. ipython:: python

   frame = pd.DataFrame(np.random.randn(20, 3), columns=['a', 'b', 'c'])
   frame.ix[:5, 'a'] = np.nan
   frame.ix[5:10, 'b'] = np.nan

   frame.cov()

   frame.cov(min_periods=12)


.. _computation.correlation:

Correlation
~~~~~~~~~~~

Several methods for computing correlations are provided:

.. csv-table::
    :header: "Method name", "Description"
    :widths: 20, 80

    ``pearson (default)``, Standard correlation coefficient
    ``kendall``, Kendall Tau correlation coefficient
    ``spearman``, Spearman rank correlation coefficient

.. \rho = \cov(x, y) / \sigma_x \sigma_y

All of these are currently computed using pairwise complete observations.

.. note::

    Please see the :ref:`caveats <computation.covariance.caveats>` associated
    with this method of calculating correlation matrices in the
    :ref:`covariance section <computation.covariance>`.

.. ipython:: python

   frame = pd.DataFrame(np.random.randn(1000, 5), columns=['a', 'b', 'c', 'd', 'e'])
   frame.ix[::2] = np.nan

   # Series with Series
   frame['a'].corr(frame['b'])
   frame['a'].corr(frame['b'], method='spearman')

   # Pairwise correlation of DataFrame columns
   frame.corr()

Note that non-numeric columns will be automatically excluded from the
correlation calculation.

Like ``cov``, ``corr`` also supports the optional ``min_periods`` keyword:

.. ipython:: python

   frame = pd.DataFrame(np.random.randn(20, 3), columns=['a', 'b', 'c'])
   frame.ix[:5, 'a'] = np.nan
   frame.ix[5:10, 'b'] = np.nan

   frame.corr()

   frame.corr(min_periods=12)


A related method ``corrwith`` is implemented on DataFrame to compute the
correlation between like-labeled Series contained in different DataFrame
objects.

.. ipython:: python

   index = ['a', 'b', 'c', 'd', 'e']
   columns = ['one', 'two', 'three', 'four']
   df1 = pd.DataFrame(np.random.randn(5, 4), index=index, columns=columns)
   df2 = pd.DataFrame(np.random.randn(4, 4), index=index[:4], columns=columns)
   df1.corrwith(df2)
   df2.corrwith(df1, axis=1)

.. _computation.ranking:

Data ranking
~~~~~~~~~~~~

The ``rank`` method produces a data ranking with ties being assigned the mean
of the ranks (by default) for the group:

.. ipython:: python

   s = pd.Series(np.random.np.random.randn(5), index=list('abcde'))
   s['d'] = s['b'] # so there's a tie
   s.rank()

``rank`` is also a DataFrame method and can rank either the rows (``axis=0``)
or the columns (``axis=1``). ``NaN`` values are excluded from the ranking.

.. ipython:: python

   df = pd.DataFrame(np.random.np.random.randn(10, 6))
   df[4] = df[2][:5] # some ties
   df
   df.rank(1)

``rank`` optionally takes a parameter ``ascending`` which by default is true;
when false, data is reverse-ranked, with larger values assigned a smaller rank.

``rank`` supports different tie-breaking methods, specified with the ``method``
parameter:

  - ``average`` : average rank of tied group
  - ``min`` : lowest rank in the group
  - ``max`` : highest rank in the group
  - ``first`` : ranks assigned in the order they appear in the array

.. _stats.moments:

Window Functions
----------------

.. currentmodule:: pandas.core.window

.. warning::

   Prior to version 0.18.0, ``pd.rolling_*``, ``pd.expanding_*``, and ``pd.ewm*`` were module level
   functions and are now deprecated. These are replaced by using the :class:`~pandas.core.window.Rolling`, :class:`~pandas.core.window.Expanding` and :class:`~pandas.core.window.EWM`. objects and a corresponding method call.

   The deprecation warning will show the new syntax, see an example :ref:`here <whatsnew_0180.window_deprecations>`
   You can view the previous documentation
   `here <http://pandas.pydata.org/pandas-docs/version/0.17.1/computation.html#moving-rolling-statistics-moments>`__

For working with data, a number of windows functions are provided for
computing common *window* or *rolling* statistics. Among these are count, sum,
mean, median, correlation, variance, covariance, standard deviation, skewness,
and kurtosis.

.. note::

   The API for window statistics is quite similar to the way one works with ``GroupBy`` objects, see the documentation :ref:`here <groupby>`

We work with ``rolling``, ``expanding`` and ``exponentially weighted`` data through the corresponding
objects, :class:`~pandas.core.window.Rolling`, :class:`~pandas.core.window.Expanding` and :class:`~pandas.core.window.EWM`.

.. ipython:: python

   s = pd.Series(np.random.randn(1000), index=pd.date_range('1/1/2000', periods=1000))
   s = s.cumsum()
   s

These are created from methods on ``Series`` and ``DataFrame``.

.. ipython:: python

   r = s.rolling(window=60)
   r

These object provide tab-completion of the avaible methods and properties.

.. code-block:: ipython

   In [14]: r.
   r.agg         r.apply       r.count       r.exclusions  r.max         r.median      r.name        r.skew        r.sum
   r.aggregate   r.corr        r.cov         r.kurt        r.mean        r.min         r.quantile    r.std         r.var

Generally these methods all have the same interface. They all
accept the following arguments:

- ``window``: size of moving window
- ``min_periods``: threshold of non-null data points to require (otherwise
  result is NA)
- ``center``: boolean, whether to set the labels at the center (default is False)

.. warning::

   The ``freq`` and ``how`` arguments were in the API prior to 0.18.0 changes. These are deprecated in the new API. You can simply resample the input prior to creating a window function.

   For example, instead of ``s.rolling(window=5,freq='D').max()`` to get the max value on a rolling 5 Day window, one could use ``s.resample('D').max().rolling(window=5).max()``, which first resamples the data to daily data, then provides a rolling 5 day window.

We can then call methods on these ``rolling`` objects. These return like-indexed objects:

.. ipython:: python

   r.mean()

.. ipython:: python

   s.plot(style='k--')

   @savefig rolling_mean_ex.png
   r.mean().plot(style='k')

.. ipython:: python
   :suppress:

   plt.close('all')

They can also be applied to DataFrame objects. This is really just syntactic
sugar for applying the moving window operator to all of the DataFrame's columns:

.. ipython:: python

   df = pd.DataFrame(np.random.randn(1000, 4),
                     index=pd.date_range('1/1/2000', periods=1000),
                     columns=['A', 'B', 'C', 'D'])
   df = df.cumsum()

   @savefig rolling_mean_frame.png
   df.rolling(window=60).sum().plot(subplots=True)

.. _stats.summary:

Method Summary
~~~~~~~~~~~~~~

We provide a number of the common statistical functions:

.. currentmodule:: pandas.core.window

.. csv-table::
    :header: "Method", "Description"
    :widths: 20, 80

    :meth:`~Rolling.count`, Number of non-null observations
    :meth:`~Rolling.sum`, Sum of values
    :meth:`~Rolling.mean`, Mean of values
    :meth:`~Rolling.median`, Arithmetic median of values
    :meth:`~Rolling.min`, Minimum
    :meth:`~Rolling.max`, Maximum
    :meth:`~Rolling.std`, Bessel-corrected sample standard deviation
    :meth:`~Rolling.var`, Unbiased variance
    :meth:`~Rolling.skew`, Sample skewness (3rd moment)
    :meth:`~Rolling.kurt`, Sample kurtosis (4th moment)
    :meth:`~Rolling.quantile`, Sample quantile (value at %)
    :meth:`~Rolling.apply`, Generic apply
    :meth:`~Rolling.cov`, Unbiased covariance (binary)
    :meth:`~Rolling.corr`, Correlation (binary)

The :meth:`~Rolling.apply` function takes an extra ``func`` argument and performs
generic rolling computations. The ``func`` argument should be a single function
that produces a single value from an ndarray input. Suppose we wanted to
compute the mean absolute deviation on a rolling basis:

.. ipython:: python

   mad = lambda x: np.fabs(x - x.mean()).mean()
   @savefig rolling_apply_ex.png
   s.rolling(window=60).apply(mad).plot(style='k')

.. _stats.rolling_window:

Rolling Windows
~~~~~~~~~~~~~~~

Passing ``win_type`` to ``.rolling`` generates a generic rolling window computation, that is weighted according the ``win_type``.
The following methods are available:

.. csv-table::
    :header: "Method", "Description"
    :widths: 20, 80

    :meth:`~Window.sum`, Sum of values
    :meth:`~Window.mean`, Mean of values

The weights used in the window are specified by the ``win_type`` keyword. The list of recognized types are:

- ``boxcar``
- ``triang``
- ``blackman``
- ``hamming``
- ``bartlett``
- ``parzen``
- ``bohman``
- ``blackmanharris``
- ``nuttall``
- ``barthann``
- ``kaiser`` (needs beta)
- ``gaussian`` (needs std)
- ``general_gaussian`` (needs power, width)
- ``slepian`` (needs width).

.. ipython:: python

   ser = pd.Series(np.random.randn(10), index=pd.date_range('1/1/2000', periods=10))

   ser.rolling(window=5, win_type='triang').mean()

Note that the ``boxcar`` window is equivalent to :meth:`~Rolling.mean`.

.. ipython:: python

   ser.rolling(window=5, win_type='boxcar').mean()
   ser.rolling(window=5).mean()

For some windowing functions, additional parameters must be specified:

.. ipython:: python

   ser.rolling(window=5, win_type='gaussian').mean(std=0.1)

.. _stats.moments.normalization:

.. note::

    For ``.sum()`` with a ``win_type``, there is no normalization done to the
    weights for the window. Passing custom weights of ``[1, 1, 1]`` will yield a different
    result than passing weights of ``[2, 2, 2]``, for example. When passing a
    ``win_type`` instead of explicitly specifying the weights, the weights are
    already normalized so that the largest weight is 1.

    In contrast, the nature of the ``.mean()`` calculation is
    such that the weights are normalized with respect to each other. Weights
    of ``[1, 1, 1]`` and ``[2, 2, 2]`` yield the same result.

.. _stats.moments.ts:

Time-aware Rolling
~~~~~~~~~~~~~~~~~~

.. versionadded:: 0.19.0

New in version 0.19.0 are the ability to pass an offset (or convertible) to a ``.rolling()`` method and have it produce
variable sized windows based on the passed time window. For each time point, this includes all preceding values occurring
within the indicated time delta.

This can be particularly useful for a non-regular time frequency index.

.. ipython:: python

   dft = pd.DataFrame({'B': [0, 1, 2, np.nan, 4]},
                      index=pd.date_range('20130101 09:00:00', periods=5, freq='s'))
   dft

This is a regular frequency index. Using an integer window parameter works to roll along the window frequency.

.. ipython:: python

   dft.rolling(2).sum()
   dft.rolling(2, min_periods=1).sum()

Specifying an offset allows a more intuitive specification of the rolling frequency.

.. ipython:: python

   dft.rolling('2s').sum()

Using a non-regular, but still monotonic index, rolling with an integer window does not impart any special calculation.


.. ipython:: python

   dft = pd.DataFrame({'B': [0, 1, 2, np.nan, 4]},
                      index = pd.Index([pd.Timestamp('20130101 09:00:00'),
                                        pd.Timestamp('20130101 09:00:02'),
                                        pd.Timestamp('20130101 09:00:03'),
                                        pd.Timestamp('20130101 09:00:05'),
                                        pd.Timestamp('20130101 09:00:06')],
                                       name='foo'))
   dft
   dft.rolling(2).sum()


Using the time-specification generates variable windows for this sparse data.

.. ipython:: python

   dft.rolling('2s').sum()

Furthermore, we now allow an optional ``on`` parameter to specify a column (rather than the
default of the index) in a DataFrame.

.. ipython:: python

   dft = dft.reset_index()
   dft
   dft.rolling('2s', on='foo').sum()

.. _stats.moments.ts-versus-resampling:

Time-aware Rolling vs. Resampling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using ``.rolling()`` with a time-based index is quite similar to :ref:`resampling <timeseries.resampling>`. They
both operate and perform reductive operations on time-indexed pandas objects.

When using ``.rolling()`` with an offset. The offset is a time-delta. Take a backwards-in-time looking window, and
aggregate all of the values in that window (including the end-point, but not the start-point). This is the new value
at that point in the result. These are variable sized windows in time-space for each point of the input. You will get
a same sized result as the input.

When using ``.resample()`` with an offset. Construct a new index that is the frequency of the offset. For each frequency
bin, aggregate points from the input within a backwards-in-time looking window that fall in that bin. The result of this
aggregation is the output for that frequency point. The windows are fixed size size in the frequency space. Your result
will have the shape of a regular frequency between the min and the max of the original input object.

To summarize, ``.rolling()`` is a time-based window operation, while ``.resample()`` is a frequency-based window operation.

Centering Windows
~~~~~~~~~~~~~~~~~

By default the labels are set to the right edge of the window, but a
``center`` keyword is available so the labels can be set at the center.

.. ipython:: python

   ser.rolling(window=5).mean()
   ser.rolling(window=5, center=True).mean()

.. _stats.moments.binary:

Binary Window Functions
~~~~~~~~~~~~~~~~~~~~~~~

:meth:`~Rolling.cov` and :meth:`~Rolling.corr` can compute moving window statistics about
two ``Series`` or any combination of ``DataFrame/Series`` or
``DataFrame/DataFrame``. Here is the behavior in each case:

- two ``Series``: compute the statistic for the pairing.
- ``DataFrame/Series``: compute the statistics for each column of the DataFrame
  with the passed Series, thus returning a DataFrame.
- ``DataFrame/DataFrame``: by default compute the statistic for matching column
  names, returning a DataFrame. If the keyword argument ``pairwise=True`` is
  passed then computes the statistic for each pair of columns, returning a
  ``Panel`` whose ``items`` are the dates in question (see :ref:`the next section
  <stats.moments.corr_pairwise>`).

For example:

.. ipython:: python

   df2 = df[:20]
   df2.rolling(window=5).corr(df2['B'])

.. _stats.moments.corr_pairwise:

Computing rolling pairwise covariances and correlations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In financial data analysis and other fields it's common to compute covariance
and correlation matrices for a collection of time series. Often one is also
interested in moving-window covariance and correlation matrices. This can be
done by passing the ``pairwise`` keyword argument, which in the case of
``DataFrame`` inputs will yield a ``Panel`` whose ``items`` are the dates in
question. In the case of a single DataFrame argument the ``pairwise`` argument
can even be omitted:

.. note::

    Missing values are ignored and each entry is computed using the pairwise
    complete observations.  Please see the :ref:`covariance section
    <computation.covariance>` for :ref:`caveats
    <computation.covariance.caveats>` associated with this method of
    calculating covariance and correlation matrices.

.. ipython:: python

   covs = df[['B','C','D']].rolling(window=50).cov(df[['A','B','C']], pairwise=True)
   covs[df.index[-50]]

.. ipython:: python

   correls = df.rolling(window=50).corr()
   correls[df.index[-50]]

You can efficiently retrieve the time series of correlations between two
columns using ``.loc`` indexing:

.. ipython:: python
   :suppress:

   plt.close('all')

.. ipython:: python

   @savefig rolling_corr_pairwise_ex.png
   correls.loc[:, 'A', 'C'].plot()

.. _stats.aggregate:

Aggregation
-----------

Once the ``Rolling``, ``Expanding`` or ``EWM`` objects have been created, several methods are available to
perform multiple computations on the data. This is very similar to a ``.groupby(...).agg`` seen :ref:`here <groupby.aggregate>`.

.. ipython:: python

   dfa = pd.DataFrame(np.random.randn(1000, 3),
                      index=pd.date_range('1/1/2000', periods=1000),
                      columns=['A', 'B', 'C'])
   r = dfa.rolling(window=60,min_periods=1)
   r

We can aggregate by passing a function to the entire DataFrame, or select a Series (or multiple Series) via standard getitem.

.. ipython:: python

   r.aggregate(np.sum)

   r['A'].aggregate(np.sum)

   r[['A','B']].aggregate(np.sum)

As you can see, the result of the aggregation will have the selected columns, or all
columns if none are selected.

.. _stats.aggregate.multifunc:

Applying multiple functions at once
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With windowed Series you can also pass a list or dict of functions to do
aggregation with, outputting a DataFrame:

.. ipython:: python

   r['A'].agg([np.sum, np.mean, np.std])

If a dict is passed, the keys will be used to name the columns. Otherwise the
function's name (stored in the function object) will be used.

.. ipython:: python

   r['A'].agg({'result1' : np.sum,
               'result2' : np.mean})

On a widowed DataFrame, you can pass a list of functions to apply to each
column, which produces an aggregated result with a hierarchical index:

.. ipython:: python

   r.agg([np.sum, np.mean])

Passing a dict of functions has different behavior by default, see the next
section.

Applying different functions to DataFrame columns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By passing a dict to ``aggregate`` you can apply a different aggregation to the
columns of a DataFrame:

.. ipython:: python
   :okexcept:

   r.agg({'A' : np.sum,
          'B' : lambda x: np.std(x, ddof=1)})

The function names can also be strings. In order for a string to be valid it
must be implemented on the windowed object

.. ipython:: python

   r.agg({'A' : 'sum', 'B' : 'std'})

Furthermore you can pass a nested dict to indicate different aggregations on different columns.

.. ipython:: python

   r.agg({'A' : ['sum','std'], 'B' : ['mean','std'] })


.. _stats.moments.expanding:

Expanding Windows
-----------------

A common alternative to rolling statistics is to use an *expanding* window,
which yields the value of the statistic with all the data available up to that
point in time.

These follow a similar interface to ``.rolling``, with the ``.expanding`` method
returning an :class:`~pandas.core.window.Expanding` object.

As these calculations are a special case of rolling statistics,
they are implemented in pandas such that the following two calls are equivalent:

.. ipython:: python

   df.rolling(window=len(df), min_periods=1).mean()[:5]

   df.expanding(min_periods=1).mean()[:5]

These have a similar set of methods to ``.rolling`` methods.

Method Summary
~~~~~~~~~~~~~~

.. currentmodule:: pandas.core.window

.. csv-table::
    :header: "Function", "Description"
    :widths: 20, 80

    :meth:`~Expanding.count`, Number of non-null observations
    :meth:`~Expanding.sum`, Sum of values
    :meth:`~Expanding.mean`, Mean of values
    :meth:`~Expanding.median`, Arithmetic median of values
    :meth:`~Expanding.min`, Minimum
    :meth:`~Expanding.max`, Maximum
    :meth:`~Expanding.std`, Unbiased standard deviation
    :meth:`~Expanding.var`, Unbiased variance
    :meth:`~Expanding.skew`, Unbiased skewness (3rd moment)
    :meth:`~Expanding.kurt`, Unbiased kurtosis (4th moment)
    :meth:`~Expanding.quantile`, Sample quantile (value at %)
    :meth:`~Expanding.apply`, Generic apply
    :meth:`~Expanding.cov`, Unbiased covariance (binary)
    :meth:`~Expanding.corr`, Correlation (binary)

Aside from not having a ``window`` parameter, these functions have the same
interfaces as their ``.rolling`` counterparts. Like above, the parameters they
all accept are:

- ``min_periods``: threshold of non-null data points to require. Defaults to
  minimum needed to compute statistic. No ``NaNs`` will be output once
  ``min_periods`` non-null data points have been seen.
- ``center``: boolean, whether to set the labels at the center (default is False)

.. note::

   The output of the ``.rolling`` and ``.expanding`` methods do not return a
   ``NaN`` if there are at least ``min_periods`` non-null values in the current
   window. This differs from ``cumsum``, ``cumprod``, ``cummax``, and
   ``cummin``, which return ``NaN`` in the output wherever a ``NaN`` is
   encountered in the input.

An expanding window statistic will be more stable (and less responsive) than
its rolling window counterpart as the increasing window size decreases the
relative impact of an individual data point. As an example, here is the
:meth:`~Expanding.mean` output for the previous time series dataset:

.. ipython:: python
   :suppress:

   plt.close('all')

.. ipython:: python

   s.plot(style='k--')

   @savefig expanding_mean_frame.png
   s.expanding().mean().plot(style='k')


.. _stats.moments.exponentially_weighted:

Exponentially Weighted Windows
------------------------------

A related set of functions are exponentially weighted versions of several of
the above statistics. A similar interface to ``.rolling`` and ``.expanding`` is accessed
thru the ``.ewm`` method to receive an :class:`~pandas.core.window.EWM` object.
A number of expanding EW (exponentially weighted)
methods are provided:

.. currentmodule:: pandas.core.window

.. csv-table::
    :header: "Function", "Description"
    :widths: 20, 80

    :meth:`~EWM.mean`, EW moving average
    :meth:`~EWM.var`, EW moving variance
    :meth:`~EWM.std`, EW moving standard deviation
    :meth:`~EWM.corr`, EW moving correlation
    :meth:`~EWM.cov`, EW moving covariance

In general, a weighted moving average is calculated as

.. math::

    y_t = \frac{\sum_{i=0}^t w_i x_{t-i}}{\sum_{i=0}^t w_i},

where :math:`x_t` is the input and :math:`y_t` is the result.

The EW functions support two variants of exponential weights.
The default, ``adjust=True``, uses the weights :math:`w_i = (1 - \alpha)^i`
which gives

.. math::

    y_t = \frac{x_t + (1 - \alpha)x_{t-1} + (1 - \alpha)^2 x_{t-2} + ...
    + (1 - \alpha)^t x_{0}}{1 + (1 - \alpha) + (1 - \alpha)^2 + ...
    + (1 - \alpha)^t}

When ``adjust=False`` is specified, moving averages are calculated as

.. math::

    y_0 &= x_0 \\
    y_t &= (1 - \alpha) y_{t-1} + \alpha x_t,

which is equivalent to using weights

.. math::

    w_i = \begin{cases}
        \alpha (1 - \alpha)^i & \text{if } i < t \\
        (1 - \alpha)^i        & \text{if } i = t.
    \end{cases}

.. note::

   These equations are sometimes written in terms of :math:`\alpha' = 1 - \alpha`, e.g.

   .. math::

      y_t = \alpha' y_{t-1} + (1 - \alpha') x_t.

The difference between the above two variants arises because we are
dealing with series which have finite history. Consider a series of infinite
history:

.. math::

    y_t = \frac{x_t + (1 - \alpha)x_{t-1} + (1 - \alpha)^2 x_{t-2} + ...}
    {1 + (1 - \alpha) + (1 - \alpha)^2 + ...}

Noting that the denominator is a geometric series with initial term equal to 1
and a ratio of :math:`1 - \alpha` we have

.. math::

    y_t &= \frac{x_t + (1 - \alpha)x_{t-1} + (1 - \alpha)^2 x_{t-2} + ...}
    {\frac{1}{1 - (1 - \alpha)}}\\
    &= [x_t + (1 - \alpha)x_{t-1} + (1 - \alpha)^2 x_{t-2} + ...] \alpha \\
    &= \alpha x_t + [(1-\alpha)x_{t-1} + (1 - \alpha)^2 x_{t-2} + ...]\alpha \\
    &= \alpha x_t + (1 - \alpha)[x_{t-1} + (1 - \alpha) x_{t-2} + ...]\alpha\\
    &= \alpha x_t + (1 - \alpha) y_{t-1}

which shows the equivalence of the above two variants for infinite series.
When ``adjust=True`` we have :math:`y_0 = x_0` and from the last
representation above we have :math:`y_t = \alpha x_t + (1 - \alpha) y_{t-1}`,
therefore there is an assumption that :math:`x_0` is not an ordinary value
but rather an exponentially weighted moment of the infinite series up to that
point.

One must have :math:`0 < \alpha \leq 1`, and while since version 0.18.0
it has been possible to pass :math:`\alpha` directly, it's often easier
to think about either the **span**, **center of mass (com)** or **half-life**
of an EW moment:

.. math::

   \alpha =
    \begin{cases}
        \frac{2}{s + 1},               & \text{for span}\ s \geq 1\\
        \frac{1}{1 + c},               & \text{for center of mass}\ c \geq 0\\
        1 - \exp^{\frac{\log 0.5}{h}}, & \text{for half-life}\ h > 0
    \end{cases}

One must specify precisely one of **span**, **center of mass**, **half-life**
and **alpha** to the EW functions:

- **Span** corresponds to what is commonly called an "N-day EW moving average".
- **Center of mass** has a more physical interpretation and can be thought of
  in terms of span: :math:`c = (s - 1) / 2`.
- **Half-life** is the period of time for the exponential weight to reduce to
  one half.
- **Alpha** specifies the smoothing factor directly.

Here is an example for a univariate time series:

.. ipython:: python

   s.plot(style='k--')

   @savefig ewma_ex.png
   s.ewm(span=20).mean().plot(style='k')

EWM has a ``min_periods`` argument, which has the same
meaning it does for all the ``.expanding`` and ``.rolling`` methods:
no output values will be set until at least ``min_periods`` non-null values
are encountered in the (expanding) window.
(This is a change from versions prior to 0.15.0, in which the ``min_periods``
argument affected only the ``min_periods`` consecutive entries starting at the
first non-null value.)

EWM also has an ``ignore_na`` argument, which deterines how
intermediate null values affect the calculation of the weights.
When ``ignore_na=False`` (the default), weights are calculated based on absolute
positions, so that intermediate null values affect the result.
When ``ignore_na=True`` (which reproduces the behavior in versions prior to 0.15.0),
weights are calculated by ignoring intermediate null values.
For example, assuming ``adjust=True``, if ``ignore_na=False``, the weighted
average of ``3, NaN, 5`` would be calculated as

.. math::

	\frac{(1-\alpha)^2 \cdot 3 + 1 \cdot 5}{(1-\alpha)^2 + 1}

Whereas if ``ignore_na=True``, the weighted average would be calculated as

.. math::

	\frac{(1-\alpha) \cdot 3 + 1 \cdot 5}{(1-\alpha) + 1}.

The :meth:`~Ewm.var`, :meth:`~Ewm.std`, and :meth:`~Ewm.cov` functions have a ``bias`` argument,
specifying whether the result should contain biased or unbiased statistics.
For example, if ``bias=True``, ``ewmvar(x)`` is calculated as
``ewmvar(x) = ewma(x**2) - ewma(x)**2``;
whereas if ``bias=False`` (the default), the biased variance statistics
are scaled by debiasing factors

.. math::

    \frac{\left(\sum_{i=0}^t w_i\right)^2}{\left(\sum_{i=0}^t w_i\right)^2 - \sum_{i=0}^t w_i^2}.

(For :math:`w_i = 1`, this reduces to the usual :math:`N / (N - 1)` factor,
with :math:`N = t + 1`.)
See `Weighted Sample Variance <http://en.wikipedia.org/wiki/Weighted_arithmetic_mean#Weighted_sample_variance>`__
for further details.
