===========
Tutorials
===========

This page gives you an overview of the general usage paradigms of our ManPy extension
We have prepared additional (complete) examples that demonstrate various capabilities.
These examples can be found in manpy/Examples.
We recommend the following order:

1. Quality_Control.py
2. Dependency.py
3. ExampleTS.py
4. Conditional_Failure.py
5. Interpolation.py
6. Data_Extraction.py


Introduction and basic principles
====================================

The original ManPy package is based on the SimPy discrete event simulation.
If you are already familiar with SimPy, you may recognize some paradigms.

The start and finish point of a production line is a Source and Exit:

.. code-block:: python
   :linenos:

    from manpy.simulation.imports import Machine, Source, Exit

    start = Source("S1", "Source",
                    interArrivalTime={"Fixed": {"mean": 0.4}},
                    entity="manpy.Part", capacity=1)

    exit = Exit("E1", "Exit1")

Then, you can add a machine to our small example.
Our machine have a mean processing time of 0.8 seconds, with a standard deviation of 0.075 seconds.
However, the minimal and maximal time is set to 0.425 and 1.175 seconds:

.. code-block:: python
    :linenos:

    m1 = Machine("M1", "Machine1",
                    processingTime={"Normal":
                                    {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}
                })

In order to complete our small example, we need to define the routing between the components.
This is done for each component individually:

.. code-block:: python
    :linenos:

    start.defineRouting(successorList=[m1])
    m1.defineRouting(predecessorList=[start], successorList=[exit])
    exit.defineRouting(predecessorList=[m1])

We can now run and evaluate our simulation, e.g. for 50 time steps:

