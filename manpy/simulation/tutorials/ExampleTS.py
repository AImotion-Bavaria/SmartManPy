from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue, Timeseries
from manpy.simulation.core.Globals import runSimulation
import matplotlib.pyplot as plt


# Objects
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.4}}, entity="manpy.Part")
Soldering = Machine("M0", "Soldering", processingTime={"Normal": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
Q = Queue("Q", "Queue")
Gluing = Machine("M1", "Gluing", processingTime={"Fixed": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
E1 = Exit("E1", "Exit1")

# ObjectProperty

# In TimeSeries distribution, one or multiple functions with different intervals are used,
# to generate a certain amount of data points across the entire range from the lowest to the highest point in any interval
# The step_time can be manually set or dynamically calculated based on the entity's processing time
# Functions in TimeSeries distribution can utilize assigned variables, similar to how dependent variables work for Features

# Soldering
Voltage = Timeseries("TS0", "Voltage", victim=Soldering, no_negative=True, step_time=0.03,
                     distribution={"Function" : {(-1, 0) : "-1.6*x**2+1.6", (0, 1) : "-1.6*x**2+2"}, "DataPoints" : 20, "Feature": {"Normal": {"stdev": 0.02}}})
Current = Timeseries("TS1", "Current", victim=Soldering, step_time=0.03,
                     distribution={"Function" : {(-1, 1) : "1000*x1 + 1900"}, "x1" : Voltage, "DataPoints" : 20, "Feature": {"Normal": {"stdev": 20}}})
Resistance = Timeseries("TS2", "Resistance", victim=Soldering, step_time=0.03,
                        distribution={"Function" : {(-1, 1) : "(x1/x2)*1000000"}, "x1" : Voltage, "x2" : Current, "DataPoints" : 20})
Pressure = Feature("Ftr0", "Pressure", victim=Soldering,
                   distribution={"Feature": {"Normal": {"mean": 180, "stdev": 30}}})
Insertion_depth = Feature("Ftr1", "Insertion_depth", victim=Soldering,
                          distribution={"Feature": {"Normal": {"mean": 400, "stdev": 50}}})

# Gluing
Flow_rate = Feature("Ftr2", "Flow_rate", victim=Gluing,
                    distribution={"Feature": {"Normal": {"mean": 50, "stdev": 5}}})
Temperature = Feature("Ftr3", "Temperature", victim=Gluing,
                      distribution={"Feature": {"Normal": {"mean": 190, "stdev": 10}}})
Mass = Feature("Ftr4", "Mass", victim=Gluing,
               distribution={"Feature": {"Normal": {"mean": 400, "stdev": 50}}})

# ObjectInterruption
Stuck = Failure("Flr0", "Failure0", victim=Gluing, entity=True,
                distribution={"TTF": {"Fixed": {"mean": 0}}, "TTR": {"Normal": {"mean": 2,"stdev": 0.2, "min":0, "probability": 0.05}}})


# Routing
S.defineRouting([Soldering])
Soldering.defineRouting([S], [Q])
Q.defineRouting([Soldering], [Gluing])
Gluing.defineRouting([Q], [E1])
E1.defineRouting([Gluing])


def main(test=0):
    maxSimTime = 50
    objectList = [S, Soldering, Q, Gluing, E1, Voltage, Current, Resistance, Pressure, Insertion_depth, Flow_rate, Temperature, Mass]
    runSimulation(objectList, maxSimTime)

    # show dependency of TimeSeries
    plt.plot(E1.entities[0].timeseries_times[0], E1.entities[0].timeseries[0])
    plt.show()
    plt.plot(E1.entities[0].timeseries_times[1], E1.entities[0].timeseries[1], c="orange")
    plt.show()
    plt.plot(E1.entities[0].timeseries_times[2], E1.entities[0].timeseries[2], c="g")
    plt.show()

    #for unittest
    if test:
        return E1.entities[0]

if __name__ == "__main__":
    main()
