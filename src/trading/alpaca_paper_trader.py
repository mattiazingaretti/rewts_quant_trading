"""
Alpaca Paper Trading Integration
Trading reale con denaro fittizio tramite REST API Alpaca
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import time
import numpy as np


class AlpacaPaperTrader:
    """
    Client per Alpaca Paper Trading API

    Permette di testare strategie nel mondo reale con denaro fittizio (paper trading).
    Alpaca offre paper trading GRATUITO con dati di mercato real-time.
    """

    def __init__(self, api_key: str, secret_key: str, base_url: str = None):
        """
        Inizializza il client Alpaca

        Args:
            api_key: Alpaca API Key (da dashboard.alpaca.markets)
            secret_key: Alpaca Secret Key
            base_url: Base URL (default: paper trading endpoint)
        """
        self.api_key = api_key
        self.secret_key = secret_key

        # Paper Trading endpoint (GRATUITO)
        self.base_url = base_url or "https://paper-api.alpaca.markets"

        # Data API endpoint
        self.data_url = "https://data.alpaca.markets"

        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Content-Type": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Helper per fare richieste HTTP"""
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Metodo HTTP non supportato: {method}")

            response.raise_for_status()
            return response.json() if response.text else {}

        except requests.exceptions.RequestException as e:
            print(f"Errore nella richiesta: {e}")
            if hasattr(e.response, 'text'):
                print(f"Dettagli errore: {e.response.text}")
            raise

    # ========== Account Management ==========

    def get_account(self) -> Dict:
        """
        Ottieni informazioni sull'account paper trading

        Returns:
            Dict con:
            - cash: Denaro disponibile
            - portfolio_value: Valore totale portfolio
            - buying_power: Potere d'acquisto
            - equity: Equity totale
        """
        return self._make_request("GET", "/v2/account")

    def get_account_summary(self) -> Dict:
        """Ottieni un sommario leggibile dell'account"""
        account = self.get_account()

        return {
            'cash': float(account['cash']),
            'portfolio_value': float(account['portfolio_value']),
            'buying_power': float(account['buying_power']),
            'equity': float(account['equity']),
            'last_equity': float(account['last_equity']),
            'profit_loss': float(account['equity']) - float(account['last_equity']),
            'profit_loss_pct': (float(account['equity']) - float(account['last_equity'])) / float(account['last_equity']) * 100 if float(account['last_equity']) > 0 else 0
        }

    # ========== Positions ==========

    def get_positions(self) -> List[Dict]:
        """
        Ottieni tutte le posizioni aperte

        Returns:
            Lista di posizioni con symbol, qty, market_value, etc.
        """
        return self._make_request("GET", "/v2/positions")

    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        Ottieni posizione per uno specifico symbol

        Args:
            symbol: Ticker symbol (es. 'AAPL')

        Returns:
            Dict con dettagli posizione, o None se non esiste
        """
        try:
            return self._make_request("GET", f"/v2/positions/{symbol}")
        except:
            return None

    def close_position(self, symbol: str) -> Dict:
        """
        Chiudi una posizione (vendi tutto)

        Args:
            symbol: Ticker symbol da chiudere

        Returns:
            Order details
        """
        return self._make_request("DELETE", f"/v2/positions/{symbol}")

    def close_all_positions(self) -> List[Dict]:
        """Chiudi TUTTE le posizioni"""
        return self._make_request("DELETE", "/v2/positions")

    # ========== Orders ==========

    def place_order(
        self,
        symbol: str,
        qty: Optional[int] = None,
        notional: Optional[float] = None,
        side: str = "buy",
        type: str = "market",
        time_in_force: str = "day",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Dict:
        """
        Piazza un ordine

        Args:
            symbol: Ticker symbol (es. 'AAPL')
            qty: Numero di azioni (opzionale se usi notional)
            notional: Valore in dollari (opzionale se usi qty)
            side: 'buy' o 'sell'
            type: 'market', 'limit', 'stop', 'stop_limit'
            time_in_force: 'day', 'gtc', 'ioc', 'fok'
            limit_price: Prezzo limite (per ordini limit)
            stop_price: Prezzo stop (per ordini stop)

        Returns:
            Order details
        """
        order_data = {
            "symbol": symbol,
            "side": side,
            "type": type,
            "time_in_force": time_in_force
        }

        if qty is not None:
            order_data["qty"] = qty
        elif notional is not None:
            order_data["notional"] = notional
        else:
            raise ValueError("Devi specificare qty o notional")

        if limit_price is not None:
            order_data["limit_price"] = limit_price
        if stop_price is not None:
            order_data["stop_price"] = stop_price

        return self._make_request("POST", "/v2/orders", order_data)

    def buy_market(self, symbol: str, qty: int) -> Dict:
        """
        Compra azioni a mercato

        Args:
            symbol: Ticker (es. 'AAPL')
            qty: Numero di azioni
        """
        return self.place_order(symbol=symbol, qty=qty, side="buy", type="market")

    def sell_market(self, symbol: str, qty: int) -> Dict:
        """
        Vendi azioni a mercato

        Args:
            symbol: Ticker (es. 'AAPL')
            qty: Numero di azioni
        """
        return self.place_order(symbol=symbol, qty=qty, side="sell", type="market")

    def buy_dollars(self, symbol: str, amount: float) -> Dict:
        """
        Compra azioni per un valore in dollari

        Args:
            symbol: Ticker (es. 'AAPL')
            amount: Importo in dollari (es. 1000.0)
        """
        return self.place_order(symbol=symbol, notional=amount, side="buy", type="market")

    def get_orders(self, status: str = "open", limit: int = 100) -> List[Dict]:
        """
        Ottieni lista ordini

        Args:
            status: 'open', 'closed', 'all'
            limit: Numero massimo ordini da ritornare
        """
        return self._make_request("GET", f"/v2/orders?status={status}&limit={limit}")

    def get_order(self, order_id: str) -> Dict:
        """Ottieni dettagli di un ordine specifico"""
        return self._make_request("GET", f"/v2/orders/{order_id}")

    def cancel_order(self, order_id: str) -> None:
        """Cancella un ordine"""
        return self._make_request("DELETE", f"/v2/orders/{order_id}")

    def cancel_all_orders(self) -> List[Dict]:
        """Cancella TUTTI gli ordini aperti"""
        return self._make_request("DELETE", "/v2/orders")

    # ========== Market Data ==========

    def get_latest_quote(self, symbol: str) -> Dict:
        """
        Ottieni ultima quotazione per un symbol

        Returns:
            Dict con bid, ask, bid_size, ask_size, timestamp
        """
        url = f"{self.data_url}/v2/stocks/{symbol}/quotes/latest"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_latest_trade(self, symbol: str) -> Dict:
        """
        Ottieni ultimo trade per un symbol

        Returns:
            Dict con price, size, timestamp
        """
        url = f"{self.data_url}/v2/stocks/{symbol}/trades/latest"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_bars(
        self,
        symbol: str,
        timeframe: str = "1Day",
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Ottieni dati storici (candlestick bars)

        Args:
            symbol: Ticker
            timeframe: '1Min', '5Min', '15Min', '1Hour', '1Day'
            start: Data inizio (ISO format: '2023-01-01')
            end: Data fine
            limit: Numero massimo bars

        Returns:
            DataFrame con OHLCV data
        """
        url = f"{self.data_url}/v2/stocks/{symbol}/bars"

        params = {
            "timeframe": timeframe,
            "limit": limit
        }
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        data = response.json()

        # Check if data contains bars and bars is not None
        bars = data.get('bars')
        if bars is not None and len(bars) > 0:
            df = pd.DataFrame(bars)
            df['timestamp'] = pd.to_datetime(df['t'])
            df = df.rename(columns={
                'o': 'open',
                'h': 'high',
                'l': 'low',
                'c': 'close',
                'v': 'volume'
            })
            df = df.set_index('timestamp')
            return df[['open', 'high', 'low', 'close', 'volume']]
        else:
            return pd.DataFrame()

    # ========== Portfolio History ==========

    def get_portfolio_history(
        self,
        period: str = "1M",
        timeframe: str = "1D"
    ) -> Dict:
        """
        Ottieni storico portfolio

        Args:
            period: '1D', '1W', '1M', '3M', '1A', 'all'
            timeframe: '1Min', '5Min', '15Min', '1H', '1D'

        Returns:
            Dict con timestamp, equity, profit_loss, etc.
        """
        return self._make_request("GET", f"/v2/account/portfolio/history?period={period}&timeframe={timeframe}")

    # ========== Strategy Execution ==========

    def execute_strategy_signal(self, signal: Dict) -> Dict:
        """
        Esegui un segnale di strategia dal modello ReWTSE-LLM-RL

        Args:
            signal: Dict con:
                - symbol: Ticker
                - action: 'LONG', 'SHORT', 'HOLD'
                - confidence: 0-1
                - portfolio_allocation: percentuale del portfolio da allocare

        Returns:
            Dict con risultato dell'esecuzione
        """
        symbol = signal['symbol']
        action = signal['action']
        allocation = signal.get('portfolio_allocation', 0.1)  # Default 10%

        # Ottieni info account
        account = self.get_account()
        buying_power = float(account['buying_power'])

        # Ottieni posizione corrente
        current_position = self.get_position(symbol)

        result = {
            'symbol': symbol,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'executed': False,
            'order_id': None,
            'message': ''
        }

        if action == 'LONG':
            # Chiudi posizione short se presente
            if current_position and float(current_position.get('qty', 0)) < 0:
                self.close_position(symbol)
                result['message'] += f"Chiusa posizione SHORT. "

            # Apri posizione LONG
            amount_to_invest = buying_power * allocation

            if amount_to_invest >= 1.0:  # Minimo $1
                order = self.buy_dollars(symbol, amount_to_invest)
                result['executed'] = True
                result['order_id'] = order['id']
                result['message'] += f"Apertura LONG: ${amount_to_invest:.2f}"
            else:
                result['message'] = "Buying power insufficiente"

        elif action == 'SHORT':
            # Chiudi posizione long se presente
            if current_position and float(current_position.get('qty', 0)) > 0:
                self.close_position(symbol)
                result['message'] += f"Chiusa posizione LONG. "

            result['message'] += "SHORT non implementato in paper trading (richiede margin)"

        elif action == 'HOLD':
            result['message'] = "HOLD - nessuna azione"

        return result


