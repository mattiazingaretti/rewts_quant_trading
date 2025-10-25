"""
Rate limiting utilities for API calls
"""

import time
import random
from threading import Lock
from collections import deque
from typing import Optional


class RateLimiter:
    """Thread-safe rate limiter per controllare il rate di API calls"""

    def __init__(self, max_per_second: float = 8.0):
        """
        Initialize rate limiter

        Args:
            max_per_second: Massimo numero di richieste per secondo
        """
        self.max_per_second = max_per_second
        self.min_interval = 1.0 / max_per_second
        self.last_request = 0.0
        self.lock = Lock()

    def wait(self):
        """Aspetta se necessario per rispettare il rate limit"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_request

            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                time.sleep(sleep_time)

            self.last_request = time.time()


class RequestMonitor:
    """Monitor per tracciare il rate di richieste in real-time"""

    def __init__(self, window_seconds: int = 60, limit_rpm: int = 1000):
        """
        Initialize request monitor

        Args:
            window_seconds: Finestra temporale per il calcolo (default: 60s = 1 min)
            limit_rpm: Limite di richieste per minuto
        """
        self.window = window_seconds
        self.limit_rpm = limit_rpm
        self.requests = deque()
        self.lock = Lock()

    def record_request(self):
        """Registra una nuova richiesta"""
        with self.lock:
            now = time.time()
            self.requests.append(now)

            # Rimuovi richieste più vecchie della finestra
            cutoff = now - self.window
            while self.requests and self.requests[0] < cutoff:
                self.requests.popleft()

    def get_rate(self) -> int:
        """
        Returns current requests per minute

        Returns:
            Numero di richieste nell'ultimo minuto
        """
        with self.lock:
            # Clean old requests
            now = time.time()
            cutoff = now - self.window
            while self.requests and self.requests[0] < cutoff:
                self.requests.popleft()

            return len(self.requests)

    def get_percent_of_limit(self) -> float:
        """
        Returns percentage of rate limit being used

        Returns:
            Percentuale del limite (0-100)
        """
        rpm = self.get_rate()
        return (rpm / self.limit_rpm) * 100

    def is_approaching_limit(self, threshold: float = 0.9) -> bool:
        """
        Check if we're approaching the rate limit

        Args:
            threshold: Soglia percentuale (default: 0.9 = 90%)

        Returns:
            True se siamo sopra la soglia
        """
        return self.get_percent_of_limit() >= (threshold * 100)

    def print_stats(self):
        """Stampa statistiche correnti"""
        rpm = self.get_rate()
        percent = self.get_percent_of_limit()

        if percent >= 90:
            icon = "🔴"
        elif percent >= 70:
            icon = "🟡"
        else:
            icon = "🟢"

        print(f"{icon} Current rate: {rpm} RPM ({percent:.1f}% of {self.limit_rpm} limit)")


def retry_with_exponential_backoff(
    func,
    max_retries: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 60.0,
    *args,
    **kwargs
):
    """
    Esegui una funzione con retry e exponential backoff

    Args:
        func: Funzione da eseguire
        max_retries: Numero massimo di tentativi
        initial_wait: Tempo di attesa iniziale (secondi)
        max_wait: Tempo di attesa massimo (secondi)
        *args, **kwargs: Argomenti per la funzione

    Returns:
        Risultato della funzione

    Raises:
        Exception se tutti i retry falliscono
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)

        except Exception as e:
            last_exception = e
            error_str = str(e)

            # Check se è un errore 429 (rate limit)
            if '429' in error_str or 'rate limit' in error_str.lower() or 'quota' in error_str.lower():
                # Exponential backoff con jitter
                wait_time = min(
                    initial_wait * (2 ** attempt) + random.uniform(0, 1),
                    max_wait
                )

                print(f"⚠️  Rate limit hit (attempt {attempt + 1}/{max_retries})")
                print(f"   Waiting {wait_time:.1f}s before retry...")
                time.sleep(wait_time)
            else:
                # Se non è un errore di rate limit, re-raise subito
                raise

    # Se arriviamo qui, tutti i retry sono falliti
    print(f"❌ Failed after {max_retries} retries")
    raise last_exception
