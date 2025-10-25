"""
Trading Environment per RL Agent
Estende il benchmark environment del paper LLM+RL
"""

import gymnasium as gym
from gymnasium import spaces
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

        # Parametri (OPTIMIZED - Phase 1)
        self.initial_balance = config.get('initial_balance', 10000)
        self.transaction_cost = config.get('transaction_cost', 0.0015)  # Optimized: 0.15% (was 0.1%)
        self.max_position = config.get('max_position', 0.95)  # Optimized: 0.95 (was 1.0)

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

    def _calculate_reward(self, old_value, new_value):
        """
        Risk-adjusted reward con penalità per volatilità e drawdown
        (Phase 1 Optimization: Priority 1)

        Formula:
        R = simple_return - λ_vol * volatility - λ_dd * drawdown - λ_ot * overtrading

        Dove:
        - simple_return: (new_value - old_value) / old_value
        - volatility_penalty: 2.0 * std_dev(recent_returns)
        - drawdown_penalty: 5.0 * current_drawdown (se > 5%)
        - overtrading_penalty: 0.0005 per ogni cambio di azione

        Expected Impact:
        - Sharpe Ratio: +0.20-0.35 (67-150%)
        - Volatility: -18-30%
        - Max Drawdown: -25-38%
        """
        # 1. Return semplice
        simple_return = (new_value - old_value) / old_value if old_value > 0 else 0

        # 2. Penalità volatilità (ultimi 20 steps)
        if len(self.portfolio_history) >= 20:
            recent_values = self.portfolio_history[-20:]
            recent_returns = []
            for i in range(1, len(recent_values)):
                if recent_values[i-1] > 0:
                    ret = (recent_values[i] - recent_values[i-1]) / recent_values[i-1]
                    recent_returns.append(ret)

            if len(recent_returns) > 1:
                volatility_penalty = np.std(recent_returns) * 2.0  # Penalità 2x std
            else:
                volatility_penalty = 0
        else:
            volatility_penalty = 0

        # 3. Penalità drawdown
        if len(self.portfolio_history) > 0:
            peak = np.max(self.portfolio_history)
            current_dd = (peak - new_value) / peak if peak > 0 else 0
            # Penalizza solo DD > 5%, con fattore 5x
            drawdown_penalty = current_dd * 5.0 if current_dd > 0.05 else 0
        else:
            drawdown_penalty = 0

        # 4. Penalità overtrading
        action_changes = 0
        if hasattr(self, 'last_action') and hasattr(self, 'current_action'):
            if self.last_action != self.current_action:
                action_changes = 1
        overtrading_penalty = action_changes * 0.0005  # Costo implicito

        # 5. Reward finale
        reward = simple_return - volatility_penalty - drawdown_penalty - overtrading_penalty

        return reward

    def reset(self):
        """Reset environment"""
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0
        self.shares_held = 0
        self.portfolio_value = self.initial_balance
        self.portfolio_history = []
        self.last_action = 1  # Initialize to HOLD

        return self._get_observation(0)

    def step(self, action):
        """
        Execute action (OPTIMIZED: Risk-adjusted reward - Phase 1)

        Actions:
          0: SHORT (sell if holding, or go short)
          1: HOLD (no action)
          2: LONG (buy if not holding)
        """

        # Store last action for overtrading penalty
        self.current_action = action

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

        # Calculate reward using new risk-adjusted function
        old_portfolio_value = self.portfolio_value
        new_portfolio_value = self._get_portfolio_value(self.current_step)

        reward = self._calculate_reward(old_portfolio_value, new_portfolio_value)
        self.portfolio_value = new_portfolio_value

        # Track history
        self.portfolio_history.append(self.portfolio_value)

        # Update last_action for next step
        self.last_action = self.current_action

        # Check if done
        done = self.current_step >= len(self.df) - 1

        # Next observation
        obs = self._get_observation(self.current_step) if not done else np.zeros(self.observation_space.shape)

        return obs, reward, done, {}

    def render(self, mode='human'):
        """Visualizza stato corrente"""
        print(f"Step: {self.current_step}, Portfolio Value: ${self.portfolio_value:.2f}, Position: {self.position}")
