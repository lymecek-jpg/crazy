"""Live order book prices from Polymarket CLOB."""
import requests
import logging

logger = logging.getLogger(__name__)

CLOB_HOST = "https://clob.polymarket.com"


def get_book(token_id: str) -> dict | None:
    """Get the current order book for a token."""
    try:
        resp = requests.get(f"{CLOB_HOST}/book", params={"token_id": token_id}, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Error fetching book for {token_id[:20]}...: {e}")
        return None


def get_best_prices(token_id: str) -> dict | None:
    """
    Returns {bid, ask, mid, has_liquidity} from the live CLOB order book.
    Returns None if the book is empty or unreachable.
    """
    book = get_book(token_id)
    if not book:
        return None

    bids = book.get("bids", [])
    asks = book.get("asks", [])

    best_bid = max((float(b["price"]) for b in bids), default=0.0)
    best_ask = min((float(a["price"]) for a in asks), default=1.0)

    if best_bid == 0 and best_ask == 1:
        return None  # empty book

    return {
        "bid": best_bid,
        "ask": best_ask,
        "mid": (best_bid + best_ask) / 2,
        "spread": best_ask - best_bid,
        "has_liquidity": len(bids) > 0 and len(asks) > 0,
    }
