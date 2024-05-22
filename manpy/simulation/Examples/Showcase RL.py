from manpy.simulation.imports import Machine, Source, Exit, Feature, Queue, SimpleStateController
from manpy.simulation.core.GymEnv import QualityEnv, PolicyNetwork
import numpy as np
import statistics
import matplotlib.pyplot as plt
from manpy.simulation.core.ProductionLineModule import generate_routing_from_list
from scipy.interpolate import UnivariateSpline


class ExampleEnv(QualityEnv):
    def prepare(self):
        # Objects
        S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.1}}, entity="manpy.Part")

        # Assign the condition as the "control" parameter for any machine
        M1 = Machine("M1", "Machine1", processingTime={"Normal": {"mean": 0.2, "stdev": 0.1, "min": 0.08, "max": 0.34}})
        M2 = Machine("M2", "Machine2", processingTime={"Normal": {"mean": 1, "stdev": 0.3, "min": 0.5, "max": 2}})
        M3 = Machine("M3", "Machine3", processingTime={"Normal": {"mean": 0.5, "stdev": 0.2, "min": 0.2, "max": 0.8}},
                     control=self.step)

        Q1 = Queue("Q1", "Queue1")
        Q2 = Queue("Q2", "Queue2")
        Q3 = Queue("Q3", "Queue3")

        E1 = Exit("E1", "Exit1")

        # ObjectProperty
        dists_1 = [{"Feature": {"Normal": {"mean": 3800, "stdev": 100, "min": 3400, "max": 4200}}},
                   {"Feature": {"Normal": {"mean": 4500, "stdev": 100, "min": 4100, "max": 4900}}}]
        dists_2 = [{"Feature": {"Normal": {"mean": 200, "stdev": 50, "min": 0, "max": 400}}},
                   {"Feature": {"Normal": {"mean": 1800, "stdev": 80, "min": 1500, "max": 2100}}}]
        dists_3 = [{"Feature": {"Normal": {"mean": 45000, "stdev": 2000, "min": 40000, "max": 50000}}},
                   {"Feature": {"Normal": {"mean": 15000, "stdev": 3000, "min": 11000, "max": 19000}}}]

        distribution_controller_1 = SimpleStateController(states=dists_1, labels=["ok", "defect"],
                                                          boundaries={(0, 25): 0, (25, None): 1},
                                                          wear_per_step=1.0, reset_amount=30)
        distribution_controller_2 = SimpleStateController(states=dists_2, labels=["ok", "defect"],
                                                          boundaries={(0, 5): 0, (5, None): 1},
                                                          wear_per_step=1.0, reset_amount=6)
        distribution_controller_3 = SimpleStateController(states=dists_3, labels=["ok", "defect"],
                                                          boundaries={(0, 50): 0, (50, None): 1},
                                                          wear_per_step=1.0, reset_amount=59)

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
        generate_routing_from_list(list(map(lambda x: [x], objectList[:8])))

        return objectList

    def obs(self):
        activeEntity = self.machine.Res.users[0]
        return np.array(activeEntity.features)

    def rew(self, action):
        activeEntity = self.machine.Res.users[0]

        if action == 1 and "defect" in activeEntity.labels:  # True Negative
            return 1
        elif action == 0 and "defect" in activeEntity.labels:  # False Positive
            return -2
        elif action == 1:  # False Negative
            return -4
        elif action == 0:  # True Positive
            return 2


