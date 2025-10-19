# Training Notebook - Guida all'uso locale

Questo documento spiega come eseguire il notebook di training in locale senza usare Google Colab.

## Prerequisiti

1. **Python 3.8+** installato
2. **Virtual environment** attivo (consigliato)
3. **Dipendenze installate**

## Setup iniziale

### 1. Attiva il virtual environment

Se hai già un virtual environment:

```bash
# Su macOS/Linux
source venv_rewts_llm/bin/activate

# Su Windows
venv_rewts_llm\Scripts\activate
```

### 2. Installa le dipendenze

```bash
# Dalla directory root del progetto
pip install -r requirements.txt
```

### 3. Configura l'API key di Gemini

Hai due opzioni:

**Opzione A: Variabile d'ambiente (consigliata)**

```bash
# Su macOS/Linux
export GEMINI_API_KEY="your-api-key-here"

# Su Windows (PowerShell)
$env:GEMINI_API_KEY="your-api-key-here"

# Su Windows (CMD)
set GEMINI_API_KEY=your-api-key-here
```

**Opzione B: File .env**

Crea un file `.env` nella directory root con:

```
GEMINI_API_KEY=your-api-key-here
```

Puoi ottenere l'API key da: https://makersuite.google.com/app/apikey

### 4. Verifica i dati

Assicurati che i dati preprocessati esistano:

```bash
ls -la data/processed/
```

Dovresti vedere:
- `AAPL_full_data.csv`
- `AAPL_news.csv`

## Esecuzione del Notebook

### Opzione 1: Jupyter Notebook (interfaccia web)

```bash
# Dalla directory notebooks/
jupyter notebook train_rewts_llm_rl.ipynb
```

Si aprirà il browser con l'interfaccia Jupyter. Esegui le celle in ordine.

### Opzione 2: VS Code (se hai l'estensione Jupyter)

1. Apri VS Code
2. Apri il file `notebooks/train_rewts_llm_rl.ipynb`
3. Seleziona il kernel Python (il tuo virtual environment)
4. Esegui le celle cliccando il pulsante play o con Shift+Enter

### Opzione 3: JupyterLab

```bash
# Dalla directory root del progetto
jupyter lab
```

Naviga a `notebooks/train_rewts_llm_rl.ipynb` e esegui le celle.

## Configurazione del Training

Prima di avviare il training, puoi modificare la configurazione nella cella di configurazione:

```python
config = {
    'tickers': ['AAPL'],  # Aggiungi più ticker se necessario

    'rewts': {
        'chunk_length': 500,         # Giorni per chunk (puoi ridurre per test veloci)
        'episodes_per_chunk': 50,    # Episodi di training (50-100 per test, 200+ per produzione)
        # ... altri parametri
    },
}
```

### Per un test rapido:

```python
config['rewts']['chunk_length'] = 200          # Chunk più piccoli
config['rewts']['episodes_per_chunk'] = 10     # Meno episodi
config['strategy_frequency'] = 10              # Strategie più frequenti
```

### Per training completo:

```python
config['rewts']['chunk_length'] = 500
config['rewts']['episodes_per_chunk'] = 100
config['strategy_frequency'] = 20
```

## Tempi di Esecuzione Stimati

Su un computer normale (CPU):

- **Pre-computazione strategie LLM**: 10-30 minuti (dipende dalle chiamate API)
- **Training DDQN per chunk**: 5-15 minuti per chunk
- **Training completo**: 1-3 ore (dipende dal numero di chunk e episodi)

Con GPU:
- Training DDQN: 2-5x più veloce

## Monitoraggio del Training

Durante il training vedrai:

```
============================================================
Training Chunk 0
============================================================
Episode 10/50, Avg Reward: 0.0234, Epsilon: 0.904
Episode 20/50, Avg Reward: 0.0456, Epsilon: 0.818
...
✓ Chunk 0 model saved to models/chunk_0_ddqn.pt
```

## Output del Training

Al termine, troverai nella directory `models/`:

- `AAPL_rewts_ensemble.pkl` - Modello ensemble completo
- `chunk_0_ddqn.pt`, `chunk_1_ddqn.pt`, ... - Singoli modelli DDQN
- `AAPL_checkpoint_YYYYMMDD_HHMMSS.pkl` - Checkpoint con metadata

E in `data/llm_strategies/`:

- `AAPL_strategies.pkl` - Strategie LLM pre-computate

## Troubleshooting

### Errore: "No module named 'src.llm_agents'"

Soluzione: Assicurati di essere nella directory root del progetto, non in `notebooks/`. Il notebook rileva automaticamente questo e cambia directory.

### Errore: "GEMINI_API_KEY not found"

Soluzione:
1. Verifica di aver esportato la variabile d'ambiente
2. Oppure inseriscila manualmente quando richiesto dal notebook

### Errore: "Data file not found"

Soluzione: Esegui prima lo script di preprocessing dei dati:

```bash
python scripts/preprocess_data.py
```

### Training molto lento

Soluzioni:
1. Riduci `episodes_per_chunk` a 10-20 per test
2. Riduci `chunk_length` a 200-300
3. Usa meno ticker (solo AAPL per iniziare)
4. Se disponibile, abilita GPU

### Out of Memory

Soluzioni:
1. Riduci `batch_size` a 32
2. Riduci `buffer_size` a 5000
3. Riduci `chunk_length`

## Prossimi Passi

Dopo il training:

1. **Valuta i risultati** guardando i grafici nell'ultima sezione del notebook
2. **Esegui il backtest** con lo script dedicato
3. **Analizza le performance** dei singoli chunk models
4. **Ottimizza gli iperparametri** basandoti sui risultati

## Risorse Utili

- [Documentazione Jupyter](https://jupyter.org/documentation)
- [Google Gemini API](https://ai.google.dev/docs)
- [PyTorch RL Tutorial](https://pytorch.org/tutorials/intermediate/reinforcement_q_learning.html)

## Supporto

Se riscontri problemi:
1. Controlla i log di errore nel notebook
2. Verifica che tutte le dipendenze siano installate
3. Consulta la documentazione del progetto
