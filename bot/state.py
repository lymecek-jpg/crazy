import json
import os
from datetime import datetime, timezone

STATE_FILE = "state.json"


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_seen_ts": 0.0, "copied_trades": [], "errors": []}


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def record_trade(state: dict, trade_id: str, detail: dict):
    state["copied_trades"].append({
        "id": trade_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        **detail,
    })
    state["copied_trades"] = state["copied_trades"][-200:]


def record_error(state: dict, msg: str):
    state["errors"].append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "msg": msg,
    })
    state["errors"] = state["errors"][-100:]
