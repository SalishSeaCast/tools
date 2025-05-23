"""Salish Sea NEMO Jupyter Notebook collection README generator


Copyright 2013 – present by the SalishSeaCast Contributors
and The University of British Columbia

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import datetime
import json
import os
import re


nbviewer = "https://nbviewer.org/urls"
repo = "github.com/SalishSeaCast/tools/blob/main"
repo_dir = "SalishSeaTools/notebooks/visualisations"
url = os.path.join(nbviewer, repo, repo_dir)
title_pattern = re.compile("#{1,6} ?")
readme = """The Jupyter Notebooks in this directory are made by for testing
functions in visualisations.py.

The links below are to static renderings of the notebooks via
[nbviewer.org](https://nbviewer.org/).
Descriptions below the links are from the first cell of the notebooks
(if that cell contains Markdown or raw text).

"""
notebooks = (fn for fn in os.listdir("./") if fn.endswith("ipynb"))
for fn in notebooks:
    readme += "* ##[{fn}]({url}/{fn})  \n    \n".format(fn=fn, url=url)
    with open(fn, "rt") as notebook:
        contents = json.load(notebook)
    try:
        first_cell = contents["worksheets"][0]["cells"][0]
    except KeyError:
        first_cell = contents["cells"][0]
    first_cell_type = first_cell["cell_type"]
    if first_cell_type in "markdown raw".split():
        desc_lines = first_cell["source"]
        for line in desc_lines:
            suffix = ""
            if title_pattern.match(line):
                line = title_pattern.sub("**", line)
                suffix = "**"
            if line.endswith("\n"):
                readme += "    {line}{suffix}  \n".format(line=line[:-1], suffix=suffix)
            else:
                readme += "    {line}{suffix}  ".format(line=line, suffix=suffix)
        readme += "\n" * 2
license = """
##License

These notebooks and files are copyright 2013-{this_year}
by the SalishSeaCast Project Contributors
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
https://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
""".format(
    this_year=datetime.date.today().year
)
with open("README.md", "wt") as f:
    f.writelines(readme)
    f.writelines(license)
