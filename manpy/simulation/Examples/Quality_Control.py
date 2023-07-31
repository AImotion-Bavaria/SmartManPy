from manpy.simulation.imports import Machine, Source, Exit, Feature
from manpy.simulation.core.Globals import runSimulation

# Any function can be employed as the condition to control the entity's quality before it exits the machine
# You can utilize any simulation values for quality control purposes
# Return True to reject/discard the entity, and False to allow it to proceed
def condition(self):
    activeEntity = self.Res.users[0]
    if activeEntity.features[0] > 7 or activeEntity.features[0] < 3:
        return True
    else:
        return False

# Objects
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.1}}, entity="manpy.Part")
# Assign the condition as the "control" parameter for any machine
M1 = Machine("M1", "Machine1", processingTime={"Normal": {"mean": 0.2, "stdev": 0.1, "min": 0.08, "max": 0.34}}, control=condition)
E1 = Exit("E1", "Exit1")

# ObjectProperty
Ftr1 = Feature("Ftr1", "Feature1", victim=M1,
               distribution={"Feature": {"Normal": {"mean": 5, "stdev": 2, "min": 1, "max": 9}}})

# Routing
S.defineRouting([M1])
M1.defineRouting([S], [E1])
E1.defineRouting([M1])


def main(test=0):
    maxSimTime = 480

    runSimulation([S, M1, E1, Ftr1], maxSimTime)

    print("""
            Discards: {}
            Produced: {}
            """.format(len(M1.discards), E1.numOfExits))

if __name__ == "__main__":
    main()
