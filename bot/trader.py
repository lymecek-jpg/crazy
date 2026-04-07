import logging
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType
from bot.config import (
    PRIVATE_KEY, PROXY_ADDRESS, CHAIN_ID, CLOB_HOST,
    COPY_FRACTION, MAX_POSITION_USDC
)

logger = logging.getLogger(__name__)


def get_client() -> ClobClient:
    client = ClobClient(
        host=CLOB_HOST,
        key=PRIVATE_KEY,
        chain_id=CHAIN_ID,
        signature_type=1,
        funder=PROXY_ADDRESS,
    )
    client.set_api_creds(client.create_or_derive_api_creds())
    return client


def place_copy_order(client: ClobClient, token_id: str, side: str, price: float, original_size: float):
    size = min(original_size * COPY_FRACTION, MAX_POSITION_USDC)
    size = round(size, 2)

    if size < 5.0:  # Polymarket minimum order size
        logger.info(f"Skipping — scaled size ${size} too small")
        return None

    order_args = OrderArgs(
        token_id=token_id,
        price=round(price, 4),
        size=size,
        side=side.upper(),
    )
    try:
        signed_order = client.create_order(order_args)
        resp = client.post_order(signed_order, OrderType.GTC)
        logger.info(f"Order placed: {resp}")
        return resp
    except Exception as e:
        logger.error(f"Order failed: {e}")
        return None
