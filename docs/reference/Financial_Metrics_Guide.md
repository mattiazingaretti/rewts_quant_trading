# Guida alle Metriche Finanziarie
## Spiegazione Semplice delle Metriche Utilizzate dagli Agent LLM

Questo documento spiega in termini semplici tutte le metriche finanziarie utilizzate dagli agenti LLM (Strategist e Analyst) nel sistema ReWTSE-LLM-RL.

---

## 📊 Dati di Mercato (Market Data)

### Close Price (Prezzo di Chiusura)
**Cosa significa**: Il prezzo finale a cui un'azione viene scambiata alla fine della giornata di trading.

**Come usarlo**:
- Prezzo in aumento = trend positivo
- Prezzo in diminuzione = trend negativo
- Usato come riferimento principale per tutti i calcoli

**Esempio**: Se AAPL chiude a $150, significa che l'ultimo scambio del giorno è avvenuto a quel prezzo.

---

### Volume
**Cosa significa**: Il numero totale di azioni scambiate in un giorno.

**Come usarlo**:
- Volume alto + prezzo in salita = forte interesse all'acquisto
- Volume alto + prezzo in discesa = forte interesse alla vendita
- Volume basso = poca attività, segnale debole

**Esempio**: 50 milioni di azioni scambiate indica un'attività molto alta.

---

### Beta (β)
**Cosa significa**: Misura quanto un'azione si muove rispetto al mercato generale (S&P 500).

**Come usarlo**:
- Beta = 1: L'azione si muove come il mercato
- Beta > 1: L'azione è più volatile del mercato (es. Beta = 1.5 significa 50% più volatile)
- Beta < 1: L'azione è meno volatile del mercato

**Esempio**: TSLA ha spesso Beta > 1.5 (molto volatile), mentre KO (Coca-Cola) ha Beta < 1 (stabile).

---

### Historical Volatility (HV) - Volatilità Storica
**Cosa significa**: Misura quanto il prezzo di un'azione è variato nel passato.

**Come usarlo**:
- HV alta = prezzo si muove molto (rischio alto, potenziale guadagno alto)
- HV bassa = prezzo stabile (rischio basso, movimenti limitati)

**Esempio**: HV del 30% annualizzato significa che il prezzo potrebbe variare del ±30% in un anno.

---

### Implied Volatility (IV) - Volatilità Implicita
**Cosa significa**: Aspettativa del mercato su quanto il prezzo varierà in futuro, derivata dai prezzi delle opzioni.

**Come usarlo**:
- IV alta = mercato si aspetta grandi movimenti (incertezza)
- IV bassa = mercato si aspetta stabilità
- IV > HV = mercato nervoso, possibile evento in arrivo

**Esempio**: Prima di un earnings report, la IV aumenta perché il mercato si aspetta un grande movimento.

---

## 📈 Analisi Tecnica (Technical Analysis)

### Moving Averages (MA) - Medie Mobili
**Cosa significa**: La media del prezzo di chiusura calcolata su un certo numero di giorni.

**Tipi**:
- **SMA_20**: Media mobile a 20 giorni (circa 1 mese)
- **SMA_50**: Media mobile a 50 giorni (circa 2-3 mesi)
- **SMA_200**: Media mobile a 200 giorni (circa 1 anno)

**Come usarle**:
- Prezzo > MA = trend rialzista
- Prezzo < MA = trend ribassista
- Golden Cross: SMA_50 incrocia sopra SMA_200 = segnale di acquisto forte
- Death Cross: SMA_50 incrocia sotto SMA_200 = segnale di vendita forte

**Esempio**: Se AAPL è a $150 e SMA_50 è $140, il trend è positivo.

---

### MA Slopes (Pendenze delle Medie Mobili)
**Cosa significa**: La velocità con cui la media mobile sta salendo o scendendo.

**Come usarle**:
- Slope positiva e ripida = trend rialzista forte
- Slope negativa e ripida = trend ribassista forte
- Slope piatta = lateralizzazione, indecisione

**Esempio**: SMA_20_Slope = +2 significa che la media sta salendo rapidamente.

---

### RSI (Relative Strength Index)
**Cosa significa**: Indicatore di momentum che misura se un'azione è ipercomprata o ipervenduta.

**Range**: 0 - 100

