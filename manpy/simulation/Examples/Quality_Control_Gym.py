from manpy.simulation.imports import Machine, Source, Exit, Feature, Queue, SimpleStateController
from manpy.simulation.core.GymEnv import QualityEnv, PolicyNetwork
import numpy as np
import statistics
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
        dists = [{"Feature": {"Normal": {"mean": 200, "stdev": 50, "min": 0, "max": 400}}},
                 {"Feature": {"Normal": {"mean": 600, "stdev": 30, "min": 400, "max": 800}}}]
        boundaries = {(0, 25): 0, (25, None): 1}
        distribution_controller = SimpleStateController(states=dists, labels=["ok", "defect"], boundaries=boundaries,
                                                        wear_per_step=1.0, reset_amount=40)
        Ftr1 = Feature("Ftr1", "Feature1", victim=M1,
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
        if action == 1 and activeEntity.labels[-1] == "ok":
            return -1
        elif action == 1 and activeEntity.labels[-1] == "defect":
            return 1
        elif action == 0 and activeEntity.labels[-1] == "ok":
            return 1
        elif action == 0 and activeEntity.labels[-1] == "defect":
            return -1


simu = ExampleEnv(observation_extremes=[(0, 800)], policy_network=PolicyNetwork(1), maxSteps=6000, steps_between_updates=5, save_policy_network=True)
simu.reset()


x = []
y = []
for i in range(0, len(simu.all_rewards), len(simu.all_rewards)//10):
    x.append(i/1000)
    y.append(statistics.mean(simu.all_rewards[i:i+len(simu.all_rewards)//10]))
plt.plot(x, y)
plt.ylim(-1, 1)
plt.xlabel('Steps in thousands')
plt.ylabel('Reward')
plt.show()
plt.savefig("reward_simple_example.png")
