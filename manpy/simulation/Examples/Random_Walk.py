from manpy.simulation.imports import Machine, Source, Exit, Feature
from manpy.simulation.core.Globals import runSimulation, G, ExcelPrinter

# Objects
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 10}}, entity="manpy.Part", capacity=100)
M1 = Machine("M1", "Machine1", processingTime={"Fixed": {"mean": 30}})
E1 = Exit("E1", "Exit1")

# ObjectProperty
Ftr1 = Feature("Ftr1", "Feature1", random_walk=True, distribution={"Feature": {"Normal": {"mean": 0, "stdev": 5, "min": -10, "max": 10}}})

# Routing
S.defineRouting([M1])
M1.defineRouting([S], [E1])
E1.defineRouting([M1])

def main(test=0):
    maxSimTime = 500

    # runSim with trace
    runSimulation([S, M1, E1, Ftr1], maxSimTime, trace=True)

    if test:
        result = {}
        result["Ftr1"] = Ftr1.featureHistory
        return result

    df = G.get_simulation_results_dataframe().drop(columns=["entity_name", "station_name"])
    ExcelPrinter(df, "Random_Walk")

if __name__ == "__main__":
    main()
