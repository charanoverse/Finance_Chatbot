import os
import json
from datetime import datetime
from cachetools import TTLCache, cached
from dateutil import tz
import yfinance as yf
import requests

from .llm import call_llm  # reuse Gemini wrapper

# -------------------------
# Caching: stocks (30s), FD rates (6h), Mutual funds (24h)
# -------------------------
STOCK_CACHE = TTLCache(maxsize=1024, ttl=30)     # 30 seconds
FD_CACHE = TTLCache(maxsize=256, ttl=6 * 3600)   # 6 hours
MF_CACHE = TTLCache(maxsize=1024, ttl=24 * 3600) # 24 hours


class RealtimeFetcher:
     # -------------------------
    # Stock price (using yfinance)
    # -------------------------
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": "https://www.nseindia.com/"
        })
        # Load homepage once to get cookies
        self.session.get("https://www.nseindia.com", timeout=10)

    def fetch_stock_price(self, symbol: str):
        try:
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol.upper()}"
            response = self.session.get(url, timeout=10)
            data = response.json()
            ltp = data["priceInfo"]["lastPrice"]
            return {
                "ticker": symbol,
                "price": ltp,
                "currency": "INR",
                "source": "nseindia"
            }
        except Exception as e:
            return {"ticker": symbol, "error": str(e)}

    # -------------------------
    # FD rates (via Gemini)
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

                # Try parsing Gemini output as JSON (fallback to raw text if parsing fails)
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
    # Mutual fund NAV (placeholder)
    # -------------------------
    @cached(MF_CACHE)
    def fetch_mf_nav(self, scheme_identifier: str):
        return {
            "scheme": scheme_identifier,
            "nav": None,
            "note": "NAV fetching not yet implemented. Use AMFI API or aggregator.",
            "timestamp": datetime.now(tz=tz.tzlocal()).isoformat()
        }


# -------------------------
# Quick test
# -------------------------
if __name__ == "__main__":
    f = RealtimeFetcher()
    print("Stock example:", f.fetch_stock_price("SBIN.NS"))  # SBI
    print("Stock example:", f.fetch_stock_price("HDFCBANK.NS"))  # HDFC
    print("FD example:", f.fetch_fd_rates(("sbi", "hdfc", "icici","axis","idfc","kotak")))
    print("MF example:", f.fetch_mf_nav("some_scheme_code"))
