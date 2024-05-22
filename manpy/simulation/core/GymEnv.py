from abc import ABC, abstractmethod
from typing import List
import gymnasium as gym
from manpy.simulation.core.Globals import runSimulation, resetSimulation, G
from tqdm import tqdm
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from statistics import mean
from datetime import datetime


class PolicyNetwork(nn.Module):
    def __init__(self, obs_space_dims, dropout_p=0.0):
        super(PolicyNetwork, self).__init__()
        self.model = nn.Sequential(
            nn.Linear(obs_space_dims, 256),
            nn.ReLU(),
            nn.Dropout(dropout_p),

            nn.Linear(256, 1024),
            nn.ReLU(),
            nn.Dropout(dropout_p),

            nn.Linear(1024, 512),
            nn.ReLU(),
            nn.Dropout(dropout_p),

            nn.Linear(512, 2),
            nn.Softmax(dim=-1)
        )

    def forward(self, x):
        return self.model(x)


class Reinforce:
    def __init__(self, policy_network, learning_rate=1e-4):
        self.policy_network = policy_network
        self.optimizer = optim.Adam(policy_network.parameters(), lr=learning_rate)
        self.all_losses = []

    def sample_action(self, state):
        state = torch.FloatTensor(state)
        action_probs = self.policy_network(state)
        action = np.random.choice([0, 1], p=action_probs.detach().numpy())

        return action, action_probs

    def update(self, probs, rewards):
        # Calculate loss
        loss = []
        for p, R in zip(probs, rewards):
            loss.append(-torch.log(p) * R)
        mean_loss = torch.mean(torch.stack(loss))

        self.all_losses.append(mean_loss.item())

        # Backpropagation
        self.optimizer.zero_grad()
        mean_loss.backward()
        self.optimizer.step()

        self.optimizer.zero_grad()


class QualityEnv(gym.Env):

    def __init__(self, observations: List, policy_network: nn.Module,  maxSimTime=100, maxSteps=None, updates=5,
                 save_policy_network=False):
        self.observations = observations
        self.steps = 0
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

        self.policy_network = policy_network
        self.save_policy_network = save_policy_network
        # setup agent
        self.agent = Reinforce(policy_network)

        # setup machine
        self.objectList = self.prepare()


    @abstractmethod
    def prepare(self):
        """
        initialize objects and routing
        return objectList
        """
        pass

    @abstractmethod
    def obs(self):
        """
        return observation
        """
        pass

    @abstractmethod
    def rew(self, action):
        """
        calculate and return reward
        """
        pass

    def reset(self):
        """
        Resets and starts the simulation.
        """
        self.pbar.n = 0

        super().reset()
        resetSimulation()

        self.objectList = self.prepare()
        runSimulation(self.objectList, self.maxSimTime)

    def step(self, o):
        self.steps += 1
        self.pbar.update(1)
        if self.agent.all_losses:
            self.pbar.set_postfix({'loss': mean(list(map(lambda x: abs(x), self.agent.all_losses[-10:]))), 'reward': mean(self.all_rewards[-self.updates*10:])})

        # update machine
        self.machine = o

        # observe, take action, calculate reward
        observation = self.obs()
        # normalize observation
        for i, ob in enumerate(observation):
            if ob:
                observation[i] = (ob - self.observations[i][0])/(self.observations[i][1]-self.observations[i][0])
            else:
                observation[i] = 0
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

        if self.save_policy_network:
            current_date_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"QualityNetwork_{current_date_time}.pt"
            torch.save(self.policy_network.state_dict(), filename)
