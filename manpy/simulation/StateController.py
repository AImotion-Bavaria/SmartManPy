class StateController:
    """
    Abstract base class for all StateControllers. A StateController must provide a get_and_update() and reset() method.
    """

    def get_initial_state(self):
        raise NotImplementedError("Subclass must define 'get_initial_state' method.")

    def get_and_update(self):
        """
        Retrieves the current state first, then updates the internal state transition mechanism and then returns the
        retrieved state.
        :return: Current state
        """
        raise NotImplementedError("Subclass must define 'get_and_update' method.")

    def reset(self):
        """
        Resets the internal statistics of the controller. Should be called after something is repaired.
        :return: None
        """
        raise NotImplementedError("Subclass must define 'reset' method.")


class SimpleStateController(StateController):
    """
    Simple version of a StateController that sets states according to a certain amount of wear.

    :param states (list): A list containing the actual states
    :param boundaries (dict): A dict defining the boundaries for each state. Must contain pairs of (interval, state_index).
           Intervals are defined as a tuple: (lower, upper). The lower bound is included, upper bound is not included.
           Example: states = [state0, state1, state2]
           boundaries = {(0, 150): 0, (150, 300): 1, (300, None): 2}
    :param amount_per_step: A number that defines how much wear is added per step.
    :param reset_amount: When the account value reaches this amount, the StateController gets reset.
    """
    def __init__(self, states: list, boundaries: dict, amount_per_step, initial_state_index=0, reset_amount=None):

        self.states = states
        self.boundaries = boundaries
        self.amount_per_step = amount_per_step

        self.account = 0
        self.current_state_index = initial_state_index
        self.initial_state_index = initial_state_index
        self.reset_amount = reset_amount

    def get_initial_state(self):
        return self.states[self.initial_state_index]

    def get_and_update(self):
        output = self.states[self.current_state_index]

        self.account += self.amount_per_step

        if self.reset_amount is not None and self.account >= self.reset_amount:
            self.reset()
        else:
            previous_state_index = self.current_state_index
            self.current_state_index = self.__get_current_state()
            if previous_state_index is not self.current_state_index:
                print(f"Change state to index {self.current_state_index}")

        return output

    def reset(self):
        print(">>> Reset SimpleStateController <<<")
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

# TODO Graduelle veränderungen -> mehrere Verteilungen zusammenaddieren zb

class ContinuosStateController(StateController):
    # TODO eg change mean of normal dist

    def get_and_update(self):
        pass

    def reset(self):
        pass

    def get_initial_state(self):
        pass


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


