************
Installation
************

Python Version
==============

:command:`marlin` is developed and tested under Python 2.7.


Dependencies
============

:command:`marlin` depends on the pysvn_ library.
On :kbd:`salish` pysvn_ is installed as the system-side :kbd:`python-svn` package.
Include it in the virtualenv in which :command:`marlin` is installed by symlinking it into the virtualenv :file:`site-packages/` directory
(see :ref:`BasicInstallation`).

.. _pysvn:


.. _BasicInstallation:

Basic Installation
==================

#. Create a :command:`marlin` virtualenv:

   .. code-block:: bash

       $ cd /data/dlatorne/.virtualenvs/
       $ virturalenv marlin

#. Symlink pysvn_ into the :command:`marlin` virtualenv :file:`site-packages/` directory:

   .. code-block:: bash

       $ cd /data/dlatorne/.virtualenvs/marlin/lib/python2.7/site-packages/
       $ ln -s /usr/lib/python2.7/dist-packages/pysvn

#. Activate the :command:`marlin` virtualenv and install :command:`marlin` in editable mode:

   .. code-block:: bash

       $ . /data/dlatorne/.virtualenvs/marlin/bin/activate
       (marlin)$ cd /data/dlatorne/MEOPAR/tools/Marlin
       (marlin)$ pip install -e .


Source Code
===========

The source code is hosted on Bitbucket: https://bitbucket.org/salishsea/tools/src/tip/Marlin/.


Reporting Bugs
==============

Please report bugs through the Bitbucket project: https://bitbucket.org/salishsea/tools/issues?component=Marlin marked with "Marlin" in the component field.
