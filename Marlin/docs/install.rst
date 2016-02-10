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


************
Installation
************

Python Version
==============

:py:obj:`Marlin` is developed and tested under Python 2.7.


Dependencies
============

:py:obj:`Marlin` depends on the pysvn_ library.
On :kbd:`salish` pysvn_ is installed as the system-side :kbd:`python-svn` package.
Include it in the virtualenv in which :py:obj:`Marlin` is installed by symlinking it into the virtualenv :file:`site-packages/` directory.

:py:obj:`Marlin` also depends on the :ref:`SalishSeaToolsPackage` :ref:`salishsea_tools.hg_commands`

Details of how to install both of these dependencies are included in the :ref:`BasicInstallation` section below.

.. _pysvn: http://pysvn.tigris.org/


.. _BasicInstallation:

Basic Installation
==================

#. Create a :kbd:`marlin` virtualenv:

   .. code-block:: bash

       $ cd /data/dlatorne/.virtualenvs/
       $ virturalenv marlin

#. Symlink pysvn_ into the :kbd:`marlin` virtualenv :file:`site-packages/` directory:

   .. code-block:: bash

       $ cd /data/dlatorne/.virtualenvs/marlin/lib/python2.7/site-packages/
       $ ln -s /usr/lib/python2.7/dist-packages/pysvn

#. Activate the :kbd:`marlin` virtualenv and install the :py:obj:`SalishSeaTools` and :py:obj:`Marlin` packages in editable mode:

   .. code-block:: bash

       $ . /data/dlatorne/.virtualenvs/marlin/bin/activate
       (marlin)$ cd /data/dlatorne/MEOPAR/tools/
       (marlin)$ pip install --no-deps -e SalishSeaTools
       (marlin)$ pip install -e Marlin


Source Code
===========

The source code is hosted on Bitbucket: https://bitbucket.org/salishsea/tools/src/tip/Marlin/.


Reporting Bugs
==============

Please report bugs through the Bitbucket project: https://bitbucket.org/salishsea/tools/issues?component=Marlin marked with "Marlin" in the component field.
