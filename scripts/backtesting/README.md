# Backtesting Scripts - Settimanale

Scripts per testare performance dei modelli trained.

**Frequenza**: 1 volta/settimana (weekend)
**Tempo**: ~10 minuti
**Costo**: $0 (VM fisso $3.72/mese)

---

## 📋 Scripts

### `run_backtest.py`
Test performance modelli su dati storici.

**Cosa fa**:
- Carica modelli trained da GCS
- Esegue backtest su periodo test (30% dati)
- Calcola metriche performance
- Genera visualizzazioni

**Metriche**:
- Sharpe Ratio (target >1.3)
- Max Drawdown (target <30%)
- Cumulative Return
- Win Rate
- Profit Factor

---

## 🚀 Usage

### Single Ticker
```python
python run_backtest.py
```

Modificare script per specificare ticker:
```python
# In run_backtest.py
client = BacktestingClient(vm_ip="YOUR_VM_IP")

result = client.run_backtest(
    ticker="AAPL",
    start_date="2020-01-01",
    end_date="2020-12-31"
)

print(f"Sharpe Ratio: {result['sharpe_ratio']:.3f}")
print(f"Cumulative Return: {result['cumulative_return']:.2%}")
print(f"Max Drawdown: {result['max_drawdown']:.2%}")
```

### Batch Backtesting
```python
from examples.backtesting_client_example import BacktestingClient

client = BacktestingClient(vm_ip="YOUR_VM_IP")

tickers = ["AAPL", "AMZN", "GOOGL", "META", "MSFT", "TSLA"]

results = client.run_batch_backtests(
    tickers=tickers,
    start_date="2020-01-01",
    end_date="2020-12-31"
)

client.print_summary(results)
```

**Output**:
```
======================================================================
📊 BACKTEST SUMMARY
======================================================================

Total: 6 | Success: 6 | Failed: 0

Ticker     Sharpe   Return       Max DD       Trades    
----------------------------------------------------------------------
AAPL       1.45     45.2%        -18.3%       124       
AMZN       1.32     38.7%        -22.1%       108       
GOOGL      1.28     35.4%        -19.8%       115       
META       1.55     52.1%        -15.6%       132       
MSFT       1.41     42.8%        -17.2%       119       
TSLA       1.18     28.3%        -28.5%       145       
----------------------------------------------------------------------
AVERAGE    1.37     40.4%        
======================================================================
```

---

## 📊 Performance Metrics

### Sharpe Ratio
```
Sharpe = (Return - Risk_Free_Rate) / Volatility

Target: >1.3
- <1.0: Poor risk-adjusted return
- 1.0-1.5: Good
- 1.5-2.0: Very Good
- >2.0: Excellent
```

### Max Drawdown
```
Max DD = (Peak - Trough) / Peak

Target: <30%
- <10%: Very resilient
- 10-20%: Acceptable
- 20-30%: Moderate risk
- >30%: High risk
```

### Win Rate
```
Win Rate = Winning Trades / Total Trades

Target: >50%
- <40%: Poor
- 40-50%: Below average
- 50-60%: Good
- >60%: Excellent
```

---

## 📅 When to Run

### Weekly Review (Recommended)
```bash
# Every Sunday evening
python run_backtest.py
```

**Purpose**:
- Monitor model performance
- Detect degradation early
- Compare vs benchmark (S&P 500)

### After Training
```bash
# Immediately after training new models
python run_backtest.py
```

**Purpose**:
- Verify new models work
- Compare vs previous models
- Decide if deploy new models

### Before Major Deployment
```bash
# Before going live with real money
python run_backtest.py
```

**Purpose**:
- Final validation
- Risk assessment
- Confidence check

---

## 🎯 Performance Targets

Based on ReWTSE-LLM-RL paper:

| Metric | Baseline | LLM+RL | ReWTSE-LLM-RL | Your Target |
|--------|----------|--------|---------------|-------------|
| Sharpe Ratio | 0.64 | 1.10 | 1.30-1.50 | >1.3 |
| Max Drawdown | 0.36 | 0.31 | 0.25-0.28 | <0.30 |
| Cum. Return | 15% | 28% | 35-45% | >30% |

**If below targets**:
- Re-train models (mensile normale)
- Review hyperparameters
- Check data quality
- Analyze market conditions

---

## 📈 Visualization

Create plots for analysis:

```python
import matplotlib.pyplot as plt

# Equity curve
plt.figure(figsize=(12, 6))
plt.plot(equity_curve)
plt.title(f'{ticker} Equity Curve')
plt.xlabel('Days')
plt.ylabel('Portfolio Value ($)')
plt.grid(True)
plt.savefig(f'{ticker}_equity_curve.png')

# Drawdown chart
plt.figure(figsize=(12, 4))
plt.fill_between(range(len(drawdowns)), drawdowns, 0, alpha=0.3, color='red')
plt.title(f'{ticker} Drawdown')
plt.xlabel('Days')
plt.ylabel('Drawdown (%)')
plt.grid(True)
plt.savefig(f'{ticker}_drawdown.png')
```

---

## 🔍 Analysis Checklist

### Weekly Review
- [ ] Run backtesting per tutti ticker
- [ ] Check Sharpe Ratio (target >1.3)
- [ ] Check Max Drawdown (target <30%)
- [ ] Compare vs last week
- [ ] Compare vs S&P 500
- [ ] Identify best/worst performers
- [ ] Note any anomalies

### Red Flags
- ⚠️ Sharpe < 1.0 (poor performance)
- ⚠️ Max DD > 35% (too risky)
- ⚠️ Win Rate < 40% (too many losses)
- ⚠️ Large deviation from expected
- ⚠️ Sudden performance drop

**Action**: Re-train models se red flags persistono 2+ settimane

---

## 💡 Tips

### 1. Compare Periods
Test su diversi periodi per robustezza:
```python
periods = [
    ("2018-01-01", "2018-12-31"),  # Pre-COVID
    ("2019-01-01", "2019-12-31"),  # Normal
    ("2020-01-01", "2020-12-31"),  # COVID
    ("2021-01-01", "2021-12-31"),  # Recovery
]

for start, end in periods:
    result = client.run_backtest(ticker, start, end)
    # Compare results
```

### 2. Walk-Forward Analysis
Test su rolling windows:
```python
# Test ogni 3 mesi
for month in range(12, 36, 3):
    start = f"2020-{month-12:02d}-01"
    end = f"2020-{month:02d}-01"
    result = client.run_backtest(ticker, start, end)
```

### 3. Benchmark Comparison
Sempre compare vs S&P 500:
```python
spy_return = client.run_backtest("SPY", start, end)
alpha = strategy_return - spy_return
print(f"Alpha: {alpha:.2%}")
```

---

## 📚 Next Steps

After backtesting:
```bash
# If performance good → use live
cd ../live
python get_live_strategy.py --all

# If performance bad → re-train
cd ../training
bash create_training_vm.sh
```

Or read: `../../TRAINING_AND_LIVE_USAGE_GUIDE.md`
