import logging
import coloredlogs
from logging.handlers import RotatingFileHandler
import os

# Tạo logger
logger = logging.getLogger('bot_logger')
logger.setLevel(logging.INFO)

# Định dạng log
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Handler cho file
log_file = 'logs/bot.log'
os.makedirs(os.path.dirname(log_file), exist_ok=True)
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=1024 * 1024,  # 1MB
    backupCount=5
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Handler cho console với màu sắc
coloredlogs.install(
    level='INFO',
    logger=logger,
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Export logger
__all__ = ['logger'] 