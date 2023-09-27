
# Extended-ManPy


[![Tests (Self-hosted)](https://github.com/AImotion-Bavaria/ManPyExperiments/actions/workflows/tests_self_hosted.yml/badge.svg)](https://github.com/AImotion-Bavaria/ManPyExperiments/actions/workflows/tests_self_hosted.yml)

This repository extends the Python 3 port of ManPy by Data Revenue GmbH (https://github.com/datarevenue-berlin/manpy)

We did the following modifications/additions:

* Fixed some bugs of the internal behavior:
* Added Machine features
* Added conditions to failures

# Workflow


1. Before you add a feature, create a new issue with a short explanation of the new feature.
2. Create a feature branch for the issue with an appropriate name.
3. When the feature is finished, merge the main branch into the feature branch. This makes the next step much easier.
4. Open a pull request an assign it to another developer.
5. After the pull request is closed and the feature branch is merged to the main branch, the issue can be closed.

# Installation

If you wish to install our extended manpy, follow the steps below.

1. Clone the Git repository to the desired directory (we call it MANPYDIR in the following)
2. Open your command line and navigate to MANPYDIR
3. Activate the virtualenv/conda env of your choice
4. Enter the following command:
   `pip install -e .`
5. You can now import manpy: `import manpy`

# Build docs

The html files for the docs are located in /docs_core/_build/html.
To build the docs based on the current version of the code, follow the steps below.

1. Install the following dependencies:

    `pip install -U sphinx`

    `pip install furo`

    `pip install sphinx-copybutton`

2. Call the following command in the base directory of this repo:

    On windows: `.\docs_core\make.bat html`

    On Linux/Ubuntu: `.\docs_core\make html`