def plot(simulation, size=40):
    sim_time = simulation.objectList[0].env.now
    steps_taken = len(simulation.all_rewards)

    # Plot Performance
    x, y1, y2, y3, defect = [], [], [], [], []
    minima, maxima = min(simulation.all_rewards), max(simulation.all_rewards)
    j = 0
    for ind, i in enumerate(range(0, steps_taken, steps_taken // 20)):
        x.append(i / 1000)

        # Rewards
        average_reward = statistics.mean(simulation.all_rewards[i:i + steps_taken // 20])
        y1.append((average_reward - minima) / (maxima - minima) * 100)

        # Correct actions
        y2.append((sum([1 for reward in simulation.all_rewards[i:i + steps_taken // 20] if reward > 0]) / (steps_taken // 20)) * 100)

        # Defect parts
        for entity in simu.objectList[7].entities[j:]:
            if max(entity.feature_times) > (sim_time // 20)*(ind+1):
                j = simu.objectList[7].entities.index(entity)
                break
            elif "defect" in entity.labels:
                defect.append(1)
            else:
                defect.append(0)
        y3.append((sum(defect) / len(defect)) * 100)
        defect = []

    print(f"Rewards:         {y1[-1]:>6.2f}%")
    print(f"Correct actions: {y2[-1]:>6.2f}%")
    print(f"Defect parts:    {y3[-1]:>6.2f}%")

    # plt.plot(x, y1, label="Rewards")
    # plt.plot(x, y2, label="Correct actions")
    # plt.plot(x, y3, label="Defect parts")
    plt.plot(x, y1, label="Rewards", color='black', linestyle='-')
    plt.plot(x, y2, label="Correct actions", color='red', linestyle='--')
    plt.plot(x, y3, label="Defect parts", color='grey', linestyle='-.')

    plt.xlabel('Steps in thousands')
    plt.ylabel('Percent')
    plt.ylim(0, 100)
    plt.legend(loc='center right')
    plt.title("Performance")
    plt.savefig("performance_percent.pdf", format="pdf")
    plt.show()

    # plot difference of probs
    x = []
    y = []
    for i in range(0, len(simulation.all_probs), len(simulation.all_probs) // 20):
        x.append(i / 1000)
        y.append(
            statistics.mean([max(probs) - min(probs) for probs in simulation.all_probs[i:i + len(simulation.all_probs) // 20]]))

    plt.plot(x, y)
    plt.ylabel('Difference of probabilities')

    plt.show()
    print(f"Difference of probabilities: {y[-1]:.2f}")

    # plot features and actions
    y1 = [[]] * 6
    good_actions_x, good_actions_y, bad_actions_x, bad_actions_y = [], [], [], []

    Ftr1 = simulation.objectList[8].featureHistory[:size]
    Ftr2 = simulation.objectList[9].featureHistory[:size]
    Ftr3 = simulation.objectList[10].featureHistory[:size]
    Ftr4 = simulation.objectList[11].featureHistory[:size]
    Ftr5 = simulation.objectList[12].featureHistory[:size]
    Ftr6 = simulation.objectList[13].featureHistory[:size]

    for ind, ((machine, action), reward) in enumerate(zip(simulation.all_actions[:size], simulation.all_rewards[:size])):
        if machine == 3:
            # features
            y = [Ftr1[ind], Ftr2[ind], Ftr3[ind], Ftr4[ind], Ftr5[ind], Ftr6[ind]]
            for i, ftr in enumerate(y):
                y1[i] = y1[i] + [ftr]
            # normalize
            for i in range(6):
                y1[i][-1] = (y1[i][-1] - observation_extremes[i][0]) / (
                    observation_extremes[i][1] - observation_extremes[i][0])

            # actions
            if reward > 0:
                good_actions_x.append(len(y1[0]))
                good_actions_y.append(action)
            else:
                bad_actions_x.append(len(y1[0]))
                bad_actions_y.append(action)

    x1 = range(len(y1[0]))
    s = 0.3

    # Machine 3
    plt.figure(figsize=(10, 4))
    xs = np.linspace(min(x1), max(x1), 1000)
    for i in range(6):
        spl = UnivariateSpline(x1, y1[i], s=s)
        if i >= 3:  # Apply grey color and alpha for the last three features
            plt.plot(xs, spl(xs), color='grey', alpha=0.3, label=f'Feature {i + 1}')
        else:
            plt.plot(xs, spl(xs), label=f'Feature {i + 1}')
    plt.scatter(good_actions_x, good_actions_y, color='green', label='Good Action')
    plt.scatter(bad_actions_x, bad_actions_y, color='red', label='Bad Action')
    plt.title("Machine 3")
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=4)
    plt.ylim(-0.1, 1.1)
    plt.tight_layout()

    plt.savefig("Machine 3.png")
    plt.show()


if __name__ == "__main__":
    # Simulation
    observation_extremes = [(3400, 4900), (0, 2100), (11000, 50000), (1, 9), (50000, 57000), (0.2, 0.8)]
    simu = ExampleEnv(observations=observation_extremes, policy_network=PolicyNetwork(len(observation_extremes)), maxSteps=24000, updates=100)
    simu.reset()

    plot(simu, size=40)
