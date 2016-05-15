.. Copyright 2013-2016 The Salish Sea MEOPAR conttributors
.. and The University of British Columbia
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.


.. _SalishSeaCmdChangesThatBreakBackwardCompatibility:

*************************************************************
:kbd:`SalishSeaCmd` Changes That Break Backward Compatibility
*************************************************************

Version 2.2
===========

The following changes that were introduced in version 2.2 of the :kbd:`SalishSeaCmd` package are incompatible with earlier versions:

* Specification of which :file:`iodef.xml` file NEMO should use has been moved from the command-line to the YAML run description file;
  see :ref:`salishsea-run` or use :command:`salishsea help run` to see the new command-line usage.

  * For NEMO-3.6 the :kbd:`output` section of the run description YAML file must now contain a :kbd:`files` key,
    the value of which is the file path/name of the :file:`iodef.xml` file to use for the run.
    For example:

    .. code-block:: yaml

        output:
          files: iodef.xml

    If the path is relative,
    it is taken from the directory in which the run description YAML file resides.

  * For NEMO-3.4 the run description YAML file must now contain an :kbd:`output` section that contains a :kbd:`files` key,
    the value of which is the file path/name of the :file:`iodef.xml` file to use for the run.
    For example:

    .. code-block:: yaml

        output:
          files: iodef.xml

    If the path is relative,
    it is taken from the directory in which the run description YAML file resides.


Version 2.1
===========

The following changes that were introduced in version 2.1 of the :kbd:`SalishSeaCmd` package are incompatible with earlier versions:

* For NEMO-3.6 the :kbd:`forcing` section of the run description YAML file now contains sub-sections that provide the names of directories and file that are to be symlinked in the run directory for NEMO to use to read initial conditions and forcing values from.
  For example:

  .. code-block:: yaml

      forcing:
        NEMO-atmos:
          link to: /results/forcing/atmospheric/GEM2.5/operational/
        restart.nc:
          link to: /results/SalishSea/nowcast-green/06dec15/SalishSea_00004320_restart.nc
        restart_trc.nc:
          link to: /results/SalishSea/nowcast-green/06dec15/SalishSea_00004320_restart_trc.nc
        open_boundaries:
          link to: open_boundaries/
        rivers:
          link to: rivers/

  The keys are the names of the symlinks that will be created in the run directory.
  Those names are expected to appear in the appropriate places in the namelists.
  The values associated with the :kbd:`link to` keys are the targets of the symlinks that will be created.

  A sub-section that provides a directory of atmospheric forcing files to link to may also include a :kbd:`check link` sub-sub-section.
  :kbd:`check link` contains 2 key-value pairs:

  * The :kbd:`type` key provides the type of checking to perform on the link
  * The value associated with the :kbd:`namelist filename` key is the name of the namelist file in which the atmospheric forcing link is used.

  .. code-block:: yaml

    forcing:
      NEMO-atmos:
        link to: /results/forcing/atmospheric/GEM2.5/operational/
        check link:
          type: atmospheric
          namelist filename: namelist_cfg

  Link checking can be disabled by excluding the :kbd:`check link` section,
  or by setting the value associated with the :kbd:`type` key to :py:obj:`None`.

  See :ref:`NEMO-3.6-Forcing` for details.

  For NEMO-3.4 the :kbd:`forcing` section is unchanged,
  the hard-coded symlink names remain the same,
  and provision of a tracers restart file is not supported.


* For NEMO-3.6 the :kbd:`namelists` section of the run description YAML file is now a dict of lists.
  The dict keys are the names of the :file:`namelist*_cfg` files to create and the element(s) of the list under each key are the namelist section files to be concatenated to create the file named by the key.
  For example:

  .. code-block:: yaml

      namelists:
        namelist_cfg:
          - namelist.time
          - namelist.domain
          - namelist.surface
          - namelist.lateral
          - namelist.bottom
          - namelist.tracer
          - namelist.dynamics
          - namelist.vertical
          - namelist.compute
        namelist_top_cfg:
          - namelist_top_cfg
        namelist_pisces_cfg:
          - namelist_pisces_cfg

  The :kbd:`namelist_cfg` key is required to create the basic namelist for running NEMO-3.6.
  Other :kbd:`namelist*_cfg` keys are optional.
  At least 1 namelist section file is required for each :kbd:`namelist*_cfg` key that is used.

  See :ref:`NEMO-3.6-Namelists` for details.

  For NEMO-3.4 the :kbd:`namelists` section remains a simple list of namelist section files,
  and construction of namelists for tracers,
  biology,
  etc. is not supported.

* The :py:func:`SalishSeaCmd.api.run_description` and :py:func:`SalishSeaCmd.api.run_in_subprocess` functions now accept a :kbd:`nemo34` argument that defaults to :py:obj:`False`.
  That means that those functions now assume that their objective is a NEMO-3.6 run.

* In the :py:func:`SalishSeaCmd.api.run_description` function,
  the name of the argument that is used to pass in the path to the :file:`NEMO-forcing/` directory has been changed from :kbd:`forcing` to :kbd:`forcing_path`.
  This change affects both NEMO-3.4 and NEMO-3.6 uses of the function.

* The :py:func:`SalishSeaCmd.api.run_description` function now accepts a :kbd:`forcing` argument that can be used to pass in a forcing links :py:obj:`dict`.
  The :py:obj:`dict` must match the forcing links data structure described in :ref:`RunDescriptionFileStructure` for the version of NEMO that you are using.
  For NEMO-3.4,
  the default value of :py:obj:`None` will result in "sensible" default values being set for the forcing links.
  For NEMO-3.6,
  it is impossible to guess what "sensible" default values might be,
  so the default value of :py:obj:`None` is simply passed through.


Version 2.0
===========

The following changes that were introduced in version 2.0 of the :kbd:`SalishSeaCmd` package are incompatible with earlier versions:

* The :kbd:`gather` and :kbd:`combine` sub-commands now take a :option:`--compress` command-line option to cause the results files to be :program:`gzip` compressed.
  Previously,
  :program:`gzip` compression was the default and the :option:`--no-compress` option was required to prevent it.
  The :kbd:`run`,
  :kbd:`gather`,
  and :kbd:`combine` sub-commands are now all consistent in defaulting to no compression of the results files.

* The run description YAML file must now contain an :kbd:`MPI decomposition` key-value pair,
  for example:

  .. code-block:: yaml

      MPI decomposition: 8x18

  The value is used to write the correct MPI decomposition values into the :file:`namelist.compute` namelist section file.
  That means that it is no longer necessary to a collection of :file:`namelist.compute.*` files for different MPI decompositions.
  The value is also used to tell the :program:`REBUILD_NEMO` script how many results file sections to operate on.
