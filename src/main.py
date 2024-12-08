#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date, time
import pytz
import logging
from logging.handlers import RotatingFileHandler
import coloredlogs
import sqlite3
import hashlib
import os
from pathlib import Path
import configparser
from tabulate import tabulate
import emoji
import json
from telegram.error import Forbidden, BadRequest
import subprocess
import pkg_resources
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil
from dotenv import load_dotenv
import time as systime
import pickle
import sys
import codecs
from typing import Dict
from .models import UserState, Violation
from src.services.violation_manager import ViolationManager
from src.utils.helpers import (
    save_user_states,
    generate_today_stats,
    generate_weekly_report,
    generate_daily_report
)

# Thêm thư mục gốc vào PYTHONPATH
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

from src.admin_handlers import AdminHandlers
from src.utils.config import (
    BOT_TOKEN, 
    ADMIN_ID,
    MAIN_ADMIN_ID,
    VN_TIMEZONE,
    BREAK_DURATIONS,
    BREAK_FREQUENCIES
)

# Load environment variables
load_dotenv()

# Cấu hình base directory
BASE_DIR = Path(__file__).parent.parent
STATE_FILE = BASE_DIR / 'data' / 'user_states.pkl'
HISTORY_FILE = BASE_DIR / 'data' / 'attendance_history.json'

# Tạo thư mục data và logs nếu chưa tồn tại
(BASE_DIR / 'data').mkdir(exist_ok=True)
(BASE_DIR / 'logs').mkdir(exist_ok=True)

# Cấu hình để xử lý Unicode trên Windows
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Cấu hình logging
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger,
                   fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Thêm file handler để lưu log
log_file = BASE_DIR / 'logs' / 'bot.log'
file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Khởi tạo violation manager
violation_manager = ViolationManager()

# Khởi tạo biến user_states toàn cục
user_states: Dict[str, UserState] = {}

def save_user_states(state: dict) -> None:
    """Lưu trạng thái người dùng"""
    try:
        # Giữ nguyên code xử lý hiện tại của bạn
        pass
    except Exception as e:
        logging.error(f"Lỗi khi lưu user states: {str(e)}")

def load_user_states():
    """Đọc trạng thái người dùng từ file"""
    global user_states
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'rb') as f:
                user_states = pickle.load(f)
        except Exception as e:
            logger.error(f"Lỗi khi đọc user states: {e}")
            user_states = {}

# Initialize bot application
application = Application.builder().token(BOT_TOKEN).build()

# Load user states
load_user_states()

# Initialize admin handlers 
admin_handlers = AdminHandlers(application, user_states)

