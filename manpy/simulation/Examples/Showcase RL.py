from manpy.simulation.imports import Machine, Source, Exit, Feature, Queue, SimpleStateController
from manpy.simulation.core.GymEnv import QualityEnv
import numpy as np
import statistics
import matplotlib.pyplot as plt
from manpy.simulation.core.ProductionLineModule import generate_routing_from_list

class ExampleEnv(QualityEnv):
    def prepare(self):
        # Objects
        S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.1}}, entity="manpy.Part", cost=3)

        # Assign the condition as the "control" parameter for any machine
        M1 = Machine("M1", "Machine1", processingTime={"Normal": {"mean": 0.2, "stdev": 0.1, "min": 0.08, "max": 0.34}},
                     control=self.step, cost=5)
        M2 = Machine("M2", "Machine2", processingTime={"Normal": {"mean": 1, "stdev": 0.3, "min": 0.5, "max": 2}}, cost=10)
        M3 = Machine("M3", "Machine3", processingTime={"Normal": {"mean": 0.5, "stdev": 0.2, "min": 0.2, "max": 0.8}},
                     control=self.step, cost=7)

        Q1 = Queue("Q1", "Queue1")
        Q2 = Queue("Q2", "Queue2")
        Q3 = Queue("Q3", "Queue3")

        E1 = Exit("E1", "Exit1", cost=2)

        # ObjectProperty
        dists_1 = [{"Feature": {"Normal": {"mean": 3800, "stdev": 100, "min": 3400, "max": 4200}}},
                   {"Feature": {"Normal": {"mean": 4000, "stdev": 10, "min": 3950, "max": 4050}}}]
        dists_2 = [{"Feature": {"Normal": {"mean": 200, "stdev": 50, "min": 0, "max": 400}}},
                   {"Feature": {"Normal": {"mean": 600, "stdev": 30, "min": 400, "max": 800}}}]
        dists_3 = [{"Feature": {"Normal": {"mean": 25000, "stdev": 2000, "min": 20000, "max": 30000}}},
                   {"Feature": {"Normal": {"mean": 18000, "stdev": 5000, "min": 15000, "max": 23000}}}]

        distribution_controller_1 = SimpleStateController(states=dists_1, labels=["ok", "defect"], boundaries={(0, 25): 0, (25, None): 1},
                                                        wear_per_step=1.0, reset_amount=27)
        distribution_controller_2 = SimpleStateController(states=dists_2, labels=["ok", "defect"], boundaries={(0, 5): 0, (5, None): 1},
                                                        wear_per_step=1.0, reset_amount=5)
        distribution_controller_3 = SimpleStateController(states=dists_3, labels=["ok", "defect"], boundaries={(0, 290): 0, (290, None): 1},
                                                        wear_per_step=1.0, reset_amount=299)

        Ftr1 = Feature("Ftr1", "Feature1", victim=M1,
                       distribution_state_controller=distribution_controller_1)
        Ftr2 = Feature("Ftr2", "Feature2", victim=M2,
                          distribution_state_controller=distribution_controller_2)
        Ftr3 = Feature("Ftr3", "Feature3", victim=M3,
                            distribution_state_controller=distribution_controller_3)
        Ftr4 = Feature("Ftr4", "Feature4", victim=M1,
                          distribution={"Feature": {"Normal": {"mean": 5, "stdev": 3, "min": 1, "max": 9}}})
        Ftr5 = Feature("Ftr5", "Feature5", victim=M1,
                            distribution={"Feature": {"Normal": {"mean": 53800, "stdev": 2000, "min": 50000, "max": 57000}}})
        Ftr6 = Feature("Ftr6", "Feature6", victim=M2,
                            distribution={"Feature": {"Normal": {"mean": 0.5, "stdev": 0.2, "min": 0.2, "max": 0.8}}})

        objectList = [S, Q1, M1, Q2, M2, Q3, M3, E1, Ftr1, Ftr2, Ftr3, Ftr4, Ftr5, Ftr6]

        # Routing
        generate_routing_from_list(list(map(lambda x: [x],objectList[:8])))

        return objectList

    def obs(self):
        activeEntity = self.machine.Res.users[0]
        return np.array(activeEntity.features)

    def rew(self, action):
        max_cost = 27
        activeEntity = self.machine.Res.users[0]
        if action == 1 and "defect" in activeEntity.labels: # True Negative
            return max_cost - activeEntity.cost
        elif action == 0 and "defect" in activeEntity.labels: # False Positive
            return -(max_cost - activeEntity.cost)
        elif action == 1: # False Negative
            return -(max_cost + activeEntity.cost)
        elif action == 0: # True Positive
            return max_cost - activeEntity.cost

observation_extrems = [(3400, 4150), (0, 800), (15000, 30000), (1, 9), (50000, 570000), (0.2, 0.8)]
simu = ExampleEnv(observations=observation_extrems, maxSteps=50000, updates=5)
simu.reset()


x = []
y = []
for i in range(0, len(simu.all_rewards), len(simu.all_rewards)//20):
    x.append(i/1000)
    y.append(statistics.mean(simu.all_rewards[i:i+len(simu.all_rewards)//20]))
plt.plot(x, y)
# plt.ylim(-45, 24)
plt.xlabel('Steps in thousands')
plt.ylabel('Cost saved')
plt.show()
