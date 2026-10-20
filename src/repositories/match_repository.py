import os
import sqlite3
import contextlib
from typing import List
from datetime import datetime
from src.models.match import Match
from src.config.settings import settings
from src.utils.logger import logger

class MatchRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.db_path
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._init_db()

    @contextlib.contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sent_matches (
                    match_id TEXT PRIMARY KEY,
                    sport TEXT NOT NULL,
                    league TEXT NOT NULL,
                    match_date TEXT NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def is_match_sent(self, match_id: str) -> bool:
        if not match_id:
            return False
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM sent_matches WHERE match_id = ?", (match_id,))
            return cursor.fetchone() is not None

    def filter_unsent_matches(self, matches: List[Match]) -> List[Match]:
        """Filters out matches that have already been sent in a previous report."""
        if not matches:
            return []
        with self._connection() as conn:
            cursor = conn.cursor()
            unsent = []
            for match in matches:
                cursor.execute("SELECT 1 FROM sent_matches WHERE match_id = ?", (match.match_id,))
                if not cursor.fetchone():
                    unsent.append(match)
                else:
                    logger.info(f"Duplicate skipped (already sent): {match.match_id} ({match.home_team} vs {match.away_team})")
            return unsent

    def mark_matches_sent(self, matches: List[Match]):
        """Records matches as sent in the local database."""
        if not matches:
            return
        with self._connection() as conn:
            cursor = conn.cursor()
            for match in matches:
                cursor.execute("""
                    INSERT OR REPLACE INTO sent_matches (match_id, sport, league, match_date, sent_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (match.match_id, match.sport, match.league, match.match_date))
            conn.commit()
            logger.info(f"{len(matches)} match(es) recorded into sent_matches database.")

    def get_sent_matches_count_for_date(self, date_str: str) -> int:
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sent_matches WHERE match_date = ?", (date_str,))
            row = cursor.fetchone()
            return row[0] if row else 0

match_repository = MatchRepository()
