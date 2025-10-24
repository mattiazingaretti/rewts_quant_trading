"""
ReWTSE Ensemble Controller
Integra chunk-based DDQN models con ottimizzazione QP dei pesi
"""

import numpy as np
from cvxopt import matrix, solvers
import torch
from typing import List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rl_agents.ddqn_agent import DDQNAgent

class ReWTSEnsembleController:
    """
    Controller per ReWTSE Ensemble di DDQN agents

    Implementa:
    - Training chunk-based di DDQN agents
    - Ottimizzazione QP dei pesi basata su look-back performance
    - Weighted ensemble prediction
    """

    def __init__(self, config):
        self.config = config

        # Chunk parameters (OPTIMIZED - Phase 1)
        self.chunk_length = config.get('chunk_length', 400)  # Optimized: 400 (was 2016)
        self.lookback_length = config.get('lookback_length', 200)  # Optimized: 200 (was 432)
        self.forecast_horizon = config.get('forecast_horizon', 1)  # 1 step ahead

        # Ensemble di DDQN agents (uno per chunk)
        self.chunk_models = []

        # Pesi correnti
        self.current_weights = None

        # Storia performance
        self.performance_history = []

    def train_chunk_model(self, chunk_id, env, num_episodes=100):
        """
        Addestra un DDQN agent su un chunk specifico

        Args:
            chunk_id: ID del chunk
            env: TradingEnv per il chunk
            num_episodes: Numero di episodi di training (OPTIMIZED: 100, was 50)

        Returns:
            Trained DDQNAgent
        """

        print(f"\n{'='*60}")
        print(f"Training Chunk {chunk_id}")
        print(f"{'='*60}")

        # Crea nuovo DDQN agent
        state_dim = env.observation_space.shape[0]
        action_dim = env.action_space.n

        agent = DDQNAgent(state_dim, action_dim, self.config)

        # Training loop
        episode_rewards = []

        for episode in range(num_episodes):
            state = env.reset()
            episode_reward = 0
            done = False

            while not done:
                # Select action
                action = agent.select_action(state, explore=True)

                # Execute action
                next_state, reward, done, _ = env.step(action)

                # Store transition
                agent.replay_buffer.push(state, action, reward, next_state, done)

                # Train
                loss = agent.train_step()

                # Update state
                state = next_state
                episode_reward += reward

            # Decay epsilon
            agent.update_epsilon()

            episode_rewards.append(episode_reward)

            if (episode + 1) % 10 == 0:
                avg_reward = np.mean(episode_rewards[-10:])
                print(f"Episode {episode+1}/{num_episodes}, Avg Reward: {avg_reward:.4f}, Epsilon: {agent.epsilon:.4f}")

        # Salva modello
        os.makedirs('models', exist_ok=True)
        model_path = f"models/chunk_{chunk_id}_ddqn.pt"
        agent.save(model_path)
        print(f"✓ Chunk {chunk_id} model saved to {model_path}")

        return agent

    def optimize_weights(self, lookback_data, lookback_returns):
        """
        Ottimizzazione QP per trovare pesi ottimali basati su look-back performance

        Risolve:
            min_w  Σ ||y_(k+1):(k+h) - M_h(X:k, y:k) * w||²
            s.t.   w >= 0
                   1^T * w = 1

        Args:
            lookback_data: Look-back observations
            lookback_returns: Actual returns nel look-back period

        Returns:
            Optimal weights array
        """

        num_models = len(self.chunk_models)
        lookback_len = len(lookback_data) - self.forecast_horizon

        if lookback_len <= 0 or num_models == 0:
            # Fallback: uniform weights
            return np.ones(num_models) / num_models if num_models > 0 else np.array([])

        # Costruisci forecast matrix M_h
        # Shape: (lookback_len, num_models)
        M_h_list = []

        for k in range(lookback_len):
            # Per ogni timestep nel look-back
            forecasts_k = []

            for model in self.chunk_models:
                # Previsione h-step del modello
                state_k = lookback_data[k]

                with torch.no_grad():
                    state_tensor = torch.FloatTensor(state_k).unsqueeze(0)
                    q_values = model.policy_net(state_tensor)

                    # Converti Q-values in expected return
                    # Usiamo il Q-value dell'azione ottimale come proxy
                    expected_return = q_values.max().item()

                forecasts_k.append(expected_return)

            M_h_list.append(forecasts_k)

        M_h = np.array(M_h_list)  # Shape: (lookback_len, num_models)

        # Target returns
        y_actual = np.array(lookback_returns[:lookback_len])

        try:
            # QP formulation
            # min 0.5 * w^T * P * w + q^T * w
            # s.t. G * w <= h (w >= 0)
            #      A * w = b  (sum(w) = 1)

            P = matrix(M_h.T @ M_h)
            q = matrix(-M_h.T @ y_actual)

            # Inequality constraints: w >= 0
            G = matrix(-np.eye(num_models))
            h = matrix(np.zeros(num_models))

            # Equality constraint: sum(w) = 1
            A = matrix(np.ones((1, num_models)))
            b = matrix(1.0)

            # Solve QP
            solvers.options['show_progress'] = False
            sol = solvers.qp(P, q, G, h, A, b)

            if sol['status'] == 'optimal':
                weights = np.array(sol['x']).flatten()
            else:
                print(f"Warning: QP solver failed with status {sol['status']}, using uniform weights")
                weights = np.ones(num_models) / num_models

        except Exception as e:
            print(f"Warning: QP optimization failed with error {e}, using uniform weights")
            weights = np.ones(num_models) / num_models

        return weights

    def predict_ensemble(self, state, weights=None):
        """
        Weighted ensemble prediction

        Args:
            state: Current observation
            weights: Model weights (if None, use self.current_weights)

        Returns:
            Ensemble action
        """

        if weights is None:
            weights = self.current_weights

        if weights is None or len(self.chunk_models) == 0:
            # Fallback: uniform weights or random action
            if len(self.chunk_models) > 0:
                weights = np.ones(len(self.chunk_models)) / len(self.chunk_models)
            else:
                return 1, np.array([0, 1, 0])  # HOLD action as fallback

        # Ottieni Q-values da ogni chunk model
        q_values_list = []

        for model in self.chunk_models:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0)
                q_values = model.policy_net(state_tensor).squeeze().numpy()
                q_values_list.append(q_values)

        # Weighted average di Q-values
        weighted_q_values = np.zeros_like(q_values_list[0])

        for i, q_vals in enumerate(q_values_list):
            weighted_q_values += weights[i] * q_vals

        # Seleziona azione con Q-value massimo
        action = np.argmax(weighted_q_values)

        return action, weighted_q_values
