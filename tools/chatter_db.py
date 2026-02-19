"""DB/delivery helpers extracted from chatter_shared (N15)."""

import logging
import time
from typing import Optional

import mysql.connector

from chatter_constants import EMOTE_LIST

logger = logging.getLogger(__name__)


def get_db_connection(config: dict, database: str = None):
    """Create database connection from config."""
    return mysql.connector.connect(
        host=config.get('LLMChatter.Database.Host', 'localhost'),
        port=int(config.get('LLMChatter.Database.Port', 3306)),
        user=config.get('LLMChatter.Database.User', 'acore'),
        password=config.get(
            'LLMChatter.Database.Password', 'acore'
        ),
        database=database or config.get(
            'LLMChatter.Database.Name', 'acore_characters'
        )
    )


def wait_for_database(
    config: dict,
    max_retries: int = 30,
    initial_delay: float = 2.0
) -> bool:
    """Wait for database to become available with exponential backoff."""
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            conn = get_db_connection(config)
            conn.close()
            logger.info(
                f"Database connection established "
                f"(attempt {attempt})"
            )
            return True
        except mysql.connector.Error as e:
            if attempt == max_retries:
                logger.error(
                    f"Failed to connect to database after "
                    f"{max_retries} attempts: {e}"
                )
                return False
            logger.info(
                f"Waiting for database... "
                f"(attempt {attempt}/{max_retries}, "
                f"retry in {delay:.1f}s)"
            )
            time.sleep(delay)
            delay = min(delay * 1.5, 30.0)

    return False


def validate_emote(emote_str: Optional[str]) -> Optional[str]:
    """Clean and validate an emote string from LLM output.

    Returns a valid emote name or None.
    """
    if not emote_str or not isinstance(emote_str, str):
        return None
    cleaned = emote_str.strip().lower()
    # Strip quotes the LLM might add
    cleaned = cleaned.strip('"').strip("'")
    if cleaned in EMOTE_LIST and cleaned != 'none':
        return cleaned
    return None


def insert_chat_message(
    db,
    bot_guid: int,
    bot_name: str,
    message: str,
    channel: str = 'party',
    delay_seconds: float = 2.0,
    event_id: int = None,
    queue_id: int = None,
    sequence: int = 0,
    emote: str = None,
):
    """Insert a message into llm_chatter_messages.

    Centralised helper replacing individual INSERT
    statements across the codebase. Handles the emote
    column transparently.
    """
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO llm_chatter_messages
        (event_id, queue_id, sequence, bot_guid,
         bot_name, message, emote, channel,
         delivered, deliver_at)
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, 0,
            DATE_ADD(NOW(), INTERVAL %s SECOND)
        )
    """, (
        event_id, queue_id, sequence,
        bot_guid, bot_name, message,
        validate_emote(emote), channel,
        int(delay_seconds),
    ))
    db.commit()