# Log current state
logging.info(f"Loaded {len(user_states)} user states")

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is admin"""
    return update.effective_user.id in ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /start"""
    keyboard = [
        [
            KeyboardButton("🚀 Lên ca (上班)"),
            KeyboardButton("🏁 Xuống ca (下班)")
        ],
        [
            KeyboardButton("🍚 Ăn cơm (吃饭)"),
            KeyboardButton("🚬 Hút thuốc (抽烟)")
        ],
        [
            KeyboardButton("↩️ Trở lại chỗ ngồi (返回)"),
            KeyboardButton("🚽 Vệ sinh (厕所)")
        ]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Chào mừng! Vui lòng chọn thao tác:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    user_id = str(user.id)
    
    if user_id not in user_states:
        user_states[user_id] = UserState(user_name=user.full_name)
    
    state = user_states[user_id]
    now = datetime.now(VN_TIMEZONE)
    
    # Xử lý các nút chính
    if text == "🚀 Lên ca (上班)":
        await handle_start_shift(update, state, now)
    
    elif text == "🏁 Xuống ca (下班)":
        await handle_end_shift(update, state, now)
        
    elif text == "🍚 Ăn cơm (吃饭)":
        await handle_break(update, state, now, "🍚 Ăn cơm (吃饭)", context)
        
    elif text == "🚬 Hút thuốc (抽烟)":
        await handle_break(update, state, now, "🚬 Hút thuốc (抽烟)", context)
        
    elif text == "🚽 Vệ sinh (厕所)":
        await handle_break(update, state, now, "🚽 Vệ sinh (厕所)", context)
        
    elif text == "↩️ Trở lại chỗ ngồi (返回)":
        await handle_end_break(update, state, now, context)

async def handle_start_shift(update, state, now):
    """Xử lý lên ca"""
    if state.is_working:
        await update.message.reply_text("❌ Bạn đã bắt đầu ca làm việc rồi!")
        return
        
    state.is_working = True
    state.start_time = now
    state.breaks = {k: timedelta(0) for k in BREAK_DURATIONS.keys()}
    state.break_counts = {k: 0 for k in BREAK_DURATIONS.keys()}
    save_user_states(state)
    
    await update.message.reply_text(
        f"✅ Đã bắt đầu ca làm việc lúc {now.strftime('%H:%M:%S')}"
    )

async def handle_end_shift(update, state, now):
    """Xử lý xuống ca"""
    if not state.is_working:
        await update.message.reply_text("❌ Bạn chưa bắt đầu ca làm việc!")
        return
            
    if state.current_break:
        await update.message.reply_text("❌ Vui lòng kết thúc giờ nghỉ trước khi kết thúc ca!")
        return
        
    state.is_working = False
    state.end_time = now
    total_time = now - state.start_time
    total_breaks = sum(state.breaks.values(), timedelta())
    work_time = total_time - total_breaks
    
    report = (
        f"📋 Báo cáo ca làm việc:\n"
        f"⏰ Thời gian bắt đầu: {state.start_time.strftime('%H:%M:%S')}\n"
        f"⌛️ Thời gian kết thúc: {now.strftime('%H:%M:%S')}\n"
        f"⏱ Tổng thời gian: {str(total_time).split('.')[0]}\n"
        f"🚽 Tổng thời gian nghỉ: {str(total_breaks).split('.')[0]}\n"
        f"💪 Thời gian làm việc thực tế: {str(work_time).split('.')[0]}\n\n"
        f"📊 Chi tiết giờ ngh:"
    )
    
    for break_type, duration in state.breaks.items():
        if duration > timedelta(0):
            report += f"\n{break_type}: {str(duration).split('.')[0]}"
    
    save_user_states(state)
    await update.message.reply_text(report)

async def handle_break(update, state, now, break_type, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý các loại nghỉ"""
    if not state.is_working:
        await update.message.reply_text("❌ Bạn chưa bắt đầu ca làm việc!")
        return
        
    if state.current_break:
        await update.message.reply_text("❌ Bạn đang trong giờ nghỉ!")
        return
        
    current_count = state.break_counts.get(break_type, 0)
    state.current_break = break_type
    state.break_start_time = now
    state.break_counts[break_type] = current_count + 1
    save_user_states(state)
    
    duration = BREAK_DURATIONS[break_type]
    message = f"✅ Bắt đầu {break_type}\n⏰ Thời gian cho phép: {duration} phút\n"
    message += f"📊 Số lần đã nghỉ: {current_count + 1}/{BREAK_FREQUENCIES[break_type]}"
    
    if current_count >= BREAK_FREQUENCIES[break_type]:
        # Thêm cảnh báo nếu vượt số lần cho phép
        message = "⚠️ CẢNH BÁO: " + message
        message += f"\n❌ Bạn đã vượt quá số lần {break_type} cho phép!"
        
        # Thông báo admin
        await notify_admins_violation(
            context,
            state.user_name,
            f"❌ Vượt số lần {break_type} ({current_count + 1}/{BREAK_FREQUENCIES[break_type]})"
        )
    
    await update.message.reply_text(message)

async def handle_end_break(update, state, now, context):
    """Xử lý kết thúc nghỉ"""
    if not state.current_break:
        await update.message.reply_text("❌ Bạn không trong giờ nghỉ!")
        return
        
    break_duration = now - state.break_start_time
    state.breaks[state.current_break] += break_duration
    allowed_duration = timedelta(minutes=BREAK_DURATIONS[state.current_break])
    
    if break_duration > allowed_duration:
        overtime = break_duration - allowed_duration
        await update.message.reply_text(
            f"⚠️ Cảnh báo: Bạn đã nghỉ quá giờ {str(overtime).split('.')[0]}"
        )
        # Thông báo admin khi quá giờ
        await notify_admins_violation(
            context,
            state.user_name,
            f"⏰ Nghỉ quá giờ {str(overtime).split('.')[0]} (cho phép {BREAK_DURATIONS[state.current_break]} phút)"
        )
    
    state.current_break = None
    state.break_start_time = None
    save_user_states(state)
    
    await update.message.reply_text(
        f"✅ Đã kết thúc nghỉ\n"
        f"⏱ Thời gian nghỉ: {str(break_duration).split('.')[0]}"
    )

async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý các action từ menu admin"""
    query = update.callback_query
    action = query.data
    
    if not admin_handlers:
        await query.answer("❌ Lỗi: Admin handlers chưa được khởi tạo!")
        return
        
    try:
        # Map action với hàm xử lý tương ứng
        action_handlers = {
            "all_start_shift": admin_handlers.handle_all_start_shift,
            "all_end_shift": admin_handlers.handle_all_end_shift,
            "force_break": admin_handlers.handle_force_break,
            "end_break": admin_handlers.handle_end_break,
            "today_stats": admin_handlers.handle_today_stats,
            "all_stats": admin_handlers.handle_all_stats,
            "daily_report": admin_handlers.handle_daily_report,
            "weekly_report": admin_handlers.handle_weekly_report,
            "back_admin": admin_handlers.admin_menu,
            "confirm_reset": admin_handlers.handle_reset_callback,
            "cancel_reset": admin_handlers.handle_reset_callback,
            "admin_shift": admin_handlers.handle_shift_menu,
            "admin_break": admin_handlers.handle_break_menu,
            "admin_stats": admin_handlers.handle_stats_menu,
            "admin_report": admin_handlers.handle_report_menu
        }
        
        if action in action_handlers:
            await action_handlers[action](update, context)
            
    except Exception as e:
        logger.error(f"Lỗi khi xử lý admin action: {e}")
        await query.answer("❌ Đã xảy ra lỗi khi thực hiện hành động!")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý callback từ các nút bấm"""
    query = update.callback_query
    
    try:
        # Kiểm tra nếu là callback từ menu admin
        if query.data.startswith('admin_'):
            if admin_handlers:
                await admin_handlers.admin_button_callback(update, context)
            return
        elif query.data in ["all_start_shift", "all_end_shift", 
                          "force_break", "end_break",
                          "today_stats", "all_stats",
                          "daily_report", "weekly_report"]:
            await handle_admin_action(update, context)
            return
            
        await query.answer()
    except Exception as e:
        logger.error(f"Lỗi khi xử lý callback: {e}")
        await query.answer("❌ Đã xảy ra lỗi!")

async def handle_violation_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xem báo cáo vi phạm"""
    if update.effective_user.id not in ADMIN_ID:
        await update.message.reply_text("⛔️ Bạn không có quyền xem báo cáo!")
        return
        
    # Lấy báo cáo vi phạm trong ngày
    start_of_day = datetime.now(VN_TIMEZONE).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    report = violation_manager.generate_violation_report(start_of_day)
    
    await update.message.reply_text(report)

async def periodic_check(context: ContextTypes.DEFAULT_TYPE):
    """Kiểm tra định kỳ các vi phạm"""
    now = datetime.now(VN_TIMEZONE)
    for user_id, state in user_states.items():
        if state.is_working and state.current_break:
            break_duration = now - state.break_start_time
            allowed_duration = timedelta(minutes=BREAK_DURATIONS[state.current_break])
            if break_duration > allowed_duration:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"⚠️ Cảnh báo: Bạn đã nghỉ quá giờ {str(break_duration - allowed_duration).split('.')[0]}"
                    )
                except (Forbidden, BadRequest):
                    logger.warning(f"Không thể gửi cảnh báo tới user {user_id}")

async def save_all_user_states(context: ContextTypes.DEFAULT_TYPE):
    """Lưu trạng thái tất cả users định kỳ"""
    try:
        active_users = len([u for u in user_states.values() if u.is_working])
        logger.info(f"Đang lưu trạng thái: {len(user_states)} users, {active_users} đang hoạt động")
        save_user_states(user_states)
    except Exception as e:
        logger.error(f"Lỗi khi lưu user states: {e}")

async def auto_end_shift(context: ContextTypes.DEFAULT_TYPE):
    """Tự động kết thúc ca làm việc lúc 1h sáng"""
    now = datetime.now(VN_TIMEZONE)
    count = 0
    for user_id, state in user_states.items():
        if state.is_working:
            state.is_working = False
            state.end_time = now
            count += 1
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🔔 Ca làm việc của bạn đã được tự động kết thúc"
                )
            except (Forbidden, BadRequest):
                logger.warning(f"Không thể gửi thông báo tới user {user_id}")
    
    save_user_states()
    logger.info(f"Đã tự động kết thúc ca cho {count} người")

