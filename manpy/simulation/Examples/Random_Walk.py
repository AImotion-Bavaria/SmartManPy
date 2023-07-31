from manpy.simulation.imports import Machine, Source, Exit, Feature
from manpy.simulation.core.Globals import runSimulation ,getFeatureData
import matplotlib.pyplot as plt

# Objects
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 10}}, entity="manpy.Part")
M1 = Machine("M1", "Machine1", processingTime={"Fixed": {"mean": 15}})
E1 = Exit("E1", "Exit1")

# ObjectProperty
# With the 'random_walk' parameter, the next feature value is influenced by the previous one
Ftr1 = Feature("Ftr1", "Feature1", victim=M1, random_walk=True, distribution={"Feature": {"Normal": {"mean": 0, "stdev": 5, "min": -10, "max": 10}}})

# Routing
S.defineRouting([M1])
M1.defineRouting([S], [E1])
E1.defineRouting([M1])

def main(test=0):
    maxSimTime = 500
    runSimulation([S, M1, E1, Ftr1], maxSimTime)

    # show the random walk
    rw = getFeatureData([M1], time=True)
    plt.plot(rw["M1_Ftr1_t"], rw["M1_Ftr1_v"])
    plt.show()


    # for unittest
    if test:
        result = {}
        result["Ftr1"] = Ftr1.featureHistory
        return result

if __name__ == "__main__":
    main()
