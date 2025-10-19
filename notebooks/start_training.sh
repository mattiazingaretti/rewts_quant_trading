#!/bin/bash

# Script per avviare il training notebook
# Uso: ./start_training.sh

echo "======================================================"
echo "  ReWTSE-LLM-RL Training Notebook Launcher"
echo "======================================================"
echo ""

# Controlla se siamo nella directory notebooks
if [ $(basename "$PWD") = "notebooks" ]; then
    cd ..
fi

PROJECT_ROOT="$PWD"
echo "Project root: $PROJECT_ROOT"
echo ""

# Verifica virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠ Warning: No virtual environment detected"
    echo ""
    echo "Activate your virtual environment first:"
    echo "  source venv_rewts_llm/bin/activate"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Virtual environment active: $VIRTUAL_ENV"
fi

# Esegui check setup
echo ""
echo "Running setup verification..."
echo ""

python notebooks/check_setup.py

CHECK_STATUS=$?

if [ $CHECK_STATUS -ne 0 ]; then
    echo ""
    read -p "Setup check failed. Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "======================================================"
echo "Starting Jupyter Notebook..."
echo "======================================================"
echo ""
echo "The notebook will open in your browser."
echo "Press Ctrl+C to stop the server when done."
echo ""

# Avvia Jupyter
cd notebooks
jupyter notebook train_rewts_llm_rl.ipynb
