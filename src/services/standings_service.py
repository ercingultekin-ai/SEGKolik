"""SportScore puan durumu (standings) servisi."""
from typing import List, Dict, Tuple
from src.config.settings import settings
from src.services.sportscore_service import sportscore_client, SportScoreException
from src.utils.logger import logger


class StandingsService:
    def __init__(self, client=None):
        self.client = client or sportscore_client

    def fetch_football_standings(self) -> Tuple[List[Dict], Dict]:
        """Süper Lig puan durumunu döndürür. (rows, meta)"""
        logger.info("SportScore Standings API requested")
        try:
            data = self.client.get(
                "api/v1/standings/",
                params={"sport": "football", "competition": settings.football_league_slug},
            )
        except SportScoreException as e:
            logger.error(f"Failed to fetch standings: {e}")
            raise

        tables = data.get("tables", []) if isinstance(data, dict) else []
        if not tables:
            return [], {}
        table = tables[0]
        rows = []
        for r in table.get("rows", []) or []:
            rows.append(
                {
                    "pos": r.get("pos"),
                    "team": (r.get("team") or "").strip(),
                    "team_logo": r.get("team_logo") or "",
                    "p": r.get("p", 0),
                    "w": r.get("w", 0),
                    "d": r.get("d", 0),
                    "l": r.get("l", 0),
                    "gf": r.get("gf", 0),
                    "ga": r.get("ga", 0),
                    "gd": r.get("gd", 0),
                    "pts": r.get("pts", 0),
                    "promo_color": r.get("promo_color") or "",
                    "promo_name": r.get("promo_name") or "",
                }
            )
        meta = {
            "competition": data.get("competition", "Türkiye Süper Lig"),
            "competition_logo": data.get("competition_logo", ""),
            "group": table.get("group", ""),
        }
        logger.info(f"Standings rows: {len(rows)}")
        return rows, meta

    def fetch_basketball_standings(self) -> Tuple[List[Dict], Dict]:
        """BSL puan durumu — API desteklemiyor, bilgi amaçlı hata fırlatır."""
        try:
            self.client.get(
                "api/v1/standings/",
                params={"sport": "basketball", "competition": settings.basketball_league_slug},
                max_retries=1,
            )
        except SportScoreException as e:
            raise SportScoreException(
                "SportScore API basketbol puan durumu sunmuyor (sadece futbol)."
            ) from e
        return [], {}


standings_service = StandingsService()
