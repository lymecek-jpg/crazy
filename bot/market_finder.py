"""Find active crypto threshold markets on Polymarket."""
import requests
import json
import logging
from datetime import datetime, timezone
from bot.parser import parse_threshold_market

logger = logging.getLogger(__name__)

GAMMA_API = "https://gamma-api.polymarket.com"


def fetch_active_crypto_markets(min_volume: float = 100) -> list[dict]:
    """Pull active markets and keep only crypto threshold ones we can parse."""
    try:
        resp = requests.get(
            f"{GAMMA_API}/markets",
            params={
                "active": "true", "closed": "false",
                "limit": 500, "order": "volume", "ascending": "false",
            },
            timeout=15,
        )
        resp.raise_for_status()
        all_markets = resp.json()
    except Exception as e:
        logger.error(f"Error fetching markets: {e}")
        return []

    out = []
    for m in all_markets:
        question = m.get("question", "")
        parsed = parse_threshold_market(question)
        if not parsed:
            continue
        try:
            vol = float(m.get("volume", 0) or 0)
        except (TypeError, ValueError):
            vol = 0
        if vol < min_volume:
            continue

        end_date_str = m.get("endDate", "")
        try:
            end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
        except Exception:
            continue
        days_left = (end_date - datetime.now(timezone.utc)).total_seconds() / 86400
        if days_left < 0 or days_left > 30:
            continue

        # parse outcome prices and tokens
        try:
            outcomes = json.loads(m.get("outcomes", "[]"))
            prices = [float(p) for p in json.loads(m.get("outcomePrices", "[]"))]
            token_ids = json.loads(m.get("clobTokenIds", "[]"))
        except Exception:
            continue
        if len(outcomes) != 2 or len(prices) != 2 or len(token_ids) != 2:
            continue

        yes_idx = 0 if outcomes[0].lower() == "yes" else 1
        no_idx = 1 - yes_idx

        out.append({
            "question": question,
            "slug": m.get("slug", ""),
            "end_date": end_date,
            "days_left": days_left,
            "volume": vol,
            "yes_price": prices[yes_idx],
            "no_price": prices[no_idx],
            "yes_token": token_ids[yes_idx],
            "no_token": token_ids[no_idx],
            **parsed,
        })

    return out
