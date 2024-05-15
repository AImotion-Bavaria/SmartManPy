from manpy.simulation.imports import Machine, Source, Exit, Feature, Queue, SimpleStateController
from manpy.simulation.core.GymEnv import QualityEnv
import numpy as np
import statistics
import matplotlib.pyplot as plt
from manpy.simulation.core.ProductionLineModule import generate_routing_from_list
from scipy.interpolate import UnivariateSpline


class ExampleEnv(QualityEnv):
    def prepare(self):
        # Objects
        S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.1}}, entity="manpy.Part", cost=12)

        # Assign the condition as the "control" parameter for any machine
        M1 = Machine("M1", "Machine1", processingTime={"Normal": {"mean": 0.2, "stdev": 0.1, "min": 0.08, "max": 0.34}},
                     cost=5)
        M2 = Machine("M2", "Machine2", processingTime={"Normal": {"mean": 1, "stdev": 0.3, "min": 0.5, "max": 2}},
                     cost=10)
        M3 = Machine("M3", "Machine3", processingTime={"Normal": {"mean": 0.5, "stdev": 0.2, "min": 0.2, "max": 0.8}},
                     control=self.step, cost=7)

        Q1 = Queue("Q1", "Queue1")
        Q2 = Queue("Q2", "Queue2")
        Q3 = Queue("Q3", "Queue3")

        E1 = Exit("E1", "Exit1", cost=2)

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
        if self.machine.id == "M1":
            cost = 15
        elif self.machine.id == "M3":
            cost = 9
        else:
            cost = 5

        c = (cost + activeEntity.cost)
        if action == 1 and "defect" in activeEntity.labels:  # True Negative
            return c * 2
        elif action == 0 and "defect" in activeEntity.labels:  # False Positive
            return -c
        elif action == 1:  # False Negative
            return -c * 4
        elif action == 0:  # True Positive
            return c


