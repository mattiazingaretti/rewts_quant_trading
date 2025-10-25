# Metriche di Valutazione AI per ReWTSE-LLM-RL
## Valutazione Performance dei Modelli di Machine Learning e Reinforcement Learning

Questo documento spiega tutte le metriche tecniche utilizzate per valutare le performance dei vari modelli AI presenti nel progetto ReWTSE-LLM-RL.

---

## 📊 Indice

1. [Metriche Reinforcement Learning (RL)](#metriche-reinforcement-learning-rl)
2. [Metriche Large Language Models (LLM)](#metriche-large-language-models-llm)
3. [Metriche Ensemble (ReWTSE)](#metriche-ensemble-rewtse)
4. [Metriche Trading Performance](#metriche-trading-performance)
5. [Metriche di Generalizzazione](#metriche-di-generalizzazione)

---

## 🤖 Metriche Reinforcement Learning (RL)

Queste metriche valutano la performance dei **DDQN agents** (Double Deep Q-Network).

---

### 1.1 Cumulative Reward (Ricompensa Cumulativa)

**Cosa misura**: La somma totale di tutte le ricompense ottenute durante un episodio.

**Formula**:
```
R_total = Σ(r_t) per t=0 a T
```

Dove:
- `r_t` = ricompensa al timestep t
- `T` = lunghezza episodio

**Interpretazione**:
- **Alto**: Agente sta guadagnando costantemente
- **Basso o negativo**: Agente sta perdendo o facendo errori
- **Trend crescente**: Apprendimento in corso

**Valori tipici nel progetto**:
- Inizio training: -0.5 a +0.5 (random)
- Dopo 50 episodi: +5 a +20
- Agente ottimale: +30 a +100

**Uso nel progetto**: Tracciato durante training in `train_chunk_model()` per monitorare apprendimento.

---

### 1.2 Average Reward per Episode

**Cosa misura**: Media delle ricompense per episodio, utile per confrontare performance su episodi di lunghezza diversa.

**Formula**:
```
R_avg = R_total / T
```

**Interpretazione**:
- **Positivo**: Agente mediamente profittevole
- **Negativo**: Agente mediamente in perdita
- **Stabile**: Agente ha convergito

**Valori target**:
- Basico: R_avg > 0.1
- Buono: R_avg > 0.5
- Ottimo: R_avg > 1.0

---

### 1.3 Loss (Training Loss)

**Cosa misura**: Errore nella predizione dei Q-values rispetto ai target values.

**Formula (MSE Loss)**:
```
Loss = (1/N) * Σ(Q_pred - Q_target)²
```

Dove:
- `Q_pred` = Q-value predetto dalla policy network
- `Q_target` = Target Q-value calcolato con Bellman equation
- `N` = batch size

**Interpretazione**:
- **Alto (>1.0)**: Predizioni molto errate
- **Medio (0.1-1.0)**: Apprendimento in corso
- **Basso (<0.1)**: Convergenza, predizioni accurate

**Trend desiderato**: Decrescente nel tempo

**Uso nel progetto**: Restituito da `train_step()` in `ddqn_agent.py`

```python
# Esempio output training
Episode 10/50, Avg Reward: 2.34, Loss: 0.456
Episode 20/50, Avg Reward: 5.67, Loss: 0.234  # Loss diminuisce
Episode 30/50, Avg Reward: 8.91, Loss: 0.123  # Convergenza
```

---

### 1.4 Epsilon (ε - Exploration Rate)

**Cosa misura**: Probabilità che l'agente esplori (azione random) invece di sfruttare (azione ottimale).

**Formula (Epsilon Decay)**:
```
ε_t = max(ε_min, ε_0 * decay^t)
```

Dove:
- `ε_0` = epsilon iniziale (1.0 = 100% esplorazione)
- `ε_min` = epsilon minimo (0.01 = 1% esplorazione)
- `decay` = tasso di decadimento (0.995)
- `t` = numero di steps

**Interpretazione**:
- **Alto (>0.5)**: Molta esplorazione, fase iniziale
- **Medio (0.1-0.5)**: Bilanciamento esplorazione/sfruttamento
- **Basso (<0.1)**: Principalmente sfruttamento, fase finale

**Config nel progetto**:
```yaml
epsilon_start: 1.0    # Inizio: 100% random
epsilon_min: 0.01     # Minimo: 1% random
epsilon_decay: 0.995  # Decadimento per step
```

**Esempio evoluzione**:
```
Step 0:    ε = 1.00  (100% random)
Step 100:  ε = 0.60  (60% random)
Step 500:  ε = 0.08  (8% random)
Step 1000: ε = 0.01  (1% random - converged)
```

---

### 1.5 Q-Values

**Cosa misura**: Valore atteso del ritorno (future rewards) per ogni azione in un dato stato.

**Formula (Bellman Equation)**:
```
Q(s,a) = E[r_t + γ * max_a' Q(s', a')]
```

Dove:
- `s` = stato corrente
- `a` = azione
- `r_t` = ricompensa immediata
- `γ` = discount factor (0.99)
- `s'` = stato successivo

**Interpretazione**:
- **Q_LONG alto**: Comprare è vantaggioso
- **Q_SHORT alto**: Vendere è vantaggioso
- **Q_HOLD alto**: Mantenere posizione è vantaggioso

**Esempio output**:
```python
State: AAPL @ $150, RSI=75 (overbought)
Q-values:
  SHORT: 0.89  ← Massimo! Agente predice SHORT
  HOLD:  0.45
  LONG:  0.23
→ Azione scelta: SHORT
```

**Uso nel progetto**: Calcolati da `policy_net.forward()` e usati per selezione azione.

---

### 1.6 TD Error (Temporal Difference Error)

**Cosa misura**: Differenza tra Q-value predetto e target Q-value (usato per calcolare loss).

**Formula**:
```
δ = r + γ * max_a' Q(s', a') - Q(s, a)
```

**Interpretazione**:
- **δ > 0**: Sottostima del valore, reward maggiore del previsto
- **δ < 0**: Sovrastima del valore, reward minore del previsto
- **|δ| piccolo**: Predizioni accurate

**Non direttamente tracciato**, ma implicito nel loss.

---

### 1.7 Action Distribution

**Cosa misura**: Distribuzione percentuale delle azioni prese dall'agente.

**Interpretazione**:
- **Inizio training**: ~33% SHORT, 33% HOLD, 33% LONG (random)
- **Durante training**: Distribuzione si sposta verso azioni migliori
- **Convergenza**: Dominanza azioni profittevoli

**Esempio evoluzione**:
```
Episode 1:   SHORT: 35%, HOLD: 30%, LONG: 35%  (random)
Episode 25:  SHORT: 20%, HOLD: 60%, LONG: 20%  (conservativo)
Episode 50:  SHORT: 15%, HOLD: 30%, LONG: 55%  (bullish se mercato sale)
```

**Red flag**: Se >90% una singola azione → overfitting o policy degenerata

---

## 🧠 Metriche Large Language Models (LLM)

Queste metriche valutano la performance degli **LLM agents** (Strategist e Analyst con Google Gemini).

---

### 2.1 Strategy Confidence Score

**Cosa misura**: Livello di confidenza dell'LLM nella strategia generata (Likert scale 1-3).

**Range**: 1-3
- **1**: Bassa confidenza (segnale debole)
- **2**: Media confidenza (segnale moderato)
- **3**: Alta confidenza (segnale forte)

**Formula Normalized**:
```
Confidence_norm = confidence / 3.0  ∈ [0.33, 1.0]
```

**Interpretazione**:
- **Trend**: Distribution delle confidenze
- **Media**: Dovrebbe essere ~2.0 (né troppo sicuro né troppo incerto)

**Uso nel progetto**: Estratto da `action_confidence` nel prompt response.

---

### 2.2 Strategy Strength (Entropy-Adjusted Confidence)

**Cosa misura**: Confidenza aggiustata per l'incertezza dell'LLM (entropy dei token).

**Formula**:
```
Strength = (confidence / 3.0) * certainty

certainty = ε + (1 - ε) * (1 - H)
```

Dove:
- `confidence` = Likert score (1-3)
- `H` = Normalized entropy dei logprobs
- `ε` = Baseline certainty (0.01)

**Interpretazione**:
- **Alto (>0.8)**: LLM molto sicuro e bassa entropy
- **Medio (0.4-0.8)**: Confidenza moderata
- **Basso (<0.4)**: LLM incerto o alto entropy

**Esempio**:
```python
Confidence = 3 (alto)
Entropy = 0.2 (basso - LLM sicuro)
→ Certainty = 0.01 + 0.99 * (1 - 0.2) = 0.802
→ Strength = 1.0 * 0.802 = 0.802  (forte!)

Confidence = 3 (alto)
Entropy = 0.8 (alto - LLM incerto)
→ Certainty = 0.01 + 0.99 * (1 - 0.8) = 0.208
→ Strength = 1.0 * 0.208 = 0.208  (debole!)
```

**Uso nel progetto**: Calcolato in `generate_strategy()` come `strength`.

---

### 2.3 Entropy (Token Prediction Uncertainty)

**Cosa misura**: Incertezza dell'LLM nella generazione dei token (quanto è "confuso").

**Formula (Shannon Entropy)**:
```
H = -Σ p_i * log(p_i)

H_normalized = H / log(K)
```

Dove:
- `p_i` = probabilità del token i
- `K` = numero totale token considerati (vocab size o top-k)

**Range**: 0-1 (normalized)
- **0**: LLM certissimo (un token ha p=1.0)
- **0.5**: Media incertezza
- **1.0**: LLM completamente incerto (distribuzione uniforme)

**Interpretazione**:
- **Basso (<0.3)**: LLM ha chiara idea della risposta
- **Alto (>0.7)**: LLM indeciso, molte opzioni valide

**Nota**: Google Gemini attualmente non espone logprobs, quindi usiamo proxy (entropy = 0.5 default).

---

### 2.4 Feature Usage Consistency

**Cosa misura**: Quali feature l'LLM Strategist usa più frequentemente nelle decisioni.

**Tracking**:
```python
features_used = [
    {"feature": "Stock_Data.Close", "direction": "LONG", "weight": 3},
    {"feature": "Technical_Analysis.RSI", "direction": "SHORT", "weight": 2},
    ...
]
```

**Analisi**:
- **Most used features**: Quali indicatori l'LLM considera più importanti
- **Consistency**: Se usa sempre le stesse feature (buono) o cambia spesso (overfitting?)

**Esempio aggregate**:
```
Top 5 Features Used by Strategist:
1. RSI: 85% delle strategie
2. MACD: 72% delle strategie
3. SMA_50: 68% delle strategie
4. News_Sentiment: 65% delle strategie
5. SPX_Close_Slope: 54% delle strategie
```

---

### 2.5 Direction Accuracy

**Cosa misura**: Percentuale di volte che la direzione predetta dall'LLM (LONG/SHORT) è corretta.

**Formula**:
```
Accuracy = (Correct Predictions / Total Predictions) * 100%
```

**Esempio**:
```
Strategy 1: Predetto LONG, Return = +2.5% → Correct ✓
Strategy 2: Predetto SHORT, Return = -1.2% → Correct ✓
Strategy 3: Predetto LONG, Return = -0.8% → Wrong ✗

Accuracy = 2/3 = 66.7%
```

**Interpretazione**:
- **<50%**: Peggio del random, c'è un problema
- **50-60%**: Barely profitable
- **60-70%**: Buono
- **>70%**: Eccellente (difficile da mantenere)

**Benchmark**:
- Random: 50%
- LLM baseline (paper): ~58%
- LLM+RL (paper): ~65%
- ReWTSE-LLM-RL (target): >65%

---

### 2.6 News Sentiment Accuracy

**Cosa misura**: Quanto il sentiment delle news estratto dall'Analyst Agent correla con i movimenti di prezzo.

**Correlation Analysis**:
```python
sentiment_scores = [-1, 0, +1, +1, -1, ...]
price_returns = [-2%, +1%, +3%, +2%, -1.5%, ...]

correlation = corr(sentiment_scores, price_returns)
```

**Interpretazione**:
- **Correlation > 0.3**: Sentiment ha potere predittivo
- **Correlation ~0**: Sentiment non utile
- **Correlation < 0**: Sentiment contrarian (inverso)

**Valori target**: >0.25 per considerare news utili

---

### 2.7 Prompt Consistency (Temperature = 0)

**Cosa misura**: Quanto sono consistenti le risposte dell'LLM con stessi input.

**Test**: Run stessa strategia 3 volte con temperature=0

**Interpretazione**:
- **100% identiche**: Perfetto (temperature=0 deterministico)
- **>95% simili**: Accettabile (piccole variazioni)
- **<90% simili**: Problema (LLM instabile o temperatura >0)

**Config nel progetto**:
```yaml
llm:
  temperature: 0.0  # Deterministico
  seed: 49          # Riproducibilità
```

---

## 🔀 Metriche Ensemble (ReWTSE)

Queste metriche valutano la performance del sistema **ReWTSE ensemble**.

---

### 3.1 Weight Distribution

**Cosa misura**: Come i pesi ottimali sono distribuiti tra i chunk models.

**Analisi**:
```python
weights = [0.45, 0.30, 0.15, 0.10]  # 4 chunk models

# Metrics
entropy_weights = -sum([w * log(w) for w in weights if w > 0])
max_weight = max(weights)
concentration = max_weight / sum(weights)
```

**Interpretazione**:
- **Uniform distribution**: Tutti i chunks contribuiscono ugualmente
- **Concentrated**: Un chunk domina (potenziale overfitting a quel periodo)
- **Sparse**: Pochi chunks attivi (buono se temporalmente rilevanti)

**Esempio visualizzazione**:
```
Chunk 1 (2012-2013): ██████████████████████ 45%
Chunk 2 (2014-2015): ██████████████ 30%
Chunk 3 (2016-2017): ███████ 15%
Chunk 4 (2018-2020): █████ 10%
```

**Red flag**: Se un solo chunk >80% → ensemble non sfruttato

---

### 3.2 Weight Adaptation Speed

**Cosa misura**: Quanto velocemente i pesi cambiano nel tempo durante backtesting.

**Formula**:
```
Δw = ||w_t - w_{t-1}||  (L2 norm)
```

**Interpretazione**:
- **Alta varianza**: Pesi cambiano drasticamente (instabile o adattivo)
- **Bassa varianza**: Pesi stabili (buono se performance è stabile)

**Esempio**:
```
Step 1:   w = [0.40, 0.30, 0.20, 0.10], Δw = N/A
Step 100: w = [0.42, 0.28, 0.22, 0.08], Δw = 0.04 (piccolo)
Step 200: w = [0.38, 0.35, 0.18, 0.09], Δw = 0.08 (medio)
Step 300: w = [0.50, 0.25, 0.15, 0.10], Δw = 0.15 (grande cambiamento!)
```

---

### 3.3 QP Optimization Convergence

**Cosa misura**: Se il solver QP converge e quanto rapidamente.

**Metrics**:
- **Convergence rate**: Percentuale di volte che solver trova soluzione ottimale
- **Iterations to converge**: Numero iterazioni necessarie
- **Objective value**: Valore della funzione obiettivo minimizzata

**Output solver**:
```python
sol = solvers.qp(P, q, G, h, A, b)

# Metrics
status = sol['status']  # 'optimal', 'primal infeasible', 'unknown'
iterations = sol['iterations']
objective = sol['primal objective']
```

**Interpretazione**:
- **status='optimal'**: Ottimo, pesi trovati
- **iterations < 50**: Convergenza rapida
- **objective basso**: Buon fit ai dati

**Config**:
```yaml
rewts:
  lookback_length: 432  # Più lungo = più dati per QP
```

---

### 3.4 Ensemble Diversity

**Cosa misura**: Quanto i chunk models sono diversi tra loro (predizioni decorrelate).

**Formula (Average Pairwise Correlation)**:
```
Diversity = 1 - (1/K²) * ΣΣ corr(pred_i, pred_j)
```

Dove:
- `pred_i` = predizioni (Q-values) del chunk i
- `K` = numero chunk models

**Interpretazione**:
- **Diversity = 1.0**: Modelli completamente diversi (ideale)
- **Diversity = 0.5**: Media diversità
- **Diversity = 0.0**: Modelli identici (ensemble inutile)

**Target**: >0.4 (buona diversità)

**Perché importante**: Ensemble funziona meglio con modelli diversi ma accurate.

---

### 3.5 Chunk Specialization Score

**Cosa misura**: Quanto ogni chunk è specializzato sul suo periodo temporale.

**Formula**:
```
Specialization_i = Performance_i(in-sample) - Performance_i(out-of-sample)
```

**Interpretazione**:
- **Positivo**: Chunk performa meglio sul suo periodo (specializzazione)
- **Zero**: Chunk generalizza ugualmente
- **Negativo**: Chunk performa peggio sul suo periodo (problema!)

**Target**: Positivo moderato (0.1-0.3)

**Troppo alto (>0.5)**: Overfitting al chunk

---

## 📈 Metriche Trading Performance

Queste sono le metriche **finali** che misurano il successo del sistema nel trading.

---

### 4.1 Sharpe Ratio

**Cosa misura**: Rendimento aggiustato per il rischio (return per unità di volatilità).

**Formula**:
```
Sharpe = sqrt(252) * (R_mean - R_f) / σ_R
```

Dove:
- `R_mean` = media dei rendimenti giornalieri
- `R_f` = risk-free rate (Treasury yield ~0%)
- `σ_R` = deviazione standard dei rendimenti
- `sqrt(252)` = annualizzazione (252 trading days)

**Interpretazione**:
- **<0.5**: Scarso
- **0.5-1.0**: Accettabile
- **1.0-2.0**: Buono
- **>2.0**: Eccellente
- **>3.0**: Straordinario (raro, sospetto)

**Benchmark**:
- S&P 500: ~0.5-0.7
- Hedge funds: 0.8-1.5
- Target progetto: **>1.3**

**Esempio calcolo**:
```python
returns = [0.02, -0.01, 0.03, 0.01, -0.02, ...]  # Daily returns
mean_return = 0.0015  # 0.15% daily
std_return = 0.012    # 1.2% volatility

Sharpe = sqrt(252) * (0.0015 - 0) / 0.012
       = 15.87 * 0.125
       = 1.98  (Buono!)
```

---

### 4.2 Maximum Drawdown (MDD)

**Cosa misura**: La massima perdita percentuale dal picco al minimo (worst-case scenario).

**Formula**:
```
MDD = min_t [(P_t - P_peak) / P_peak]
```

Dove:
- `P_t` = portfolio value al tempo t
- `P_peak` = massimo portfolio value fino a t

**Interpretazione**:
- **-10%**: Basso rischio, drawdown contenuto
- **-20%**: Rischio moderato
- **-30%**: Alto rischio
- **>-40%**: Rischio molto alto

**Target progetto**: **<-28%** (meglio di -31% baseline LLM+RL)

**Esempio**:
```
Day 1:  $100,000 (peak)
Day 5:  $105,000 (new peak)
Day 10: $98,000  → Drawdown = -6.7%
Day 15: $92,000  → Drawdown = -12.4% (MDD finora)
Day 20: $103,000 → Recovery, ma MDD resta -12.4%
```

**Visualizzazione**:
```python
plt.plot(portfolio_values)
plt.fill_between(range(len(portfolio_values)),
                 running_max,
                 portfolio_values,
                 alpha=0.3, color='red', label='Drawdown')
```

---

### 4.3 Cumulative Return

**Cosa misura**: Rendimento percentuale totale dall'inizio alla fine del periodo.

**Formula**:
```
Cumulative Return = (P_final / P_initial - 1) * 100%
```

**Interpretazione**:
- **>0%**: Profitto
- **<0%**: Perdita

**Benchmark annualizzato**:
- S&P 500: ~10% annuo
- Target: >15% annuo

**Esempio**:
```
Initial: $100,000
Final:   $145,000
Cumulative Return = (145000 / 100000 - 1) * 100%
                  = 45%

Se periodo = 3 anni:
Annualized Return = (1.45^(1/3) - 1) * 100%
                  = 13.2% annuo
```

---

### 4.4 Win Rate

**Cosa misura**: Percentuale di trade profittevoli.

**Formula**:
```
Win Rate = (Winning Trades / Total Trades) * 100%
```

**Interpretazione**:
- **<50%**: Perdente nel lungo termine (a meno che big wins)
- **50-55%**: Marginalmente profittevole
- **55-65%**: Buono
- **>65%**: Eccellente

**Non è tutto**: Win rate alto ma piccoli wins e grandi losses = negativo

**Esempio**:
```
10 trade: 6 wins (+1% avg), 4 losses (-2% avg)
Win Rate = 60% (buono!)
Ma: 6 * 1% - 4 * 2% = -2% (negativo!)
→ Serve anche guardare Risk/Reward Ratio
```

---

### 4.5 Profit Factor

**Cosa misura**: Rapporto tra profitti totali e perdite totali.

**Formula**:
```
Profit Factor = Σ(Winning Trades) / |Σ(Losing Trades)|
```

**Interpretazione**:
- **<1.0**: Sistema perdente
- **1.0-1.5**: Marginalmente profittevole
- **1.5-2.0**: Buono
- **>2.0**: Eccellente

**Esempio**:
```
Winning trades: +$10,000 + $5,000 + $8,000 = $23,000
Losing trades:  -$4,000 - $3,000 - $2,000 = -$9,000

Profit Factor = 23000 / 9000 = 2.56 (eccellente!)
```

**Target**: >1.5

---

### 4.6 Calmar Ratio

**Cosa misura**: Rendimento annualizzato diviso per maximum drawdown (risk-adjusted return).

**Formula**:
```
Calmar = Annualized Return / |Max Drawdown|
```

**Interpretazione**:
- **<1.0**: Scarso
- **1.0-3.0**: Buono
- **>3.0**: Eccellente

**Esempio**:
```
Annualized Return = 18%
Max Drawdown = -12%

Calmar = 18 / 12 = 1.5 (buono)
```

**Vs Sharpe**: Calmar usa worst-case (MDD) invece di volatilità media.

---

### 4.7 Sortino Ratio

**Cosa misura**: Come Sharpe, ma penalizza solo volatilità al ribasso (downside risk).

**Formula**:
```
Sortino = sqrt(252) * (R_mean - R_f) / σ_downside
```

Dove:
```
σ_downside = sqrt(mean([min(0, r)]²))
```

**Interpretazione**: Sempre ≥ Sharpe Ratio (più generoso)

**Target**: >1.5

---

## 🎯 Metriche di Generalizzazione

Queste metriche valutano quanto bene il modello generalizza a dati non visti.

---

### 5.1 Train/Val/Test Split Performance

**Cosa misura**: Performance su train/validation/test set separati.

**Split tipico**:
- Train: 60% (2012-2016)
- Validation: 20% (2017-2018)
- Test: 20% (2019-2020)

**Analisi**:
```
Sharpe_train = 1.8
Sharpe_val   = 1.5
Sharpe_test  = 1.3

→ Leggero calo accettabile (generalizza bene)
```

**Red flags**:
- `Sharpe_train >> Sharpe_test`: Overfitting
- `Sharpe_test >> Sharpe_train`: Problemi dataset o data leakage
- `Sharpe_val` e `Sharpe_test` molto diversi: Validation set non rappresentativo

---

### 5.2 Cross-Ticker Consistency

**Cosa misura**: Se la strategia funziona consistentemente su ticker diversi.

**Analisi**:
```
Ticker     Sharpe   MDD
AAPL       1.45    -22%
TSLA       1.38    -28%
GOOGL      1.52    -19%
META       1.28    -31%
MSFT       1.61    -17%
AMZN       1.34    -25%

Mean:      1.43    -24%
Std:       0.12     5%
```

**Interpretazione**:
- **Bassa std**: Strategia robusta, generalizza bene
- **Alta std**: Funziona bene solo su certi ticker (overfitting)

**Target**: Std(Sharpe) < 0.20

---

### 5.3 Out-of-Sample Period Performance

**Cosa misura**: Performance su periodo completamente futuro (es. 2021-2023).

**Gold standard**: Testare su dati mai visti durante sviluppo.

**Esempio**:
```
Training: 2012-2018
Testing:  2019-2020 → Sharpe = 1.35
OOS:      2021-2023 → Sharpe = 1.22 (calo minimo, buono!)
```

**Se drasticamente peggiore**: Overfitting a condizioni di mercato specifiche.

---

### 5.4 Regime Change Robustness

**Cosa misura**: Performance in diversi regimi di mercato (bull, bear, lateral).

**Analisi**:
```
Bull Market (2017-2018):   Sharpe = 1.8
Bear Market (2018):        Sharpe = 0.9  (resistente!)
Lateral Market (2015):     Sharpe = 1.1

→ Strategia robusta a vari regimi
```

**Red flag**: Se funziona solo in bull market → non generalizza.

---

## 📊 Dashboard Metriche Consigliato

### Durante Training

```
[Epoch 25/50]
  RL Metrics:
    Avg Reward:    15.34  ↑
    Loss:          0.234  ↓
    Epsilon:       0.156
    Actions:       SHORT: 18%, HOLD: 35%, LONG: 47%

  LLM Metrics:
    Avg Confidence:     2.1
    Avg Strength:       0.68
    Direction Accuracy: 62.5%
```

---

### Dopo Backtesting

```
[Backtest Results - AAPL]
  Trading Performance:
    Sharpe Ratio:      1.45  ✓ (target: >1.3)
    Max Drawdown:      -22%  ✓ (target: <-28%)
    Cumulative Return: 47%
    Win Rate:          58%
    Profit Factor:     1.85

  Ensemble Metrics:
    Chunk Models:      4
    Weight Entropy:    0.72 (good diversity)
    QP Convergence:    98%

  Generalization:
    Train Sharpe:      1.52
    Val Sharpe:        1.48
    Test Sharpe:       1.45  (consistent!)
```

---

## 🎯 Target Metrics per ReWTSE-LLM-RL

| Metrica | Baseline RL | LLM+RL | **Target ReWTSE-LLM-RL** |
|---------|-------------|--------|--------------------------|
| **Sharpe Ratio** | 0.64 | 1.10 | **≥1.30** |
| **Max Drawdown** | -36% | -31% | **≤-28%** |
| **Win Rate** | 52% | 58% | **≥60%** |
| **LLM Direction Acc** | N/A | 58% | **≥65%** |
| **Ensemble Weight Entropy** | N/A | N/A | **≥0.60** |

---

## 📈 Tools per Visualizzazione Metriche

### TensorBoard (per training RL)

```python
from torch.utils.tensorboard import SummaryWriter

writer = SummaryWriter('runs/experiment_1')

# Log metrics durante training
writer.add_scalar('Loss/train', loss, step)
writer.add_scalar('Reward/episode', reward, episode)
writer.add_scalar('Epsilon', epsilon, step)

# Visualizza
# tensorboard --logdir=runs
```

---

### Weights & Biases (avanzato)

```python
import wandb

wandb.init(project="rewts-llm-rl")

wandb.log({
    "train/loss": loss,
    "train/reward": reward,
    "val/sharpe_ratio": sharpe
})
```

---

### Custom Plotting

```python
import matplotlib.pyplot as plt

# Training curves
plt.subplot(2, 2, 1)
plt.plot(rewards)
plt.title('Cumulative Reward')

plt.subplot(2, 2, 2)
plt.plot(losses)
plt.title('Training Loss')

plt.subplot(2, 2, 3)
plt.plot(portfolio_values)
plt.title('Portfolio Value')

plt.subplot(2, 2, 4)
plt.plot(drawdowns)
plt.title('Drawdown')

plt.tight_layout()
plt.savefig('training_metrics.png')
```

---

## 🏁 Conclusione

Le metriche di valutazione AI sono fondamentali per:
1. **Monitorare training**: Convergenza, overfitting, stabilità
2. **Confrontare modelli**: Quale configurazione funziona meglio
3. **Validare generalizzazione**: Funziona su nuovi dati?
4. **Debugging**: Identificare problemi (reward collapse, policy degradation, etc.)
5. **Reporting**: Comunicare risultati in modo scientifico

**Best Practice**:
- Tracciare **tutte** le metriche durante training
- Salvare checkpoint periodici
- Confrontare sempre con baseline
- Testare su out-of-sample data
- Non ottimizzare su test set!

---

Per domande sulle metriche, consulta:
- Paper LLM+RL: Sezione 4 (Evaluation)
- Paper ReWTSE: Sezione 5 (Experiments)
- `AI_Evaluation_Metrics.md`: Questo documento
