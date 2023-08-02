Tutorials
===========
This page gives you an overview of the general usage paradigms of our ManPy extension

Introduction
-------------
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


Features
--------

Features are our most important extension to the original ManPy.
TODO:

* Dependencies

.. code-block:: python
    :linenos:

    f1 = Feature("F1", "Feature1", victim=m1, entity=True,
                    distribution={"Time": {"Fixed": {"mean": 1}},
                                  "Feature": {"Normal": {"mean": 50, "stdev": 5}}})

Time Series
------------

TODO


Failures
---------

TODO

Quality Control
-----------------

TODO

Distributions and StateControllers
-----------------------------------

Using our StateControllers in combination with distributions allows for complex control over the lifecycle behaviour of features.
This can be used to model data drifts of distribution shifts.

.. code-block:: python
    :linenos:

    # TODO

Export
------

TODO how to export features and timeseries to csv, how to export to database, ...

Further customization
------------------------

How to write new classes that fit into the ManPy Framework?

