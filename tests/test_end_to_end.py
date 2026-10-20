import os
import sys
import unittest

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.config.settings import settings
from src.models.match import Match
from src.services.email_service import email_service
from src.repositories.match_repository import MatchRepository
from src.jobs.daily_report_job import DailyReportJob

class TestEndToEnd(unittest.TestCase):
    def test_full_report_generation_and_html(self):
        # Create representative match dataset matching user prompt example:
        # Galatasaray 2 - 1 Trabzonspor
        # Fenerbahçe 3 - 0 Kasımpaşa
        # ⭐ Beşiktaş 2 - 1 Başakşehir
        # Beşiktaş Fibabanka 84 - 79 Darüşşafaka
        # Fenerbahçe Beko 91 - 76 Türk Telekom

        football_matches = [
            Match(
                match_id="fb_gs_ts",
                sport="football",
                league="Turkish Super League",
                league_slug="turkish-super-league",
                home_team="Galatasaray",
                away_team="Trabzonspor",
                home_score="2",
                away_score="1",
                match_date="2026-09-15",
                status="finished"
            ),
            Match(
                match_id="fb_fb_kp",
                sport="football",
                league="Turkish Super League",
                league_slug="turkish-super-league",
                home_team="Fenerbahçe",
                away_team="Kasımpaşa",
                home_score="3",
                away_score="0",
                match_date="2026-09-15",
                status="finished"
            ),
            Match(
                match_id="fb_bjk_bs",
                sport="football",
                league="Turkish Super League",
                league_slug="turkish-super-league",
                home_team="Beşiktaş JK",
                away_team="Başakşehir",
                home_score="2",
                away_score="1",
                match_date="2026-09-15",
                status="finished"
            )
        ]

        basketball_matches = [
            Match(
                match_id="bb_bjk_ds",
                sport="basketball",
                league="Basketbol Super Ligi",
                league_slug="basketbol-super-ligi",
                home_team="Beşiktaş Fibabanka",
                away_team="Darüşşafaka",
                home_score="84",
                away_score="79",
                match_date="2026-09-15",
                status="finished"
            ),
            Match(
                match_id="bb_fb_tt",
                sport="basketball",
                league="Basketbol Super Ligi",
                league_slug="basketbol-super-ligi",
                home_team="Fenerbahçe Beko",
                away_team="Türk Telekom",
                home_score="91",
                away_score="76",
                match_date="2026-09-15",
                status="finished"
            )
        ]

        # Generate HTML and plain text
        html = email_service.generate_html("2026-09-15", football_matches, basketball_matches)
        plain = email_service.generate_plain_text("2026-09-15", football_matches, basketball_matches)

        # Write to preview_report.html so user can inspect visually
        with open("preview_report.html", "w", encoding="utf-8") as f:
            f.write(html)

        # Assertions
        self.assertIn("TÜRKİYE SÜPER LİG", html)
        self.assertIn("TÜRKİYE BASKETBOL SÜPER LİGİ (BSL)", html)
        self.assertIn("BEŞİKTAŞ MAÇI", html)
        self.assertIn("15 Eylül 2026", html)
        self.assertIn("Powered by SportScore", html)

        # Verify plain text matches user format
        self.assertIn("Galatasaray 2 - 1 Trabzonspor", plain)
        self.assertIn("Fenerbahçe 3 - 0 Kasımpaşa", plain)
        self.assertIn("⭐ Beşiktaş JK 2 - 1 Başakşehir", plain)
        self.assertIn("⭐ Beşiktaş Fibabanka 84 - 79 Darüşşafaka", plain)
        self.assertIn("Fenerbahçe Beko 91 - 76 Türk Telekom", plain)

if __name__ == "__main__":
    unittest.main()
