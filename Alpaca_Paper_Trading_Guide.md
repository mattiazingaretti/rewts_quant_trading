# Guida Alpaca Paper Trading
## Trading Real-Time con Denaro Fittizio

Questa guida spiega come utilizzare **Alpaca Paper Trading** per testare le strategie ReWTSE-LLM-RL nel mondo reale con denaro fittizio (100% GRATUITO).

---

## 🎯 Cos'è Alpaca Paper Trading?

**Alpaca** è una piattaforma di trading programmabile che offre:
- ✅ **Paper Trading GRATUITO** (denaro fittizio)
- ✅ Dati di mercato **real-time** gratuiti
- ✅ API REST semplice da usare
- ✅ Esecuzione ordini simulata realistica
- ✅ Nessun costo nascosto

**Paper Trading** = Trading con denaro virtuale che simula il mercato reale perfettamente.

---

## 💰 Costi

| Servizio | Costo |
|----------|-------|
| **Paper Trading** | **€0 - GRATUITO** ✅ |
| **Dati Real-Time** | **€0 - GRATUITO** ✅ |
| **API Access** | **€0 - GRATUITO** ✅ |
| **Live Trading (denaro reale)** | Opzionale - Commission-free |

**Totale costo per testare strategie: €0** 🎉

---

## 🚀 Setup Rapido (5 minuti)

### Step 1: Crea Account Alpaca (GRATUITO)

1. Vai su **https://alpaca.markets/**
2. Click su **"Sign Up"**
3. Scegli **"Paper Trading Only"** (non servono documenti finanziari!)
4. Completa la registrazione (email + password)

**Nota**: Non serve verificare identità o aggiungere carte di credito per paper trading!

---

### Step 2: Ottieni API Keys

1. Login su https://app.alpaca.markets/paper/dashboard/overview
2. Nel menu a sinistra, vai su **"API Keys"** (ultima voce)
3. Click su **"Generate New Key"**
4. Copia:
   - **API Key ID**
   - **Secret Key** (⚠️ mostrato una sola volta!)
5. Salva le keys in un posto sicuro

**Screenshot percorso**:
```
Dashboard → API Keys (menu sinistra) → Generate New Key
```

---

### Step 3: Configura Environment Variables

#### Linux/Mac:
```bash
export ALPACA_API_KEY="your_api_key_here"
export ALPACA_SECRET_KEY="your_secret_key_here"
```

Per renderle permanenti, aggiungi a `~/.bashrc` o `~/.zshrc`:
```bash
echo 'export ALPACA_API_KEY="your_api_key_here"' >> ~/.bashrc
echo 'export ALPACA_SECRET_KEY="your_secret_key_here"' >> ~/.bashrc
source ~/.bashrc
```

#### Windows:
```cmd
set ALPACA_API_KEY=your_api_key_here
set ALPACA_SECRET_KEY=your_secret_key_here
```

Per renderle permanenti (PowerShell come Admin):
```powershell
[System.Environment]::SetEnvironmentVariable("ALPACA_API_KEY", "your_key", "User")
[System.Environment]::SetEnvironmentVariable("ALPACA_SECRET_KEY", "your_secret", "User")
```

#### Oppure usa file .env:
Aggiungi al file `.env`:
```
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
```

---

### Step 4: Installa Dipendenza

```bash
pip install alpaca-trade-api
```

Già incluso in `requirements.txt` (decommenta la riga).

---

### Step 5: Test Connessione

```bash
python scripts/run_alpaca_paper_trading.py --mode test
```

Output atteso:
```
🔍 Testing Alpaca connection...
============================================================
✅ Connessione riuscita!

💰 Account Summary:
   Cash: $100,000.00
   Portfolio Value: $100,000.00
   Buying Power: $200,000.00
   Equity: $100,000.00
```

Se vedi questo, sei pronto! 🎉

---

## 📖 Modalità d'Uso

### Modalità 1: Test Connessione

Verifica che le API keys funzionino:

```bash
python scripts/run_alpaca_paper_trading.py --mode test
```

---

### Modalità 2: Trading Live Automatico

Esegui trading automatico con il modello addestrato:

```bash
python scripts/run_alpaca_paper_trading.py \
  --mode run \
  --ticker AAPL \
  --interval 300 \
  --max-iter 100
```

**Parametri**:
- `--ticker`: Ticker da tradare (es. AAPL, TSLA, GOOGL)
- `--interval`: Secondi tra ogni check (300 = 5 minuti)
- `--max-iter`: Numero iterazioni (ometti per infinito)

**Cosa fa**:
1. Carica il modello ensemble per il ticker
2. Ogni 5 minuti:
   - Scarica dati real-time da Alpaca
   - Genera predizione con l'ensemble
   - Esegue azione (BUY/SELL/HOLD) su Alpaca
   - Mostra portfolio value e profit/loss
3. Salva storico in `results/metrics/`

