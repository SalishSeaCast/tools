# Copyright 2013-2016 The Salish Sea MEOPAR contributors
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

"""Pytest fixtures for the salishsea_tools package.
"""
import os

import netCDF4 as nc
import pytest


@pytest.yield_fixture()
def nc_dataset():
    """Return a netCDF4.Dataset instance called foo that is open for writing.

    Remove the created file as a clean-up operation.
    """
    dataset = nc.Dataset('foo', 'w')
    yield dataset
    dataset.close()
    os.remove('foo')
