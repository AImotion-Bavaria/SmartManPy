from manpy.simulation.imports import Machine, Source, Exit, Feature, Queue, SimpleStateController
from manpy.simulation.core.GymEnv import QualityEnv
from manpy.simulation.core.Globals import get_feature_values_by_id, get_feature_labels_by_id
import numpy as np
import statistics
import pandas as pd
# import seaborn as sns
import matplotlib.pyplot as plt

class ExampleEnv(QualityEnv):
    def prepare(self):
        # Objects
        S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.1}}, entity="manpy.Part")

        # Assign the condition as the "control" parameter for any machine
        M1 = Machine("M1", "Machine1", processingTime={"Normal": {"mean": 0.2, "stdev": 0.1, "min": 0.08, "max": 0.34}},
                     control=self.step)

        E1 = Exit("E1", "Exit1")

        # ObjectProperty
        dists = [{"Feature": {"Normal": {"mean": 400, "stdev": 50}}},
                 {"Feature": {"Normal": {"mean": 500, "stdev": 30}}}]
        boundaries = {(0, 25): 0, (25, None): 1}
        distribution_controller = SimpleStateController(states=dists, labels=["ok", "defect"], boundaries=boundaries,
                                                        wear_per_step=1.0, reset_amount=40)
        Ftr1 = Feature("Ftr1", "Feature1", victim=M1,
                       # distribution={"Feature": {"Normal": {"mean": 5, "stdev": 2, "min": 1, "max": 9}}},
                       distribution_state_controller=distribution_controller,
                       )

        # Routing
        S.defineRouting([M1])
        M1.defineRouting([S], [E1])
        E1.defineRouting([M1])

        return [S, M1, E1, Ftr1]

    def obs(self):
        activeEntity = self.machine.Res.users[0]
        return np.array(activeEntity.features)

    def rew(self, action):
        activeEntity = self.machine.Res.users[0]
        feature_value = get_feature_values_by_id(activeEntity, ["Ftr1"])[0]

        if feature_value > 7 or feature_value < 3:
            defect = 1
        else:
            defect = 0
        if action == defect:
            return 1
        else:
            return 0



simu = ExampleEnv('M1', observations=1, maxSimTime=float('inf'), maxSteps=100000, updates=1)
simu.reset()


# df1 = pd.DataFrame(simu.all_rewards).melt()
# df1.rename(columns={"variable": "steps", "value": "reward"}, inplace=True)
# sns.set(style="darkgrid", context="talk", palette="rainbow")
# sns.lineplot(x="steps", y="reward", data=df1).set(

#     title="Reinforce Example Quality Control"
# )
l = []
for i in range(0, len(simu.all_rewards), 10000):
    if i+1000 > len(simu.all_rewards):
        l.append(statistics.mean(simu.all_rewards[i:len(simu.all_rewards)]))
    else:
        l.append(statistics.mean(simu.all_rewards[i:i+1000]))
plt.plot(list(range(1, len(l) + 1)), l)
plt.show()
