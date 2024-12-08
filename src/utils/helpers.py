import pickle
from pathlib import Path
import logging
from typing import Dict
from datetime import datetime, timedelta

from src.models import UserState
from src.utils.config import VN_TIMEZONE

logger = logging.getLogger(__name__)

# Cấu hình base directory
BASE_DIR = Path(__file__).parent.parent.parent
STATE_FILE = BASE_DIR / 'data' / 'user_states.pkl'

def save_user_states(user_states: Dict[str, UserState]):
    """Lưu trạng thái người dùng vào file"""
    try:
        logger.debug(f"Đang lưu {len(user_states)} trạng thái người dùng")
        for user_id, state in user_states.items():
            logger.debug(f"Lưu trạng thái cho user {state.user_name}")
        
        with open(STATE_FILE, 'wb') as f:
            pickle.dump(user_states, f)
        logger.info("Đã lưu trạng thái người dùng thành công")
    except Exception as e:
        logger.error(f"Lỗi khi lưu user states: {e}")

def generate_today_stats(user_states: Dict[str, UserState]) -> str:
    """Tạo thống kê hôm nay"""
    now = datetime.now(VN_TIMEZONE)
    stats = f"📊 Thống kê ngày {now.strftime('%d/%m/%Y')}:\n\n"
    
    has_data = False
    for state in user_states.values():
        if state.is_working or (state.start_time and state.start_time.date() == now.date()):
            has_data = True
            stats += f"👤 {state.user_name}:\n"
            if state.is_working:
                work_time = now - state.start_time
                total_breaks = sum(state.breaks.values(), timedelta())
                actual_work = work_time - total_breaks
                stats += f"⏱ Đang làm: {str(actual_work).split('.')[0]}\n"
                if state.current_break:
                    stats += f"🚽 Đang nghỉ: {state.current_break}\n"
            elif state.end_time:
                work_time = state.end_time - state.start_time
                total_breaks = sum(state.breaks.values(), timedelta())
                actual_work = work_time - total_breaks
                stats += f"⏱ Đã làm: {str(actual_work).split('.')[0]}\n"
            else:
                stats += "🔴 Đã xuống ca\n"
            
            stats += "🚽 Số lần nghỉ:\n"
            for break_type, count in state.break_counts.items():
                stats += f"- {break_type}: {count}\n"
            stats += "\n"
    
    if not has_data:
        stats += "Không có dữ liệu cho ngày hôm nay"
    
    return stats

def generate_weekly_report(user_states: Dict[str, UserState]) -> str:
    """Tạo báo cáo tuần"""
    now = datetime.now(VN_TIMEZONE)
    start_of_week = now - timedelta(days=now.weekday())
    report = f"📑 Báo cáo tuần {start_of_week.strftime('%d/%m')} - {now.strftime('%d/%m/%Y')}:\n\n"
    
    for state in user_states.values():
        if state.start_time and state.start_time.date() >= start_of_week.date():
            report += f"👤 {state.user_name}:\n"
            total_work = timedelta()
            total_breaks = timedelta()
            
            if state.end_time:
                total_work = state.end_time - state.start_time
                total_breaks = sum(state.breaks.values(), timedelta())
            
            report += f"⏱ Tổng thời gian làm: {str(total_work).split('.')[0]}\n"
            report += f"🚽 Tổng thời gian nghỉ: {str(total_breaks).split('.')[0]}\n\n"
    return report

def generate_daily_report(user_states: Dict[str, UserState]) -> str:
    """Tạo báo cáo ngày"""
    today = datetime.now(VN_TIMEZONE).date()
    report = f"📋 Báo cáo ngày {today.strftime('%d/%m/%Y')}:\n\n"
    
    has_data = False
    for state in user_states.values():
        if state.is_working or (state.start_time and state.start_time.date() == today):
            has_data = True
            report += f"👤 {state.user_name}:\n"
            
            if state.is_working:
                current_time = datetime.now(VN_TIMEZONE)
                work_duration = current_time - state.start_time
                total_breaks = sum(state.breaks.values(), timedelta())
                actual_work = work_duration - total_breaks
                report += f"⏱ Đang làm: {str(actual_work).split('.')[0]}\n"
                report += f"⏰ Bắt đầu: {state.start_time.strftime('%H:%M:%S')}\n"
                
                if state.current_break:
                    break_duration = current_time - state.break_start_time
                    report += f"🚽 Đang nghỉ: {state.current_break} ({str(break_duration).split('.')[0]})\n"
            
            elif state.end_time:
                work_duration = state.end_time - state.start_time
                total_breaks = sum(state.breaks.values(), timedelta())
                actual_work = work_duration - total_breaks
                report += f"✅ Đã xong ca\n"
                report += f"⏰ Thời gian làm thực tế: {str(actual_work).split('.')[0]}\n"
            
            report += f"🚽 Tổng thời gian nghỉ: {str(sum(state.breaks.values(), timedelta())).split('.')[0]}\n"
            report += f"📊 Số lần nghỉ: {sum(state.break_counts.values())}\n\n"
    
    if not has_data:
        report += "Không có dữ liệu cho ngày hôm nay"
    
    return report