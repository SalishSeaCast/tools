.. Copyright 2013-2016 The Salish Sea MEOPAR contributors
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


***************
Marlin Commands
***************

The main purpose of the :py:obj:`Marlin` package is to automate the process of incorporating Subversion revisions from the NEMO master repository into our Mercurial repository.
See :ref:`PullChangesFromNEMOsvn` for details of how the :command:`marlin` command is used.

Use :kbd:`marlin --help` to see the available options and sub-commands::

  (marlin)$ marlin --help
  usage: marlin [--version] [-v] [--log-file LOG_FILE] [-q] [-h] [--debug]

  Salish Sea NEMO svn-hg Maintenance Tool

  optional arguments:
    --version            show program's version number and exit
    -v, --verbose        Increase verbosity of output. Can be repeated.
    --log-file LOG_FILE  Specify a file to log output. Disabled by default.
    -q, --quiet          suppress output except warnings and errors
    -h, --help           show this help message and exit
    --debug              show tracebacks on errors

  Commands:
    complete       print bash completion command
    help           print detailed help for another command
    incoming       Display SVN log of revisions that have not yet been brought in
    update         Apply SVN updates from upstream repo & commit them to Mercurial


:kbd:`incoming`
===============

The :kbd:`incoming` sub-command displays a list of SVN revisions from the upstream repo that have not yet been applied to the local working copy.
The list defaults to just the next revision that would be applied by an update operation,
but the :kbd:`-l` or :kbd:`--limit` option allows the list to be extended.
In particular,
:kbd:`-l 0` will show all revisions between the working copy revision and the upstream repo HEAD revision.

.. code-block:: bash

    (marlin)$ marlin help incoming
    usage: marlin incoming [-h] [-l LIMIT]

    Display SVN log of revisions that have not yet been brought in from the
    upstream repo.

    optional arguments:
      -h, --help            show this help message and exit
      -l LIMIT, --limit LIMIT
                            maximum number of log messages to show; defaults to 1


:kbd:`update`
=============

The :kbd:`update` sub-command applies SVN updates from the upstream repo one revision at a time.
After each :command:`svn update` operation is completed the changes are committed to Mercurial using a commit message that identifies the SVN revision of the changes,
and which includes the SVN commit message.

:kbd:`update` defaults to applying just the next revision,
but the :kbd:`--to-rev` option allows revisions up to and including a specific revision number to be applied.

.. code-block:: bash

    $ marlin help update
    usage: marlin update [-h] [--to-rev TO_REV]

    Apply SVN updates from upstream repo & commit them to Mercurial one at a time.

    optional arguments:
      -h, --help       show this help message and exit
      --to-rev TO_REV  SVN revision number to update repo to
