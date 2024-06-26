===================
SmartManPy
===================

SmartManPy focuses on simulating complex features that evolve over time.

This project extends the Python 3 port of ManPy by Data Revenue GmbH (https://github.com/datarevenue-berlin/manpy).

ManPy was originally developed as part of the FP7 DREAM project: https://www.manpy-simulation.org/, which was released under the LGPL license

We performed the following modifications/additions (non-exhaustive):

* Added complex features to machines:
    - Features can be drawn from a variety of random distributions
    - Simulation of data drift / shifting distributions
    - Failures based on feature values
    - Different random distributions for different entity labels
    - Functional dependencies between features
    - Timeseries that can be interpolated from a couple of real-world data points
* Quality control based on feature values or distributions
* Database connection
* CSV export

License: LGPL

How to get started
===================

Follow the steps below to install SmartManPy:

1. Clone the Git repository to the desired directory (we call it MANPYDIR in the following)
2. Open your command line and navigate to MANPYDIR
3. Activate the virtualenv/conda env of your choice
4. Enter the following command:

.. code-block:: bash

    pip install -e .

5. You can now import manpy:

.. code-block:: python

    import manpy


Documentation
================

Most important modules

.. toctree::
   :maxdepth: 3

   tutorials
   core
   rng
   examples
