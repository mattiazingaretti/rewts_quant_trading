"""
DDQN Agent per trading
Implementazione basata sul paper benchmark [Theate & Ernst 2021]
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import deque
import random

class DQN(nn.Module):
    """Deep Q-Network"""

    def __init__(self, input_dim, output_dim, hidden_dims=[128, 64]):
        super(DQN, self).__init__()

        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, output_dim))

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)

class ReplayBuffer:
    """Experience Replay Buffer"""

    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            torch.FloatTensor(states),
            torch.LongTensor(actions),
            torch.FloatTensor(rewards),
            torch.FloatTensor(next_states),
            torch.FloatTensor(dones)
        )

    def __len__(self):
        return len(self.buffer)

class DDQNAgent:
    """Double DQN Agent"""

    def __init__(self, state_dim, action_dim, config):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.config = config

        # Hyperparameters (OPTIMIZED - Phase 1)
        self.gamma = config.get('gamma', 0.995)  # Optimized: 0.995 (was 0.99)
        self.epsilon = config.get('epsilon_start', 1.0)
        self.epsilon_min = config.get('epsilon_min', 0.05)  # Optimized: 0.05 (was 0.01)
        self.epsilon_decay = config.get('epsilon_decay', 0.998)  # Optimized: 0.998 (was 0.995)
        self.learning_rate = config.get('learning_rate', 5e-4)  # Optimized: 5e-4 (was 1e-3)
        self.batch_size = config.get('batch_size', 128)  # Optimized: 128 (was 64)
        self.target_update_freq = config.get('target_update_freq', 20)  # Optimized: 20 (was 10)

        # Networks
        hidden_dims = config.get('hidden_dims', [256, 256, 128])  # Optimized: [256, 256, 128] (was [128, 64])
        self.policy_net = DQN(state_dim, action_dim, hidden_dims)
        self.target_net = DQN(state_dim, action_dim, hidden_dims)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        # Optimizer
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=self.learning_rate)

        # Replay buffer
        buffer_size = config.get('buffer_size', 50000)  # Optimized: 50000 (was 10000)
        self.replay_buffer = ReplayBuffer(buffer_size)

        # Training state
        self.steps_done = 0
        self.episode_count = 0

    def select_action(self, state, explore=True):
        """ε-greedy action selection"""

        if explore and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)

        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.policy_net(state_tensor)
            return q_values.argmax().item()

    def train_step(self):
        """Single training step usando experience replay"""

        if len(self.replay_buffer) < self.batch_size:
            return None

        # Sample batch
        states, actions, rewards, next_states, dones = self.replay_buffer.sample(self.batch_size)

        # Compute Q(s_t, a)
        q_values = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        # Compute V(s_{t+1}) usando Double DQN
        with torch.no_grad():
            # Azione selezionata dalla policy net
            next_actions = self.policy_net(next_states).argmax(1)
            # Q-value dalla target net
            next_q_values = self.target_net(next_states).gather(1, next_actions.unsqueeze(1)).squeeze(1)
            target_q_values = rewards + self.gamma * next_q_values * (1 - dones)

        # Loss
        loss = nn.MSELoss()(q_values, target_q_values)

        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()

        self.steps_done += 1

        # Update target network
        if self.steps_done % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

        return loss.item()

    def update_epsilon(self):
        """Decay epsilon"""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def save(self, path):
        """Save model"""
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'target_net': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'steps_done': self.steps_done
        }, path)

    def load(self, path):
        """Load model"""
        checkpoint = torch.load(path)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.target_net.load_state_dict(checkpoint['target_net'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint['epsilon']
        self.steps_done = checkpoint['steps_done']
