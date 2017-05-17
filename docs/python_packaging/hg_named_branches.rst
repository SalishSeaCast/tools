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


.. _MercurialNamedBranches:

************************
Mercurial Named Branches
************************

Mercurial named branches are a "power user" technique that applies a persistent name to a branch of development.
A named branch can be used to isolate a line of development that is expected to take days,
weeks,
or longer to complete.
Isolation of such development on a named branch means that development on the "main" branch of the repository
(which is, in fact, named :kbd:`default`)
can continue in parallel.
Another use case for named branches is isolation of a line of development that will take time and may not prove to be useful in the end,
in which case the branch can be marked as closed,
and abandoned.

Examples of the use of named branches in the :ref:`tools-repo` include:

* Development of v2.0 of the :ref:`SalishSeaCmdProcessor` to support NEMO-3.6 in the :kbd:`SalishSeaCmd-3.6` branch
* Separation of the nowcast system code from the :ref:`SalishSeaToolsPackage` into the :ref:`SalishSeaNowcastPackage` in the :kbd:`SalishSeaNowcast` branch
* Refactoring of the nowcast system web page results figures into a 1 figure per module architecture in the :kbd:`refactor-nowcast-figures` branch

There is a brief description of the key elements of `working with named branches`_ in the Mercurial docs,
and a more narrative discussion in the `Naming branches within a repository`_ in the `Mercurial - The Definitive Guide`_.

.. _Naming branches within a repository: http://hgbook.red-bean.com/read/managing-releases-and-branchy-development.html
.. _working with named branches: https://www.mercurial-scm.org/wiki/NamedBranches
.. _Mercurial - The Definitive Guide: http://hgbook.red-bean.com/

To see the active named branches in a repo use:

.. code-block:: bash

    $ hg branches
    default                     3099:c2c481bf14eb
    refactor-nowcast-figures    3098:ec4ce3412411

To included closed branches in the list use :command:`hg branches --closed`.

To create a new named branch use:

.. code-block:: bash

    $ hg branch refactor-nowcast-figures

To see what branch you are presently on use:

.. code-block:: bash

    $ hg branch

You can also start a named branch from an earlier stage of development by updating to a specific revision before creating the branch:

.. code-block:: bash

    $ hg update -r 500
    $ hg branch my-branch

Commits made on a branch other than :kbd:`default` include the name of the branch in their metadata as you can see with commands like :command:`hg log`,
:command:`hg glog`,
:command:`hg log --graph`,
or :command:`hg tip`::

  changeset:   3097:fb2b10884a4f
  branch:      refactor-nowcast-figures
  tag:         tip
  user:        Doug Latornell <djl@douglatornell.ca>
  date:        Sun Mar 27 23:01:33 2016 -0700
  summary:     Continue development of prototype nowcast figure module.

To switch between named branches use the :command:`hg update` command with the branch name:

.. code-block:: bash

    $ hg update default

.. note::

    Your working copy must be clean (no uncommitted changes) before you can update to another branch.

It is almost always a good idea to regularly merge changes from the :kbd:`default` branch into your named branch.
Doing so means that when you finally merge your named branch back into the :kbd:`default` branch the merge should be relatively small and manageable.
To merge the :kbd:`default` branch into your development branch use:

.. code-block:: bash

    $ hg update refactor-nowcast-figures
    $ hg merge default

Obviously,
if the development your are doing in your named branch conflicts with the changes that have occurred in the :kbd:`default` branch,
you will have to resolve the merge conflicts.

When you have finished development on your named branch,
either by merging into the :kbd:`default` branch,
or by abandoning it,
you can chose it to remove it from the list of branches displayed by the :command:`hg branches` command:

.. code-block:: bash

    $ hg update refactor-nowcast-figures
    $ hg commit --close-branch -m"Close refactor-nowcast-figures branch."
    $ hg update default

If you merged your named branch into :kbd:`default`
(in contrast to abandoning it),
do one more :command:`hg merge` to capture the branch closure commit:

.. code-block:: bash

    $ hg merge refactor-nowcast-figures

It is possible to avoid an explicit branch closure commit by including the :kbd:`--close-branch` option on the final commit before you merge a named branch into :kbd:`default`,
but that requires rare prescience.

You can re-open a closed branch by updating to it:

.. code-block:: bash

    $ hg update my-closed-branch

and subsequent commits will apply to the re-opened branch.
