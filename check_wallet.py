from py_clob_client.client import ClobClient
import os
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY")  # loaded from .env, never hardcoded

client = ClobClient(
    host="https://clob.polymarket.com",
    key=PRIVATE_KEY,
    chain_id=137,
)

print("Your address:", client.get_address())
