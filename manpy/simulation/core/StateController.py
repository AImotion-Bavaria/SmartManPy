import numpy as np
import random
from abc import ABC, abstractmethod

class StateController(ABC):
    """
    Abstract base class for all StateControllers. A StateController must provide a get_and_update() and reset() method.
    """

    @abstractmethod
    def get_initial_state(self):
        """
        :return: Initial state and label: (state, label (bool))
        """
        pass

    @abstractmethod
    def get_and_update(self):
        """
        Retrieves the current state first, then updates the internal state transition mechanism and then returns the
        retrieved state and a label for the state.

        :return: Current state and label: (state, label (bool))
        """
        pass

    @abstractmethod
    def reset(self):
        """
        Resets the internal statistics of the controller. Should be called after something is repaired.

        :return: None
        """
        pass


class SimpleStateController(StateController):
    """
    Simple version of a StateController that sets states according to a certain amount of wear.

    :param states (list): A list containing the actual states
    :param boundaries (dict): A dict defining the boundaries for each state. Must contain pairs of (interval, state_index).
           Intervals are defined as a tuple: (lower, upper). The lower bound is included, upper bound is not included.
           0 must be included.
           Example: states = [state0, state1, state2]
           boundaries = {(0, 150): 0, (150, 300): 1, (300, None): 2}
    :param wear_per_step: A number that defines how much wear is added per step. The account starts at 0.
    :param reset_amount: When the account value reaches this amount, the StateController gets reset.
    """
    def __init__(self,
                 states: list,
                 boundaries: dict,
                 wear_per_step,
                 labels=None,
                 initial_state_index=0,
                 reset_amount=None
                 ):

        self.states = states

        self.boundaries = boundaries
        self.wear_per_step = wear_per_step

        self.labels = labels

        self.account = 0
        self.current_state_index = initial_state_index
        self.initial_state_index = initial_state_index
        self.reset_amount = reset_amount

    def get_initial_state(self):
        if self.labels is not None:
            return self.states[self.initial_state_index], self.labels[self.initial_state_index]
        else:
            return self.states[self.initial_state_index], None

    def get_and_update(self):
        output = self.states[self.current_state_index]

        if self.labels is not None:
            label = self.labels[self.current_state_index]
        else:
            label = None

        self.account += self.wear_per_step

        if self.reset_amount is not None and self.account >= self.reset_amount:
            self.reset()
        else:
            previous_state_index = self.current_state_index
            self.current_state_index = self.__get_current_state()
            if previous_state_index is not self.current_state_index:
                # print(f"Change state to index {self.current_state_index}")
                pass

        return output, label

    def reset(self):
        self.account = 0
        self.current_state_index = self.initial_state_index

    def __get_current_state(self):
        res = []
        for (lower, upper) in self.boundaries.keys():

            if lower is None:
                if self.account < upper:
                    res.append(self.boundaries[(lower, upper)])
                continue

            if upper is None:
                if self.account >= lower:
                    res.append(self.boundaries[(lower, upper)])
                continue

            if lower <= self.account < upper:
                res.append(self.boundaries[(lower, upper)])

        if not len(res) == 1:
            raise AttributeError("The boundaries dictionary contains incorrect intervals (e.g. overlapping)")

        return res[0]


class ContinuousNormalDistribution(StateController):
    """
    Normal Distribution that changes its mean value with each step. Optionally, a defect can occur after a defined
    period. Provides label.

    :param wear_per_step: How much wear happens per step
    :param break_point: When this value of wear is reached, a defect happens. Will be ignored if None
    :param mean_change_per_step: Value that is added to the mean of the normal distribution in each step
    :param initial_mean: Initial mean value of the normal distribution
    :param std: STD of the normal distribution, does not change
    :param defect_mean: Mean value in the defect state
    :param defect_std: STD in the defect state
    """
    def __init__(self,
                 mean_change_per_step,
                 initial_mean,
                 std,
                 wear_per_step=0,
                 break_point=None,
                 defect_mean=None,
                 defect_std=None,
                 ):

        self.mean_change_per_step = mean_change_per_step

        self.initial_mean = initial_mean
        self.std = std

        self.account = 0

        self.current_mean = self.initial_mean

        self.wear_per_step = wear_per_step
        self.break_point = break_point
        self.defect_mean = defect_mean
        self.defect_std = defect_std

    def get_initial_state(self):
        return self.__get_distribution(self.initial_mean, self.std), False

    def get_and_update(self):
        # parameters are incremented before return
        if self.break_point is not None and self.account >= self.break_point:
            mean = self.defect_mean
            std = self.defect_std
            label = True
        else:
            self.current_mean += self.mean_change_per_step
            mean = self.current_mean
            std = self.std
            self.account += self.wear_per_step
            label = False

        return self.__get_distribution(mean, std), label

    def __get_distribution(self, mean, std):
        return {"Feature": {"Normal": {"mean": mean, "stdev": std}}}

    def reset(self):
        self.current_mean = self.initial_mean
        self.account = 0

# TODO kurtosis


class RandomDefectStateController(StateController):
    """
    Orchestrates multiple StateControllers. Using a Bernoulli-Distribution, it chooses either the
    ok or the defect distribution.

    :param failure_probability: Probability of failure for the Bernoulli-Distribution.
    :param ok_controller:
    :param defect_controllers: list of StateControllers. If a random failure occurs, one of them is
                                drawn with uniform distribution. Example: in case of defect, a value can be either
                                too high or too low
    """
    def __init__(self,
                 failure_probability,
                 ok_controller: StateController,
                 defect_controllers: list
                 ):

        self.failure_probability = failure_probability
        self.ok_controller = ok_controller
        self.defect_controllers = defect_controllers

    def get_initial_state(self):
        return self.ok_controller.get_initial_state()

    def get_and_update(self):
        defect = int(np.random.binomial(1, self.failure_probability))

        if defect == 1:
            defect_controller = random.choice(self.defect_controllers)
            dist, _ = defect_controller.get_and_update()
            label = True
        else:
            dist, y = self.ok_controller.get_and_update()
            # if the state controller returns <defect> (e.g. due to a reached break point) we need to keep this label!
            if y:
                label = True
            else:
                label = False

        return dist, label

    def reset(self):
        self.ok_controller.reset()
        for c in self.defect_controllers:
            c.reset()


if __name__ == '__main__':
    states = ["A", "B", "C"]
    boundaries = {(0, 150): 0, (150, 300): 1, (300, None): 2}

    sc = SimpleStateController(states, boundaries, 50)

    for i in range(3):
        print(sc.get_and_update())
    print("------------")
    for i in range(3):
        print(sc.get_and_update())

    print("------------")
    print(sc.get_and_update())

    sc.reset()
    print("------------")
    for i in range(3):
        print(sc.get_and_update())
    print("------------")
    for i in range(3):
        print(sc.get_and_update())

    print("------------")
    print(sc.get_and_update())


