.. Copyright 2013-2015 The Salish Sea MEOPAR conttributors
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


.. _GuidelinesAndBestPracticesForWritingLibraryCode:

Guidelines and Best Practices for Writing Library Code
======================================================

The notes in this section are about writing readable,
maintainable Python code that your future self and other people will be able to use,
maintain,
and improve.
While much of what follows is applicable to any Python code that you may write,
some of the points are particularly relevant to code going into modules in the :ref:`tools-repo`;
e.g. the :ref:`SalishSeaToolsPackage` and the :ref:`SalishSeaNowcastPackage`.

A primary guide for writing Python code is `PEP 8 -- Style Guide for Python Code`_.

.. _PEP 8 -- Style Guide for Python Code: https://www.python.org/dev/peps/pep-0008/

Installing the `flake8`_ static analysis tool and enabling your editor to use it to highlight problem code will help you to write well-styled code.
See :ref:`PythonSourceCodeCheckingViaFlake8` for details of how to set that up for emacs.

.. _flake8: https://flake8.readthedocs.org/en/latest/
