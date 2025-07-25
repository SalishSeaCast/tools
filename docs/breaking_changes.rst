.. Copyright 2013 – present by the SalishSeaCast Project Contributors
.. and The University of British Columbia
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    https://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

.. SPDX-License-Identifier: Apache-2.0


.. _toolsRepoChangesThatBreakBackwardCompatibility:

*****************************************
Changes That Break Backward Compatibility
*****************************************

.. _BreakingChangesVersion25.1:

Version 25.1 (unreleased)
=========================

The following changes that were introduced in version 25.1 of the ``tools`` repository
are incompatible with earlier versions:

* The minimum supported version of Python is 3.11.
  Development of the :py:obj:`SalishSeaTools` package is done using Python 3.13.

* The `erddapy`_ package is now a required dependency to use the :py:mod:`evaltools` module.
  The recommended way to add :py:obj:`erddapy` to your activated ``salishsea-tools`` environment
  is with the command :command:`conda env update -f SalishSeaTools/envs/environment-dev.yaml`

  .. _erddapy: https://ioos.github.io/erddapy/

* The ``variables`` argument has been dropped from the :py:func:`evaltools.load_ferry_ERDDAP`
  and  :py:func:`evaltools.load_ONC_node_ERDDAP` functions because custom variables
  selection was not fully implemented.

* Support for atmospheric forcing data matching has been removed from
  the :py:func:`evaltools.matchData` function.
  A :py:exc:`ValueError` is now raised if ``maskName="ops"``.

* ``mesh_mask_path`` is now a required argument for the :py:func:`evaltools.matchData`
  function.
  The ``mesh_mask_path`` argument was previously called ``meshPath``.
  Requiring a mesh mask path ensures that the user can specify the correct mesh mask for
  the model version that they are matching data to instead of possibly using an incorrect
  mesh mask by default..

* The ``sdim``  argument of the :py:func:`evaltools.matchData` function has been changed to
  ``n_spatial_dims`` to make its meaning more evident.

* The ``preIndexed``  argument of the :py:func:`evaltools.matchData` function has been
  changed to ``pre_indexed`` to make it consistent with Python variable naming style.

* The ``fdict``  argument of the :py:func:`evaltools.matchData` function has been changed to
  ``model_file_hours_res`` to make its meaning more evident.


.. _BreakingChangesVersion24.1:

Version 24.1 (2025-01-09)
=========================

The following changes that were introduced in version 24.1 of the ``tools`` repository
are incompatible with earlier versions:

* Removed docs and package stub for `SalishSeaNowcast`_ package.
  It was moved into its own repository in late-2016.

  .. _SalishSeaNowcast: https://github.com/SalishSeaCast/SalishSeaNowcast

* Removed docs and package stub for `SalishSeaCmd`_ package.
  It was moved into its own repository in late-2016.

  .. _SalishSeaCmd: https://github.com/SalishSeaCast/SalishSeaCmd

* Changed to `CalVer`_ versioning convention.
  Version identifier format is now ``yy.n[.devn]``,
  where ``yy`` is the (post-2000) year of release,
  and ``n`` is the number of the release within the year, starting at ``1``.
  After a release has been made the value of ``n`` is incremented by 1,
  and ``.dev0`` is appended to the version identifier to indicate changes that will be
  included in the next release.
  ``24.1.dev0`` is an exception to that scheme.
  That version identifies the period of development between the ``2.0`` and ``24.1``
  releases.

  .. _CalVer: https://calver.org/
