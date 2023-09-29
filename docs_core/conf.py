# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
sys.path.insert(0, os.path.abspath("../"))

project = 'SmartManPy'
copyright = '2023, AImotion Bavaria'
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
html_logo = 'images/logo.png'
html_favicon = 'images/logo.png'

# autodoc_member_order = 'bysource'
# autodoc_member_order = 'alphabetical'
