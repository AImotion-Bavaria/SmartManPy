from manpy.simulation.imports import Machine, Source, Exit, Feature, Assembly
from manpy.simulation.core.Globals import runSimulation, G, getFeatureData

# Objects
S1 = Source("S1", "Source1", interArrivalTime={"Fixed": {"mean": 1}}, entity="manpy.Part")
# Setting a capacity for a Frame part means that the next assembly process will wait until that quantity of parts has arrived
S2 = Source("S2", "Source2", interArrivalTime={"Fixed": {"mean": 15}}, entity="manpy.Frame", capacity=20)
M1 = Machine("M1", "Machine1", processingTime={"Normal": {"mean": 1, "stdev": 0.1}})
M2 = Machine("M2", "Machine2", processingTime={"Normal": {"mean": 10, "stdev": 1}})
A = Assembly("A", "Assembly")
E1 = Exit("E1", "Exit1")

# ObjectProperty
Ftr1 = Feature("Ftr1", "Feature1", victim=M1,
               distribution={"Feature": {"Normal": {"mean": 5, "stdev": 2, "min": 1, "max": 9}}})

# Routing
S1.defineRouting([M1])
S2.defineRouting([M2])
M1.defineRouting([S1], [A])
M2.defineRouting([S2], [A])
A.defineRouting([M1, M2], [E1])
E1.defineRouting([A])


def main(test=0):
    maxSimTime = 480
    runSimulation([S1, S2, M1, M2, A, E1, Ftr1], maxSimTime)

    # show results of assembly
    print("""
    Produced by M1: {}\n
    Produced by M2: {}\n
    Finished Parts: {}\n
    """.format(len(M1.entities), len(M2.entities), len(E1.entities)))

    # for unittest
    if test:
        result = {}
        result["M1"] = len(M1.entities)
        result["E1"] = len(E1.entities)
        return result

if __name__ == "__main__":
    main()
