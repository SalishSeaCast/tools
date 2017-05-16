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


.. _ImportingFilesFromAnotherMercurialRepo:

Importing Files from Another Mercurial Repo
===========================================

Sometimes code and other files that we want to create a new Python package from start life in another Mercurial repo.
That was the case with what is now the :kbd:`SOGTools` package,
which was started in Ben Moore-Maley's `SOG_utils`_ repo.
This section documents the example of how the files and repo history from there were imported into the :file:`tools` repo.

.. _SOG_utils: https://bitbucket.org/bmoorema/sog_utils

To import changesets from another Mercurial repo we use the `Convert Extension`_ that is bundles with Mercurial.
To activate it,
edit your Mercurial configuration file with:

.. code-block:: bash

    $ hg config --edit

and add :kbd:`hgext.convert =` to the :kbd:`[extensions]` section:

.. code-block:: ini

    [extensions]

    hgext.convert =


.. _Convert Extension: https://www.mercurial-scm.org/wiki/ConvertExtension

The most important step of importing files from another repo is the creation of a file map to filter and rename/relocate the files that are being imported.
The `Convert Extension`_ docs explain the syntax and effect of the file map directives.
Here is the file map for the `SOG_utils`_ import into :file:`tools/SOGTools/`:

.. include:: ../../SOG_utils_SOGTools_filemap.txt
    :literal:

That file map is stored in :file:`tools/SOG_utils_SOGTools_filemap.txt` and tracked by Mercurial as part of the record of the creation of the :kbd:`SOGTools` package.
It causes the :file:`SOG_loader.py` and :file:`carbonate.py` files the be stored in :file:`SOGTools/sog_tools/`,
and the :file:`SOG_plotting.ipynb` IPython notebook file to be stored in :file:`SOGTools/notebooks/`.
The necessary directories are created as part of the :command:`hg convert` process.

.. note::

    It is strongly recommended that you practise the :command:`hg convert` process in a clone of the :file:`tools` repo until you are sure that the result is what you intend.
    Getting the file map correct for a complicated repo import can be tricky.

Clone the source repo,
typically beside the :file:`tools` repo:

.. code-block:: bash

    $ cd MEOPAR
    $ hg clone ssh://hg@bitbucket.org/bmoorema/sog_utils

Import the changesets from :file:`sog_utils` into :file:`tools`:

.. code-block:: bash

    $ hg convert --filemap tools/SOG_utitls_SOGTools_filemap.txt sog_utils tools
    scanning source...
    sorting...
    converting...
    2 init repo
    1 Added carbonate and SOG_loader modules
    0 Included more examples in SOG_plotting.ipynb

:file:`tools` now contains a "disconnected" branch that is the changesets from :file:`sog_utils` with the files renamed/relocated according to the file map::

  $ hg glog
  o  changeset:   2156:4c84368d5aab
  |  tag:         tip
  |  user:        Ben Moore-Maley <bmoorema@eos.ubc.ca>
  |  date:        Tue May 05 15:27:45 2015 -0700
  |  summary:     Included more examples in SOG_plotting.ipynb
  |
  o  changeset:   2155:b30c444dfa05
     parent:      -1:000000000000
     user:        Ben Moore-Maley <bmoorema@eos.ubc.ca>
     date:        Tue May 05 15:01:12 2015 -0700
     summary:     Added carbonate and SOG_loader modules

  @  changeset:   2154:3d2c1ce8506d
  |  user:        Doug Latornell <djl@douglatornell.ca>
  |  date:        Thu May 07 11:31:41 2015 -0700
  |  summary:     Remove automatic run date decrement for forecast2 run case.
  |
  ...

Merge the "disconnected" branch,
and commit the result:

.. code-block:: bash

    $ hg merge
    3 files updated, 0 files merged, 0 files removed, 0 files unresolved
    $ hg ci -m"Import @bmoorema's SOG_utils repo to form the basis of the SOGTools package."

resulting in this graph::

  $ hg glog
  @    changeset:   2157:220da9ad7ef9
  |\   tag:         tip
  | |  parent:      2154:3d2c1ce8506d
  | |  parent:      2156:4c84368d5aab
  | |  user:        Doug Latornell <djl@douglatornell.ca>
  | |  date:        Fri May 15 14:36:01 2015 -0700
  | |  summary:     Import @bmoorema's SOG_utils repo to form the basis of the SOGTools package.
  | |
  | o  changeset:   2156:4c84368d5aab
  | |  user:        Ben Moore-Maley <bmoorema@eos.ubc.ca>
  | |  date:        Tue May 05 15:27:45 2015 -0700
  | |  summary:     Included more examples in SOG_plotting.ipynb
  | |
  | o  changeset:   2155:b30c444dfa05
  |    parent:      -1:000000000000
  |    user:        Ben Moore-Maley <bmoorema@eos.ubc.ca>
  |    date:        Tue May 05 15:01:12 2015 -0700
  |    summary:     Added carbonate and SOG_loader modules
  |
  o  changeset:   2154:3d2c1ce8506d
  |  user:        Doug Latornell <djl@douglatornell.ca>
  |  date:        Thu May 07 11:31:41 2015 -0700
  |  summary:     Remove automatic run date decrement for forecast2 run case.
  |
  ...

Now :file:`tools/SOGTools/` contains the files and from the :file:`sog_utils` repo and that repo's history is part of the :file:`tools` repo history,
so we can proceed with turning :file:`SOGTools/` into a Python package.
