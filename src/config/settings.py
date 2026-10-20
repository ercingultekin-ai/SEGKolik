import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def get_bool_env(key: str, default: bool = False) -> bool:
    val = os.getenv(key, '').strip().lower()
    if val in ('true', '1', 'yes', 'y'):
        return True
    elif val in ('false', '0', 'no', 'n'):
        return False
    return default

@dataclass
class Settings:
    # SportScore API
    sportscore_api_url: str = os.getenv('SPORTSCORE_API_URL', 'https://sportscore.com').rstrip('/')
    sportscore_app_name: str = os.getenv('SPORTSCORE_APP_NAME', 'turkey-sports-mailer')
    
    # Leagues
    football_league_slug: str = os.getenv('FOOTBALL_LEAGUE_SLUG', 'turkish-super-league')
    football_league_id: str = os.getenv('FOOTBALL_LEAGUE_ID', '8y39mp1h6jmojxg')
    basketball_league_slug: str = os.getenv('BASKETBALL_LEAGUE_SLUG', 'basketbol-super-ligi')
    basketball_league_id: str = os.getenv('BASKETBALL_LEAGUE_ID', 'xz318q6ntxmo9jd')
    
    # Team identifiers (Beşiktaş)
    besiktas_football_slug: str = os.getenv('BESIKTAS_FOOTBALL_TEAM_SLUG', 'besiktas-jk')
    besiktas_basketball_slug: str = os.getenv('BESIKTAS_BASKETBALL_TEAM_SLUG', 'besiktas-gain')
    
    # Email / SMTP
    email_from: str = os.getenv('EMAIL_FROM', '')
    email_to: str = os.getenv('EMAIL_TO', '')
    smtp_host: str = os.getenv('SMTP_HOST', '')
    smtp_port: int = int(os.getenv('SMTP_PORT', '587'))
    smtp_user: str = os.getenv('SMTP_USER', '')
    smtp_password: str = os.getenv('SMTP_PASSWORD', '')
    smtp_use_tls: bool = get_bool_env('SMTP_USE_TLS', True)
    
    # Scheduling & Timing
    report_day: str = os.getenv('REPORT_DAY', 'tuesday').strip().lower()
    report_time: str = os.getenv('REPORT_TIME', '10:00')
    timezone: str = os.getenv('TIMEZONE', 'Europe/Istanbul')
    send_empty_report: bool = get_bool_env('SEND_EMPTY_REPORT', False)
    startup_delay_seconds: int = int(os.getenv('STARTUP_DELAY_SECONDS', '300'))
    report_days: int = int(os.getenv('REPORT_DAYS', '7'))
    
    # Mode
    test_mode: bool = get_bool_env('TEST_MODE', False)
    db_path: str = os.getenv('DB_PATH', 'data/matches.db')

    # Web arayüz (SEG_Maçkolik) adresi - maildeki "web'de görüntüle" linki için
    app_url: str = os.getenv('APP_URL', 'http://localhost:8501').rstrip('/')

    def is_smtp_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_password and self.email_to)

settings = Settings()
