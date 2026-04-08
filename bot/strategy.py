"""Decide when a market is mispriced relative to spot."""
import math
import logging
from bot.orderbook import get_best_prices

logger = logging.getLogger(__name__)

MAX_PRICE_STALENESS = 0.10  # if Gamma vs CLOB price differ by >10%, treat as stale


def fair_probability(spot: float, threshold: float, days_left: float, direction: str,
                     annual_vol: float = 0.6) -> float:
    """
    Compute the fair probability that spot > threshold at expiry,
    using a simple lognormal model with assumed crypto vol of 60% annually.
    """
    if days_left <= 0:
        if direction == "above":
            return 1.0 if spot > threshold else 0.0
        else:
            return 1.0 if spot < threshold else 0.0

    t = days_left / 365.0
    sigma = annual_vol * math.sqrt(t)
    if sigma == 0:
        return 0.5
    # log-distance in standard deviations
    z = math.log(spot / threshold) / sigma
    # standard normal CDF
    prob_above = 0.5 * (1 + math.erf(z / math.sqrt(2)))

    if direction == "above":
        return prob_above
    elif direction == "below":
        return 1 - prob_above
    return 0.5


def find_opportunities(markets: list[dict], spots: dict[str, float],
                       min_edge: float = 0.10, verify_live: bool = True) -> list[dict]:
    """
    For each market, compare implied probability vs fair probability.
    Returns mispricings where edge > min_edge (default 10%).
    Verifies live CLOB book prices to filter out stale Gamma data.
    """
    opps = []
    for m in markets:
        spot = spots.get(m["symbol"])
        if not spot:
            continue
        if m["direction"] == "between":
            continue  # skip range markets for v1

        fair = fair_probability(
            spot=spot,
            threshold=m["threshold"],
            days_left=m["days_left"],
            direction=m["direction"],
        )
        implied_yes = m["yes_price"]
        edge_yes = fair - implied_yes
        edge_no = (1 - fair) - m["no_price"]

        # decide which side has edge
        if edge_yes >= min_edge:
            side_token = m["yes_token"]
            gamma_price = implied_yes
            edge = edge_yes
            implied = implied_yes
        elif edge_no >= min_edge:
            side_token = m["no_token"]
            gamma_price = m["no_price"]
            edge = edge_no
            implied = m["no_price"]
        else:
            continue

        # ---- LIVE VERIFICATION via CLOB order book ----
        if verify_live:
            book = get_best_prices(side_token)
            if not book or not book["has_liquidity"]:
                logger.info(f"Skip {m['question'][:50]}: no live liquidity")
                continue
            live_ask = book["ask"]
            # check if Gamma data was stale
            if abs(live_ask - gamma_price) > MAX_PRICE_STALENESS:
                logger.info(
                    f"Skip {m['question'][:50]}: stale Gamma price "
                    f"(gamma={gamma_price:.2f}, live ask={live_ask:.2f})"
                )
                continue
            # recompute edge using live ask (the actual price you'd pay)
            if side_token == m["yes_token"]:
                live_edge = fair - live_ask
            else:
                live_edge = (1 - fair) - live_ask
            if live_edge < min_edge:
                logger.info(
                    f"Skip {m['question'][:50]}: edge gone after live check "
                    f"({live_edge*100:.0f}% < {min_edge*100:.0f}%)"
                )
                continue
            edge = live_edge
            implied = live_ask
            price_to_pay = live_ask
        else:
            price_to_pay = gamma_price

        opps.append({
            **m,
            "spot": spot,
            "fair_prob": fair,
            "implied": implied,
            "edge": edge,
            "side": "BUY",
            "token_id": side_token,
            "price_to_pay": price_to_pay,
        })

    opps.sort(key=lambda x: x["edge"], reverse=True)
    return opps
