"""Decide when a market is mispriced relative to spot."""
import math


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
                       min_edge: float = 0.10) -> list[dict]:
    """
    For each market, compare implied probability vs fair probability.
    Returns mispricings where edge > min_edge (default 10%).
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
        edge_yes = fair - implied_yes  # positive => YES is underpriced
        edge_no = (1 - fair) - m["no_price"]  # positive => NO is underpriced

        if edge_yes >= min_edge:
            opps.append({
                **m,
                "spot": spot,
                "fair_prob": fair,
                "implied": implied_yes,
                "edge": edge_yes,
                "side": "BUY",
                "token_id": m["yes_token"],
                "price_to_pay": implied_yes,
            })
        elif edge_no >= min_edge:
            opps.append({
                **m,
                "spot": spot,
                "fair_prob": fair,
                "implied": m["no_price"],
                "edge": edge_no,
                "side": "BUY",
                "token_id": m["no_token"],
                "price_to_pay": m["no_price"],
            })

    opps.sort(key=lambda x: x["edge"], reverse=True)
    return opps
