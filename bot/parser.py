"""Parse Polymarket question text to extract threshold info."""
import re
from datetime import datetime


def parse_threshold_market(question: str) -> dict | None:
    """
    Parse questions like:
      'Will the price of Bitcoin be above $66,000 on April 12?'
      'Will the price of Ethereum be above $1,700 on April 11?'
      'Will Ethereum dip to $1,600 in April?'
    Returns: {'asset': 'BTC', 'direction': 'above', 'threshold': 66000, ...}
    """
    q = question.lower()

    # Detect asset
    if "bitcoin" in q or "btc" in q:
        asset = "BTC"
        symbol = "BTCUSDT"
    elif "ethereum" in q or " eth " in q:
        asset = "ETH"
        symbol = "ETHUSDT"
    else:
        return None

    # Detect direction
    if "above" in q:
        direction = "above"
    elif "below" in q or "dip to" in q:
        direction = "below"
    elif "between" in q:
        direction = "between"
    else:
        return None

    # Extract numeric threshold(s) — handles $66,000 / $1,700 / 66k
    nums = re.findall(r"\$?([\d,]+(?:\.\d+)?)\s*k?", q)
    parsed = []
    for n in nums:
        try:
            v = float(n.replace(",", ""))
            if 100 <= v <= 10_000_000:  # plausible crypto price range
                parsed.append(v)
        except ValueError:
            pass

    if not parsed:
        return None

    if direction == "between" and len(parsed) >= 2:
        return {
            "asset": asset, "symbol": symbol, "direction": "between",
            "low": min(parsed[:2]), "high": max(parsed[:2]),
        }

    return {
        "asset": asset, "symbol": symbol, "direction": direction,
        "threshold": parsed[0],
    }