**Come usarlo**:
- RSI > 70 = **Ipercomprato** → possibile correzione al ribasso
- RSI < 30 = **Ipervenduto** → possibile rimbalzo al rialzo
- RSI = 50 = neutrale

**Esempio**: RSI = 85 per TSLA significa che è molto ipercomprata, potrebbe scendere presto.

---

### MACD (Moving Average Convergence Divergence)
**Cosa significa**: Indicatore di trend e momentum basato sulla differenza tra due medie mobili esponenziali.

**Componenti**:
- **MACD Line**: Differenza tra EMA a 12 e 26 giorni
- **Signal Line**: Media mobile a 9 giorni del MACD
- **MACD Histogram**: Differenza tra MACD e Signal

**Come usarlo**:
- MACD incrocia sopra Signal Line = segnale di acquisto
- MACD incrocia sotto Signal Line = segnale di vendita
- Histogram positivo = momentum rialzista

**Esempio**: MACD = 2.5, Signal = 2.0 → MACD sopra Signal, segnale bullish.

---

### ATR (Average True Range)
**Cosa significa**: Misura la volatilità media del prezzo, utile per setting stop-loss.

**Come usarlo**:
- ATR alto = grande volatilità, mercato nervoso
- ATR basso = volatilità ridotta, mercato calmo
- Usato per determinare la dimensione delle posizioni

**Esempio**: ATR = $5 per AAPL significa che il prezzo varia mediamente di $5 al giorno.

---

## 💰 Dati Fondamentali (Fundamental Data)

### P/E Ratio (Price-to-Earnings)
**Cosa significa**: Rapporto tra il prezzo dell'azione e gli utili per azione (EPS).

**Formula**: P/E = Prezzo / EPS

**Come usarlo**:
- P/E alto (>25) = azione cara, aspettative di crescita alte
- P/E basso (<15) = azione economica o sottovalutata
- P/E negativo = azienda in perdita

**Esempio**: P/E = 30 per TSLA significa che gli investitori pagano $30 per ogni $1 di utile.

---

### Debt-to-Equity Ratio (Rapporto Debito/Patrimonio Netto)
**Cosa significa**: Quanto debito ha un'azienda rispetto al suo patrimonio netto.

**Formula**: Debt-to-Equity = Debito Totale / Patrimonio Netto

**Come usarlo**:
- Ratio < 1 = azienda con poco debito (più sicura)
- Ratio > 2 = azienda molto indebitata (rischio più alto)

**Esempio**: Ratio = 0.5 significa che l'azienda ha $0.50 di debito per ogni $1 di equity.

---

### Current Ratio (Rapporto di Liquidità)
**Cosa significa**: Capacità di un'azienda di pagare i debiti a breve termine con le attività correnti.

**Formula**: Current Ratio = Attività Correnti / Passività Correnti

**Come usarlo**:
- Ratio > 2 = ottima liquidità
- Ratio tra 1-2 = liquidità sufficiente
- Ratio < 1 = problemi di liquidità, rischio insolvenza

**Esempio**: Ratio = 1.5 significa che l'azienda ha $1.50 di attività per ogni $1 di debito a breve termine.

---

### Gross Margin (Margine Lordo)
**Cosa significa**: Percentuale di ricavi che rimane dopo aver sottratto i costi diretti di produzione.

**Formula**: Gross Margin = (Ricavi - Costo del Venduto) / Ricavi

**Come usarlo**:
- Margin alto (>50%) = business molto profittevole (es. software)
- Margin basso (<20%) = business a basso margine (es. retail)

**Esempio**: Gross Margin = 60% per Apple significa che trattiene $0.60 per ogni $1 di vendita.

---

### Operating Margin (Margine Operativo)
**Cosa significa**: Percentuale di ricavi che rimane dopo tutte le spese operative (ma prima di tasse e interessi).

**Formula**: Operating Margin = Utile Operativo / Ricavi

**Come usarlo**:
- Margin positivo = azienda profittevole nelle operazioni
- Margin in crescita = efficienza in miglioramento
- Margin negativo = azienda in perdita operativa

**Esempio**: Operating Margin = 25% significa che l'azienda genera $0.25 di utile operativo per ogni $1 di vendita.

---

### ROE (Return on Equity)
**Cosa significa**: Rendimento generato sul capitale investito dagli azionisti.

**Formula**: ROE = Utile Netto / Patrimonio Netto

