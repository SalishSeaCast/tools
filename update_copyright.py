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

"""Salish Sea NEMO project copyright year range updater.

Walks a directory tree searching .py, .rst, and .txt files for the string
  Copyright *{year - 1}
and updates it to
  Copyright *{year}
"""
from __future__ import print_function

import datetime
import re
import os


def main():
    this_yr = datetime.date.today().year
    last_yr = this_yr - 1
    p_last_yr = re.compile('(Copyright) (.*){}'.format(last_yr), re.IGNORECASE)
    p_this_yr = re.compile('Copyright (.*){}'.format(this_yr), re.IGNORECASE)

    for root, dirs, files in os.walk('.'):
        for name in files:
            if os.path.splitext(name)[1] not in '.py .rst .txt'.split():
                continue
            if any(('.hg' in root, '_build/html' in root, 'egg-info' in root)):
                continue
            with open(os.path.join(root, name), 'rt') as f:
                contents = f.read()
            m = p_last_yr.search(contents)
            if not m:
                if not p_this_yr.search(contents):
                    print('{}: no copyright'.format(os.path.join(root, name)))
                continue
            if not m.groups()[1]:
                # Single year copyright
                new_copyright = (
                    '{0[0]} {1}-{2}'.format(m.groups(), last_yr, this_yr))
            else:
                new_copyright = '{0[0]} {0[1]}{1}'.format(m.groups(), this_yr)
            updated = p_last_yr.sub(new_copyright, contents)
            with open(os.path.join(root, name), 'wt') as f:
                f.write(updated)


if __name__ == '__main__':
    main()
