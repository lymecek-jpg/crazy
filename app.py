"""Streamlit dashboard for the crypto reactor bot."""
import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from bot.price_feed import get_24h_change
from bot.market_finder import fetch_active_crypto_markets
from bot.strategy import find_opportunities
from bot.config import MIN_EDGE, MIN_VOLUME, MAX_POSITION_USDC, DRY_RUN

st.set_page_config(page_title="Crypto Reactor", layout="wide")
st.title("Polymarket Crypto Reactor")

with st.sidebar:
    st.header("Settings")
    st.metric("Max position", f"${MAX_POSITION_USDC}")
    st.metric("Min edge", f"{MIN_EDGE*100:.0f}%")
    st.metric("Min volume", f"${MIN_VOLUME}")
    st.write(f"Mode: **{'DRY RUN' if DRY_RUN else 'LIVE'}**")
    st.caption("Edit .env to change settings")
    if st.button("Refresh"):
        st.rerun()

# Live spot prices
col1, col2 = st.columns(2)
with col1:
    btc = get_24h_change("BTCUSDT")
    if btc:
        st.metric("BTC", f"${btc['price']:,.0f}", f"{btc['change_pct']:+.2f}%")
with col2:
    eth = get_24h_change("ETHUSDT")
    if eth:
        st.metric("ETH", f"${eth['price']:,.0f}", f"{eth['change_pct']:+.2f}%")

st.divider()

# State
STATE_FILE = "state.json"
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_seen_ts": 0, "copied_trades": [], "errors": []}

state = load_state()
c1, c2, c3 = st.columns(3)
c1.metric("Trades placed", len(state["copied_trades"]))
c2.metric("Errors", len(state["errors"]))
c3.metric("Mode", "DRY RUN" if DRY_RUN else "LIVE")

# Live opportunity scan
st.subheader("Live Opportunity Scan")
with st.spinner("Scanning markets..."):
    markets = fetch_active_crypto_markets(min_volume=MIN_VOLUME)
    spots = {}
    if btc: spots["BTCUSDT"] = btc["price"]
    if eth: spots["ETHUSDT"] = eth["price"]
    opps = find_opportunities(markets, spots, min_edge=MIN_EDGE)

st.write(f"Scanned {len(markets)} markets — found {len(opps)} opportunities")

if opps:
    rows = []
    for o in opps:
        rows.append({
            "Question": o["question"][:60],
            "Asset": o["asset"],
            "Spot": f"${o['spot']:,.0f}",
            "Threshold": f"${o['threshold']:,.0f}",
            "Days left": f"{o['days_left']:.1f}",
            "Fair %": f"{o['fair_prob']*100:.0f}",
            "Market %": f"{o['implied']*100:.0f}",
            "Edge %": f"{o['edge']*100:.0f}",
            "Side": o["side"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

# All scanned markets
with st.expander(f"All scanned crypto markets ({len(markets)})"):
    if markets:
        rows = []
        for m in markets:
            spot = spots.get(m["symbol"], 0)
            threshold = m.get("threshold")
            rows.append({
                "Question": m["question"][:60],
                "Asset": m["asset"],
                "Direction": m["direction"],
                "Threshold": f"${threshold:,.0f}" if threshold else "—",
                "Spot": f"${spot:,.0f}" if spot else "—",
                "Days": f"{m['days_left']:.1f}",
                "Yes %": f"{m['yes_price']*100:.0f}",
                "Volume": f"${m['volume']:,.0f}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

# Trade history
st.subheader("Trade History")
if state["copied_trades"]:
    df = pd.DataFrame(state["copied_trades"])
    cols = [c for c in ["ts", "question", "side", "price", "size", "edge"] if c in df.columns]
    st.dataframe(df[cols].tail(50), use_container_width=True)
else:
    st.info("No trades yet.")

# Errors
if state["errors"]:
    with st.expander(f"Errors ({len(state['errors'])})"):
        for e in reversed(state["errors"][-10:]):
            st.error(f"{e['ts']}: {e['msg']}")

# Log
with st.expander("Bot log (last 50 lines)"):
    if os.path.exists("bot.log"):
        with open("bot.log") as f:
            lines = f.readlines()[-50:]
        st.code("".join(lines))
    else:
        st.info("Run main.py first.")
