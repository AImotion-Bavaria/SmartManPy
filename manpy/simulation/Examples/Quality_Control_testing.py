from manpy.simulation.imports import Repairman, Machine, Source, Exit, Failure, Feature
from manpy.simulation.Globals import runSimulation, G, ExcelPrinter

class Machine(Machine):
    def condition(self):
        activeEntity = self.Res.users[0]
        if activeEntity.features[0] > 7 or activeEntity.features[0] < 3:
            return True

# Objects
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.1}}, entity="manpy.Part", capacity=100)
M1 = Machine("M1", "Machine1", processingTime={"Normal": {"mean": 0.2, "stdev": 0.1, "min": 0.08, "max": 0.34}}, control=True)
E1 = Exit("E1", "Exit1")

# ObjectInterruption
Ftr1 = Feature("Ftr1", "Feature1", victim=M1, entity=True,
               distribution={"Time": {"Fixed": {"mean": 0.5}}, "Feature": {"Normal": {"mean": 5, "stdev": 2, "min": 1, "max": 9}}})

# Routing
S.defineRouting([M1])
M1.defineRouting([S], [E1])
E1.defineRouting([M1])


def main(test=0):
    maxSimTime = 480

    # runSim with trace
    runSimulation([S, M1, E1, Ftr1], maxSimTime, trace="Yes")

    df = G.get_simulation_results_dataframe().drop(columns=["entity_name", "station_name"])
    ExcelPrinter(df, "Quality_Control_testing")

    print("""
            Ausschuss: {}
            Menge Ausschuss: {}
            Produziert: {}
            """.format(len(M1.discards), M1.discards, E1.numOfExits))

if __name__ == "__main__":
    main()
