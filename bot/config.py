import os
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
PROXY_ADDRESS = os.getenv("POLYMARKET_PROXY_ADDRESS")
CHAIN_ID = int(os.getenv("CHAIN_ID", 137))

# Reactor settings
MAX_POSITION_USDC = float(os.getenv("MAX_POSITION_USDC", 5))
MIN_EDGE = float(os.getenv("MIN_EDGE", 0.10))   # 10% mispricing required
MIN_VOLUME = float(os.getenv("MIN_VOLUME", 500))  # min market volume
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", 30))
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_HOST = "https://clob.polymarket.com"

# legacy (kept for backward compat)
TARGET_WALLET = os.getenv("TARGET_WALLET", "").lower()
COPY_FRACTION = float(os.getenv("COPY_FRACTION", 0.5))
