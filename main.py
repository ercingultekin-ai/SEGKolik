import sys
import io

# Ensure UTF-8 output on Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import time
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
import schedule

from src.config.settings import settings
from src.jobs.daily_report_job import daily_report_job
from src.services.email_service import email_service
from src.utils.logger import logger
from src.utils.date_utils import (
    get_turkey_timezone,
    get_today_turkey_date,
    format_date_dots,
    get_dates_ending_at,
)

def run_test_smtp():
    print("Testing SMTP connection...")
    if not settings.is_smtp_configured():
        print("[ERROR] SMTP settings are missing or incomplete in .env!")
        print("Please check SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM, EMAIL_TO.")
        return False

    subject = "Test E-postası - Türkiye Spor Ajanı"
    body_text = "Bu bir test e-postasıdır. SMTP bağlantınız ve e-posta ayarlarınız başarıyla çalışmaktadır."
    body_html = f"<h3>Test E-postası</h3><p>{body_text}</p>"

    # Temporarily disable test_mode to actually send
    prev_mode = settings.test_mode
    settings.test_mode = False
    success = email_service.send_email(subject, body_html, body_text)
    settings.test_mode = prev_mode
    if success:
        print("[SUCCESS] Test email sent successfully to " + settings.email_to)
    else:
        print("[ERROR] Failed to send test email. Check logs/app.log for details.")
    return success

def wait_startup_delay(delay_seconds: int) -> bool:
    """Waits delay_seconds before sending. Returns False if interrupted."""
    if delay_seconds <= 0:
        return True
    logger.info(f"Startup delay: report will be sent in {delay_seconds} seconds (~{delay_seconds // 60} min).")
    print(f"[*] Program baslatildi. Rapor {delay_seconds} saniye (~{delay_seconds // 60} dk) sonra gonderilecek.")
    print("[*] Iptal icin Ctrl + C.")
    try:
        # Countdown in 30s steps to keep logs readable
        remaining = delay_seconds
        while remaining > 0:
            step = min(30, remaining)
            time.sleep(step)
            remaining -= step
            if remaining > 0:
                logger.info(f"Startup delay: {remaining} seconds remaining...")
    except KeyboardInterrupt:
        print("\n[!] Baslamadan iptal edildi.")
        return False
    return True

def run_scheduler(delay_seconds: int, days: int, run_on_start: bool = True):
    day_name = settings.report_day.lower()
    
    def job_wrapper():
        logger.info(f"Scheduled trigger fired ({day_name} at {settings.report_time})")
        try:
            daily_report_job.run(days=days)
        except Exception as e:
            logger.error(f"Error during scheduled execution: {e}")

    day_labels = {
        "tuesday": "Her Salı",
        "monday": "Her Pazartesi",
        "wednesday": "Her Çarşamba",
        "thursday": "Her Perşembe",
        "friday": "Her Cuma",
        "saturday": "Her Cumartesi",
        "sunday": "Her Pazar",
        "daily": "Her Gün",
    }
    day_label = day_labels.get(day_name, "Her Gün")

    if day_name == "tuesday":
        schedule.every().tuesday.at(settings.report_time).do(job_wrapper)
    elif day_name == "monday":
        schedule.every().monday.at(settings.report_time).do(job_wrapper)
    elif day_name == "wednesday":
        schedule.every().wednesday.at(settings.report_time).do(job_wrapper)
    elif day_name == "thursday":
        schedule.every().thursday.at(settings.report_time).do(job_wrapper)
    elif day_name == "friday":
        schedule.every().friday.at(settings.report_time).do(job_wrapper)
    elif day_name == "saturday":
        schedule.every().saturday.at(settings.report_time).do(job_wrapper)
    elif day_name == "sunday":
        schedule.every().sunday.at(settings.report_time).do(job_wrapper)
    else:
        schedule.every().day.at(settings.report_time).do(job_wrapper)

    logger.info(f"Zamanlayıcı aktif: {day_label} saat {settings.report_time} ({settings.timezone}). Kapsam: son {days} gün.")
    print(f"[*] Türkiye Spor Sonuçları Zamanlayıcısı Başlatıldı.")
    print(f"[*] Planlama: {day_label} saat {settings.report_time} ({settings.timezone}).")
    if run_on_start:
        print(f"[*] Ilk rapor {delay_seconds} saniye sonra gonderilecek.")
    print("[*] Durdurmak için Ctrl + C tuşlarına basabilirsiniz.\n")

    # 1. First run after startup delay if enabled
    if run_on_start:
        if wait_startup_delay(delay_seconds):
            try:
                logger.info("Running initial delayed report...")
                daily_report_job.run(days=days)
            except Exception as e:
                logger.error(f"Error during initial delayed execution: {e}")
        else:
            return

    # 2. Continue with schedule loop
    while True:
        try:
            schedule.run_pending()
            time.sleep(15)
        except KeyboardInterrupt:
            print("\n[!] Zamanlayici durduruldu.")
            break
        except Exception as e:
            logger.error(f"Scheduler exception: {e}")
            time.sleep(30)

