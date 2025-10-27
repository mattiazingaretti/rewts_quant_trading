#!/usr/bin/env python3
"""
Test script per simulare l'esecuzione del notebook Colab in locale.
Questo NON testa l'integrazione con Colab, ma verifica che il codice funzioni.
"""

import sys
import os

def test_imports():
    """Test che tutti gli import necessari siano disponibili"""
    print("\n" + "="*60)
    print("TEST 1: Import Dependencies")
    print("="*60)

    required_imports = [
        ('torch', 'PyTorch'),
        ('pandas', 'Pandas'),
        ('numpy', 'NumPy'),
        ('tqdm', 'tqdm'),
        ('pickle', 'pickle (built-in)'),
        ('matplotlib.pyplot', 'Matplotlib'),
    ]

    missing = []
    for module, name in required_imports:
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - MISSING")
            missing.append(name)

    if missing:
        print(f"\n❌ Missing {len(missing)} dependencies: {', '.join(missing)}")
        print("   Install with: pip install -r requirements.txt")
        return False
    else:
        print(f"\n✅ All external dependencies available")
        return True

def test_project_modules():
    """Test che tutti i moduli del progetto esistano"""
    print("\n" + "="*60)
    print("TEST 2: Project Modules")
    print("="*60)

    # Add src to path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

    modules = [
        ('scripts.training.download_data', 'DataDownloader'),
        ('src.llm_agents.strategist_agent', 'StrategistAgent'),
        ('src.llm_agents.analyst_agent', 'AnalystAgent'),
        ('src.rl_agents.trading_env', 'TradingEnv'),
        ('src.hybrid_model.ensemble_controller', 'ReWTSEnsembleController'),
        ('src.utils.data_utils', 'load_market_data'),
        ('src.utils.strategy_cache', 'StrategyCache'),
        ('src.utils.rate_limiter', 'RateLimiter'),
    ]

    missing = []
    for module_path, class_name in modules:
        try:
            module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)
            print(f"  ✓ {module_path}.{class_name}")
        except (ImportError, AttributeError) as e:
            print(f"  ✗ {module_path}.{class_name} - {e}")
            missing.append(f"{module_path}.{class_name}")

    if missing:
        print(f"\n❌ Missing {len(missing)} project modules")
        return False
    else:
        print(f"\n✅ All project modules available")
        return True

def test_api_key():
    """Test che la API key sia configurata"""
    print("\n" + "="*60)
    print("TEST 3: API Key Configuration")
    print("="*60)

    api_key = os.getenv('GEMINI_API_KEY')

    if api_key:
        print(f"  ✓ GEMINI_API_KEY found (length: {len(api_key)})")
        print(f"\n✅ API key configured")
        return True
    else:
        print(f"  ✗ GEMINI_API_KEY not found")
        print(f"\n⚠️  Set with: export GEMINI_API_KEY='your_key'")
        return False

def test_data_structure():
    """Test che la struttura delle directory sia corretta"""
    print("\n" + "="*60)
    print("TEST 4: Directory Structure")
    print("="*60)

    required_dirs = [
        'data/processed',
        'data/llm_strategies',
        'models',
        'results/metrics',
        'results/visualizations',
    ]

    missing = []
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ⊘ {dir_path} (will be created)")
            os.makedirs(dir_path, exist_ok=True)

    print(f"\n✅ Directory structure ready")
    return True

def test_training_script():
    """Test che lo script di training sia eseguibile"""
    print("\n" + "="*60)
    print("TEST 5: Training Script")
    print("="*60)

    script_path = 'scripts/training/train_rewts_llm_rl.py'

    if os.path.exists(script_path):
        print(f"  ✓ {script_path} exists")

        # Check if executable
        if os.access(script_path, os.R_OK):
            print(f"  ✓ Script is readable")
            print(f"\n✅ Training script ready")
            print(f"\n  You can run it with:")
            print(f"    python {script_path}")
            return True
        else:
            print(f"  ✗ Script is not readable")
            return False
    else:
        print(f"  ✗ {script_path} not found")
        return False

def main():
    print("="*60)
    print("NOTEBOOK LOCAL TEST SUITE")
    print("="*60)
    print("\nThis tests if the notebook code can run locally.")
    print("It does NOT test Colab-specific features (Drive mount, etc.)")

    results = []

    # Run all tests
    results.append(("Dependencies", test_imports()))
    results.append(("Project Modules", test_project_modules()))
    results.append(("API Key", test_api_key()))
    results.append(("Directory Structure", test_data_structure()))
    results.append(("Training Script", test_training_script()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")

    all_passed = all(p for _, p in results)

    if all_passed:
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        print("\nYou can now:")
        print("  1. Test locally: python scripts/training/train_rewts_llm_rl.py")
        print("  2. Upload to Colab: notebooks/train_rewts_complete.ipynb")
        return 0
    else:
        print("\n" + "="*60)
        print("⚠️  SOME TESTS FAILED")
        print("="*60)
        print("\nFix the failing tests before running the notebook.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
