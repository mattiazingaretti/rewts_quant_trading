"""
Trading Environment per RL Agent
Estende il benchmark environment del paper LLM+RL
"""

import gym
from gym import spaces
import numpy as np
import pandas as pd

class TradingEnv(gym.Env):
    """
    Custom Trading Environment per DDQN

    Observation Space: price features + technical indicators + LLM signal (τ)
    Action Space: [0: SHORT, 1: HOLD, 2: LONG]
    Reward: Differenza nei rendimenti del portafoglio
    """

    metadata = {'render.modes': ['human']}

    def __init__(self, df, llm_strategies, config):
        super(TradingEnv, self).__init__()

        self.df = df.reset_index(drop=True)
        self.llm_strategies = llm_strategies  # Pre-computed LLM strategies
        self.config = config

        # Parametri
        self.initial_balance = config.get('initial_balance', 10000)
        self.transaction_cost = config.get('transaction_cost', 0.001)  # 0.1%
        self.max_position = config.get('max_position', 1.0)  # No leverage

        # State
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0  # -1: SHORT, 0: HOLD, 1: LONG
        self.shares_held = 0
        self.portfolio_value = self.initial_balance

        # Observation space
        # Features: Close, Volume, HV, technical indicators, LLM signal τ
        num_features = len(self._get_observation(0))
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf,
            shape=(num_features,),
            dtype=np.float32
        )

        # Action space: [SHORT, HOLD, LONG]
        self.action_space = spaces.Discrete(3)

        # Tracking
        self.portfolio_history = []

    def _get_observation(self, step):
        """Costruisce observation vector includendo LLM signal τ"""

        row = self.df.iloc[step]

        # Price features (normalized)
        close = row.get('Close', 0)
        volume = row.get('Volume', 0)
        hv = row.get('HV_Close', 0)

        # Technical indicators
        sma_20 = row.get('SMA_20', close)
        sma_50 = row.get('SMA_50', close)
        sma_200 = row.get('SMA_200', close)
        rsi = row.get('RSI', 50)
        macd = row.get('MACD', 0)

        # LLM signal τ = dir(πg) * str(πg)
        # Ottieni strategia LLM corrente (mensile)
        month_idx = step // 20  # Strategia mensile (20 trading days)
        if month_idx < len(self.llm_strategies):
            strategy = self.llm_strategies[month_idx]
            direction = 2 * strategy.direction - 1  # {0,1} -> {-1,1}
            strength = strategy.strength
            tau = direction * strength
        else:
            tau = 0.0

        # Portfolio state
        portfolio_value = self._get_portfolio_value(step)

        # Normalizzazione
        obs = np.array([
            close / 100.0 if close > 0 else 0,  # Normalize price
            volume / 1e6 if volume > 0 else 0,
            hv * 100 if hv > 0 else 0,
            sma_20 / close if close > 0 else 1.0,
            sma_50 / close if close > 0 else 1.0,
            sma_200 / close if close > 0 else 1.0,
            rsi / 100.0 if rsi > 0 else 0.5,
            macd if np.isfinite(macd) else 0,
            tau,  # LLM guidance signal
            portfolio_value / self.initial_balance,
            self.position  # Current position
        ], dtype=np.float32)

        # Replace any NaN or Inf values
        obs = np.nan_to_num(obs, nan=0.0, posinf=1.0, neginf=-1.0)

        return obs

    def _get_portfolio_value(self, step):
        """Calcola portfolio value corrente"""
        current_price = self.df.iloc[step].get('Close', 0)
        return self.balance + self.shares_held * current_price

    def reset(self):
        """Reset environment"""
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0
        self.shares_held = 0
        self.portfolio_value = self.initial_balance
        self.portfolio_history = []

        return self._get_observation(0)

    def step(self, action):
        """
        Execute action

        Actions:
          0: SHORT (sell if holding, or go short)
          1: HOLD (no action)
          2: LONG (buy if not holding)
        """

        current_price = self.df.iloc[self.current_step].get('Close', 0)

        if current_price <= 0:
            # Invalid price, skip action
            pass
        else:
            # Execute trade
            if action == 0:  # SHORT
                if self.position == 1:  # Close LONG position
                    revenue = self.shares_held * current_price * (1 - self.transaction_cost)
                    self.balance += revenue
                    self.shares_held = 0
                    self.position = 0

            elif action == 2:  # LONG
                if self.position == 0:  # Open LONG position
                    max_shares = self.balance / current_price
                    shares_to_buy = int(max_shares * self.max_position)
                    cost = shares_to_buy * current_price * (1 + self.transaction_cost)

                    if cost <= self.balance and shares_to_buy > 0:
                        self.shares_held += shares_to_buy
                        self.balance -= cost
                        self.position = 1

        # Move to next step
        self.current_step += 1

        # Calculate reward (portfolio value change)
        new_portfolio_value = self._get_portfolio_value(self.current_step)
        reward = (new_portfolio_value - self.portfolio_value) / self.portfolio_value if self.portfolio_value > 0 else 0
        self.portfolio_value = new_portfolio_value

        # Track history
        self.portfolio_history.append(self.portfolio_value)

        # Check if done
        done = self.current_step >= len(self.df) - 1

        # Next observation
        obs = self._get_observation(self.current_step) if not done else np.zeros(self.observation_space.shape)

        return obs, reward, done, {}

    def render(self, mode='human'):
        """Visualizza stato corrente"""
        print(f"Step: {self.current_step}, Portfolio Value: ${self.portfolio_value:.2f}, Position: {self.position}")
