import requests
import logging
from bot.config import GAMMA_API

logger = logging.getLogger(__name__)

DATA_API = "https://data-api.polymarket.com"


def get_recent_trades(wallet: str, since_ts: float = 0) -> list:
    url = f"{DATA_API}/activity"
    params = {"user": wallet.lower(), "limit": 50}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        trades = resp.json()
        # only copy actual trades, not redemptions
        trades = [t for t in trades if t.get("type") == "TRADE"]
        if since_ts:
            trades = [t for t in trades if float(t.get("timestamp", 0)) > since_ts]
        return trades
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        return []


def get_open_positions(wallet: str) -> list:
    url = f"{DATA_API}/positions"
    params = {"user": wallet.lower()}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        return []
