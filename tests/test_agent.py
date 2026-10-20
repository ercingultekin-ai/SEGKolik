import os
import sys
import unittest
import tempfile
import shutil

# Ensure UTF-8 output on Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.utils.date_utils import (
    get_today_turkey_date,
    format_report_date,
    format_date_dots,
    parse_utc_to_turkey_time,
    get_turkey_date_from_utc_time
)
from src.utils.team_utils import is_besiktas_team, normalize_text
from src.models.match import Match, DailyReport
from src.repositories.match_repository import MatchRepository
from src.services.email_service import EmailService

class TestDateUtils(unittest.TestCase):
    def test_format_report_date(self):
        self.assertEqual(format_report_date("2026-09-15"), "15 Eylül 2026")
        self.assertEqual(format_date_dots("2026-09-15"), "15.09.2026")

    def test_utc_to_turkey_time(self):
        # UTC 17:00 is Turkey 20:00 (UTC+3)
        turkey_time = parse_utc_to_turkey_time("2026-09-15T17:00:00+00:00")
        self.assertEqual(turkey_time, "20:00")

    def test_turkey_date_from_utc(self):
        # UTC 21:30 is 00:30 next day in Turkey
        turkey_date = get_turkey_date_from_utc_time("2026-09-15T21:30:00+00:00")
        self.assertEqual(turkey_date, "2026-09-16")


class TestTeamUtils(unittest.TestCase):
    def test_besiktas_variations(self):
        variations = [
            "Beşiktaş",
            "Beşiktaş JK",
            "Besiktas JK",
            "Besiktas GAIN",
            "Beşiktaş Fibabanka",
            "Beşiktaş Emlakjet",
            "BEŞİKTAŞ A.Ş.",
            "besiktas"
        ]
        for name in variations:
            self.assertTrue(is_besiktas_team(name), f"Failed to identify: {name}")

    def test_non_besiktas_teams(self):
        non_bjk = ["Fenerbahçe", "Galatasaray", "Trabzonspor", "Anadolu Efes", "Kasımpaşa"]
        for name in non_bjk:
            self.assertFalse(is_besiktas_team(name), f"Incorrectly marked as Besiktas: {name}")


class TestMatchRepository(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_matches.db")
        self.repo = MatchRepository(db_path=self.db_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_duplicate_prevention(self):
        m1 = Match(
            match_id="fb_bjk_gs_20260915",
            sport="football",
            league="Turkish Super League",
            league_slug="turkish-super-league",
            home_team="Beşiktaş JK",
            away_team="Galatasaray",
            home_score="2",
            away_score="1",
            match_date="2026-09-15",
            status="finished"
        )
        # Initially unsent
        unsent = self.repo.filter_unsent_matches([m1])
        self.assertEqual(len(unsent), 1)

        # Mark as sent
        self.repo.mark_matches_sent([m1])
        self.assertTrue(self.repo.is_match_sent("fb_bjk_gs_20260915"))

        # Second check: must be filtered out (duplicate)
        unsent_again = self.repo.filter_unsent_matches([m1])
        self.assertEqual(len(unsent_again), 0)


class TestEmailService(unittest.TestCase):
    def setUp(self):
        self.email_service = EmailService()

    def test_html_generation_with_besiktas_highlight(self):
        fb_match = Match(
            match_id="fb_1",
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
        bb_match = Match(
            match_id="bb_1",
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

        html = self.email_service.generate_html("2026-09-15", [fb_match], [bb_match])
        plain = self.email_service.generate_plain_text("2026-09-15", [fb_match], [bb_match])

        # Verify Beşiktaş special highlights
        self.assertIn("BEŞİKTAŞ MAÇI", html)
        self.assertIn("⭐", html)
        self.assertIn("Beşiktaş JK", html)
        self.assertIn("2 - 1", html)

        # Verify basketball match
        self.assertIn("Fenerbahçe Beko", html)
        self.assertIn("91 - 76", html)
        self.assertIn("Türk Telekom", html)

        # Verify SportScore attribution
        self.assertIn("Powered by SportScore", html)
        self.assertIn("https://sportscore.com/", html)

        # Verify plain text
        self.assertIn("⭐ Beşiktaş JK 2 - 1 Başakşehir", plain)
        self.assertIn("Fenerbahçe Beko 91 - 76 Türk Telekom", plain)

if __name__ == "__main__":
    unittest.main()
