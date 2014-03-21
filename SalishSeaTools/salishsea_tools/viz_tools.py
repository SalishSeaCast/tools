# Copyright 2013-2014 The Salish Sea MEOPAR contributors
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

"""A collection of Python functions to do routine tasks associated with
plotting and visualization.
"""
from __future__ import division


__all__ = ['set_aspect']


def set_aspect(axes, aspect=5/4.4, adjustable='box-forced'):
    """Set the aspect ratio on axes.

    This is a thin wrapper on the :py:meth:`matplotlib.axes.Axes.set_aspect`
    method.
    Its primary purpose is to free the user from needing to remember the
    5/4.4 nominal aspect ratio for the Salish Sea NEMO model grid.
    It also sets the axes aspect ratio with :py:attr:`adjustable='box-forced'`
    so that the axes can be shared if desired.

    :arg axes: Axes instance to set the aspect ratio of.
    :type axes: :py:class:`matplotlib.axes.Axes`

    :arg aspect: Aspect ratio.
    :type aspect: float

    :arg adjustable: How to adjust the axes box.
    :type adjustable: str
    """
    axes.set_aspect(aspect, adjustable=adjustable)
