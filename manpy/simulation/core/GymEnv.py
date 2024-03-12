from abc import ABC, abstractmethod
import gymnasium as gym
from gymnasium import spaces
from manpy.simulation.core.Globals import runSimulation, resetSimulation
import torch
import torch.nn as nn
import numpy as np
from torch.distributions import Bernoulli


class Policy_Network(nn.Module):
    def __init__(self, obs_space_dims: int, action_space_dims: int):
        super().__init__()

        hidden_space1 = 16
        hidden_space2 = 32

        self.hidden_layer = nn.Sequential(
            nn.Linear(obs_space_dims, hidden_space1),
            nn.Tanh(),
            nn.Linear(hidden_space1, hidden_space2),
            nn.Tanh(),
        )

        self.output_layer = nn.Sequential(
            nn.Linear(hidden_space2, action_space_dims),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        hidden_features = self.hidden_layer(x.float())
        action_probs = self.output_layer(hidden_features)

        return action_probs

class Reinforce:
    def __init__(self, obs_space_dims: int, action_space_dims: int):

        # Hyperparameters
        self.learning_rate = 1e-4
        self.gamma = 0.99
        self.eps = 1e-6

        self.probs = []
        self.rewards = []

        self.net = Policy_Network(obs_space_dims, action_space_dims)
        self.optimizer = torch.optim.AdamW(self.net.parameters(), lr=self.learning_rate)

    def sample_action(self, state: np.ndarray) -> float:
        """Returns an action, conditioned on the policy and observation.

        Args:
            state: Observation from the environment

        Returns:
            action: Action to be performed
        """
        state = torch.tensor(np.array([state]))
        action_probs = self.net(state)

        # create a normal distribution from the predicted
        # mean and standard deviation and sample an action
        distrib = Bernoulli(action_probs)
        action = distrib.sample().item()

        prob = distrib.log_prob(torch.tensor(action))
        self.probs.append(prob.item())

        return action

    def update(self):
        """Updates the policy network's weights."""
        running_g = 0
        gs = []

        # Discounted return (backwards) - [::-1] will return an array in reverse
        for R in self.rewards[::-1]:
            running_g = R + self.gamma * running_g
            gs.insert(0, running_g)

        deltas = torch.tensor(gs, requires_grad=True)

        loss = 0
        # Multiply log probabilities by rewards and deltas
        for log_prob, delta in zip(self.probs, deltas):
            loss += log_prob * delta  # No need to multiply by -1 as we're maximizing

        # Negative because we're performing gradient ascent
        loss = -loss.mean()

        # Update the policy network
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # Empty / zero out all episode-centric/related variables
        self.probs = []
        self.rewards = []


class QualityEnv(gym.Env):

    def __init__(self, machine: str, observations: int, maxSimTime=100, maxSteps=None, updates=None):
        self.observation_space = spaces.Box(low=float('-inf'), high=float('inf'), shape=(observations,))
        self.action_space = spaces.Discrete(2)

        self.steps = 0
        self.all_rewards = []

        self.maxSimTime = maxSimTime
        self.maxSteps = maxSteps
        self.updates = updates

        # setup agent
        self.agent = Reinforce(observations, 1)

        # setup machine
        objectList = self.prepare()
        for o in objectList:
            if machine == o.id:
                self.machine = o
                break

    @abstractmethod
    def prepare(self):
        # initialize objects and routing
        # return objectList
        pass

    @abstractmethod
    def obs(self):
        # return observation
        pass

    @abstractmethod
    def rew(self, action):
        # calculate and return reward
        pass


    def reset(self):
        super().reset()

        resetSimulation()
        self.objectList = self.prepare()
        runSimulation(self.objectList, self.maxSimTime)

    def step(self, o):
        self.steps += 1
        print("Step: ", self.steps)

        # update machine
        self.machine = o

        # observe, take action, calculate reward
        observation = self.obs()
        action = self.agent.sample_action(observation)
        reward = self.rew(action)

        # add reward
        self.all_rewards.append(reward)
        self.agent.rewards.append(reward)

        # update
        if self.updates:
            if self.steps % self.updates == 0:
                self.agent.update()

        # check maxSteps
        if self.maxSteps:
            if self.steps >= self.maxSteps:
                print("close")
                self.close()

        # take action
        if action == 1:
            return True
        else:
            return False

    def close(self):
        self.objectList[0].endSimulation()
