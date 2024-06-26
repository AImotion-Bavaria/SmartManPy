from manpy.simulation.imports import Machine, Source, Exit, Feature, Timeseries
from manpy.simulation.core.Globals import runSimulation
import matplotlib.pyplot as plt


# Objects
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 2}}, entity="manpy.Part")
M1 = Machine("M1", "Machine1", processingTime={"Normal": {"mean": 5, "stdev": 0.5}})
E1 = Exit("E1", "Exit1")

# ObjectProperty
Ftr1 = Feature("Ftr1", "Feature1", victim=M1, distribution={"Feature": {"Normal": {"mean": 2.71828, "stdev": 0.3}}})
Ftr2 = Feature("Ftr2", "Feature2", victim=M1, distribution={"Feature": {"Normal": {"mean": 2.71828**2, "stdev": 0.3}}})
# Interpolation uses at least 4 points to interpolate a unique function for every entity
# It is possible to use feature values or even functions as points
TS = Timeseries("TS", "TimeSeries", victim=M1, no_negative=True,
                      distribution={"Function": {(0, 1): "-5*x**2+10*x",
                                                 (1, 4): [[1, 2, 3, 4], [5, "Ftr1", "Ftr2", "Ftr1**3"]]},
                                    "Ftr1": Ftr1, "Ftr2": Ftr2,
                                    "DataPoints": 100})

# Routing
S.defineRouting([M1])
M1.defineRouting([S], [E1])
E1.defineRouting([M1])


def main():
    maxSimTime = 20

    runSimulation([S, M1, E1, Ftr1, Ftr2, TS], maxSimTime)

    for i in M1.entities:
        plt.plot([2], [i.features[0]], "o", c="blue", label="Ftr1")
        plt.plot([3], [i.features[1]], "o", c="green", label="Ftr2")
        plt.plot(i.timeseries_times[0], i.timeseries[0], c="red", label="TS")
        plt.legend()
        plt.show()

if __name__ == "__main__":
    main()