class AlpacaPaperTradingBackend:
    """
    Backend per integrare Alpaca Paper Trading con ReWTSE-LLM-RL
    """

    def __init__(self, api_key: str, secret_key: str):
        self.trader = AlpacaPaperTrader(api_key, secret_key)
        self.portfolio_history = []

    def run_live_trading(
        self,
        ensemble,
        ticker: str,
        check_interval: int = 60,
        max_iterations: Optional[int] = None
    ):
        """
        Esegui trading live con Alpaca usando l'ensemble ReWTSE

        Args:
            ensemble: ReWTSEnsembleController addestrato
            ticker: Symbol da tradare
            check_interval: Secondi tra ogni check (default: 60)
            max_iterations: Numero massimo iterazioni (None = infinito)
        """
        print(f"🚀 Avvio live trading per {ticker}")
        print(f"Check interval: {check_interval}s")
        print(f"=" * 60)

        iteration = 0

        try:
            while max_iterations is None or iteration < max_iterations:
                iteration += 1
                print(f"\n[Iteration {iteration}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                # 1. Ottieni dati di mercato real-time
                try:
                    bars = self.trader.get_bars(ticker, timeframe="1Day", limit=200)

                    if bars is None or bars.empty:
                        print(f"⚠️ Nessun dato disponibile per {ticker}")
                        print(f"   Possibile causa: mercato chiuso o ticker non valido")
                        time.sleep(check_interval)
                        continue

                    if len(bars) < 50:
                        print(f"⚠️ Dati insufficienti per {ticker} (solo {len(bars)} bars)")
                        print(f"   Richiesti almeno 50 bars per calcolare indicatori")
                        time.sleep(check_interval)
                        continue

                    # 2. Prepara observation per l'ensemble
                    # (semplificato - in produzione calcolare tutti gli indicatori)
                    latest_close = bars['close'].iloc[-1]
                    latest_volume = bars['volume'].iloc[-1]

                    observation = self._prepare_observation(bars)

                    # 3. Ottieni predizione dall'ensemble
                    action, q_values = ensemble.predict_ensemble(observation)

                    # Mapping azioni: 0=SHORT, 1=HOLD, 2=LONG
                    action_name = ['SHORT', 'HOLD', 'LONG'][action]

                    print(f"📊 Close: ${latest_close:.2f} | Volume: {latest_volume:,.0f}")
                    print(f"🤖 Azione predetta: {action_name}")
                    print(f"Q-values: SHORT={q_values[0]:.3f}, HOLD={q_values[1]:.3f}, LONG={q_values[2]:.3f}")

                    # 4. Esegui azione su Alpaca
                    signal = {
                        'symbol': ticker,
                        'action': action_name,
                        'confidence': max(q_values),
                        'portfolio_allocation': 0.2  # 20% del portfolio
                    }

                    result = self.trader.execute_strategy_signal(signal)

                    if result['executed']:
                        print(f"✅ {result['message']}")
                    else:
                        print(f"ℹ️ {result['message']}")

                    # 5. Monitora portfolio
                    account_summary = self.trader.get_account_summary()
                    print(f"\n💰 Portfolio:")
                    print(f"   Cash: ${account_summary['cash']:,.2f}")
                    print(f"   Portfolio Value: ${account_summary['portfolio_value']:,.2f}")
                    print(f"   Profit/Loss: ${account_summary['profit_loss']:,.2f} ({account_summary['profit_loss_pct']:.2f}%)")

                    # Salva storico
                    self.portfolio_history.append({
                        'timestamp': datetime.now(),
                        'ticker': ticker,
                        'action': action_name,
                        'portfolio_value': account_summary['portfolio_value'],
                        'profit_loss': account_summary['profit_loss']
                    })

                except Exception as e:
                    print(f"❌ Errore durante l'iterazione: {e}")

                # 6. Attendi prossimo check
                print(f"\n⏳ Prossimo check tra {check_interval}s...")
                time.sleep(check_interval)

        except KeyboardInterrupt:
            print("\n\n🛑 Trading interrotto dall'utente")
            self._save_history()

    def _prepare_observation(self, bars: pd.DataFrame) -> np.ndarray:
        """Prepara observation vector dai bars"""
        import numpy as np

        # Calcola indicatori base
        close = bars['close'].iloc[-1]
        volume = bars['volume'].iloc[-1]
        sma_20 = bars['close'].rolling(20).mean().iloc[-1]
        sma_50 = bars['close'].rolling(50).mean().iloc[-1]

        # RSI semplificato
        delta = bars['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]

        # Observation vector (semplificato)
        obs = np.array([
            close / 100.0,
            volume / 1e6,
            0.2,  # HV placeholder
            sma_20 / close if close > 0 else 1.0,
            sma_50 / close if close > 0 else 1.0,
            1.0,  # SMA_200 placeholder
            rsi / 100.0,
            0.0,  # MACD placeholder
            0.0,  # LLM signal placeholder
            1.0,  # Portfolio value placeholder
            0    # Position placeholder
        ], dtype=np.float32)

        return obs

    def _save_history(self):
        """Salva storico portfolio"""
        if self.portfolio_history:
            df = pd.DataFrame(self.portfolio_history)
            filename = f"alpaca_trading_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(f"results/metrics/{filename}", index=False)
            print(f"✅ Storico salvato in: results/metrics/{filename}")
