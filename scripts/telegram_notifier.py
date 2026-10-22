"""Telegram notifier utility for HeatSense progress updates via ZestogramAI bot."""

import json
import logging
import time
import urllib.parse
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

BOT_TOKEN = "8993189628:AAFDGAynR1F4TuBL_aBI-ak9ivskoeVy2NA"
DEFAULT_CHAT_ID = "6061716582"


def send_telegram_notification(text: str, chat_id: str = DEFAULT_CHAT_ID, parse_mode: str = "Markdown") -> bool:
    """Send a notification message to the user on Telegram via ZestogramAI bot."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "HeatSense-Notifier/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            return bool(res_data.get("ok"))
    except Exception as exc:
        logger.warning(f"Failed to send Telegram notification: {exc}")
        return False


if __name__ == "__main__":
    success = send_telegram_notification("🔥 HeatSense Live: Telegram notification engine online.")
    print(f"Test notification status: {success}")
