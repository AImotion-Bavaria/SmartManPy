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
    def __init__(self,
                 policy_network,
                 learning_rate=1e-4):
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
    """
    Simple RL Env for quality predictions. Is assigned instead of a quality control function.

    :param observation_extremes: List of tuples that contain the observation extremes for each observation.
    :param policy_network: torch NN that is used for predicting the policy.
    :param maxSimTime: Used to correctly display the progress bar.
    :param maxSteps: Number of maximum training steps. Training ends after maxSteps is reached.
    :param steps_between_updates: Determines how many steps are between each update, essentially the batch size.
    :param save_policy_network: Saves the policy NN's state dict if True.
    """

    def __init__(self,
                 observation_extremes: List,
                 policy_network: nn.Module,
                 maxSimTime=100,
                 maxSteps=None,
                 steps_between_updates=5,
                 save_policy_network=False):

        self.observation_extremes = observation_extremes
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
        self.steps_between_updates = steps_between_updates

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
        return observations
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
        """
        this function is called when the agent should make an action and replaces a quality control function.
        """
        self.steps += 1
        self.pbar.update(1)
        if self.agent.all_losses:
            self.pbar.set_postfix({'loss': mean(list(map(lambda x: abs(x), self.agent.all_losses[-10:]))),
                                   'reward': mean(self.all_rewards[-self.steps_between_updates * 10:])})

        # update machine
        self.machine = o

        # observe, take action, calculate reward
        observation = self.obs()
        # normalize observation
        for i, ob in enumerate(observation):
            if ob:
                observation[i] = (ob - self.observation_extremes[i][0]) / (
                        self.observation_extremes[i][1] - self.observation_extremes[i][0])
            else:
                observation[i] = 0
        observation = observation.astype(np.float32)
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
        if self.steps % self.steps_between_updates == 0:
            self.agent.update(self.probs, self.rewards)
            self.probs, self.rewards = [], []

        # check maxSteps
        if self.maxSteps:
            if self.steps >= self.maxSteps:
                print("close")
                self.close()

        # take action, 1 == True == discard the part
        if action == 1:
            return True
        else:
            return False

    def close(self):
        """
        close the simulation and potentially save the policy network.
        """
        self.objectList[0].endSimulation()
        self.pbar.close()

        if self.save_policy_network:
            current_date_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"QualityNetwork_{current_date_time}.pt"
            torch.save(self.policy_network.state_dict(), filename)
