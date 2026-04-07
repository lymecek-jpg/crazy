"""Crypto reactor bot — finds mispriced Polymarket crypto markets vs Binance spot."""
import time
import logging
from bot.config import (
    POLL_INTERVAL_SECONDS, MIN_EDGE, MIN_VOLUME,
    MAX_POSITION_USDC, DRY_RUN
)
from bot.price_feed import get_spot_prices
from bot.market_finder import fetch_active_crypto_markets
from bot.strategy import find_opportunities
from bot.trader import get_client, place_copy_order
from bot.state import load_state, save_state, record_trade, record_error

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

MARKET_REFRESH_SECONDS = 60   # how often to refetch market list
PRICE_TICK_SECONDS = POLL_INTERVAL_SECONDS  # how often to recheck spot + opps


def already_traded(state: dict, key: str) -> bool:
    return any(t["id"] == key for t in state["copied_trades"])


def execute_opps(opps, client, state):
    for opp in opps[:5]:
        key = f"{opp['slug']}_{opp['token_id']}"
        if already_traded(state, key):
            continue

        logger.info(
            f"OPPORTUNITY: {opp['question'][:60]} | "
            f"spot=${opp['spot']:,.0f} | fair={opp['fair_prob']*100:.0f}% | "
            f"market={opp['implied']*100:.0f}% | edge={opp['edge']*100:.0f}%"
        )

        if DRY_RUN:
            logger.info(f"  [DRY RUN] would buy {opp['side']} ${MAX_POSITION_USDC} @ {opp['price_to_pay']}")
            record_trade(state, key, {
                "question": opp["question"],
                "side": opp["side"],
                "price": opp["price_to_pay"],
                "size": MAX_POSITION_USDC,
                "edge": opp["edge"],
                "dry_run": True,
            })
            continue

        result = place_copy_order(
            client=client,
            token_id=opp["token_id"],
            side=opp["side"],
            price=opp["price_to_pay"],
            original_size=MAX_POSITION_USDC * 2,
        )
        if result:
            record_trade(state, key, {
                "question": opp["question"],
                "side": opp["side"],
                "price": opp["price_to_pay"],
                "size": MAX_POSITION_USDC,
                "edge": opp["edge"],
            })


def run():
    logger.info("Crypto reactor starting")
    logger.info(
        f"MAX=${MAX_POSITION_USDC} EDGE>={MIN_EDGE*100:.0f}% "
        f"VOL>=${MIN_VOLUME} TICK={PRICE_TICK_SECONDS}s "
        f"MARKET_REFRESH={MARKET_REFRESH_SECONDS}s DRY_RUN={DRY_RUN}"
    )

    state = load_state()
    client = None if DRY_RUN else get_client()

    markets = []
    last_market_fetch = 0
    last_log_minute = -1

    while True:
        try:
            now = time.time()

            # 1. Refresh market list periodically (slow)
            if now - last_market_fetch >= MARKET_REFRESH_SECONDS:
                markets = fetch_active_crypto_markets(min_volume=MIN_VOLUME)
                last_market_fetch = now
                logger.info(f"Refreshed market list — {len(markets)} active crypto markets")

            if not markets:
                time.sleep(PRICE_TICK_SECONDS)
                continue

            # 2. Fast tick — fetch spot, recompute opps
            symbols = list({m["symbol"] for m in markets})
            spots = get_spot_prices(symbols)

            opps = find_opportunities(markets, spots, min_edge=MIN_EDGE)

            # log spot price once per minute to avoid log spam
            current_minute = int(now // 60)
            if current_minute != last_log_minute:
                spot_str = " | ".join(f"{s}=${p:,.0f}" for s, p in spots.items())
                logger.info(f"tick: {spot_str} | {len(opps)} opps")
                last_log_minute = current_minute

            if opps:
                execute_opps(opps, client, state)
                save_state(state)

        except Exception as e:
            logger.error(f"Main loop error: {e}", exc_info=True)
            record_error(state, str(e))
            save_state(state)

        time.sleep(PRICE_TICK_SECONDS)


if __name__ == "__main__":
    run()
