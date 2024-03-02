from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue
from manpy.simulation.core.Globals import runSimulation, getFeatureData, resetSimulation, G
from manpy.simulation.core.GymEnv import QualityEnv
import numpy as np
import types

def step(self, action):
    self._action_discard(action)

    activeEntity = self.Res.users[0]
    observation = np.array(activeEntity.features)

    # calculate reward
    means = [1.6, 3500, 450, 180, 400]
    stdevs = [0.2, 200, 50, 30, 50]
    for idx, feature in enumerate(activeEntity.features):
        if feature != None:
            min = means[idx] - 2 * stdevs[idx]
            max = means[idx] + 2 * stdevs[idx]
            if feature < min or feature > max:
                if action == 1:
                    reward = 1
                else:
                    reward = 0
                break
            else:
                if action == 1:
                    reward = 0
                else:
                    reward = 1

    info = None

    return observation, reward, False, False, info


def prepare():
    # Objects
    S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.4}}, entity="manpy.Part", capacity=1)
    Löten = Machine("M0", "Löten", processingTime={"Normal": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}},
                                                   control=Agent.step)
    Q = Queue("Q", "Queue")
    Kleben = Machine("M1", "Kleben",
                     processingTime={"Fixed": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
    E1 = Exit("E1", "Exit1")

    # ObjectProperty
    # Löten
    Spannung = Feature("Ftr0", "Feature0", victim=Löten,
                       distribution={"Feature": {"Normal": {"mean": 1.6, "stdev": 0.2}}})
    Strom = Feature("Ftr1", "Feature1", victim=Löten,
                    distribution={"Feature": {"Normal": {"mean": 3500, "stdev": 200}}})
    Widerstand = Feature("Ftr2", "Feature2", victim=Löten,
                         distribution={"Feature": {"Normal": {"mean": 450, "stdev": 50}}})
    Kraft = Feature("Ftr3", "Feature3", victim=Löten,
                    distribution={"Feature": {"Normal": {"mean": 180, "stdev": 30}}})
    Einsinktiefe = Feature("Ftr4", "Feature4", victim=Löten,
                           distribution={"Feature": {"Normal": {"mean": 400, "stdev": 50}}})

    # Routing
    S.defineRouting([Löten])
    Löten.defineRouting([S], [Q])
    Q.defineRouting([Löten], [Kleben])
    Kleben.defineRouting([Q], [E1])
    E1.defineRouting([Kleben])

    return [S, Löten, Q, Kleben, E1, Spannung, Strom, Widerstand, Kraft, Einsinktiefe]

Agent = QualityEnv("M0", 5, 10000)
Agent.prepare = types.MethodType(prepare, Agent)
Agent.step = types.MethodType(step, Agent)
