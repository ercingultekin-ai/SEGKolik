from dataclasses import dataclass
from typing import Optional
from src.utils.team_utils import is_besiktas_team

@dataclass
class Match:
    match_id: str
    sport: str  # 'football' or 'basketball'
    league: str
    league_slug: str
    home_team: str
    away_team: str
    home_score: Optional[str] = None
    away_score: Optional[str] = None
    match_date: str = ""  # YYYY-MM-DD in Turkey time
    start_time: str = ""  # HH:MM in Turkey time
    status: str = ""      # 'finished', 'upcoming', etc.
    status_text: str = ""
    url: str = ""
    home_logo: str = ""
    away_logo: str = ""
    round_info: str = ""

    @property
    def is_finished(self) -> bool:
        return self.status.strip().lower() == "finished"

    @property
    def is_besiktas_match(self) -> bool:
        return is_besiktas_team(self.home_team) or is_besiktas_team(self.away_team)

    @property
    def is_home_besiktas(self) -> bool:
        return is_besiktas_team(self.home_team)

    @property
    def is_away_besiktas(self) -> bool:
        return is_besiktas_team(self.away_team)

    def to_text_summary(self) -> str:
        score_str = f"{self.home_score if self.home_score is not None else '-'} - {self.away_score if self.away_score is not None else '-'}"
        prefix = "⭐ " if self.is_besiktas_match else ""
        return f"{prefix}{self.home_team} {score_str} {self.away_team}"

@dataclass
class DailyReport:
    date_str: str  # YYYY-MM-DD
    football_matches: list[Match]
    basketball_matches: list[Match]
    has_error: bool = False
    error_message: str = ""

    @property
    def total_finished_count(self) -> int:
        f_count = len([m for m in self.football_matches if m.is_finished])
        b_count = len([m for m in self.basketball_matches if m.is_finished])
        return f_count + b_count
