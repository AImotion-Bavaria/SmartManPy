from manpy.simulation.imports import Machine, Source, Exit, Failure, Queue, Feature, SimpleStateController
from manpy.simulation.core.Globals import runSimulation, G, ExcelPrinter


def condition(self):
    value_1 = Ftr1.get_feature_value()
    value_2 = Ftr2.get_feature_value()
    if (value_1 + 20 * value_2) > 200: # prev 360
        Ftr1.start_time = G.env.now
        Ftr2.start_time = G.env.now
        return True
    else:
        return False

# Objects
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.1}}, entity="manpy.Part", capacity=100)
Q = Queue("Q1", "Queue")
M1 = Machine("M1", "Machine1", processingTime={"Normal": {"mean": 0.2, "stdev": 0.1, "min": 0.08, "max": 0.34}})
M2 = Machine("M2", "Machine2", processingTime={"Normal": {"mean": "0.01*x+0.2", "stdev": "0.01*x+0.1", "min": "0.01*x+0.08", "max": "0.01*x+0.34"}})
E1 = Exit("E1", "Exit1")

# ObjectInterruption
F1 = Failure(victim=M1, conditional=condition,
                         distribution={"TTR": {"Fixed": {"mean": 30}}})

Ftr1 = Feature("Ftr1", "Feature1", victim=M1, contribute=[F1], no_negative=True,
               distribution={"Feature": {"Normal": {"mean": "3*x", "stdev": "0.02*x+3", "min": "2.98*x-3", "max": "3.02*x+3"}}}
               )

dists = [{"Time": {"Fixed": {"mean": 10}}, "Feature": {"Normal": {"mean": 0.5, "stdev": 0.2, "min": 0.1, "max": 0.9}}},
         {"Time": {"Fixed": {"mean": 10}}, "Feature": {"Normal": {"mean": 0.5, "stdev": 0.2, "min": 0.1, "max": 0.9}}}]
boundaries = {(0, 10): 0, (10, None): 1}
distribution_controller = SimpleStateController(states=dists, boundaries=boundaries, wear_per_step=1.0, reset_amount=None)

Ftr2 = Feature("Ftr2", "Feature2", victim=M1,
               start_time=60,
               contribute=[F1],
               # distribution={"Time": {"Fixed": {"mean": 10}},
               #               "Feature": {"Normal": {"mean": 0.5, "stdev": 0.2, "min": 0.1, "max": 0.9}}},
               distribution_state_controller=distribution_controller, reset_distributions=True
               )

# Routing
S.defineRouting([M1])
M1.defineRouting([S], [Q])
Q.defineRouting([M1], [M2])
M2.defineRouting([Q], [E1])
E1.defineRouting([M2])

def main(test=0):
    maxSimTime = 250

    # runSim with trace
    runSimulation([S, Q, M1, M2, E1, F1, Ftr1, Ftr2], maxSimTime, trace="Yes")

    df = G.get_simulation_results_dataframe().drop(columns=["entity_name", "station_name"])
    ExcelPrinter(df, "RNG")
    #df.to_csv("RNG_testing.csv", index=False, encoding="utf8")
    #print(df)

if __name__ == "__main__":
    main()