**Come usarlo**:
- ROE > 15% = ottimo rendimento per gli azionisti
- ROE < 10% = rendimento modesto
- ROE negativo = azienda in perdita

**Esempio**: ROE = 20% significa che l'azienda genera $0.20 di utile per ogni $1 di equity.

---

### EPS YoY (Earnings Per Share Year-over-Year)
**Cosa significa**: Variazione percentuale degli utili per azione rispetto all'anno precedente.

**Come usarlo**:
- EPS YoY positivo = crescita degli utili
- EPS YoY > 10% = forte crescita
- EPS YoY negativo = calo degli utili

**Esempio**: EPS YoY = 15% significa che gli utili per azione sono cresciuti del 15% rispetto all'anno scorso.

---

### Net Income YoY (Variazione Utile Netto Anno su Anno)
**Cosa significa**: Variazione percentuale dell'utile netto rispetto all'anno precedente.

**Come usarlo**:
- Positivo = azienda in crescita
- Negativo = azienda in difficoltà
- Confronta con crescita ricavi per vedere efficienza

**Esempio**: Net Income YoY = 20% significa che l'utile netto è cresciuto del 20%.

---

## 🌍 Dati Macro-Economici (Macro Data)

### SPX (S&P 500 Index)
**Cosa significa**: Indice delle 500 maggiori aziende USA, rappresenta lo stato generale del mercato.

**Come usarlo**:
- SPX in salita = mercato bullish (Risk-On)
- SPX in discesa = mercato bearish (Risk-Off)
- SPX_Slope positiva = momentum positivo del mercato

**Esempio**: SPX = 4500 e in salita = buon momento per investire in growth stocks.

---

### VIX (Volatility Index)
**Cosa significa**: "Indice della paura" - misura la volatilità attesa del mercato nei prossimi 30 giorni.

**Come usarlo**:
- VIX < 15 = mercato calmo, bassa paura
- VIX 15-25 = volatilità normale
- VIX > 25 = mercato nervoso, alta incertezza
- VIX > 40 = panico estremo

**Esempio**: VIX = 35 durante una crisi significa che il mercato è molto nervoso.

---

### GDP (Gross Domestic Product) - PIL
**Cosa significa**: Valore totale di beni e servizi prodotti da un paese, misura la salute dell'economia.

**Come usarlo**:
- GDP QoQ positivo = economia in crescita → bullish per azioni
- GDP QoQ negativo = economia in contrazione → bearish
- 2 trimestri consecutivi negativi = recessione

**Esempio**: GDP QoQ = 2.5% significa che l'economia è cresciuta del 2.5% rispetto al trimestre precedente.

---

### PMI (Purchasing Managers Index)
**Cosa significa**: Indice che misura la salute del settore manifatturiero.

**Range**: 0 - 100

**Come usarlo**:
- PMI > 50 = settore in espansione → bullish
- PMI < 50 = settore in contrazione → bearish
- PMI > 55 = forte espansione

**Esempio**: PMI = 58 indica una forte crescita nel settore manifatturiero.

---

### PPI (Producer Price Index) - Indice Prezzi alla Produzione
**Cosa significa**: Misura l'inflazione a livello di produttori (prima che arrivi ai consumatori).

**Come usarlo**:
- PPI in aumento = inflazione in crescita → possibile rialzo tassi
- PPI in calo = pressioni inflazionistiche in diminuzione
- PPI alto danneggia i margini delle aziende

**Esempio**: PPI YoY = 5% significa che i prezzi alla produzione sono saliti del 5% rispetto all'anno scorso.

---

### Treasury Yields (Rendimenti Titoli di Stato USA)
**Cosa significa**: Tasso di interesse pagato dai titoli di stato USA (considerati risk-free).

**Tipi**:
- **10-Year Treasury**: Più comune, usato come benchmark

**Come usarlo**:
- Yields in aumento = bond più attraenti → denaro esce dalle azioni
- Yields in calo = azioni più attraenti
- Yields > 4% = forte concorrenza per le azioni

**Esempio**: Treasury Yields = 4.5% significa che puoi guadagnare il 4.5% annuo senza rischio, quindi le azioni devono offrire di più.

---

### CCI (Consumer Confidence Index)
**Cosa significa**: Misura quanto i consumatori sono ottimisti sull'economia.

**Come usarlo**:
- CCI alto = consumatori fiduciosi → spenderanno di più → bullish per retail/consumer stocks
- CCI basso = consumatori preoccupati → spenderanno meno → bearish