.. code-block:: python
    :linenos:

    maxSimTime = 50
    objectList = [start, m1, exit]

    runSimulation(objectList, maxSimTime)

    df = getEntityData()
    df.to_csv("ExampleLine.csv", index=False, encoding="utf8")

    print(f"Produced:         {exit.numOfExits}
            Simulationszeit:    {maxSimTime}")

* Queues
* Failures
* Assembly

Our example currently consists of only one production step.
Since ManPy was designed to simulate production lines, let's see what it takes to add mode machines to a simulation.
First of all, we need to define a second machine:

.. code-block:: python
    :linenos:

    m2 = Machine("M2", "Machine2",
                    processingTime={"Normal":
                                    {"mean": 2.0, "stdev": 0.1, "min": 1.7, "max": 2.3}
                })

Now we need to define how the output of Machine1 proceeds to Machine2.
ManPy is capable of simulating complex routings, e.g. using conveyor belts.
This makes sense if you are interested in the overall behaviour of the production line.
For this example, we'll stick to the simplest connection between two machines: the queue.
Queues in ManPy act as a simple buffer with a certain capacity.
In order to work correctly, we also need to update the routing of the production line and add the new objects to the objectList:

.. code-block:: python
    :linenos:

    q1 = Queue("Q1", "Queue1", capacity=10)

    start.defineRouting(successorList=[m1])
    m1.defineRouting(predecessorList=[start], successorList=[q1])
    q1.defineRouting(predecessorList=[m1], successorList=[m2])
    m2.defineRouting(predecessorList=[q1], successorList=[exit])
    exit.defineRouting(predecessorList=[m2])

    objectList = [start, m1, m2, q1, exit]


Advanced usage
================

The following sections provides an introduction into the more advanced concepts of our ManPy extension.

Quality Control
-----------------

Quality control is a standard process in manufacturing.
Therefore, we added the option for quality control to machines.
As a result, machines can either have an additional quality control step at the end of their production step or be a standalone quality control instance.
The condition for quality control can be set via a custom defined function, which is simply called "condition" in the following example.
We can access the currently active entity in a machine with the following statement:

.. code-block:: python

    activeEntity = self.Res.users[0]

We can then use any simulated value of the entity as measurement for quality control, e.g. feature values or internal labels.
The condition function must return True if a defect was found, otherwise False must be returned.
In the following example, we simply check if a given Feature value is inside a certain interval ([3, 7]).

.. code-block:: python
    :linenos:

    def condition(self):
        # self is w.r.t. to the machine in which we apply the condition!
        activeEntity = self.Res.users[0]
        if activeEntity.features[0] > 7 or activeEntity.features[0] < 3:
            return True
        else:
            return False

Features
--------

Features are our most important extension to the original ManPy and also the most complex one.
Features are a sub-class of ObjectProperty, which is a generic base class for all kinds of data a machine/object can generate during production.
We currently have two sub_classes of ObjectProperty: Features and TimeSeries.
While TimeSeries is concerned with (as the name suggests) time series data that is generated during production
(e.g. temperature curves), Feature is concerned with properties that are measured/logged once for each entity at a production station.
In the following section, we will explore the most important mechanics of the Feature class.

The following statement shows the most basic definition of a Feature:

.. code-block:: python

    feature1 = Feature(id="f1",
                       name="Feature1",
                       victim=m1,
                       distribution={"Feature": {"Normal": {"mean": 0, "stdev": 1.0}}}
                       )

This statements assigns a new Feature with the internal id "f1" and name "Feature1" (used for data output) to Machine m1.
The feature values are randomly drawn from a normal distribution with mean 0 and standard deviation 1.
It is possible to select different distributions and to control the behaviour of the underlying distribution over the course of a simulation.
Further explanations for these mechanics are provided in `Distributions and StateControllers`_.

We can of course add many more features to a machine.
Sometimes, there are certain relationships between features, e.g. physical dependencies.
We can model these dependencies using the "dependency" parameter:

.. code-block:: python

    feature2 = Feature(id="f2",
                       name="Feature2",
                       victim=m1,
                       dependent={"Function": "10*x + 3", "x": feature1}
                       distribution={"Feature": {"Normal": {"stdev": 0.1}}}
                       )

Here, we define a functional dependency between feature2 and feature1, in this case the linear function 10x + 3.
To simulate eventual measurement errors, we can apply a standard deviation to this dependency, in this cas 0.1.
However, it is also possible to have strict functional dependencies between features by simply not passing anything as an argument for distribution:

.. code-block:: python

    feature2 = Feature(id="f2",
                       name="Feature2",
                       victim=m1,
                       dependent={"Function": "10*x + 3", "x": feature1}
                       )

Sometimes, Features depend on the previous value, e.g. Temperatures.
To model this, we can use random walks.
When the random walk mode is activated, the randomly drawn feature value is added to the last feature value.
A Feature generated using a random walk can be defined as follows:

.. code-block:: python

    random_walk_feature = Feature(id="ftr_rw",
                                  name="Feature_Random_Walk",
                                  victim=m1,
                                  random_walk=True,
                                  start_value=20,
                                  distribution={"Feature": {"Normal": {"mean": 0, "stdev": 1.0}}})

Feature "Feature_Random_Walk" has a starting value of 20.
For each data point, a value is drawn from a normal distribution with mean 0 and standard deviation 1 and then added to the current value.
The starting value is 20, which can be interpreted as the "mean" of the random walk.


Time Series
------------

TimeSeries represents the second type of ObjectProperty in our ManPy Extension.
At each production step, TimeSeries generates a configurable amount of data points in a certain time frame.
Let' have a look at a simple example:

.. code-block:: python

    ts_features = Feature(id="ftr_ts,
                          name="Feature_Time_Series",
                          step_time=0.1,
                          distribution={"Function": {(0, 2): "0.5*x + 2"},
                                        "DataPoints": 20,
                                        "Feature": {"Normal": {"stdev": 0.1}}
                                       }
                          )

This example generates a time series in which the data points are 0.1 second apart.
The time series is defined in the interval [0, 2], in which 20 data points are sampled.
The resulting values are governed by a linear function.
At each data point in the time series, a standard deviation of 0.1 is applied to model small differences between production steps.
It is possible to define multiple intervals to further customize the mathematical despription of the time series:

.. code-block:: python

    ts_features = Feature(id="ftr_ts,
                          name="Feature_Time_Series",
                          step_time=0.1,
                          distribution={"Function": {(0, 1): "0.5*x + 2", (1, 2): "0.1*x + 2"},
                                        "DataPoints": 20,
                                        "Feature": {"Normal": {"stdev": 0.1}}
                                       }
                          )

The aforementioned ways of creating time series are quite powerful, but only if a functional relationship ís known.
Sometimes, only certain values are known, which makes interpolation a very useful tool for these cases:

.. code-block:: python

    ts_features = Feature(id="ftr_ts,
                          name="Feature_Time_Series",
                          step_time=0.1,
                          distribution={"Function": {(0, 1): "0.5*x + 2",
                                                     (1, 3): [[1, 1.5, 2, 3], [4, 4.2, 4.3, 5.1]]},
                                        "DataPoints": 20,
                                        "Feature": {"Normal": {"stdev": 0.1}}
                                       }
                          )

In this example, we give the interpolation algorithm 4 data points in the interval, between which it interpolates.
No matter how small or large the interval is, the interpolation algorithm needs at least 4 values.
The data points for interpolation can also have a Feature with all its customization possibilities as source:

.. code-block:: python
    :linenos:

     endVal = Feature(id="endVal",
                       name="endVal",
                       victim=m1,
                       distribution={"Feature": {"Normal": {"mean": 5.2, "stdev": 0.1}}}
                       )


    ts_features = Feature(id="ftr_ts,
                          name="Feature_Time_Series",
                          step_time=0.1,
                          distribution={"Function": {(0, 1): "0.5*x + 2",
                                                     (1, 3): [[1, 1.5, 2, 3], [4, 4.2, 4.3, "EndVal"]]},
                                        "EndVal": endVal,
                                        "DataPoints": 20,
                                        "Feature": {"Normal": {"stdev": 0.1}}
                                       }
                          )

In this example, the final value for interpolation is received from Feature "endVal".

Failures
---------

TODO

.. _distributions:

Distributions and StateControllers
-----------------------------------

Using our StateControllers in combination with distributions allows for complex control over the lifecycle behaviour of features.
This can be used to model data drifts or distribution shifts.

.. code-block:: python
    :linenos:

    # TODO

* Labels

Export
------

TODO how to export features and timeseries to csv, how to export to database, ...

Further customization
------------------------

How to write new classes that fit into the ManPy Framework?

