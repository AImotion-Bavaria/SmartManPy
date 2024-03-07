# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
from datetime import date

sys.path.insert(0, os.path.abspath("../"))

project = 'SmartManPy'

current_year = date.today().year
copyright = f"{current_year}, AImotion Bavaria"

author = 'LOMA'
release = 'beta'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.todo",
              "sphinx.ext.viewcode",
              "sphinx.ext.autodoc",
              "sphinx_copybutton"
              ]


templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'classic'
html_theme = 'furo'
html_static_path = ['_static']
html_title = 'SmartManPy (beta) Docs'
html_link_suffix = ".html"
html_logo = 'images/SmartManPy_logo_transparent.png'
html_favicon = 'images/SmartManPy_logo_transparent.png'

# autodoc_member_order = 'bysource'
# autodoc_member_order = 'alphabetical'