async def send_daily_report(context: ContextTypes.DEFAULT_TYPE):
    """Gửi báo cáo hàng ngày cho admin"""
    yesterday = datetime.now(VN_TIMEZONE) - timedelta(days=1)
    
    # Tạo báo cáo vi phạm
    violation_report = violation_manager.generate_violation_report(yesterday)
    
    # Tạo báo cáo tổng hợp
    daily_report = generate_daily_report(user_states)
    
    final_report = f"📊 Báo cáo ngày {yesterday.strftime('%d/%m/%Y')}:\n\n"
    final_report += daily_report + "\n\n"
    final_report += "🚫 Báo cáo vi phạm:\n" + violation_report
    
    for admin_id in ADMIN_ID:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=final_report
            )
        except (Forbidden, BadRequest):
            logger.warning(f"Không thể gửi báo cáo tới admin {admin_id}")

async def notify_admins_violation(context: ContextTypes.DEFAULT_TYPE, user_name: str, violation_msg: str):
    """Gửi thông báo vi phạm tới admin"""
    message = f"⚠️ VI PHẠM\n {user_name}\n{violation_msg}"
    
    for admin_id in ADMIN_ID:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=message
            )
        except (Forbidden, BadRequest):
            logger.warning(f"Không thể gửi thông báo vi phạm tới admin {admin_id}")

