"""Salish Sea NEMO IPython Notebook collection README generator


Copyright 2013-2016 The Salish Sea MEOPAR Contributors
and The University of British Columbia

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import datetime
import glob
import json
import os
import re


NBVIEWER = 'https://nbviewer.jupyter.org/urls'
REPO = 'bitbucket.org/salishsea/tools/raw/tip'
REPO_DIR = 'analysis_tools'
TITLE_PATTERN = re.compile('#{1,6} ?')


def main():
    url = os.path.join(NBVIEWER, REPO, REPO_DIR)
    readme = """\
The IPython Notebooks in this directory provide discussion,
examples, and best practices for plotting various kinds of model results
from netCDF files. There are code examples in the notebooks and also
examples of the use of functions from the
[`salishsea_tools`](http://salishsea-meopar-tools.readthedocs.org/en/latest/SalishSeaTools/salishsea-tools.html)
package.
If you are new to the Salish Sea MEOPAR project or to IPython Notebook,
netCDF, and Matplotlib you should read the introductory notebooks
in the following order:

* [Exploring netCDF Files.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Exploring netCDF Files.ipynb)
* [Plotting Bathymetry Colour Meshes.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Bathymetry Colour Meshes.ipynb)
* [Plotting Tracers on Horizontal Planes.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Tracers on Horizontal Planes.ipynb)
* [Plotting Velocity Fields on Horizontal Planes.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Velocity Fields on Horizontal Planes.ipynb)
* [Plotting Velocities and Tracers on Vertical Planes.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Velocities and Tracers on Vertical Planes.ipynb)

The links above and below are to static renderings of the notebooks via
[nbviewer.ipython.org](https://nbviewer.jupyter.org/).
Descriptions under the links below are from the first cell of the notebooks
(if that cell contains Markdown or raw text).

"""
    for fn in glob.glob('*.ipynb'):
        readme += '* ##[{fn}]({url}/{fn})  \n    \n'.format(fn=fn, url=url)
        readme += notebook_description(fn)
    license = """
##License

These notebooks and files are copyright 2013-{this_year}
by the Salish Sea MEOPAR Project Contributors
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
""".format(this_year=datetime.date.today().year)
    with open('README.md', 'wt') as f:
        f.writelines(readme)
        f.writelines(license)


def notebook_description(fn):
    description = ''
    with open(fn, 'rt') as notebook:
        contents = json.load(notebook)
    try:
        first_cell = contents['worksheets'][0]['cells'][0]
    except KeyError:
        first_cell = contents['cells'][0]
    first_cell_type = first_cell['cell_type']
    if first_cell_type not in 'markdown raw'.split():
        return description
    desc_lines = first_cell['source']
    for line in desc_lines:
        suffix = ''
        if TITLE_PATTERN.match(line):
            line = TITLE_PATTERN.sub('**', line)
            suffix = '**'
        if line.endswith('\n'):
            description += (
                '    {line}{suffix}  \n'
                .format(line=line[:-1], suffix=suffix))
        else:
            description += (
                '    {line}{suffix}  '.format(line=line, suffix=suffix))
    description += '\n' * 2
    return description


if __name__ == '__main__':
    main()