def main():
    parser = argparse.ArgumentParser(description="Türkiye Spor Maç Sonuçları E-posta Ajanı")
    parser.add_argument("--test", "-t", action="store_true", help="Test modu: e-posta göndermez, terminalde ve preview_report.html dosyasında çıktıyı gösterir.")
    parser.add_argument("--now", "-n", action="store_true", help="Baslangic gecikmesinden sonra bir defa çalıştırır (varsayılan 5 dk).")
    parser.add_argument("--date", "-d", type=str, help="Belirli bir tarih için çalıştırır (Format: YYYY-MM-DD). Bu tarih aralıgın BITIS tarihi olur.")
    parser.add_argument("--days", type=int, default=None, help="Kaç günlük aralık taranacak (varsayılan: REPORT_DAYS, örn. 7).")
    parser.add_argument("--delay-seconds", type=int, default=None, help="Başlangıç gecikmesi saniye (varsayılan: STARTUP_DELAY_SECONDS=300).")
    parser.add_argument("--no-delay", action="store_true", help="Başlangıç gecikmesini atlar, hemen çalışır.")
    parser.add_argument("--schedule", "-s", action="store_true", help="Zamanlayıcıyı başlatır (varsayılan: Salı 10:00).")
    parser.add_argument("--skip-initial", action="store_true", help="Zamanlayıcı başlarken ilk raporu göndermez, sadece Salı 10:00 vaktini bekler.")
    parser.add_argument("--day", type=str, help="Hangi gün çalışacağı (örn: tuesday, monday, daily).")
    parser.add_argument("--time", type=str, help="Hangi saatte çalışacağı (örn: 10:00).")
    parser.add_argument("--test-smtp", action="store_true", help="SMTP e-posta sunucu bağlantısını test eder.")
    parser.add_argument("--force-empty", action="store_true", help="Maç bulunamasa dahi boş rapor maili gönderir.")
    parser.add_argument("--bypass-duplicate", action="store_true", help="Duplicate (mükerrer) kontrolünü atlar.")

    parser.add_argument("--demo", action="store_true", help="Ornek mac verileriyle zengin HTML onizleme raporu uretir.")

    args = parser.parse_args()

    if args.demo:
        run_demo()
        return

    if args.test_smtp:
        run_test_smtp()
        return

    if args.test:
        settings.test_mode = True

    days = args.days if args.days is not None else settings.report_days
    if args.no_delay:
        delay_seconds = 0
    elif args.delay_seconds is not None:
        delay_seconds = max(0, args.delay_seconds)
    else:
        delay_seconds = max(0, settings.startup_delay_seconds)

    if args.day:
        settings.report_day = args.day.lower()
    if args.time:
        settings.report_time = args.time

    if args.schedule:
        run_scheduler(delay_seconds, days, run_on_start=not args.skip_initial)
        return

    # Single run: wait startup delay first (gece PC kapalı senaryosu için),
    # then send last N days report.
    if not wait_startup_delay(delay_seconds):
        return
    target_date = args.date or get_today_turkey_date()
    daily_report_job.run(
        target_date=target_date,
        force_send_empty=args.force_empty if args.force_empty else None,
        bypass_duplicate_check=args.bypass_duplicate or settings.test_mode,
        days=days,
    )

def run_demo():
    from src.models.match import Match
    from src.utils.date_utils import format_date_range_readable
    print("[*] Ornek mac verileri ile demo raporu olusturuluyor...")
    today = get_today_turkey_date()
    dates = get_dates_ending_at(today, 7)
    start = dates[0]
    fb = [
        Match(match_id="d1", sport="football", league="Türkiye Süper Lig", league_slug="turkish-super-league", home_team="Galatasaray", away_team="Trabzonspor", home_score="2", away_score="1", match_date=dates[-1], status="finished"),
        Match(match_id="d2", sport="football", league="Türkiye Süper Lig", league_slug="turkish-super-league", home_team="Fenerbahçe", away_team="Kasımpaşa", home_score="3", away_score="0", match_date=dates[-3], status="finished"),
        Match(match_id="d3", sport="football", league="Türkiye Süper Lig", league_slug="turkish-super-league", home_team="Beşiktaş JK", away_team="Başakşehir", home_score="2", away_score="1", match_date=dates[-5], status="finished")
    ]
    bb = [
        Match(match_id="d4", sport="basketball", league="Türkiye Basketbol Süper Ligi", league_slug="basketbol-super-ligi", home_team="Beşiktaş Fibabanka", away_team="Darüşşafaka", home_score="84", away_score="79", match_date=dates[-2], status="finished"),
        Match(match_id="d5", sport="basketball", league="Türkiye Basketbol Süper Ligi", league_slug="basketbol-super-ligi", home_team="Fenerbahçe Beko", away_team="Türk Telekom", home_score="91", away_score="76", match_date=dates[-4], status="finished")
    ]
    subject = f"Türkiye Spor Sonuçları - {format_date_dots(start)} - {format_date_dots(today)}"
    html = email_service.generate_html(today, fb, bb, start_date=start, end_date=today)
    plain = email_service.generate_plain_text(today, fb, bb, start_date=start, end_date=today)
    prev = settings.test_mode
    settings.test_mode = True
    email_service.send_email(subject, html, plain)
    settings.test_mode = prev
    print("[SUCCESS] Demo HTML raporu 'preview_report.html' dosyasina yazildi.")

if __name__ == "__main__":
    main()
