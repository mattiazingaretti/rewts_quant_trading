#!/usr/bin/env python3
"""
Quick test script to verify the setup works before full training
This runs a minimal version of the training pipeline as a sanity check
"""

import os
import sys
import pandas as pd
import numpy as np

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

print("=" * 60)
print("Quick Test - Training Pipeline Verification")
print("=" * 60)

# Import utility functions
from src.utils.data_utils import load_market_data, load_news_data, filter_news_by_period

# 1. Test data loading
print("\n1. Testing data loading...")
try:
    # Use utility functions for robust loading
    market_df = load_market_data('AAPL')
    news_df = load_news_data('AAPL')

    print(f"   ✓ Market data loaded: {market_df.shape}")
    print(f"     Date range: {market_df.index.min()} to {market_df.index.max()}")

    print(f"   ✓ News data loaded: {news_df.shape}")
    print(f"     Date range: {news_df.index.min()} to {news_df.index.max()}")

except Exception as e:
    print(f"   ✗ Error loading data: {e}")
    sys.exit(1)

# 2. Test LLM imports
print("\n2. Testing LLM agent imports...")
try:
    from src.llm_agents.strategist_agent import StrategistAgent
    from src.llm_agents.analyst_agent import AnalystAgent
    print("   ✓ LLM agents imported successfully")
except Exception as e:
    print(f"   ✗ Error importing LLM agents: {e}")
    sys.exit(1)

# 3. Test RL imports
print("\n3. Testing RL agent imports...")
try:
    from src.rl_agents.trading_env import TradingEnv
    from src.rl_agents.ddqn_agent import DDQNAgent
    print("   ✓ RL agents imported successfully")
except Exception as e:
    print(f"   ✗ Error importing RL agents: {e}")
    sys.exit(1)

# 4. Test ensemble controller
print("\n4. Testing ensemble controller import...")
try:
    from src.hybrid_model.ensemble_controller import ReWTSEnsembleController
    print("   ✓ Ensemble controller imported successfully")
except Exception as e:
    print(f"   ✗ Error importing ensemble controller: {e}")
    sys.exit(1)

# 5. Test date filtering (the bug we just fixed)
print("\n5. Testing date filtering logic...")
try:
    period_data = market_df.iloc[0:20]

    # Use utility function for filtering
    period_news = filter_news_by_period(
        news_df,
        period_data.index[0],
        period_data.index[-1]
    )

    print(f"   ✓ Date filtering works correctly")
    print(f"     Period: {period_data.index[0]} to {period_data.index[-1]}")
    print(f"     News found: {len(period_news)}")

except Exception as e:
    print(f"   ✗ Error in date filtering: {e}")
    sys.exit(1)

# 6. Test environment creation
print("\n6. Testing trading environment creation...")
try:
    # Create dummy strategy
    class DummyStrategy:
        def __init__(self):
            self.direction = 1
            self.strength = 0.7

    chunk_df = market_df.iloc[:100].copy()
    dummy_strategies = [DummyStrategy() for _ in range(5)]

    config = {
        'initial_balance': 10000,
        'transaction_cost': 0.001,
        'max_position': 1.0
    }

    env = TradingEnv(chunk_df, dummy_strategies, config)

    # Test reset
    state = env.reset()
    print(f"   ✓ Environment created successfully")
    print(f"     State shape: {state.shape}")
    print(f"     Action space: {env.action_space}")

    # Test one step
    action = 1  # HOLD
    next_state, reward, done, info = env.step(action)
    print(f"   ✓ Environment step works")

except Exception as e:
    print(f"   ✗ Error creating environment: {e}")
    sys.exit(1)

# 7. Test API key (optional)
print("\n7. Checking API key...")
api_key = os.getenv('GEMINI_API_KEY')
if api_key:
    print(f"   ✓ GEMINI_API_KEY found ({len(api_key)} chars)")
else:
    print("   ⚠ GEMINI_API_KEY not set (you'll be prompted in the notebook)")

# 8. Test PyTorch
print("\n8. Testing PyTorch...")
try:
    import torch
    print(f"   ✓ PyTorch version: {torch.__version__}")
    if torch.cuda.is_available():
        print(f"   ✓ CUDA available: {torch.cuda.get_device_name(0)}")
    else:
        print("   ℹ No GPU (will use CPU)")
except Exception as e:
    print(f"   ✗ Error with PyTorch: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("✓ All tests passed! Ready to run the training notebook.")
print("=" * 60)

print("\nNext steps:")
print("1. Set GEMINI_API_KEY if not already set:")
print("   export GEMINI_API_KEY='your-key-here'")
print("\n2. Start the training notebook:")
print("   ./notebooks/start_training.sh")
print("   or")
print("   jupyter notebook notebooks/train_rewts_llm_rl.ipynb")
print("\n3. For a quick test, reduce these config values in the notebook:")
print("   - chunk_length: 200 (instead of 500)")
print("   - episodes_per_chunk: 10 (instead of 50)")
print("   - strategy_frequency: 10 (instead of 20)")
