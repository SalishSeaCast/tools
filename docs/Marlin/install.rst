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

:py:obj:`Marlin` also depends on the :ref:`SalishSeaTools` :ref:`salishsea_tools.hg_commands`

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
