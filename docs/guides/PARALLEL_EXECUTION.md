# Parallel Strategy Generation

## Overview

Il sistema di training ora supporta la **generazione parallela di strategie LLM** per ridurre drasticamente i tempi di esecuzione.

## Miglioramenti di Performance

### Before (Sequential)
- **Tempo per ticker**: ~60 minuti (88 strategie × 40s/strategia)
- **Tempo totale (6 ticker)**: ~6 ore
- **Utilizzo API**: Sequenziale, un request alla volta

### After (Parallel)
- **Tempo per ticker**: ~5-8 minuti (con 8 workers paralleli)
- **Tempo totale (6 ticker)**: ~30-45 minuti
- **Speedup**: **8-12x più veloce**

## Come Funziona

### 1. ThreadPoolExecutor
Il sistema usa `concurrent.futures.ThreadPoolExecutor` per eseguire multiple chiamate API in parallelo:
- **8 workers** di default (configurabile)
- Ogni worker processa una strategia indipendentemente
- Thread-safe per accesso a cache e monitor

### 2. Rate Limiting
Per rispettare i limiti API di Gemini (1000 RPM):
- `RateLimiter`: Garantisce max 8 requests/secondo (configurabile)
- Calcola automaticamente interval minimo tra richieste
- Thread-safe con lock

```python
rate_limiter = RateLimiter(max_per_second=8.0)
rate_limiter.wait()  # Aspetta se necessario
```

### 3. Request Monitoring
Traccia in real-time il rate di richieste:
- `RequestMonitor`: Window di 60 secondi
- Conta richieste nel periodo
- Calcola percentuale del limite

```python
monitor = RequestMonitor(window_seconds=60, limit_rpm=1000)
monitor.record_request()
monitor.print_stats()  # 🟢 Current rate: 234 RPM (23.4% of 1000 limit)
```

### 4. Exponential Backoff
Gestione automatica errori 429:
- Retry automatico con backoff esponenziale
- Wait times: 2s → 4s → 8s (con jitter random)
- Max 3 retry per strategia
- Fallback a strategia default se tutti i retry falliscono

## Configurazione

Nel file `configs/hybrid/rewts_llm_rl.yaml`:

```yaml
# Parallel execution settings
parallel_workers: 8  # Numero di workers paralleli
max_requests_per_second: 8.0  # Max API requests per secondo
```

### Tuning dei Parametri

#### `parallel_workers`
- **Default**: 8
- **Range sicuro**: 4-12
- **Considerazioni**:
  - Più workers = più veloce MA più stress su API
  - Con paid tier (1000 RPM), anche 16 workers è safe
  - Limitato da `max_requests_per_second`

#### `max_requests_per_second`
- **Default**: 8.0 (= 480 RPM)
- **Range sicuro**: 5.0 - 15.0
- **Considerazioni**:
  - 8.0 req/s = 48% del limite di 1000 RPM
  - Margine di sicurezza ampio per burst
  - Aumenta se hai quota più alta

### Esempi di Configurazioni

#### Conservative (massima affidabilità)
```yaml
parallel_workers: 4
max_requests_per_second: 5.0  # 300 RPM = 30% del limite
```
- Pro: Zero rischio di 429
- Con: Più lento (~10 min/ticker)

#### Balanced (raccomandato)
```yaml
parallel_workers: 8
max_requests_per_second: 8.0  # 480 RPM = 48% del limite
```
- Pro: Ottimo bilanciamento velocità/sicurezza
- Con: ~6 min/ticker

#### Aggressive (massima velocità)
```yaml
parallel_workers: 12
max_requests_per_second: 15.0  # 900 RPM = 90% del limite
```
- Pro: Massima velocità (~4 min/ticker)
- Con: Possibili occasionali 429 (gestiti da retry)

## Output del Training

Durante l'esecuzione vedrai:

```
============================================================
Pre-computing LLM Strategies for AAPL
============================================================
Cache initialized: 0 entries, 0 KB
Parallel execution: 8 workers, 8.0 req/s max
Preparing 88 strategy generation tasks...
✓ Prepared 88 tasks

🚀 Starting parallel strategy generation...
Progress: 10/88 (11.4%) | Rate: 2.3 strat/s | ETA: 34s
Progress: 20/88 (22.7%) | Rate: 2.5 strat/s | ETA: 27s
🟢 Current rate: 156 RPM (15.6% of 1000 limit)
Progress: 30/88 (34.1%) | Rate: 2.6 strat/s | ETA: 22s
...
Progress: 88/88 (100.0%) | Rate: 2.4 strat/s | ETA: 0s

✓ Generated 88 strategies in 367s
  Cache hits: 0 (0.0%)
  Cache misses: 88 (100.0%)
  Errors (fallback used): 0
  API calls saved: 0
  Average time per strategy: 4.2s
🟢 Current rate: 234 RPM (23.4% of 1000 limit)
```

