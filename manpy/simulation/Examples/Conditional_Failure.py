from manpy.simulation.imports import Machine, Source, Exit, Failure, Queue, Feature, SimpleStateController
from manpy.simulation.core.Globals import runSimulation, G

# Any function can be employed as the condition for a Failure to occur
# You can utilize any simulation values for the condition
# Return True to let the Failure occur


def condition(self):
    value_1 = Ftr1.get_feature_value()
    value_2 = Ftr2.get_feature_value()

    if value_1 is not None and value_2 is not None:
        if (value_1 + 20 * value_2) > 200:
            return True
        else:
            return False
    else:
        return False


# Objects
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.1}}, entity="manpy.Part", capacity=1)
Q = Queue("Q1", "Queue")
M1 = Machine("M1", "Machine1", processingTime={"Normal": {"mean": 0.2, "stdev": 0.1, "min": 0.08, "max": 0.34}})
M2 = Machine("M2", "Machine2", processingTime={"Normal": {"mean": 0.3, "stdev": 0.1, "min": 0.1, "max": 0.4}})

E1 = Exit("E1", "Exit1")

# ObjectInterruption
# Assign the condition as the "conditional" parameter for any machine
F1 = Failure("CondFlr", "CondFailure", victim=M1, conditional=condition, waitOnTie=True,
             distribution={"TTF": {"Fixed": {"mean": 0}}, "TTR": {"Fixed": {"mean": 10}}})

# ObjectProperty
# Link failures to "contribute" for a Feature when utilizing its values
Ftr1 = Feature("Ftr1", "Feature1", victim=M1, contribute=[F1], no_negative=True,
               distribution={"Feature": {"Normal": {"mean": 5, "stdev": 1, "min": 1, "max": 10}}}
               )

dists = [{"Feature": {"Normal": {"mean": 0.5, "stdev": 0.2, "min": 0.1, "max": 0.9}}},
         {"Feature": {"Normal": {"mean": 500, "stdev": 0.2, "min": 400, "max": 600}}}]
boundaries = {(0, 10): 0, (10, None): 1}
distribution_controller = SimpleStateController(states=dists, boundaries=boundaries, wear_per_step=1.0, reset_amount=None)

Ftr2 = Feature("Ftr2", "Feature2", victim=M1,
               contribute=[F1],
               distribution_state_controller=distribution_controller, reset_distributions=True
               )

# Routing
S.defineRouting([M1])
M1.defineRouting([S], [Q])
Q.defineRouting([M1], [M2])
M2.defineRouting([Q], [E1])
E1.defineRouting([M2])


def main(test=0):
    maxSimTime = 1000
    runSimulation([S, Q, M1, M2, E1,
                   F1,
                   Ftr1, Ftr2], maxSimTime)


if __name__ == "__main__":
    main()
