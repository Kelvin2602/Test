#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import coloredlogs
from datetime import datetime, time
import pytz

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes
)

from src.services.violation_manager import ViolationManager
from src.main import (
    start,
    handle_message,
    button_callback,
    periodic_check,
    save_all_user_states,
    auto_end_shift,
    send_daily_report,
    load_user_states,
    user_states,
    handle_admin_action
)
from src.utils.config import VN_TIMEZONE, BOT_TOKEN
from src.admin_handlers import AdminHandlers
from src.commands.help_handler import help_command

# Cấu hình base directory
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# Cấu hình logging
logger = logging.getLogger(__name__)
coloredlogs.install(
    level='DEBUG',
    logger=logger,
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Thêm file handler
log_file = LOG_DIR / 'violation_monitor.log'
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
logger.addHandler(file_handler)

# Khởi tạo violation manager
violation_manager = ViolationManager()

def run_bot():
    # Khởi tạo user_states
    load_user_states()
    
    # Khởi tạo application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Khởi tạo AdminHandlers và đăng ký handlers
    admin_handlers = AdminHandlers(application, user_states)
    
    # Thêm handlers cơ bản
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_admin_action))
    
    # Thêm handlers cho admin commands
    application.add_handler(CommandHandler("admin", admin_handlers.admin_menu))
    application.add_handler(CommandHandler("shift", admin_handlers.handle_shift_menu))
    application.add_handler(CommandHandler("break", admin_handlers.handle_break_menu))
    application.add_handler(CommandHandler("stats", admin_handlers.handle_stats_menu))
    application.add_handler(CommandHandler("report", admin_handlers.handle_report_menu))
    application.add_handler(CommandHandler("reset", admin_handlers.handle_reset_data))
    
    # Thêm handlers cho lệnh tắt
    application.add_handler(CommandHandler("as", admin_handlers.handle_all_start_shift_command))
    application.add_handler(CommandHandler("ae", admin_handlers.handle_all_end_shift_command))
    application.add_handler(CommandHandler("fb", admin_handlers.handle_force_break_command))
    application.add_handler(CommandHandler("eb", admin_handlers.handle_end_break_command))
    application.add_handler(CommandHandler("ts", admin_handlers.handle_today_stats_command))
    application.add_handler(CommandHandler("st", admin_handlers.handle_all_stats_command))
    application.add_handler(CommandHandler("dr", admin_handlers.handle_daily_report_command))
    application.add_handler(CommandHandler("wr", admin_handlers.handle_weekly_report_command))
    
    # Thêm handler cho lệnh help
    application.add_handler(CommandHandler("help", help_command))
    
    # Khởi tạo job queue
    job_queue = application.job_queue
    job_queue.run_repeating(periodic_check, interval=300)
    job_queue.run_repeating(save_all_user_states, interval=300)
    job_queue.run_daily(auto_end_shift, time=time(hour=1, minute=0))
    job_queue.run_daily(send_daily_report, time=time(hour=1, minute=5))
    
    logger.info("Bot đã sẵn sàng và đang chạy...")
    
    # Khởi động bot
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("Đã dừng ứng dụng theo yêu cầu")
    except Exception as e:
        logger.error(f"Lỗi không mong muốn: {e}")