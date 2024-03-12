from manpy.simulation.imports import Machine, Source, Exit, Feature, Queue, SimpleStateController
from manpy.simulation.core.GymEnv import QualityEnv
import numpy as np
import statistics
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

class ExampleEnv(QualityEnv):
    def prepare(self):
        # Objects
        S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.4}}, entity="manpy.Part", capacity=1)
        Löten = Machine("M0", "Löten", processingTime={"Normal": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}},
                                                       control=self.step)
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

        dists = [{"Feature": {"Normal": {"mean": 400, "stdev": 50}}},
                 {"Feature": {"Normal": {"mean": 500, "stdev": 30}}}]
        boundaries = {(0, 25): 0, (25, None): 1}
        distribution_controller = SimpleStateController(states=dists, labels=["ok", "defect"], boundaries=boundaries, wear_per_step=1.0, reset_amount=40)

        Einsinktiefe = Feature("Ftr4", "Feature4", victim=Löten,
                               distribution_state_controller=distribution_controller)

        # Routing
        S.defineRouting([Löten])
        Löten.defineRouting([S], [Q])
        Q.defineRouting([Löten], [Kleben])
        Kleben.defineRouting([Q], [E1])
        E1.defineRouting([Kleben])

        return [S, Löten, Q, Kleben, E1, Spannung, Strom, Widerstand, Kraft, Einsinktiefe]

    def obs(self):
        activeEntity = self.machine.Res.users[0]
        return np.array(activeEntity.features)

    def rew(self, action):
        activeEntity = self.machine.Res.users[0]
        if action == 1 and activeEntity.labels[-1] == "ok":
            return 0
        elif action == 1 and activeEntity.labels[-1] == "defect":
            return 1
        elif action == 0 and activeEntity.labels[-1] == "ok":
            return 1
        elif action == 0 and activeEntity.labels[-1] == "defect":
            return 0

simu = ExampleEnv('M0', observations=5, maxSimTime=float('inf'), maxSteps=100000, updates=1)
simu.reset()


# df1 = pd.DataFrame(simu.all_rewards).melt()
# df1.rename(columns={"variable": "steps", "value": "reward"}, inplace=True)
# sns.set(style="darkgrid", context="talk", palette="rainbow")
# sns.lineplot(x="steps", y="reward", data=df1).set(

#     title="Reinforce Example Quality Control"
# )
l = []
for i in range(0, len(simu.all_rewards), 1000):
    if i+1000 > len(simu.all_rewards):
        l.append(statistics.mean(simu.all_rewards[i:len(simu.all_rewards)]))
    else:
        l.append(statistics.mean(simu.all_rewards[i:i+1000]))
plt.plot(list(range(1, len(l) + 1)), l)
plt.show()
