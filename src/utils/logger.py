import sys
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

class TurkeyFormatter(logging.Formatter):
    def __init__(self, tz_name='Europe/Istanbul'):
        super().__init__()
        try:
            self.tz = ZoneInfo(tz_name)
        except Exception:
            self.tz = None

    def format(self, record):
        dt = datetime.now(self.tz) if self.tz else datetime.now()
        time_str = dt.strftime('%H:%M:%S')
        if record.levelno >= logging.ERROR:
            return f'[{time_str}] [ERROR] {record.getMessage()}'
        elif record.levelno == logging.WARNING:
            return f'[{time_str}] [WARN] {record.getMessage()}'
        return f'[{time_str}] {record.getMessage()}'

def setup_logger(name='TurkeySportsAgent', level=logging.INFO, log_to_file=True):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(TurkeyFormatter())
        logger.addHandler(console_handler)
        
        # File Handler (logs/app.log)
        if log_to_file:
            import os
            os.makedirs('logs', exist_ok=True)
            file_handler = logging.FileHandler('logs/app.log', encoding='utf-8')
            file_handler.setFormatter(TurkeyFormatter())
            logger.addHandler(file_handler)
            
    return logger

logger = setup_logger()
