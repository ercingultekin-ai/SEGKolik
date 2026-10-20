from typing import Optional
from src.config.settings import settings
from src.models.match import DailyReport, Match
from src.services.football_service import football_service
from src.services.basketball_service import basketball_service
from src.services.email_service import email_service
from src.repositories.match_repository import match_repository
from src.utils.date_utils import (
    get_today_turkey_date,
    format_date_dots,
    format_report_date,
    format_date_range_readable,
    get_dates_ending_at,
)
from src.utils.logger import logger
from src.services.sportscore_service import SportScoreException

class DailyReportJob:
    def __init__(self):
        self.football_service = football_service
        self.basketball_service = basketball_service
        self.email_service = email_service
        self.match_repository = match_repository

    def _fetch_range(self, service, date_list: list[str]) -> list[Match]:
        """Fetches matches for each date in range, dedupes by match_id."""
        combined: dict[str, Match] = {}
        for d in date_list:
            try:
                matches = service.fetch_matches_for_date(d)
                for m in matches:
                    combined[m.match_id] = m
            except SportScoreException:
                raise
            except Exception as e:
                logger.warning(f"Error fetching fixtures for date {d}: {e}")
        return list(combined.values())

    def run(self, target_date: Optional[str] = None, force_send_empty: Optional[bool] = None, bypass_duplicate_check: bool = False, days: Optional[int] = None) -> bool:
        """
        Executes report job for a date RANGE ending at target_date (Europe/Istanbul).
        Default: last N days (settings.report_days, default 7).
        """
        end_date = target_date or get_today_turkey_date()
        range_days = days if days is not None else settings.report_days
        if range_days < 1:
            range_days = 1
        date_list = get_dates_ending_at(end_date, range_days)
        start_date = date_list[0]
        is_range = not (len(date_list) == 1 and start_date == end_date)

        if is_range:
            logger.info("Application started")
            logger.info(f"Processing matches for date range: {start_date} to {end_date} ({range_days} days, Europe/Istanbul)")
        else:
            logger.info("Application started")
            logger.info(f"Processing matches for date: {end_date} (Europe/Istanbul)")

        api_error_occurred = False

        # 1. Fetch Football Matches (range)
        football_matches = []
        try:
            raw_football = self._fetch_range(self.football_service, date_list)
            # Only finished matches
            football_matches = [m for m in raw_football if m.is_finished]
        except SportScoreException as e:
            api_error_occurred = True
            logger.error(f"SportScore Football API error: {e}")

        # 2. Fetch Basketball Matches (range)
        basketball_matches = []
        try:
            raw_basketball = self._fetch_range(self.basketball_service, date_list)
            # Only finished matches
            basketball_matches = [m for m in raw_basketball if m.is_finished]
        except SportScoreException as e:
            api_error_occurred = True
            logger.error(f"SportScore Basketball API error: {e}")

        # If all APIs failed, do NOT claim "No matches", treat as API failure
        if api_error_occurred and not football_matches and not basketball_matches:
            logger.error("SportScore API could not be reached. Will NOT send email and will NOT mark as 'no matches'.")
            logger.info("Application finished with error")
            return False

        # Sort by date then start time for a chronological weekly report
        football_matches.sort(key=lambda m: (m.match_date, m.start_time))
        basketball_matches.sort(key=lambda m: (m.match_date, m.start_time))

        # 3. Duplicate check
        unsent_football = football_matches
        unsent_basketball = basketball_matches

        if not bypass_duplicate_check and not settings.test_mode:
            unsent_football = self.match_repository.filter_unsent_matches(football_matches)
            unsent_basketball = self.match_repository.filter_unsent_matches(basketball_matches)

        total_unsent_finished = len(unsent_football) + len(unsent_basketball)
        should_send_empty = force_send_empty if force_send_empty is not None else settings.send_empty_report

        # Subject / date label
        if is_range:
            subject = f"Türkiye Spor Sonuçları - {format_date_dots(start_date)} - {format_date_dots(end_date)}"
        else:
            subject = f"Türkiye Spor Sonuçları - {format_date_dots(end_date)}"

        # 4. Handle Empty or Sent state
        if total_unsent_finished == 0:
            if should_send_empty:
                logger.info("No finished matches found, but SEND_EMPTY_REPORT is true. Preparing empty report email...")
                html = self.email_service.generate_html(end_date, [], [], is_empty=True, start_date=start_date, end_date=end_date)
                plain = self.email_service.generate_plain_text(end_date, [], [], is_empty=True, start_date=start_date, end_date=end_date)
                logger.info("Email prepared")
                self.email_service.send_email(subject, html, plain)
                logger.info("Application finished")
                return True
            else:
                logger.info("No new completed matches to report. Skipping email according to configuration (SEND_EMPTY_REPORT=false).")
                logger.info("Application finished")
                return True

        # 5. Prepare and Send Email
        html = self.email_service.generate_html(end_date, unsent_football, unsent_basketball, is_empty=False, start_date=start_date, end_date=end_date)
        plain = self.email_service.generate_plain_text(end_date, unsent_football, unsent_basketball, is_empty=False, start_date=start_date, end_date=end_date)

        logger.info("Email prepared")
        success = self.email_service.send_email(subject, html, plain)

        # 6. Record to duplicate database if successfully sent and not in test mode
        if success and not settings.test_mode:
            all_sent = unsent_football + unsent_basketball
            self.match_repository.mark_matches_sent(all_sent)

        logger.info("Application finished")
        return success

daily_report_job = DailyReportJob()
