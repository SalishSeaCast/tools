# Copyright 2013-2016 The Salish Sea MEOPAR Contributors
# and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""SalishSeaTools Package
"""
from setuptools import setup

import __pkg_metadata__


python_classifiers = [
    'Programming Language :: Python :: {0}'.format(py_version)
    for py_version in ['2', '2.7', '3', '3.4', '3.5']
]
other_classifiers = [
    'Development Status :: ' + __pkg_metadata__.DEV_STATUS,
    'License :: OSI Approved :: Apache Software License',
    'Programming Language :: Python :: Implementation :: CPython',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: POSIX :: Linux',
    'Operating System :: Unix',
    'Environment :: Console',
    'Intended Audience :: Science/Research',
    'Intended Audience :: Education',
    'Intended Audience :: Developers',
]

try:
    long_description = open('README.rst', 'rt').read()
except IOError:
    long_description = ''
install_requires = [
    # see requirements.pip for versions most recently used in development
    'angles',
    'arrow',
    'bottleneck',
    'cmocean',
    'gsw',
    'matplotlib',
    'netCDF4',
    'numpy',
    'pandas',
    "progressbar",
    'python-dateutil',
    'pytz',
    'requests',
    'retrying',
    'scipy',
    'xarray',

    # 'basemap',
    # basemap is required to use the LiveOcean_BCs module,
    # but it is difficult to install on HPC systems like jasper, orcinus, et al.
    # If you plan to use the LiveOcean_BCs module,
    # please conda install basemap.
]

setup(
    name=__pkg_metadata__.PROJECT,
    version=__pkg_metadata__.VERSION,
    description=__pkg_metadata__.DESCRIPTION,
    long_description=long_description,
    author='Doug Latornell and the Salish Sea MEOPAR Project Contributors',
    author_email='djl@douglatornell.ca',
    url=(
        'http://salishsea-meopar-tools.readthedocs.org/en/latest/'
        'SalishSeaTools/'),
    license='Apache License, Version 2.0',
    classifiers=python_classifiers + other_classifiers,
    platforms=['MacOS X', 'Linux'],
    install_requires=install_requires,
    packages=['salishsea_tools'],
)