def plot(simulation, m_one=True, size=70):
    # plot rewards
    s = 0.3  # smoothing factor
    x, y = [], []
    for i in range(0, len(simulation.all_rewards), len(simulation.all_rewards) // 20):
        x.append(i / 1000)
        y.append(statistics.mean(simulation.all_rewards[i:i + len(simulation.all_rewards) // 20]))

    # smoothing
    # spl = UnivariateSpline(x, y, s=s)
    # xs = np.linspace(min(x), max(x), 1000)
    # plt.plot(xs, spl(xs))

    plt.plot(x, y)
    plt.xlabel('Steps in thousands')
    plt.ylabel('Reward')
    plt.title('Reward over steps')
    plt.show()
    plt.savefig("reward.png")
    print(f"Reward: {y[-1]}")

    # plot % of defect parts in exit
    x, y, defect = [], [], []
    for i in range(0, len(simulation.objectList[7].entities), len(simulation.objectList[7].entities) // 20):
        for entity in simulation.objectList[7].entities[i:i + len(simulation.objectList[7].entities) // 20]:
            if "defect" in entity.labels:
                defect.append(1)
            else:
                defect.append(0)
        if len(defect) < 500:
            continue
        x.append(i / 1000)
        y.append((sum(defect) / len(defect)) * 100)
        defect = []

    # smoothing
    # spl = UnivariateSpline(x, y, s=s)
    # xs = np.linspace(min(x), max(x), 1000)
    # plt.plot(xs, spl(xs))

    plt.plot(x, y)
    plt.xlabel('Parts in thousands')
    plt.ylabel('% defect parts')
    plt.ylim(0, 100)
    plt.title('Percent of defect parts produced')
    plt.show()
    plt.savefig("defect_parts.png")
    print(f"Percent of defect parts produced: {y[-1]}")

    # plot features and actions
    y1 = [[]] * 3
    y2 = [[]] * 6
    good_actions_x1, good_actions_y1, bad_actions_x1, bad_actions_y1 = [], [], [], []
    good_actions_x2, good_actions_y2, bad_actions_x2, bad_actions_y2 = [], [], [], []

    Ftr1 = simulation.objectList[8].featureHistory[:size]
    Ftr2 = simulation.objectList[9].featureHistory[:size]
    Ftr3 = simulation.objectList[10].featureHistory[:size]
    Ftr4 = simulation.objectList[11].featureHistory[:size]
    Ftr5 = simulation.objectList[12].featureHistory[:size]
    Ftr6 = simulation.objectList[13].featureHistory[:size]

    for ind, ((machine, action), reward) in enumerate(zip(simulation.all_actions[:size], simulation.all_rewards[:size])):
        if machine == 1:
            # features
            y = [Ftr1[ind], Ftr4[ind], Ftr5[ind]]
            for i, ftr in enumerate(y):
                y1[i] = y1[i] + [ftr]
            # normalize
            y1[0][-1] = (y1[0][-1] - observation_extremes[0][0]) / (
                observation_extremes[0][1] - observation_extremes[0][0])
            y1[1][-1] = (y1[1][-1] - observation_extremes[3][0]) / (
                observation_extremes[3][1] - observation_extremes[3][0])
            y1[2][-1] = (y1[2][-1] - observation_extremes[4][0]) / (
                observation_extremes[4][1] - observation_extremes[4][0])

            # actions
            if reward > 0:
                good_actions_x1.append(len(y1[0]))
                good_actions_y1.append(action)
            else:
                bad_actions_x1.append(len(y1[0]))
                bad_actions_y1.append(action)
        if machine == 3:
            # features
            y = [Ftr1[ind], Ftr2[ind], Ftr3[ind], Ftr4[ind], Ftr5[ind], Ftr6[ind]]
            for i, ftr in enumerate(y):
                y2[i] = y2[i] + [ftr]
            # normalize
            for i in range(6):
                y2[i][-1] = (y2[i][-1] - observation_extremes[i][0]) / (
                    observation_extremes[i][1] - observation_extremes[i][0])

            # actions
            if reward > 0:
                good_actions_x2.append(len(y2[0]))
                good_actions_y2.append(action)
            else:
                bad_actions_x2.append(len(y2[0]))
                bad_actions_y2.append(action)

    x1 = range(len(y1[0]))
    x2 = range(len(y2[0]))

    fig, axs = plt.subplots(2, 1)

    # Machine 1
    if m_one:
        xs = np.linspace(min(x1), max(x1), 1000)
        spl = UnivariateSpline(x1, y1[0], s=s)
        axs[0].plot(xs, spl(xs), label='Feature 1')
        spl = UnivariateSpline(x1, y1[1], s=s)
        axs[0].plot(xs, spl(xs), color='grey', alpha=0.3, label='Feature 4')
        spl = UnivariateSpline(x1, y1[2], s=s)
        axs[0].plot(xs, spl(xs), color='grey', alpha=0.3, label='Feature 5')
        axs[0].scatter(good_actions_x1, good_actions_y1, color='green', label='Good Action')
        axs[0].scatter(bad_actions_x1, bad_actions_y1, color='red', label='Bad Action')
        axs[0].set_title("Machine 1")
        axs[0].legend(loc='upper left', bbox_to_anchor=(1, 1))

    # Machine 3
    xs = np.linspace(min(x2), max(x2), 1000)
    for i in range(6):
        spl = UnivariateSpline(x2, y2[i], s=s)
        if i >= 3:  # Apply grey color and alpha for the last three features
            axs[1].plot(xs, spl(xs), color='grey', alpha=0.3, label=f'Feature {i + 1}')
        else:
            axs[1].plot(xs, spl(xs), label=f'Feature {i + 1}')
    axs[1].scatter(good_actions_x2, good_actions_y2, color='green', label='Good Action')
    axs[1].scatter(bad_actions_x2, bad_actions_y2, color='red', label='Bad Action')
    axs[1].set_title("Machine 3")
    axs[1].legend(loc='upper left', bbox_to_anchor=(1, 1))

    fig.suptitle('Features and Actions')
    axs[0].set_ylim(-0.1, 1.1)
    axs[1].set_ylim(-0.1, 1.1)
    plt.tight_layout()
    plt.show()
    plt.savefig("features_actions.png")

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
    plt.savefig("prob_differences.png")
    print(f"Difference of probabilities: {y[-1]}")


if __name__ == "__main__":
    # Simulation
    observation_extremes = [(3400, 4900), (0, 2100), (11000, 50000), (1, 9), (50000, 57000), (0.2, 0.8)]
    simu = ExampleEnv(observations=observation_extremes, maxSteps=20000, updates=300)
    simu.reset()

    plot(simu, m_one=False, size=30)
