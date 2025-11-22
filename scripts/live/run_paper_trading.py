"""
Script per eseguire Paper Trading Real-Time con Alpaca
"""

import sys
import os
import pickle
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.trading.alpaca_paper_trader import AlpacaPaperTrader, AlpacaPaperTradingBackend


def test_alpaca_connection(api_key: str, secret_key: str):
    """Testa la connessione ad Alpaca"""
    print("🔍 Testing Alpaca connection...")
    print("=" * 60)

    trader = AlpacaPaperTrader(api_key, secret_key)

    try:
        # Test account access
        account = trader.get_account_summary()
        print("✅ Connessione riuscita!")
        print(f"\n💰 Account Summary:")
        print(f"   Cash: ${account['cash']:,.2f}")
        print(f"   Portfolio Value: ${account['portfolio_value']:,.2f}")
        print(f"   Buying Power: ${account['buying_power']:,.2f}")
        print(f"   Equity: ${account['equity']:,.2f}")

        # Test positions
        positions = trader.get_positions()
        print(f"\n📊 Posizioni aperte: {len(positions)}")
        for pos in positions:
            print(f"   {pos['symbol']}: {pos['qty']} shares @ ${pos['current_price']}")

        # Test orders
        orders = trader.get_orders(status='open')
        print(f"\n📋 Ordini aperti: {len(orders)}")

        return True

    except Exception as e:
        print(f"❌ Errore di connessione: {e}")
        return False


def run_paper_trading(
    api_key: str,
    secret_key: str,
    ticker: str = 'AAPL',
    model_path: str = None,
    check_interval: int = 300,  # 5 minuti
    max_iterations: int = None
):
    """
    Esegui paper trading real-time

    Args:
        api_key: Alpaca API Key
        secret_key: Alpaca Secret Key
        ticker: Ticker da tradare
        model_path: Path al modello ensemble salvato
        check_interval: Secondi tra ogni check
        max_iterations: Numero massimo iterazioni (None = infinito)
    """
    print(f"🚀 Avvio Paper Trading per {ticker}")
    print("=" * 60)

    # 1. Test connessione
    if not test_alpaca_connection(api_key, secret_key):
        print("\n❌ Impossibile connettersi ad Alpaca. Verifica le credenziali.")
        return

    # 2. Carica modello ensemble
    if model_path is None:
        model_path = f"models/{ticker}_rewts_ensemble.pkl"

    print(f"\n📦 Caricamento modello da: {model_path}")

    try:
        with open(model_path, 'rb') as f:
            ensemble = pickle.load(f)
        print("✅ Modello caricato con successo!")
        print(f"   Chunk models: {len(ensemble.chunk_models)}")
    except FileNotFoundError:
        print(f"❌ Modello non trovato: {model_path}")
        print("   Esegui prima: python scripts/train_rewts_llm_rl.py")
        return

    # 3. Inizializza backend
    backend = AlpacaPaperTradingBackend(api_key, secret_key)

    # 4. Avvia trading loop
    print(f"\n🔄 Avvio trading loop...")
    print(f"   Check interval: {check_interval}s ({check_interval/60:.1f} minuti)")
    print(f"   Max iterations: {'Infinito' if max_iterations is None else max_iterations}")
    print("\n⚠️ Premi Ctrl+C per interrompere\n")

    backend.run_live_trading(
        ensemble=ensemble,
        ticker=ticker,
        check_interval=check_interval,
        max_iterations=max_iterations
    )


