import gymnasium as gym
from gymnasium import spaces
from manpy.simulation.core.Globals import runSimulation, resetSimulation

class QualityEnv(gym.Env):

    def __init__(self, machine=None, observations=0, maxSimTime=100, maxSteps=None):
        self.observation_space = spaces.Box(low=float('-inf'), high=float('inf'), shape=(observations,))
        self.action_space = spaces.Discrete(2)

        self.machine = machine
        self.maxSimTime = maxSimTime
        self.maxSteps = maxSteps
    def prepare(self):
        # initialize objects and routing
        return []

    def _action_discard(self, action):
        for o in self.objectList:
            if o.id == self.machine:
                m = o
                break

        if action == 1:
            m.removeEntity(self.m.Res.users[0])

    def reset(self):
        super().reset()

        resetSimulation()
        self.objectList = self.prepare()
        runSimulation(self.objectList, self.maxSimTime)

    def step(self, action):
        # define Quality Control here
        self._action_discard(action)

        observation = None
        reward = None
        info = None

        return observation, reward, False, False, info

    def close(self):
        self.objectList[0].endSimulation()
