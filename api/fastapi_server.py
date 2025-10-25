"""
FastAPI server for backtesting - optimized for VM deployment
More cost-effective than Cloud Run for frequent usage
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import torch
from google.cloud import storage
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ReWTSE Backtesting API",
    description="API for running backtests on trained ReWTSE-LLM-RL models",
    version="1.0.0"
)

# Global state
models_loaded = False
ensemble_controller = None
GCS_BUCKET = os.getenv("GCS_BUCKET", "rewts-trading-data")


# Pydantic models
class BacktestRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol (e.g., AAPL)")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    initial_balance: float = Field(10000, description="Initial balance in USD")
    transaction_cost: float = Field(0.001, description="Transaction cost (0.1% = 0.001)")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "start_date": "2020-01-01",
                "end_date": "2020-12-31",
                "initial_balance": 10000,
                "transaction_cost": 0.001
            }
        }


class BacktestResponse(BaseModel):
    ticker: str
    start_date: str
    end_date: str
    sharpe_ratio: float
    max_drawdown: float
    cumulative_return: float
    total_trades: int
    win_rate: float
    profit_factor: float
    final_balance: float
    execution_time_seconds: float


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    gpu_available: bool
    timestamp: str


@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    global models_loaded, ensemble_controller

    logger.info("🚀 Starting FastAPI server...")
    logger.info(f"GCS Bucket: {GCS_BUCKET}")
    logger.info(f"GPU Available: {torch.cuda.is_available()}")

    try:
        # Download models from GCS
        logger.info("📦 Downloading models from GCS...")
        download_models_from_gcs()

        # Load ensemble controller
        logger.info("🔧 Loading ensemble controller...")
        ensemble_controller = load_ensemble_controller()

        models_loaded = True
        logger.info("✅ Models loaded successfully!")

    except Exception as e:
        logger.error(f"❌ Failed to load models: {e}")
        models_loaded = False


def download_models_from_gcs():
    """Download trained models from Google Cloud Storage"""
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET)

    # Create local models directory
    os.makedirs("/tmp/models", exist_ok=True)

    # List all model files
    blobs = bucket.list_blobs(prefix="models/")

    for blob in blobs:
        if blob.name.endswith('.pt'):
            local_path = f"/tmp/{blob.name}"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            logger.info(f"Downloading {blob.name}...")
            blob.download_to_filename(local_path)

    logger.info("✅ All models downloaded")


def load_ensemble_controller():
    """Load the ensemble controller with all chunk models"""
    # TODO: Implement actual ensemble loading
    # This is a placeholder - replace with your actual implementation

    from src.hybrid_model.ensemble_controller import EnsembleController

    controller = EnsembleController(
        num_chunks=10,  # Adjust based on your config
        model_dir="/tmp/models"
    )

    return controller


def run_backtest(
    ticker: str,
    start_date: str,
    end_date: str,
    initial_balance: float,
    transaction_cost: float
) -> Dict[str, Any]:
    """
    Execute backtest with ensemble model

    TODO: Replace with actual backtesting implementation
    """
    import time
    import numpy as np

    start_time = time.time()

    # Placeholder implementation
    # Replace with actual backtesting logic using ensemble_controller

    # Simulate some computation
    time.sleep(1)

    # Mock results (replace with real results)
    results = {
        'sharpe_ratio': np.random.uniform(0.5, 2.0),
        'max_drawdown': np.random.uniform(0.1, 0.4),
        'cumulative_return': np.random.uniform(-0.2, 0.8),
        'total_trades': np.random.randint(50, 200),
        'win_rate': np.random.uniform(0.4, 0.7),
        'profit_factor': np.random.uniform(0.8, 2.5),
        'final_balance': initial_balance * (1 + np.random.uniform(-0.2, 0.8)),
        'execution_time_seconds': time.time() - start_time
    }

    return results


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "ReWTSE Backtesting API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if models_loaded else "degraded",
        models_loaded=models_loaded,
        gpu_available=torch.cuda.is_available(),
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/backtest", response_model=BacktestResponse)
async def backtest(request: BacktestRequest):
    """
    Run backtest for a given ticker and date range

    Returns detailed performance metrics
    """
    if not models_loaded:
        raise HTTPException(
            status_code=503,
            detail="Models not loaded yet. Please wait and retry."
        )

    logger.info(f"📊 Running backtest for {request.ticker} ({request.start_date} to {request.end_date})")

    try:
        # Run backtest
        results = run_backtest(
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_balance=request.initial_balance,
            transaction_cost=request.transaction_cost
        )

        # Prepare response
        response = BacktestResponse(
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            sharpe_ratio=round(results['sharpe_ratio'], 3),
            max_drawdown=round(results['max_drawdown'], 3),
            cumulative_return=round(results['cumulative_return'], 3),
            total_trades=results['total_trades'],
            win_rate=round(results['win_rate'], 3),
            profit_factor=round(results['profit_factor'], 3),
            final_balance=round(results['final_balance'], 2),
            execution_time_seconds=round(results['execution_time_seconds'], 2)
        )

        logger.info(f"✅ Backtest completed - Sharpe: {response.sharpe_ratio}, Return: {response.cumulative_return}")

        return response

    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@app.get("/models/info")
async def models_info():
    """Get information about loaded models"""
    if not models_loaded:
        return {"status": "not_loaded", "models": []}

    # TODO: Return actual model information
    return {
        "status": "loaded",
        "num_chunks": 10,
        "model_dir": "/tmp/models",
        "ensemble_type": "ReWTSE"
    }


@app.get("/tickers")
async def available_tickers():
    """Get list of available tickers"""
    # TODO: Return actual list from config or data
    return {
        "tickers": ["AAPL", "AMZN", "GOOGL", "META", "MSFT", "TSLA"],
        "count": 6
    }


if __name__ == "__main__":
    # Run server
    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable in production
        workers=1,     # Single worker (models loaded once)
        log_level="info"
    )
