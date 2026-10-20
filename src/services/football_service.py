from typing import List
from src.config.settings import settings
from src.models.match import Match
from src.services.sportscore_service import sportscore_client, SportScoreException
from src.utils.date_utils import parse_utc_to_turkey_time, get_turkey_date_from_utc_time
from src.utils.logger import logger

class FootballService:
    def __init__(self, client=None):
        self.client = client or sportscore_client

    def fetch_matches_for_date(self, date_str: str) -> List[Match]:
        """
        Fetches Süper Lig matches for the specified date (YYYY-MM-DD).
        Handles API errors, parses and validates JSON fields safely.
        """
        logger.info("SportScore Football API requested")
        params = {
            "sport": "football",
            "competition": settings.football_league_slug,
            "date": date_str,
            "limit": 100
        }
        
        try:
            data = self.client.get("api/v1/fixtures/", params=params)
        except SportScoreException as e:
            logger.error(f"Failed to fetch Süper Lig matches: {e}")
            raise

        raw_matches = data.get("matches", [])
        logger.info(f"Süper Lig matches found: {len(raw_matches)}")
        
        parsed_matches = []
        for item in raw_matches:
            match = self._parse_match(item, date_str)
            if match:
                parsed_matches.append(match)
        
        finished_count = len([m for m in parsed_matches if m.is_finished])
        logger.info(f"Finished matches: {finished_count}")
        return parsed_matches

    def fetch_matches_for_last_days(self, days: int = 7) -> List[Match]:
        from src.utils.date_utils import get_last_n_days_turkey
        date_list = get_last_n_days_turkey(days)
        logger.info(f"Fetching Süper Lig matches for last {days} days ({date_list[0]} to {date_list[-1]})...")
        
        all_matches_dict = {}
        for d in date_list:
            try:
                matches = self.fetch_matches_for_date(d)
                for m in matches:
                    all_matches_dict[m.match_id] = m
            except Exception as e:
                logger.warning(f"Error fetching football fixtures for date {d}: {e}")

        combined = list(all_matches_dict.values())
        finished = [m for m in combined if m.is_finished]
        logger.info(f"Total Süper Lig matches (last {days} days): {len(combined)}, Finished: {len(finished)}")
        return combined

    def _parse_match(self, item: dict, query_date: str) -> Match:
        # Null/undefined checks & safe extraction
        home_team = (item.get("home") or "").strip()
        away_team = (item.get("away") or "").strip()
        if not home_team or not away_team:
            return None

        status = str(item.get("status") or "").strip().lower()
        status_text = str(item.get("status_text") or "").strip()
        utc_time = item.get("time") or ""
        turkey_time = parse_utc_to_turkey_time(utc_time)
        match_date = get_turkey_date_from_utc_time(utc_time) or query_date

        home_score = item.get("home_score")
        away_score = item.get("away_score")
        home_score_str = str(home_score) if home_score is not None else None
        away_score_str = str(away_score) if away_score is not None else None

        url = item.get("url") or ""
        # Create deterministic unique match ID
        if url:
            match_id = url.strip("/").split("/")[-1]
        else:
            match_id = f"fb_{home_team}_{away_team}_{match_date}".replace(" ", "-").lower()

        league_name = item.get("competition") or "Türkiye Süper Lig"

        return Match(
            match_id=match_id,
            sport="football",
            league=league_name,
            league_slug=settings.football_league_slug,
            home_team=home_team,
            away_team=away_team,
            home_score=home_score_str,
            away_score=away_score_str,
            match_date=match_date,
            start_time=turkey_time,
            status=status,
            status_text=status_text,
            url=url,
            home_logo=item.get("home_logo") or "",
            away_logo=item.get("away_logo") or ""
        )

football_service = FootballService()
