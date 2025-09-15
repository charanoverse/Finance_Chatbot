# tests/test_realtime.py
from realtime import RealtimeFetcher

def test_fetch_stock_price_monkeypatched(monkeypatch):
    class DummyTicker:
        def history(self, period):
            import pandas as pd
            return pd.DataFrame({"Close":[100.0]})
        info = {"currency":"INR"}
    monkeypatch.setattr("yfinance.Ticker", lambda symbol: DummyTicker())
    f = RealtimeFetcher()
    out = f.fetch_stock_price("SBIN.NS")
    assert out["price"] == 100.0
    assert out["currency"] == "INR"
