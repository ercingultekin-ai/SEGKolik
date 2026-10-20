"""SportScore gol krallığı / asist liderliği (topscorers) servisi."""
from typing import List, Dict
from src.config.settings import settings
from src.services.sportscore_service import sportscore_client, SportScoreException
from src.utils.logger import logger


class ScorersService:
    def __init__(self, client=None):
        self.client = client or sportscore_client

    def fetch_top_scorers(self, stat_type: str = "goals", limit: int = 20) -> List[Dict]:
        """Süper Lig gol/asist liderleri. stat_type: 'goals' veya 'assists'."""
        if stat_type not in ("goals", "assists"):
            stat_type = "goals"
        logger.info(f"SportScore TopScorers API requested ({stat_type})")
        try:
            data = self.client.get(
                "api/v1/topscorers/",
                params={
                    "sport": "football",
                    "competition": settings.football_league_slug,
                    "stat_type": stat_type,
                },
            )
        except SportScoreException as e:
            logger.error(f"Failed to fetch topscorers: {e}")
            raise

        out = []
        for s in (data.get("scorers", []) if isinstance(data, dict) else [])[:limit]:
            out.append(
                {
                    "rank": s.get("rank"),
                    "player": (s.get("player") or "").strip(),
                    "player_logo": s.get("player_logo") or "",
                    "team": (s.get("team") or "").strip(),
                    "team_logo": s.get("team_logo") or "",
                    "goals": s.get("goals", 0),
                    "assists": s.get("assists", 0),
                    "matches": s.get("matches", 0),
                    "minutes": s.get("minutes", 0),
                    "rating": s.get("rating", ""),
                }
            )
        logger.info(f"TopScorers rows ({stat_type}): {len(out)}")
        return out


scorers_service = ScorersService()
