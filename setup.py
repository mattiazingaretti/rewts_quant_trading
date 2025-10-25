"""
Setup configuration for ReWTS Quant Trading
"""

from setuptools import setup, find_packages

setup(
    name="rewts_quant_trading",
    version="0.1.0",
    description="ReWTSE-LLM-RL Hybrid Quantitative Trading System",
    author="Marco Zingaretti",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # Core dependencies
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "torch>=2.0.0",
        "google-generativeai>=0.3.0",
        "yfinance>=0.2.0",
        "ta>=0.10.0",
        "scipy>=1.7.0",
        "cvxpy>=1.2.0",
        "matplotlib>=3.4.0",
        "seaborn>=0.11.0",
        "pyyaml>=6.0",
        "tqdm>=4.62.0",
        "alpaca-py>=0.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
