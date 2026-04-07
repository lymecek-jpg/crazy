"""Live spot prices from Binance (free, no auth)."""
import requests
import logging

logger = logging.getLogger(__name__)

BINANCE_API = "https://api.binance.com/api/v3"


def get_spot_price(symbol: str = "BTCUSDT") -> float | None:
    """Get current spot price for a symbol like BTCUSDT or ETHUSDT."""
    try:
        resp = requests.get(f"{BINANCE_API}/ticker/price", params={"symbol": symbol}, timeout=5)
        resp.raise_for_status()
        return float(resp.json()["price"])
    except Exception as e:
        logger.error(f"Error fetching {symbol} price: {e}")
        return None


def get_spot_prices(symbols: list[str]) -> dict[str, float]:
    """Get multiple spot prices in one call."""
    out = {}
    for s in symbols:
        p = get_spot_price(s)
        if p:
            out[s] = p
    return out


def get_24h_change(symbol: str = "BTCUSDT") -> dict | None:
    """Get 24h price change stats."""
    try:
        resp = requests.get(f"{BINANCE_API}/ticker/24hr", params={"symbol": symbol}, timeout=5)
        resp.raise_for_status()
        d = resp.json()
        return {
            "price": float(d["lastPrice"]),
            "change_pct": float(d["priceChangePercent"]),
            "high_24h": float(d["highPrice"]),
            "low_24h": float(d["lowPrice"]),
        }
    except Exception as e:
        logger.error(f"Error fetching {symbol} 24h: {e}")
        return None
