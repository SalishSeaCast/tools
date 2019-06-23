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

"""Set of parameters to calculate Si from Live Ocean NO3 and to correct NO3 values
"""


def set_parameters(parameter_set):
    """Set the parameters given the parameter set name
    arg: string: parameter_set

    returns a dictionary of parameters
    """

    LO_to_SSC_parameters = {
        # Original base paramter set: using NO3 directly from Live Ocean and
        # a linear fit to get Si from NO3
        "v201702": {
            "NO3": {"smax": 100.0, "nmax": 120.0},
            "Si": {"a": 6.46, "b": 1.35, "c": 0.0, "sigma": 1.0, "tsa": 29},
        },
        # Parameter set that corrects the highest Live Ocean NO3 values and
        # improves the Si parametrization by including salinity
        "v201905": {
            "NO3": {"smax": 25.880, "nmax": 46.050},
            "Si": {"a": 1.756, "b": 1.556, "c": -7.331, "sigma": 1.631, "tsa": 32.4929},
        },
    }
    return LO_to_SSC_parameters[parameter_set]
