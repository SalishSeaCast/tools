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

"""Prepare for and run the Salish Sea NEMO model for the current day.

Step are:

1. Create a run description dict for the current day's run.
   Run-specific values are the run id,
   atmospheric forcing directory,
   initial conditions restart file,
   open boundaries directory,
   and rivers directory.

2. Edit the `namelist.time` file to set the first and last time step
   values for the current day's run.

3. Execute the `salishsea run` command to queue or launch the run.
"""
from __future__ import division

from datetime import (
    date,
    timedelta,
)
import os

import salishsea_cmd.api


FORCING_HOME = '/home/sallen/MEOPAR/nowcast'
TIMESTEPS_PER_DAY = 8640


def main():
    today = date.today()
    prev_itend = update_time_namelist(today)
    dmy = today.strftime('%d%b%y').lower()
    run_id = '{dmy}nowcast'.format(dmy=dmy)
    run_desc = run_description(run_id, today, prev_itend)
    results_dir = os.path.join('../SalishSea/nowcast', dmy)
    salishsea_cmd.api.run_in_subprocess(
        run_id, run_desc, 'iodef.xml', os.path.abspath(results_dir))


def update_time_namelist(today, timesteps_per_day=TIMESTEPS_PER_DAY):
    with open('namelist.time', 'rt') as f:
        lines = f.readlines()
    it000_line, prev_it000 = get_namelist_value('nn_it000', lines)
    itend_line, prev_itend = get_namelist_value('nn_itend', lines)
    date0_line, date0 = get_namelist_value('nn_date0', lines)
    # Prevent namelist from being updated past today
    next_itend = int(prev_itend) + timesteps_per_day
    date0 = date(*map(int, [date0[:4], date0[4:6], date0[-2:]]))
    one_day = timedelta(days=1)
    if next_itend / timesteps_per_day > (today - date0 + one_day).days:
        return int(prev_it000) - 1
    # Increment 1st and last time steps to values for today
    lines[it000_line] = lines[it000_line].replace(
        prev_it000, str(int(prev_itend) + 1))
    lines[itend_line] = lines[itend_line].replace(prev_itend, str(next_itend))
    with open('namelist.time', 'wt') as f:
        f.writelines(lines)
    return int(prev_itend)


def get_namelist_value(key, lines):
    line_index = [
        i for i, line in enumerate(lines)
        if line.split()[0] == key][-1]
    value = lines[line_index].split()[2]
    return line_index, value


def run_description(run_id, today, prev_itend, forcing_home=FORCING_HOME):
    # Relative paths from MEOPAR/nowcast/
    yesterday = today - timedelta(days=1)
    init_conditions = os.path.join(
        '../SalishSea/nowcast',
        yesterday.strftime('%d%b%y').lower(),
        'SalishSea_{:08d}_restart.nc'.format(prev_itend),
    )
    run_desc = salishsea_cmd.api.run_description(
        walltime='1:00:00',
        NEMO_code=os.path.abspath('../NEMO-code/'),
        forcing=os.path.abspath('../NEMO-forcing/'),
        runs_dir=os.path.abspath('../SalishSea/'),
        init_conditions=os.path.abspath(init_conditions),
    )
    run_desc['run_id'] = run_id
    run_desc['email'] = 'sallen@eos.ubc.ca'
    # Paths to run-specific forcing directories
    run_desc['forcing']['atmospheric'] = os.path.abspath(
        os.path.join(forcing_home, 'NEMO-atmos'))
    run_desc['forcing']['open boundaries'] = os.path.abspath(
        os.path.join(forcing_home, 'open_boundaries'))
    run_desc['forcing']['rivers'] = os.path.abspath(
        os.path.join(forcing_home, 'rivers'))
    # Paths to namelist section files
    run_desc['namelists'] = [
        os.path.abspath('namelist.time'),
        os.path.abspath('../SS-run-sets/SalishSea/namelist.domain'),
        os.path.abspath('../SS-run-sets/SalishSea/namelist.surface.nowcast'),
        os.path.abspath('../SS-run-sets/SalishSea/namelist.lateral.nowcast'),
        os.path.abspath('../SS-run-sets/SalishSea/namelist.bottom'),
        os.path.abspath('../SS-run-sets/SalishSea/namelist.tracers'),
        os.path.abspath('../SS-run-sets/SalishSea/namelist.dynamics'),
        os.path.abspath('../SS-run-sets/SalishSea/namelist.compute.12x27'),
    ]
    return run_desc


if __name__ == '__main__':
    main()