**Esempio**: CCI = 110 indica che i consumatori sono molto fiduciosi.

---

## 📰 Dati News e Sentiment

### News Sentiment (Sentimento delle News)
**Cosa significa**: Tono generale delle notizie (positivo, negativo, neutro).

**Scala**: -1 (molto negativo), 0 (neutro), +1 (molto positivo)

**Come usarlo**:
- Sentiment positivo = aspettative positive → segnale di acquisto
- Sentiment negativo = aspettative negative → segnale di vendita
- Sentiment neutro = nessun segnale chiaro

**Esempio**: Sentiment = +0.8 dopo un earnings beat significa mercato molto ottimista.

---

### News Impact Score (Punteggio Impatto News)
**Cosa significa**: Quanto una notizia può influenzare il prezzo dell'azione.

**Scala Likert**: 1 (basso impatto), 2 (medio impatto), 3 (alto impatto)

**Come usarlo**:
- Impact = 3 + Sentiment positivo = forte segnale di acquisto
- Impact = 3 + Sentiment negativo = forte segnale di vendita
- Impact = 1 = notizia poco rilevante, ignorala

**Esempio**: "Apple acquisisce startup AI" → Impact = 3, Sentiment = +1.

---

## 📊 Metriche di Performance (Backtesting)

### Sharpe Ratio
**Cosa significa**: Misura il rendimento aggiustato per il rischio. Più alto è meglio.

**Formula**: Sharpe = (Rendimento - Risk-Free Rate) / Volatilità

**Come interpretarlo**:
- Sharpe < 1 = rendimento scarso per il rischio preso
- Sharpe 1-2 = buon rendimento
- Sharpe > 2 = eccellente rendimento
- Sharpe > 3 = straordinario (raro)

**Esempio**: Sharpe = 1.5 significa che guadagni 1.5 unità di rendimento per ogni unità di rischio.

---

### Max Drawdown (Massimo Ribasso)
**Cosa significa**: La massima perdita percentuale dal picco al minimo durante un periodo.

**Come interpretarlo**:
- Max Drawdown -10% = piccola perdita, strategia resiliente
- Max Drawdown -20% = perdita moderata
- Max Drawdown -50% = grande perdita, strategia molto rischiosa

**Esempio**: Max Drawdown = -25% significa che a un certo punto hai perso il 25% dal tuo picco massimo.

---

### Cumulative Return (Rendimento Cumulativo)
**Cosa significa**: Il guadagno/perdita totale percentuale dall'inizio alla fine del periodo.

**Come interpretarlo**:
- Positivo = hai guadagnato
- Negativo = hai perso
- Confronta con benchmark (es. S&P 500) per vedere se hai battuto il mercato

**Esempio**: Cumulative Return = 45% significa che il tuo capitale è cresciuto del 45%.

---

## 🎯 Come gli Agenti LLM Usano Queste Metriche

### Strategist Agent
L'agente Strategist combina tutte queste metriche per generare una strategia mensile (LONG o SHORT):

1. **Stock Analysis**: Confronta Close con MA, analizza Weekly Returns, valuta HV e IV
2. **Technical Analysis**: Usa RSI, MACD, MA slopes per identificare momentum
3. **Fundamental Analysis**: Valuta salute finanziaria con ratios e margins
4. **Macro Analysis**: Considera SPX, VIX, GDP, PMI per il contesto macroeconomico
5. **News Analysis**: Integra News Sentiment e Impact Score

### Analyst Agent
L'agente Analyst processa le news e genera:
- Top 3 fattori più rilevanti
- Sentiment per ogni fattore (-1, 0, +1)
- Market Impact Score (1-3)
- Aggregate Sentiment e Impact complessivo

---

## 📚 Risorse per Approfondire

- **Technical Analysis**: "Technical Analysis of the Financial Markets" - John Murphy
- **Fundamental Analysis**: "The Intelligent Investor" - Benjamin Graham
- **Macro Economics**: Federal Reserve Economic Data (FRED) - https://fred.stlouisfed.org
- **Options & Volatility**: "Option Volatility and Pricing" - Sheldon Natenberg

---

**Nota**: Questo documento è pensato per chi non ha esperienza finanziaria. Le metriche sono spiegate in modo semplificato per facilitare la comprensione del funzionamento degli agenti LLM nel sistema di trading.
