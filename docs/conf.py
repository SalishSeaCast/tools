# Configuration file for the Sphinx documentation builder
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


import os
import sys

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath("../SalishSeaTools"))


# -- General configuration ----------------------------------------------------

# Add any Sphinx extension module names here, as strings.
# They can be extensions coming with Sphinx
# (named 'sphinx.ext.*')
# or your custom ones.
extensions = [
    "IPython.sphinxext.ipython_console_highlighting",
    "nbsphinx",
    "notfound.extension",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
]

intersphinx_mapping = {
    "docs": ("https://salishsea-meopar-docs.readthedocs.io/en/latest/", None),
    "salishseacmd": ("https://salishseacmd.readthedocs.io/en/latest/", None),
    "salishseanowcast": ("https://salishsea-nowcast.readthedocs.io/en/latest/", None),
    "numpy": ("https://docs.scipy.org/doc/numpy/", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/reference/", None),
}

todo_include_todos = True

autodoc_mock_imports = [
    "angles",
    "arrow",
    "cmocean",
    "erddapy",
    "f90nml",
    "gsw",
    "matplotlib",
    "netCDF4",
    "nowcast",
    "numpy",
    "pandas",
    "retrying",
    "scipy",
    "tqdm",
    "xarray",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "SalishSeaCast Tools"
copyright = (
    "2013 – present, "
    "SalishSeaCast Project Contributors "
    "and The University of British Columbia"
)

# For autoclass
autoclass_content = "init"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = ""
# The full version, including alpha/beta/rc tags.
release = ""

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build", "**.ipynb_checkpoints"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"


# -- Options for HTML output --------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "_static/MEOPAR_favicon.ico"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = "%b %d, %Y"

# If false, no module index is generated.
html_domain_indices = False

# If false, no index is generated.
html_use_index = False

# Output file base name for HTML help builder.
htmlhelp_basename = "SalishSea-MEOPAR-toolsdoc"


# -- Options for LaTeX output -------------------------------------------------

# Grouping the document tree into LaTeX files.
# List of tuples
# (source start file, target name, title,
#  author, documentclass [howto/manual]).
latex_documents = [
    (
        "index",
        "SalishSea-MEOPAR-toolsdoc.tex",
        "SalishSeaCast Tools Documentation",
        "SalishSeaCast Project Contributors",
        "manual",
    )
]
