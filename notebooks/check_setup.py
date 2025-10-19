#!/usr/bin/env python3
"""
Script di verifica setup per il training
Esegui questo script prima di avviare il notebook per verificare che tutto sia configurato correttamente
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Verifica l'ambiente Python"""
    print("=" * 60)
    print("1. Checking Python Environment")
    print("=" * 60)

    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")

    # Check if in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓ Virtual environment detected")
    else:
        print("⚠ Warning: Not in a virtual environment (recommended)")

    print()

def check_dependencies():
    """Verifica le dipendenze installate"""
    print("=" * 60)
    print("2. Checking Dependencies")
    print("=" * 60)

    required_packages = [
        'torch',
        'gym',
        'pandas',
        'numpy',
        'matplotlib',
        'seaborn',
        'yfinance',
        'cvxopt',
        'tqdm',
        'yaml',
        'google.generativeai',
        'stable_baselines3'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            if package == 'yaml':
                __import__('yaml')
            elif package == 'google.generativeai':
                __import__('google.generativeai')
            else:
                __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - NOT INSTALLED")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n⚠ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    else:
        print("\n✓ All dependencies installed")
        return True

def check_api_key():
    """Verifica l'API key di Gemini"""
    print("=" * 60)
    print("3. Checking API Configuration")
    print("=" * 60)

    api_key = os.getenv('GEMINI_API_KEY')

    if api_key:
        print(f"✓ GEMINI_API_KEY found in environment")
        print(f"  Key length: {len(api_key)} characters")
        print(f"  Key preview: {api_key[:8]}...{api_key[-4:]}")
        return True
    else:
        print("✗ GEMINI_API_KEY not found in environment")
        print("\nSet it with:")
        print("  export GEMINI_API_KEY='your-key-here'  # macOS/Linux")
        print("  set GEMINI_API_KEY=your-key-here       # Windows CMD")
        print("  $env:GEMINI_API_KEY='your-key-here'    # Windows PowerShell")
        print("\nOr the notebook will prompt you to enter it manually")
        return False

def check_data():
    """Verifica la presenza dei dati"""
    print("\n" + "=" * 60)
    print("4. Checking Data Files")
    print("=" * 60)

    # Check if we're in the right directory
    current_dir = Path.cwd()
    if current_dir.name == 'notebooks':
        project_root = current_dir.parent
    else:
        project_root = current_dir

    print(f"Project root: {project_root}")

    data_dir = project_root / 'data' / 'processed'

    if not data_dir.exists():
        print(f"✗ Data directory not found: {data_dir}")
        return False

    print(f"✓ Data directory found: {data_dir}")

    # Check for AAPL data
    required_files = [
        'AAPL_full_data.csv',
        'AAPL_news.csv'
    ]

    all_found = True
    for filename in required_files:
        filepath = data_dir / filename
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"✓ {filename} ({size_mb:.2f} MB)")
        else:
            print(f"✗ {filename} - NOT FOUND")
            all_found = False

    if not all_found:
        print("\n⚠ Some data files are missing")
        print("Run the preprocessing scripts first:")
        print("  python scripts/preprocess_data.py")
        return False

    return True

def check_directories():
    """Verifica e crea le directory necessarie"""
    print("\n" + "=" * 60)
    print("5. Checking Project Directories")
    print("=" * 60)

    # Check if we're in the right directory
    current_dir = Path.cwd()
    if current_dir.name == 'notebooks':
        project_root = current_dir.parent
    else:
        project_root = current_dir

    required_dirs = [
        'data/processed',
        'data/llm_strategies',
        'models',
        'results',
        'src/llm_agents',
        'src/rl_agents',
        'src/hybrid_model'
    ]

    all_found = True
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"✓ {dir_path}")
        else:
            print(f"⚠ {dir_path} - NOT FOUND (will be created)")
            all_found = False

    return all_found

def check_gpu():
    """Verifica disponibilità GPU"""
    print("\n" + "=" * 60)
    print("6. Checking GPU")
    print("=" * 60)

    try:
        import torch
        if torch.cuda.is_available():
            print(f"✓ CUDA available")
            print(f"  Device: {torch.cuda.get_device_name(0)}")
            print(f"  CUDA version: {torch.version.cuda}")
            print(f"  PyTorch version: {torch.__version__}")
            return True
        else:
            print("ℹ No GPU available (training will use CPU)")
            print("  This is fine but training will be slower")
            return False
    except ImportError:
        print("✗ PyTorch not installed")
        return False

def main():
    """Esegui tutti i controlli"""
    print("\n" + "█" * 60)
    print("  ReWTSE-LLM-RL Setup Verification")
    print("█" * 60 + "\n")

    results = []

    check_environment()
    results.append(("Dependencies", check_dependencies()))
    results.append(("API Key", check_api_key()))
    results.append(("Data Files", check_data()))
    results.append(("Directories", check_directories()))
    results.append(("GPU", check_gpu()))

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for name, status in results:
        if status:
            print(f"✓ {name}: OK")
        else:
            print(f"⚠ {name}: NEEDS ATTENTION")

    all_ok = all(status for _, status in results if _ not in ["GPU", "API Key"])

    print("\n" + "=" * 60)
    if all_ok:
        print("✓ Setup complete! You can run the training notebook.")
    else:
        print("⚠ Some issues need to be resolved before training.")
        print("See the details above.")
    print("=" * 60 + "\n")

    return all_ok

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
