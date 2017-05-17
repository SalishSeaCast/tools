# Copyright 2013-2016 The Salish Sea NEMO Project and
# The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Ocean Networks Canada Strait of Georgia ADCPs Metadata.
"""
from collections import namedtuple

import arrow


adcp = namedtuple('ADCP', 'device_id, sensor_id')
adcps = {
    # Keys are instrument serial numbers
    8580: adcp(device_id=65, sensor_id=95),  # rdi adcp 150 khz wh
    8497: adcp(device_id=37, sensor_id=92),  # rdi adcp 150 khz wh
    17955: adcp(device_id=525, sensor_id=738),  # rdi adcp 300 khz wh
    7992: adcp(device_id=1220, sensor_id=91),  # rdi adcp 600khz wh
    2940: adcp(device_id=22635, sensor_id=7530),  # rdi adcp 300 khz wh
    17457: adcp(device_id=23097, sensor_id=9372),  # rdi adcp 150 khz wh
}


deployment = namedtuple('Deployment', 'id, start, end, serial_no, site_id')
deployments = {
    # Keys are the same as in :py:data:`~salishsea_tools.places.PLACES`
    'Central node': {
        'location id': 4,
        'history': [
            deployment(
                id='VIP-14',
                start=arrow.get(2016, 5, 3),
                end=arrow.now().to('Canada/Pacific'),
                serial_no=8580, site_id=1000661),
            deployment(
                id='VIP-13',
                start=arrow.get(2015, 8, 31), end=arrow.get(2016, 5, 3),
                serial_no=8580, site_id=1000479),
        ],
    },
    'East node': {
        'location id': 3,
        'history': [
            deployment(
                id='VIP-14',
                start=arrow.get(2016, 5, 1),
                end=arrow.now().to('Canada/Pacific'),
                serial_no=8497, site_id=1000670),
            deployment(
                id='VIP-13',
                start=arrow.get(2015, 8, 27), end=arrow.get(2016, 5, 1),
                serial_no=8497, site_id=1000475),
        ]
    },
    'Delta BBL node': {
        'location id': 14,
        'history': [
            deployment(
                id='BBL-SG-05',
                start=arrow.get(2016, 5, 1),
                end=arrow.now().to('Canada/Pacific'),
                serial_no=17955, site_id=1000668),
            deployment(
                id='BBL-SG-04',
                start=arrow.get(2015, 8, 30), end=arrow.get(2016, 5, 1),
                serial_no=17955, site_id=1000474),
        ]
    },
}
