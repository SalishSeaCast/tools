"""Salish Sea NEMO IPython Notebook collection README generator


Copyright 2013-2014 The Salish Sea MEOPAR Contributors
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
import os


nbviewer = 'http://nbviewer.ipython.org/urls'
repo = 'bitbucket.org/salishsea/tools/raw/tip'
repo_dir = 'NetCDF_Plot'
url = os.path.join(nbviewer, repo, repo_dir)
readme = """The IPython Notebooks in this directory are initial experiments
around visualization of NEMO results.

"""
for fn in (fn for fn in os.listdir('./') if fn.endswith('ipynb')):
    readme += '* [{fn}]({url}/{fn})\n'.format(url=url, fn=fn)
license = """
##License

These notebooks are copyright 2013-2014
by the Salish Sea MEOPAR Project Contributors
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
"""
with open('README.md', 'wt') as f:
    f.writelines(readme)
    f.writelines(license)
