import logging
import time
from typing import List

import requests

from ..config import Config

logger = logging.getLogger(__name__)

# Telegram message length limit (UTF-8 code-points)
_MAX_MESSAGE_LENGTH = 4096


class TelegramService:
    """Send messages to Telegram with retry and auto-split."""

    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_message(self, message: str) -> bool:
        """Send *message* to the configured chat.

        Automatically splits messages that exceed the Telegram 4096-char
        limit and retries on transient failures / rate-limits.
        """
        if not self.token or not self.chat_id:
            logger.error("Telegram credentials missing")
            return False

        chunks = self._split_message(message)
        all_ok = True
        for chunk in chunks:
            if not self._send_chunk(chunk):
                all_ok = False

        return all_ok

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _send_chunk(self, text: str) -> bool:
        """Send a single chunk with retry + backoff."""
        max_retries = Config.SCRAPER_MAX_RETRIES
        retry_delay = Config.SCRAPER_RETRY_DELAY

        for attempt in range(1, max_retries + 1):
            try:
                payload = {
                    'chat_id': self.chat_id,
                    'text': text,
                    'parse_mode': 'Markdown',
                }
                resp = requests.post(self.base_url, json=payload, timeout=15)

                # Telegram rate-limit → honour Retry-After header
                if resp.status_code == 429:
                    retry_after = int(
                        resp.json()
                        .get('parameters', {})
                        .get('retry_after', retry_delay * 2)
                    )
                    logger.warning(
                        "Telegram rate-limited, waiting %ds (attempt %d/%d)",
                        retry_after, attempt, max_retries,
                    )
                    time.sleep(retry_after)
                    continue

                if resp.status_code == 200:
                    resp_json = resp.json()
                    if resp_json.get('ok'):
                        logger.info("Telegram message sent successfully")
                        return True
                    # API returned ok=False — log description for debugging
                    logger.error(
                        "Telegram API error: %s", resp_json.get('description'),
                    )
                    return False

                # Other HTTP errors
                logger.warning(
                    "Telegram HTTP %s (attempt %d/%d): %s",
                    resp.status_code, attempt, max_retries,
                    resp.text[:200],
                )

            except requests.RequestException as exc:
                logger.warning(
                    "Telegram request error (attempt %d/%d): %s",
                    attempt, max_retries, exc,
                )

            if attempt < max_retries:
                time.sleep(retry_delay * (2 ** (attempt - 1)))

        logger.error("Failed to send Telegram message after %d attempts", max_retries)
        return False

    @staticmethod
    def _split_message(message: str) -> List[str]:
        """Split a long message into ≤ 4096-char chunks at line boundaries."""
        if len(message) <= _MAX_MESSAGE_LENGTH:
            return [message]

        chunks: List[str] = []
        current = ""
        for line in message.split('\n'):
            candidate = f"{current}\n{line}" if current else line
            if len(candidate) > _MAX_MESSAGE_LENGTH:
                if current:
                    chunks.append(current)
                current = line
            else:
                current = candidate

        if current:
            chunks.append(current)

        return chunks