def demo_manual_trading(api_key: str, secret_key: str):
    """Demo di trading manuale con Alpaca"""
    print("🎮 Demo: Trading Manuale con Alpaca")
    print("=" * 60)

    trader = AlpacaPaperTrader(api_key, secret_key)

    # 1. Check account
    account = trader.get_account_summary()
    print(f"\n💰 Starting Balance: ${account['portfolio_value']:,.2f}")

    # 2. Place demo orders
    print("\n📝 Piazzando ordine demo...")

    try:
        # Compra $100 di AAPL
        order = trader.buy_dollars('AAPL', 100.0)
        print(f"✅ Ordine piazzato:")
        print(f"   Order ID: {order['id']}")
        print(f"   Symbol: {order['symbol']}")
        print(f"   Side: {order['side']}")
        print(f"   Notional: ${order.get('notional', 'N/A')}")
        print(f"   Status: {order['status']}")

        # Wait for order to fill
        print("\n⏳ Attendendo esecuzione ordine...")
        import time
        time.sleep(5)

        # Check position
        position = trader.get_position('AAPL')
        if position:
            print(f"\n📊 Posizione aperta:")
            print(f"   Symbol: {position['symbol']}")
            print(f"   Qty: {position['qty']}")
            print(f"   Avg Entry Price: ${position['avg_entry_price']}")
            print(f"   Current Price: ${position['current_price']}")
            print(f"   Market Value: ${position['market_value']}")
            print(f"   Unrealized P/L: ${position['unrealized_pl']} ({position['unrealized_plpc']}%)")

        # Final account
        account_final = trader.get_account_summary()
        print(f"\n💰 Final Balance: ${account_final['portfolio_value']:,.2f}")
        print(f"   Profit/Loss: ${account_final['profit_loss']:,.2f}")

    except Exception as e:
        print(f"❌ Errore: {e}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Alpaca Paper Trading per ReWTSE-LLM-RL')

    parser.add_argument('--mode', type=str, default='test',
                        choices=['test', 'run', 'demo'],
                        help='Modalità: test (test connessione), run (trading live), demo (demo manuale)')

    parser.add_argument('--api-key', type=str, required=False,
                        help='Alpaca API Key (o usa ALPACA_API_KEY env var)')

    parser.add_argument('--secret-key', type=str, required=False,
                        help='Alpaca Secret Key (o usa ALPACA_SECRET_KEY env var)')

    parser.add_argument('--ticker', type=str, default='AAPL',
                        help='Ticker da tradare (default: AAPL)')

    parser.add_argument('--model', type=str, default=None,
                        help='Path al modello ensemble (default: models/{ticker}_rewts_ensemble.pkl)')

    parser.add_argument('--interval', type=int, default=300,
                        help='Intervallo check in secondi (default: 300 = 5 minuti)')

    parser.add_argument('--max-iter', type=int, default=None,
                        help='Numero massimo iterazioni (default: infinito)')

    args = parser.parse_args()

    # Get API keys from args or environment
    # Support both ALPACA_API_KEY and ALPACA_KEY for backward compatibility
    api_key = args.api_key or os.getenv('ALPACA_API_KEY') or os.getenv('ALPACA_KEY')
    secret_key = args.secret_key or os.getenv('ALPACA_SECRET_KEY') or os.getenv('ALPACA_SECRET')

    if not api_key or not secret_key:
        print("❌ Errore: API keys mancanti!")
        print("\nOpzioni:")
        print("1. Aggiungi al file .env nella directory root:")
        print("   ALPACA_KEY=your_key")
        print("   ALPACA_SECRET=your_secret")
        print("   (oppure ALPACA_API_KEY e ALPACA_SECRET_KEY)")
        print("\n2. Passa come argomenti: --api-key YOUR_KEY --secret-key YOUR_SECRET")
        print("\n3. Imposta environment variables:")
        print("   export ALPACA_KEY=your_key")
        print("   export ALPACA_SECRET=your_secret")
        print("\n📚 Ottieni le keys gratuite su: https://app.alpaca.markets/paper/dashboard/overview")
        return

    # Execute based on mode
    if args.mode == 'test':
        test_alpaca_connection(api_key, secret_key)

    elif args.mode == 'run':
        run_paper_trading(
            api_key=api_key,
            secret_key=secret_key,
            ticker=args.ticker,
            model_path=args.model,
            check_interval=args.interval,
            max_iterations=args.max_iter
        )

    elif args.mode == 'demo':
        demo_manual_trading(api_key, secret_key)


if __name__ == '__main__':
    main()
