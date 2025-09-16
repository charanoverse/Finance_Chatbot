import time
import json
import logging
import requests
import yfinance as yf
from datetime import datetime
from dateutil import tz
from cachetools import TTLCache, cached
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .llm import call_llm  # reuse Gemini wrapper

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# caching
STOCK_CACHE = TTLCache(maxsize=1024, ttl=30)      # 30 seconds for stock data
FD_CACHE = TTLCache(maxsize=128, ttl=3600)        # 1 hour for FD rates
MF_CACHE = TTLCache(maxsize=128, ttl=12 * 3600)   # 12 hours for MF NAV (updates daily after 9PM IST)

class RealtimeFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://www.nseindia.com/"
        })
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self._bootstrap_session()

    def _bootstrap_session(self):
        try:
            self.session.get("https://www.nseindia.com", timeout=5)
            time.sleep(0.1)
        except Exception as e:
            log.debug("bootstrap session failed: %s", e)

    # -------------------------
    # Stocks
    # -------------------------
    @cached(STOCK_CACHE)
    def fetch_stock_price(self, symbol: str):
        symbol = symbol.strip().upper()
        timestamp = datetime.now(tz=tz.tzlocal()).isoformat()

        # 1) NSE API
        try:
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            resp = self.session.get(url, timeout=8)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    price_info = data.get("priceInfo") or {}
                    ltp = price_info.get("lastPrice")
                    if ltp is not None:
                        return {
                            "ticker": symbol,
                            "price": float(ltp),
                            "currency": "INR",
                            "timestamp": timestamp,
                            "source": "nseindia"
                        }
                except ValueError:
                    log.debug("NSE returned non-JSON for %s", symbol)
        except Exception as e:
            log.debug("NSE request failed for %s: %s", symbol, e)

        # 2) yfinance fallback
        try:
            yf_ticker = symbol + ".NS"
            t = yf.Ticker(yf_ticker)
            hist = t.history(period="1d")
            if hist is not None and not hist.empty:
                price = hist["Close"].iloc[-1]
                return {
                    "ticker": symbol,
                    "price": round(float(price), 2),
                    "currency": "INR",
                    "timestamp": timestamp,
                    "source": "yfinance"
                }
            info = getattr(t, "info", {})
            reg = info.get("regularMarketPrice") or info.get("previousClose")
            if reg:
                return {
                    "ticker": symbol,
                    "price": round(float(reg), 2),
                    "currency": "INR",
                    "timestamp": timestamp,
                    "source": "yfinance"
                }
        except Exception as e:
            log.debug("yfinance fallback failed for %s: %s", symbol, e)

        # 3) failure
        return {
            "ticker": symbol,
            "price": None,
            "currency": "INR",
            "timestamp": timestamp,
            "source": "none",
            "note": "No data from NSE or yfinance"
        }

    # -------------------------
    # FD rates (Gemini)
    # -------------------------
    @cached(FD_CACHE)
    def fetch_fd_rates(self, bank_keys: tuple):
        results = []
        for bank in bank_keys:
            prompt = (
                f"Provide the latest Fixed Deposit (FD) interest rates for {bank} bank in India. "
                f"Return a JSON object exactly like this:\n"
                f'{{"bank": "{bank}", "1yr": "x%", "2yr": "y%", "5yr": "z%"}}\n'
                f"No explanation, only valid JSON."
            )
            try:
                answer = call_llm([{"role": "user", "content": prompt}])
                try:
                    parsed = json.loads(answer)
                except Exception:
                    parsed = {"bank": bank, "rates_raw": answer}

                parsed["source"] = "gemini"
                parsed["timestamp"] = datetime.now(tz=tz.tzlocal()).isoformat()
                results.append(parsed)
            except Exception as e:
                results.append({"bank": bank, "error": str(e)})
        return results

    # -------------------------
    # Mutual fund NAV (via AMFI)
    # -------------------------
    @cached(MF_CACHE)
    def fetch_mf_nav(self, scheme_identifier: str):
        """
        Fetch NAV for a given mutual fund using AMFI data.
        scheme_identifier can be either scheme code (e.g., "120503") or scheme name (e.g., "Axis Bluechip Fund").
        """
        scheme_identifier = scheme_identifier.strip().lower()
        timestamp = datetime.now(tz=tz.tzlocal()).isoformat()

        try:
            url = "https://www.amfiindia.com/spages/NAVAll.txt"
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()

            lines = resp.text.splitlines()
            found = None

            for line in lines:
                parts = line.split(";")
                if len(parts) < 6:
                    continue  # skip headers or malformed rows

                scheme_code, isin_div_payout, isin_div_reinv, scheme_name, nav, nav_date = parts[:6]

                # Match by scheme code
                if scheme_identifier == scheme_code.strip().lower():
                    found = {
                        "scheme_code": scheme_code.strip(),
                        "scheme_name": scheme_name.strip(),
                        "nav": float(nav.replace(",", "")),
                        "currency": "INR",
                        "date": nav_date.strip(),
                        "timestamp": timestamp,
                        "source": "amfi"
                    }
                    break

                # Match by scheme name (partial match allowed)
                if scheme_identifier in scheme_name.strip().lower():
                    found = {
                        "scheme_code": scheme_code.strip(),
                        "scheme_name": scheme_name.strip(),
                        "nav": float(nav.replace(",", "")),
                        "currency": "INR",
                        "date": nav_date.strip(),
                        "timestamp": timestamp,
                        "source": "amfi"
                    }
                    break

            if not found:
                return {
                    "scheme_code": None,
                    "scheme_name": scheme_identifier,
                    "nav": None,
                    "currency": "INR",
                    "date": None,
                    "timestamp": timestamp,
                    "source": "amfi",
                    "note": "No match found"
                }

            return found

        except Exception as e:
            return {
                "scheme_code": None,
                "scheme_name": scheme_identifier,
                "nav": None,
                "currency": "INR",
                "date": None,
                "timestamp": timestamp,
                "source": "amfi",
                "error": str(e)
            }


# -------------------------
# Quick test
# -------------------------
if __name__ == "__main__":
    f = RealtimeFetcher()
    print("Stock example:", f.fetch_stock_price("SBIN"))  # SBI
    print("FD example:", f.fetch_fd_rates(("sbi", "hdfc", "icici","axis","idfc","kotak")))
    print("MF example:", f.fetch_mf_nav("SBI Small Cap Fund"))
    print("MF example:", f.fetch_mf_nav("HDFC Top 100 Fund"))
