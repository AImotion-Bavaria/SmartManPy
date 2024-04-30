from abc import ABC, abstractmethod
import gymnasium as gym
from manpy.simulation.core.Globals import runSimulation, resetSimulation, G
from tqdm import tqdm
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
from torch.optim.lr_scheduler import StepLR


class PolicyNetwork(nn.Module):
    def __init__(self, obs_space_dims):
        super(PolicyNetwork, self).__init__()
        self.dense1 = nn.Linear(obs_space_dims, 128)
        self.dropout1 = nn.Dropout(0.3)
        self.dense2 = nn.Linear(128, 1024)
        self.dropout2 = nn.Dropout(0.3)
        self.dense3 = nn.Linear(1024, 512)
        self.dropout3 = nn.Dropout(0.3)
        self.dense4 = nn.Linear(512, 2)

    def forward(self, x):
        x = F.relu(self.dense1(x))
        x = self.dropout1(x)
        x = F.relu(self.dense2(x))
        x = self.dropout2(x)
        x = F.relu(self.dense3(x))
        x = self.dropout3(x)
        return torch.softmax(self.dense4(x), dim=-1)


class Reinforce:
    def __init__(self, policy_network, learning_rate=1e-4, step_size=100, gamma=0.1):
        self.policy_network = policy_network
        self.optimizer = optim.Adam(policy_network.parameters(), lr=learning_rate)
        self.scheduler = StepLR(self.optimizer, step_size=step_size, gamma=gamma)

    def sample_action(self, state):
        state = torch.FloatTensor(state)
        action_probs = self.policy_network(state)
        action = np.random.choice([0, 1], p=action_probs.detach().numpy())

        return action, action_probs

    def update(self, probs, rewards):
        # Calculate loss
        loss = 0
        for p, R in zip(probs, rewards):
            loss += -torch.log(p) * R

        # Backpropagation
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # Decay learning rate
        self.scheduler.step()


class QualityEnv(gym.Env):

    def __init__(self, observations: int, maxSimTime=100, maxSteps=None, updates=1, normalize=None):
        self.observations = observations
        self.steps = 0
        self.normalize = normalize
        self.probs, self.rewards, self.all_rewards, self.all_actions, self.all_probs = [], [], [], [], []

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
        action, probs = self.agent.sample_action(observation)
        prob = probs[action]
        reward = self.rew(action)

        # add reward
        self.probs.append(prob)
        self.rewards.append(reward)
        self.all_rewards.append(reward)
        self.all_actions.append((int(o.id[1:]), action))
        self.all_probs.append(probs.detach().numpy())

        # update
        if self.steps % self.updates == 0:
            # normalize between -1 and 1
            if self.normalize:
                self.rewards = [(r - self.normalize[0]) / (self.normalize[1] - self.normalize[0]) * 2 - 1 for r in self.rewards]

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