**Output esempio**:
```
[Iteration 1] 2024-01-15 14:30:00
📊 Close: $185.23 | Volume: 2,453,821
🤖 Azione predetta: LONG
Q-values: SHORT=0.123, HOLD=0.456, LONG=0.789
✅ Apertura LONG: $20000.00

💰 Portfolio:
   Cash: $80,000.00
   Portfolio Value: $100,235.50
   Profit/Loss: $235.50 (0.24%)

⏳ Prossimo check tra 300s...
```

**Interrompi con**: `Ctrl+C` (salva automaticamente storico)

---

### Modalità 3: Demo Manuale

Testa manualmente l'API Alpaca:

```bash
python scripts/run_alpaca_paper_trading.py --mode demo
```

Esegue:
- Compra $100 di AAPL
- Mostra posizione aperta
- Mostra profit/loss

Utile per capire come funziona l'API.

---

## 🔧 Uso Programmatico

### Esempio 1: Trading Manuale

```python
from src.trading.alpaca_paper_trader import AlpacaPaperTrader

# Inizializza
trader = AlpacaPaperTrader(
    api_key="your_key",
    secret_key="your_secret"
)

# Check account
account = trader.get_account_summary()
print(f"Cash: ${account['cash']}")

# Compra 10 azioni AAPL a mercato
order = trader.buy_market('AAPL', qty=10)
print(f"Order ID: {order['id']}")

# Compra TSLA per $1000
order = trader.buy_dollars('TSLA', amount=1000.0)

# Check posizioni
positions = trader.get_positions()
for pos in positions:
    print(f"{pos['symbol']}: {pos['qty']} shares")

# Chiudi posizione AAPL
trader.close_position('AAPL')

# Chiudi TUTTE le posizioni
trader.close_all_positions()
```

---

### Esempio 2: Integrazione con Ensemble

```python
from src.trading.alpaca_paper_trader import AlpacaPaperTradingBackend
import pickle

# Carica ensemble
with open('models/AAPL_rewts_ensemble.pkl', 'rb') as f:
    ensemble = pickle.load(f)

# Inizializza backend
backend = AlpacaPaperTradingBackend(
    api_key="your_key",
    secret_key="your_secret"
)

# Esegui trading live
backend.run_live_trading(
    ensemble=ensemble,
    ticker='AAPL',
    check_interval=300,  # 5 minuti
    max_iterations=100   # 100 iterazioni = ~8 ore
)
```

---

### Esempio 3: Get Market Data

```python
trader = AlpacaPaperTrader(api_key, secret_key)

# Ultima quotazione
quote = trader.get_latest_quote('AAPL')
print(f"Bid: ${quote['quote']['bp']}")
print(f"Ask: ${quote['quote']['ap']}")

# Ultimo trade
trade = trader.get_latest_trade('AAPL')
print(f"Price: ${trade['trade']['p']}")

# Dati storici (candlestick)
bars = trader.get_bars(
    symbol='AAPL',
    timeframe='1Day',
    limit=100
)
print(bars.head())
```

---

## 📊 Metriche e Monitoring

### Durante il Trading

Il sistema mostra automaticamente:
- **Azione predetta**: LONG/SHORT/HOLD
- **Q-values**: Confidence per ogni azione
- **Portfolio Value**: Valore totale portfolio
- **Profit/Loss**: Guadagno/perdita da inizio
- **Cash**: Liquidità disponibile

### Storico Salvato

Dopo ogni sessione, viene salvato un CSV:
```
results/metrics/alpaca_trading_history_20240115_143000.csv
```

Contiene:
- Timestamp
- Ticker
- Azione eseguita
- Portfolio value
- Profit/loss

Puoi analizzarlo con pandas:
```python
import pandas as pd
df = pd.read_csv('results/metrics/alpaca_trading_history_*.csv')
df.plot(x='timestamp', y='portfolio_value')
```

---

## 🎛️ Configurazione Avanzata

### Modifica Allocazione Portfolio

Default: 20% del portfolio per trade

Modifica in `alpaca_paper_trader.py`:
```python
signal = {
    'symbol': ticker,
    'action': action_name,
    'portfolio_allocation': 0.5  # 50% invece di 20%
}
```

### Modifica Check Interval

Per trading più frequente:
```bash
# Check ogni 1 minuto
python scripts/run_alpaca_paper_trading.py --mode run --interval 60

# Check ogni 30 secondi
python scripts/run_alpaca_paper_trading.py --mode run --interval 30
```

**Nota**: Alpaca rate limit = 200 richieste/minuto (più che sufficiente)

### Trading Multi-Ticker

Esegui più istanze in parallelo:
```bash
# Terminal 1
python scripts/run_alpaca_paper_trading.py --mode run --ticker AAPL --interval 300 &

# Terminal 2
python scripts/run_alpaca_paper_trading.py --mode run --ticker TSLA --interval 300 &

# Terminal 3
python scripts/run_alpaca_paper_trading.py --mode run --ticker GOOGL --interval 300 &
```

