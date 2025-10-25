"""
Script per verificare che le API keys siano configurate correttamente
"""

import os
import sys

def mask_key(key: str) -> str:
    """Maschera una API key per visualizzazione sicura"""
    if not key or len(key) < 8:
        return "***"
    return f"{key[:10]}...{key[-4:]}"

def verify_gemini_key():
    """Verifica che Gemini API key sia configurata e funzionante"""
    print("\n" + "="*60)
    print("Verifica Gemini API Key")
    print("="*60)

    api_key = os.getenv('GEMINI_API_KEY')

    if not api_key:
        print("❌ GEMINI_API_KEY non trovata nelle variabili d'ambiente")
        print("\nCome configurarla:")
        print("  1. Copia .env.example in .env")
        print("  2. Ottieni una API key da: https://ai.google.dev/")
        print("  3. Sostituisci 'your_gemini_api_key_here' con la tua key")
        print("  4. Carica il file .env (non fare commit!)")
        return False

    print(f"✓ API Key trovata: {mask_key(api_key)}")

    # Testa la connessione
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        # Test semplice
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Test")

        print("✓ Connessione a Gemini API riuscita")
        print(f"✓ Modello: gemini-2.0-flash-exp funzionante")
        return True

    except ImportError:
        print("⚠ Libreria google-generativeai non installata")
        print("  Esegui: pip install google-generativeai")
        return False
    except Exception as e:
        print(f"❌ Errore nel test API: {str(e)}")
        print("\nPossibili cause:")
        print("  - API key non valida")
        print("  - Quota esaurita")
        print("  - Problemi di rete")
        return False

def verify_optional_keys():
    """Verifica API keys opzionali"""
    print("\n" + "="*60)
    print("API Keys Opzionali")
    print("="*60)

    optional_keys = {
        'ALPACA_API_KEY': 'Paper trading (Alpaca)',
        'ALPACA_SECRET_KEY': 'Paper trading (Alpaca)',
        'FRED_API_KEY': 'Dati macroeconomici (FRED)',
        'SEC_API_KEY': 'Dati SEC filings'
    }

    found_any = False
    for key_name, description in optional_keys.items():
        key_value = os.getenv(key_name)
        if key_value:
            print(f"✓ {key_name}: {mask_key(key_value)}")
            print(f"  Uso: {description}")
            found_any = True

    if not found_any:
        print("ℹ Nessuna API key opzionale configurata")
        print("  (non necessarie per il training base)")

def verify_environment():
    """Verifica l'ambiente di esecuzione"""
    print("\n" + "="*60)
    print("Ambiente di Esecuzione")
    print("="*60)

    # Controlla se siamo su Colab
    try:
        import google.colab
        print("✓ Ambiente: Google Colab")

        # Verifica GPU
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"✓ GPU disponibile: {gpu_name}")
            print(f"✓ Memoria GPU: {gpu_memory:.2f} GB")
        else:
            print("⚠ GPU non disponibile")
            print("  Vai su: Runtime > Change runtime type > GPU")

    except ImportError:
        print("✓ Ambiente: Locale")

        # Verifica PyTorch locale
        try:
            import torch
            if torch.cuda.is_available():
                print(f"✓ GPU disponibile: {torch.cuda.get_device_name(0)}")
            else:
                print("ℹ GPU non disponibile (training sarà più lento)")
        except ImportError:
            print("⚠ PyTorch non installato")

def main():
    """Main verification"""
    print("\n" + "#"*60)
    print("# ReWTS-LLM-RL - Verifica Configurazione")
    print("#"*60)

    # Verifica environment
    verify_environment()

    # Verifica Gemini API key (obbligatoria)
    gemini_ok = verify_gemini_key()

    # Verifica API keys opzionali
    verify_optional_keys()

    # Summary
    print("\n" + "="*60)
    print("Riepilogo")
    print("="*60)

    if gemini_ok:
        print("✅ Configurazione OK - Puoi procedere con il training")
        return 0
    else:
        print("❌ Configurazione incompleta")
        print("\nRisolvi i problemi sopra prima di procedere.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