async def get_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lấy danh sách thành viên trong group"""
    try:
        chat_id = update.effective_chat.id
        members = await context.bot.get_chat_administrators(chat_id)
        logging.info(f"Got {len(members)} chat members")
        return members
    except Exception as e:
        logging.error(f"Lỗi khi lấy danh sách thành viên: {e}")
        return []

async def handle_all_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh admin cho tất cả lên ca"""
    try:
        # Kiểm tra quyền admin
        if not await is_admin(update, context):
            return
            
        # Lấy danh sách thành viên
        chat_members = await get_chat_members(update, context)
        logging.info(f"Processing {len(chat_members)} members for all start")
        
        count = 0
        for member in chat_members:
            if not member.user.is_bot:
                user_id = member.user.id
                user_states[user_id] = {
                    'is_working': True,
                    'start_time': datetime.now(),
                    'break_time': 0
                }
                count += 1
        
        save_user_states(user_states)
        await update.message.reply_text(f"✅ Đã cho {count} người lên ca!")
        
    except Exception as e:
        logging.error(f"Lỗi khi cho tất cả lên ca: {e}")
        await update.message.reply_text("❌ Có lỗi xảy ra!")

def check_working_status(user_id: int) -> bool:
    """Kiểm tra user đã lên ca chưa"""
    return (user_id in user_states and 
            user_states[user_id].get('is_working', False))

async def handle_end_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Kiểm tra đã lên ca chưa
    if not check_working_status(user_id):
        await update.message.reply_text("❌ Bạn chưa bắt đầu ca làm việc!")
        return
    
    # Xử lý xuống ca
    # ... code xử lý ...

if __name__ == "__main__":
    # Khởi tạo logging
    logging.info("Starting bot...")
    
    # Load trạng thái user
    load_user_states()
    
    # Log trạng thái hiện tại
    logging.info(f"Loaded {len(user_states)} user states")