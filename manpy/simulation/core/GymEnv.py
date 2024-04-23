from abc import ABC, abstractmethod
import gymnasium as gym
from gymnasium import spaces
from manpy.simulation.core.Globals import runSimulation, resetSimulation, G
from tqdm import tqdm
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np


class PolicyNetwork(nn.Module):
    def __init__(self, obs_space_dims):
        super(PolicyNetwork, self).__init__()
        self.dense1 = nn.Linear(obs_space_dims, 64)
        self.dense2 = nn.Linear(64, 32)
        self.dense3 = nn.Linear(32, 16)
        self.dense4 = nn.Linear(16, 2)

    def forward(self, x):
        x = F.relu(self.dense1(x))
        x = F.relu(self.dense2(x))
        x = F.relu(self.dense3(x))
        return F.softmax(self.dense4(x), dim=-1)


class Reinforce:
    def __init__(self, policy_network, learning_rate=0.001):
        self.policy_network = policy_network
        self.optimizer = optim.Adam(policy_network.parameters(), lr=learning_rate)

    def sample_action(self, state):
        state = torch.FloatTensor(state)
        action_probs = self.policy_network(state)
        action = np.random.choice([0, 1], p=action_probs.detach().numpy())
        return action, action_probs[action]

    def update(self, probs, rewards):
        # Calculate loss
        loss = 0
        for p, R in zip(probs, rewards):
            loss += -torch.log(p) * R

        # Backpropagation
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()


class QualityEnv(gym.Env):

    def __init__(self, observations: int, maxSimTime=100, maxSteps=None, updates=1):
        self.observations = observations
        self.steps = 0
        self.probs, self.rewards, self.all_rewards = [], [], []

        if maxSteps is None:
            self.maxSimTime = maxSimTime
            self.pbar = tqdm(total=maxSimTime, desc='Simulation Progress',
                             bar_format="\033[92m{l_bar}{bar:25}{r_bar}\033[0m")
        else:
            self.maxSimTime = float('inf')
            self.pbar = tqdm(total=maxSteps, desc='Simulation Progress',
                             bar_format="\033[92m{l_bar}{bar:25}{r_bar}\033[0m")
        self.maxSteps = maxSteps
        self.updates = updates

        # setup agent
        self.agent = Reinforce(PolicyNetwork(len(observations)))

        # setup machine
        self.objectList = self.prepare()


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
        self.pbar.n = 0

        super().reset()
        resetSimulation()

        self.objectList = self.prepare()
        runSimulation(self.objectList, self.maxSimTime)

    def step(self, o):
        self.steps += 1
        self.pbar.update(1)

        # update machine
        self.machine = o

        # observe, take action, calculate reward
        observation = self.obs()
        # normalize observation
        for i, ob in enumerate(observation):
            if ob:
                observation[i] = (ob - self.observations[i][0])/(self.observations[i][1]-self.observations[i][0])
            else:
                observation[i] = -1
        observation = observation.astype(np.float32)
        if self.steps % 1000 == 0:
            pass
        action, prob = self.agent.sample_action(observation)
        reward = self.rew(action)

        # add reward
        self.probs.append(prob)
        self.rewards.append(reward)
        self.all_rewards.append(reward)

        # update
        if self.steps % self.updates == 0:
            self.agent.update(self.probs, self.rewards)
            self.probs, self.rewards = [], []

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
        self.pbar.close()