---

## 🔒 Sicurezza

### Best Practices

1. **MAI committare le API keys** su Git
   - Già in `.gitignore`: `.env`
   - Usa sempre environment variables

2. **Usa Paper Trading per testing**
   - Zero rischio finanziario
   - Dati real-time identici al live

3. **Paper vs Live**
   - Paper: Endpoint `https://paper-api.alpaca.markets`
   - Live: Endpoint `https://api.alpaca.markets`
   - Il codice usa paper by default (modificabile in `alpaca_paper_trader.py`)

4. **Rigenera keys se compromesse**
   - Dashboard → API Keys → Regenerate

---

## 🐛 Troubleshooting

### Errore: "Forbidden" o "Unauthorized"

**Causa**: API keys errate o scadute

**Soluzione**:
1. Verifica keys su https://app.alpaca.markets/paper/dashboard/api
2. Rigenera keys se necessario
3. Ricarica environment variables: `source ~/.bashrc`

---

### Errore: "Insufficient buying power"

**Causa**: Non hai abbastanza cash per il trade

**Soluzione**:
1. Check account: `--mode test`
2. Riduci `portfolio_allocation` (default: 0.2)
3. Reset paper account su Alpaca dashboard

---

### Errore: "Market is closed"

**Causa**: Mercato USA chiuso (fuori orario 9:30-16:00 ET)

**Soluzione**:
- Paper trading funziona solo in orari di mercato
- Alpaca supporta extended hours (pre-market/after-hours) ma limitato
- Usa `time_in_force='gtc'` per ordini che persistono

---

### Nessun dato per ticker

**Causa**: Ticker non esistente o non supportato

**Soluzione**:
- Verifica ticker su https://finance.yahoo.com
- Alpaca supporta solo US stocks
- Lista completa: https://alpaca.markets/support/what-stocks-are-supported-for-trading/

---

### Connection timeout

**Causa**: Problemi di rete o Alpaca API down

**Soluzione**:
1. Check status: https://status.alpaca.markets/
2. Verifica connessione internet
3. Retry dopo qualche minuto

---

## 📈 Passaggio a Live Trading (Denaro Reale)

### ⚠️ IMPORTANTE: Testare SEMPRE con Paper Trading prima!

Quando sei pronto per live trading:

1. **Verifica risultati Paper Trading**
   - Almeno 3-6 mesi di paper trading
   - Sharpe Ratio > 1.0
   - Max Drawdown accettabile
   - Strategie consistenti

2. **Crea Live Trading Account**
   - Su Alpaca: serve verifica identità (documenti)
   - Deposito minimo: $0 (ma consigliato almeno $500-1000)

3. **Ottieni Live API Keys**
   - Dashboard → Switch to "Live Trading" → API Keys

4. **Modifica endpoint**
   ```python
   # In alpaca_paper_trader.py
   self.base_url = "https://api.alpaca.markets"  # Live
   ```

5. **INIZIA CON POCO CAPITALE**
   - Test con $100-500 inizialmente
   - Scala gradualmente se funziona

### Disclaimer

⚠️ **Il trading comporta rischi sostanziali di perdita. Usa denaro reale solo se:**
- Hai testato estensivamente in paper trading
- Comprendi i rischi finanziari
- Puoi permetterti di perdere il capitale investito
- Hai consultato un consulente finanziario

**Gli autori di questo progetto non sono responsabili per perdite finanziarie.**

---

## 📚 Risorse

### Documentazione Alpaca
- **API Docs**: https://alpaca.markets/docs/api-references/trading-api/
- **Python SDK**: https://github.com/alpacahq/alpaca-trade-api-python
- **Market Data**: https://alpaca.markets/docs/api-references/market-data-api/

### Dashboard Alpaca
- **Paper Trading**: https://app.alpaca.markets/paper/dashboard/overview
- **API Keys**: https://app.alpaca.markets/paper/dashboard/api
- **Account**: https://app.alpaca.markets/paper/dashboard/account

### Support
- **Forum**: https://forum.alpaca.markets/
- **Status**: https://status.alpaca.markets/
- **Email**: support@alpaca.markets

---

## 🎯 Quick Start TL;DR

```bash
# 1. Crea account su https://alpaca.markets/ (GRATUITO)

# 2. Ottieni API keys da dashboard

# 3. Configura environment
export ALPACA_API_KEY="your_key"
export ALPACA_SECRET_KEY="your_secret"

# 4. Test connessione
python scripts/run_alpaca_paper_trading.py --mode test

# 5. Addestra modello (se non già fatto)
python scripts/train_rewts_llm_rl.py

# 6. Avvia trading live!
python scripts/run_alpaca_paper_trading.py --mode run --ticker AAPL --interval 300
```

**Costo totale: €0** ✅
**Tempo setup: 5 minuti** ✅
**Rischio finanziario: ZERO** ✅

---

Buon trading! 🚀📈