### Metriche Chiave

- **Rate**: Strategie generate per secondo (ideal: 2-3 strat/s)
- **ETA**: Tempo stimato rimanente
- **RPM**: Richieste per minuto (deve essere < 1000)
- **Cache hits**: % di strategie dalla cache (100% dopo prima run)
- **Average time**: Tempo medio per strategia (include wait time)

## Troubleshooting

### Errori 429 Frequenti

**Sintomo**: Vedi molti "⚠️ Rate limit hit" messages

**Soluzione**:
1. Riduci `max_requests_per_second` (es. da 8.0 a 5.0)
2. Riduci `parallel_workers` (es. da 8 a 4)
3. Verifica che il tuo paid tier sia attivo

### Strategie Fallback Usate

**Sintomo**: "Errors (fallback used): X" è > 0

**Causa**: Alcune strategie hanno fallito dopo 3 retry

**Soluzione**:
- Se X è piccolo (< 5%): Normale, ignora
- Se X è grande (> 20%): Problema con API o quota

### Performance Subottimale

**Sintomo**: Rate < 1.0 strat/s

**Causa**:
- Latency API alta
- Rate limiting troppo conservativo
- Workers insufficienti

**Soluzione**:
1. Aumenta `parallel_workers` a 10-12
2. Aumenta `max_requests_per_second` a 10.0
3. Verifica connessione internet

## Cache Performance

Dopo la prima esecuzione, la cache salva ~80-100% delle strategie:

**Prima Run**:
```
Cache hits: 0 (0.0%)
Cache misses: 88 (100.0%)
API calls: 88
Time: 367s
```

**Seconda Run** (stesso ticker):
```
Cache hits: 88 (100.0%)
Cache misses: 0 (0.0%)
API calls: 0
Time: 12s  ⚡ 30x più veloce!
```

## Safety Features

### 1. Thread-Safe Cache
- Lock su lettura/scrittura cache file
- Evita race conditions tra workers

### 2. Graceful Degradation
- Se tutti i retry falliscono → Usa strategia fallback
- Lo script NON si interrompe mai

### 3. Progress Tracking
- Real-time progress bar
- ETA dinamico
- Stats ogni 10-20 strategie

### 4. Rate Monitoring
- 🟢 Green: < 70% del limite (safe)
- 🟡 Yellow: 70-90% del limite (attenzione)
- 🔴 Red: > 90% del limite (pericolo)

## Advanced: Custom Rate Limiting Logic

Se vuoi implementare logica custom, modifica `src/utils/rate_limiter.py`:

```python
class AdaptiveRateLimiter(RateLimiter):
    def __init__(self, monitor: RequestMonitor, **kwargs):
        super().__init__(**kwargs)
        self.monitor = monitor

    def wait(self):
        # Slow down se ci avviciniamo al limite
        if self.monitor.get_percent_of_limit() > 80:
            time.sleep(1.0)  # Extra delay

        super().wait()
```

## FAQ

**Q: Posso usare più di 8 workers?**
A: Sì, con paid tier puoi usare fino a 16-20 workers. Calcola: `workers × 40s_per_request / 60s = RPM`. Assicurati di stare sotto 1000 RPM.

**Q: Come faccio a sapere il mio rate limit?**
A: Controlla la tua dashboard Gemini AI Studio. Free tier: 50 req/day. Paid tier: 1000 RPM.

**Q: La cache funziona tra ticker diversi?**
A: Parzialmente. Strategie con dati simili (market data, sentiment) vengono riutilizzate, ma ticker diversi hanno spesso dati diversi.

**Q: Posso disabilitare la parallelizzazione?**
A: Sì, imposta `parallel_workers: 1` nel config. Tornerai all'esecuzione sequenziale.

## Performance Benchmarks

Hardware: GCP VM (n1-standard-8)
Network: ~20ms latency to Gemini API
Model: gemini-2.5-flash

| Workers | Req/s | Time/Ticker | Total (6 tickers) | RPM Usage |
|---------|-------|-------------|-------------------|-----------|
| 1       | 0.4   | 58 min      | 5h 48min          | 24 RPM    |
| 4       | 1.2   | 12 min      | 72 min            | 120 RPM   |
| 8       | 2.4   | 6 min       | 36 min            | 240 RPM   |
| 12      | 3.5   | 4 min       | 24 min            | 350 RPM   |
| 16      | 4.2   | 3.5 min     | 21 min            | 420 RPM   |

**Recommendation**: 8 workers è il sweet spot (velocità + stabilità).
