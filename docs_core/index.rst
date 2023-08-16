===================
Extended ManPy
===================
Extended ManPy focuses on simulating complex features that evolve over time.

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

License: MIT/LGPL

Documentation
================

Most important modules

.. toctree::
   :maxdepth: 3

   tutorials
   core
   examples
