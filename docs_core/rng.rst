RandomNumberGenerator
======================

RandomNumberGenerator is used for generating the individual data points.
It supports a wide variety of configurations, which we describe here.

manpy.simulation.RandomNumberGenerator.py
-------------------------------------------

.. automodule:: manpy.simulation.RandomNumberGenerator
   :members:
   :show-inheritance:

Configuring the distribution
-----------------------------------------

The configuration of the RNG's internal distribution is usually done via several parameters, e.g. of Feature, Machine or Source.
As of now, the distribution is described using dictionaries.
There exist plans to improve this mechanism, but we don't have a concrete roadmap.

Generally speaking, the config dictionary describes the distribution name and its parameters.
It always has the following format:

.. code-block:: python

    distribution = {"DistributionName": {"Parameter1": value1,
                                         "Parameter2": value2,
                                         ...
                                         }
                   }

When configuring the underlying probability distribution of a feature, you add such a dictionary as a value to "Feature".

.. code-block:: python

    distribution = {"Feature": {"DistributionName": {"Parameter1": value1,
                                                     "Parameter2": value2,
                                                     ...
                                                    }
                               }
                   }

The following probability distributions and parameters exist:

.. table:: Distributions and their respective parameters

    +----------------+-------------------------------+
    | Distribution   | Parameters                    |
    +================+===============================+
    | Fixed          | mean: specifies the value     |
    +----------------+-------------------------------+
    | Normal         | mean and stdev                |
    +----------------+-------------------------------+
    | Exp            | mean                          |
    +----------------+-------------------------------+
    | Gamma          | alpha/shape, beta/rate        |
    +----------------+-------------------------------+
    | Logistic       | location, scale               |
    +----------------+-------------------------------+
    | Erlang         | alpha/shape, beta/rate        |
    +----------------+-------------------------------+
    | Lognormal      | mean, stdev                   |
    +----------------+-------------------------------+
    | Weibull        | shape                         |
    +----------------+-------------------------------+
    | Cauchy         | location, scale               |
    +----------------+-------------------------------+
    | Triangular     | min, max, mean                |
    +----------------+-------------------------------+
    | Categorical    | See tutorial below            |
    +----------------+-------------------------------+
    | General Params | min: minimum output value     |
    |                | max: maximum output value     |
    +----------------+-------------------------------+

Besides of numbers, RandomNumberGenerator can also return categorical values, which can be useful in industrial settings.
To use this functionality, you need to pass "Categorical" as distribution name.
In the parameter dictionary, you specify the probabilities of the individual categorical feature values:

.. code-block:: python

    distribution = {"Feature": {"Categorical": {"A": 0.2,
                                                "B": 0.7,
                                                "C": 0.1
                                               }
                               }
                   }

