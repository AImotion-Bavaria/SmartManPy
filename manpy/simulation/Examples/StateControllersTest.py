from manpy.simulation.imports import RandomNumberGenerator, SimpleStateController, ContinuosNormalDistribution
import numpy as np
import matplotlib.pyplot as plt


def generate_n_values(state_controller, num_values, reset_every_nth_step=None):
    values = list()

    for i in range(num_values):
        distribution = state_controller.get_and_update()
        rng_feature = RandomNumberGenerator(object(), distribution.get("Feature"))
        value = rng_feature.generateNumber()
        values.append(value)

        if reset_every_nth_step and i % reset_every_nth_step == 0:
            state_controller.reset()

    values = np.array(values)
    return values


if __name__ == "__main__":
    # TODO test Weibull
    feature_cycle_time = 1.
    dists = [{"Time": {"Fixed": {"mean": feature_cycle_time}}, "Feature": {"Normal": {"mean": 1, "stdev": 2}}},
             {"Time": {"Fixed": {"mean": feature_cycle_time}}, "Feature": {"Normal": {"mean": 100, "stdev": 2}}}]
    boundaries = {(0, 25): 0, (25, None): 1}
    # controller = SimpleStateController(states=dists, boundaries=boundaries, wear_per_step=1.0, reset_amount=None)

    mean_change_per_step = 0.02

    controller = ContinuosNormalDistribution(wear_per_step=0.7,
                                             break_point=None,
                                             mean_change_per_step=mean_change_per_step,
                                             initial_mean=2.0,
                                             std=2.0,
                                             defect_mean=7.0,
                                             defect_std=3.0
                                             )

    features = generate_n_values(controller, 250, 100)

    defect_controller = ContinuosNormalDistribution(wear_per_step=0.7,
                                                    mean_change_per_step=mean_change_per_step,
                                                    initial_mean=7.0,
                                                    std=2.0,
                                                    break_point=None,
                                                    defect_mean=None,
                                                    defect_std=None
                                                    )
    defect_features = generate_n_values(defect_controller, 250, 100)

    plt.plot(features, color='blue', label='OK')
    plt.plot(defect_features, color='red', label='defect')
    plt.ylabel("Value")
    plt.xlabel("Step")
    plt.legend()
    plt.title(f"Mean Change: {mean_change_per_step}")
    plt.show()



