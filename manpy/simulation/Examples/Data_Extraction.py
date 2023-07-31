from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue, Timeseries
from manpy.simulation.core.Globals import runSimulation, getTimeSeriesData, getFeatureData


# Objects
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.4}}, entity="manpy.Part")
Soldering = Machine("M0", "Soldering", processingTime={"Normal": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
Q = Queue("Q", "Queue")
Gluing = Machine("M1", "Gluing", processingTime={"Fixed": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
E1 = Exit("E1", "Exit1")

# ObjectProperty
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
    maxSimTime = 5
    objectList = [S, Soldering, Q, Gluing, E1, Voltage, Current, Resistance, Pressure, Insertion_depth, Flow_rate, Temperature, Mass]


    # To utilize a database, you have two options:
    # 1. Import a pre-existing `DataBase` class from `DataBase.py`
    # 2. Easily set up your own database using the `ManPyDatabase` interface
    from manpy.simulation.core.Database import ManPyQuestDBDatabase
    db = ManPyQuestDBDatabase()
    runSimulation(objectList, maxSimTime, db=db)


    # To retrieve feature data from the simulation, utilize the getFeatureData function
    # The function accepts a list of machines and produces a DataFrame with all of their occurring features
    solder = getFeatureData([Soldering])
    print(solder.to_string(index=False), "\n")

    # With 'time=True', timestamps of the feature values are included in the DataFrame
    solder_time = getFeatureData([Soldering], time=True)
    print(solder_time.to_string(index=False), "\n")

    # The function supports multiple machines
    both = getFeatureData([Soldering, Gluing])
    print(both.to_string(index=False), "\n")

    # To retrieve timeseries data from the simulation, utilize the getTimeSeriesData function
    # The function accepts a timeSeries and returns a DataFrame representing that timeseries
    vol = getTimeSeriesData(Voltage)
    print(vol)


if __name__ == "__main__":
    main()
