from manpy.simulation.imports import Repairman, Machine, Source, Exit, Failure, Feature
from manpy.simulation.Globals import runSimulation, G, ExcelPrinter

class Failure(Failure):
    def condition(self):
        value_1 = Ftr1.get_feature_value()
        value_2 = Ftr2.get_feature_value()
        if (value_1 + 40 * value_2) > 360:
            Ftr1.start_time = G.env.now
            Ftr2.start_time = G.env.now
            return True

# Objects
R = Repairman("R1", "Sascha")
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.1}}, entity="manpy.Part", capacity=100)
M1 = Machine("M1", "Machine1", processingTime={"Normal": {"mean": 0.2, "stdev": 0.1, "min": 0.08, "max": 0.34}})
M2 = Machine("M2", "Machine2", processingTime={"Normal": {"mean": "0.01*x+0.2", "stdev": "0.01*x+0.1", "min": "0.01*x+0.08", "max": "0.01*x+0.34"}})
E1 = Exit("E1", "Exit1")

# ObjectInterruption
F1 = Failure(victim=M1, conditional=True)
F2 = Failure(victim=M2, distribution={"TTF": {"Normal": {"mean": 120, "stdev": 45, "min": 60, "max": 200}}, "TTR": {"Normal": {"mean": 10, "stdev": 3, "min": 5, "max": 18}}}, repairman=R)
Ftr1 = Feature("Ftr1", "Feature1", victim=M1, deteriorationType="constant", contribution=[F1], no_zero=True,
               distribution={"Time": {"Fixed": {"mean": 10}},
                             "Feature": {"Normal": {"mean": "3*x", "stdev": "0.02*x+3", "min": "2.98*x-3", "max": "3.02*x+3"}},
                             "TTR": {"Fixed": {"mean": 3}}})
Ftr2 = Feature("Ftr2", "Feature2", victim=M1, deteriorationType="working", start_time=120, contribution=[F1],
               distribution={"Time": {"Fixed": {"mean": 1}},
                             "Feature": {"Normal": {"mean": 0.5, "stdev": 0.2, "min": 0.1, "max": 0.9}}})

# Routing
S.defineRouting([M1])
M1.defineRouting([S], [M2])
M2.defineRouting([M1], [M2])
E1.defineRouting([M1])


def main(test=0):
    maxSimTime = 480

    # runSim with trace
    runSimulation([S, M1, M2, E1, F1, Ftr1, Ftr2, R], maxSimTime, trace="Yes")

    df = G.get_simulation_results_dataframe().drop(columns=["entity_name", "station_name"])
    ExcelPrinter(df, "RNG_testing")
    #df.to_csv("RNG_testing.csv", index=False, encoding="utf8")
    #print(df)

if __name__ == "__main__":
    main()
