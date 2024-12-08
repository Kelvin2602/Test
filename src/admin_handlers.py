import sys
import os
from pathlib import Path

# Thêm thư mục gốc vào PYTHONPATH
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from telegram.ext import Application, ContextTypes, CommandHandler, CallbackQueryHandler
from datetime import datetime, timedelta
from typing import Dict
import logging
import json

from src.utils.config import ADMIN_ID, VN_TIMEZONE, BREAK_DURATIONS, BREAK_FREQUENCIES
from src.models import UserState
from src.utils.helpers import generate_today_stats, generate_weekly_report, save_user_states, generate_daily_report

logger = logging.getLogger(__name__)

def calculate_work_hours(state):
    """Calculate total work hours for a user state"""
    if not state.start_time:
        return timedelta(0)
        
    end = state.end_time if state.end_time else datetime.now(VN_TIMEZONE)
    total_time = end - state.start_time
    total_breaks = sum(state.breaks.values(), timedelta())
    return total_time - total_breaks

class AdminHandlers:
    def __init__(self, application: Application, user_states: Dict[str, UserState]):
        self.application = application
        self.user_states = user_states
        self._register_handlers()

    def _register_handlers(self):
        """Đăng ký các command handlers"""
        commands = {
            "admin": self.admin_menu,
            "shift": self.handle_shift_menu,
            "break": self.handle_break_menu,
            "stats": self.handle_stats_menu,
            "report": self.handle_report_menu,
            "allstart": self.handle_all_start_shift,
            "allend": self.handle_all_end_shift,
            "reset": self.handle_reset_data,
            "as": self.handle_all_start_shift_command,
            "ae": self.handle_all_end_shift_command,
            "fb": self.handle_force_break_command,
            "eb": self.handle_end_break_command,
            "ts": self.handle_today_stats_command,
            "st": self.handle_all_stats_command,
            "dr": self.handle_daily_report_command,
            "wr": self.handle_weekly_report_command,
        }
        
        for command, handler in commands.items():
            self.application.add_handler(CommandHandler(command, handler))
            
        # Callback handler cho các nút bấm
        self.application.add_handler(CallbackQueryHandler(self.button_callback))

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý tất cả các callback"""
        query = update.callback_query
        if query.from_user.id not in ADMIN_ID:
            await query.answer("⛔️ Bạn không có quyền!")
            return
            
        await query.answer()
        
        # Map các callback với handler tương ứng
        callbacks = {
            "all_start_shift": self.handle_all_start_shift,
            "all_end_shift": self.handle_all_end_shift,
            "force_break": self.handle_force_break,
            "end_break": self.handle_end_break,
            "today_stats": self.handle_today_stats,
            "all_stats": self.handle_all_stats,
            "daily_report": self.handle_daily_report,
            "weekly_report": self.handle_weekly_report,
            "back_admin": self.admin_menu,
            "confirm_reset": self.handle_reset_callback,
            "cancel_reset": self.handle_reset_callback
        }
        
        if query.data in callbacks:
            await callbacks[query.data](update, context)

    async def admin_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị menu admin với các lệnh tắt"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền admin!")
            return
        
        help_text = """
🔰 *Các lệnh tắt cho Admin:*

*Quản lý ca:*
/as - Tất cả lên ca
/ae - Tất cả xuống ca

*Quản lý nghỉ:*
/fb - Bắt đầu nghỉ
/eb - Kết thúc nghỉ

*Thống kê & Báo cáo:*
/ts - Thống kê hôm nay
/st - Thống kê tổng
/dr - Báo cáo ngày
/wr - Báo cáo tuần

*Menu chính:*
/admin - Hiện menu này
/shift - Menu quản lý ca
/break - Menu quản lý nghỉ
/reset - Reset dữ liệu
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def handle_shift_menu(self, query):
        keyboard = [
            [
                InlineKeyboardButton("🚀 Tất cả lên ca", callback_data="all_start_shift"),
                InlineKeyboardButton("🏁 Tất cả xuống ca", callback_data="all_end_shift")
            ],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="back_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="🔰 Quản lý ca làm việc:",
            reply_markup=reply_markup
        )

    async def handle_break_menu(self, query):
        keyboard = [
            [
                InlineKeyboardButton("➕ Bắt đầu nghỉ", callback_data="force_break"),
                InlineKeyboardButton("➖ Kết thúc nghỉ", callback_data="end_break")
            ],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="back_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="🔰 Quản lý nghỉ:",
            reply_markup=reply_markup
        )

    async def handle_stats_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý menu thống kê"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền xem thống kê!")
            return
        
        keyboard = [
            [
                InlineKeyboardButton("📈 Thống kê hôm nay", callback_data="today_stats"),
                InlineKeyboardButton("📊 Thống kê tổng", callback_data="all_stats")
            ],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="back_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if isinstance(update.effective_message, Message):
            await update.effective_message.reply_text("📊 Chọn loại thống kê:", reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.edit_message_text("📊 Chọn loại thống kê:", reply_markup=reply_markup)

    async def handle_report_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý menu báo cáo"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền xem báo cáo!")
            return
        
        keyboard = [
            [
                InlineKeyboardButton("📋 Báo cáo ngày", callback_data="daily_report"),
                InlineKeyboardButton("📑 Báo cáo tuần", callback_data="weekly_report")
            ],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="back_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if isinstance(update.effective_message, Message):
            await update.effective_message.reply_text("📝 Chọn loại báo cáo:", reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.edit_message_text("📝 Chọn loại báo cáo:", reply_markup=reply_markup)

    async def handle_all_start_shift(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cho tất cả nhân viên lên ca"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền thực hiện hành động này!")
            return
        
        now = datetime.now(VN_TIMEZONE)
        count = 0
        for state in self.user_states.values():
            if not state.is_working:
                state.is_working = True
                state.start_time = now
                state.breaks = {k: timedelta(0) for k in BREAK_DURATIONS.keys()}
                state.break_counts = {k: 0 for k in BREAK_DURATIONS.keys()}
                state.current_break = None
                state.break_start_time = None
                count += 1
        save_user_states(self.user_states)
        await update.message.reply_text(f"✅ Đã cho {count} nhân viên lên ca")

    async def handle_all_end_shift(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cho tất cả nhân viên xuống ca"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền thực hiện hành động này!")
            return
        
        now = datetime.now(VN_TIMEZONE)
        count = 0
        for state in self.user_states.values():
            if state.is_working and not state.current_break:
                state.is_working = False
                state.end_time = now
                count += 1
        save_user_states(self.user_states)
        await update.message.reply_text(f"✅ Đã cho {count} nhân viên xuống ca")

    async def handle_force_break(self, query):
        """Bắt đầu giờ nghỉ cho nhân viên"""
        keyboard = []
        for break_type in BREAK_DURATIONS.keys():
            keyboard.append([InlineKeyboardButton(
                f"➕ {break_type}", 
                callback_data=f"force_{break_type}"
            )])
        keyboard.append([InlineKeyboardButton("⬅️ Quay lại", callback_data="admin_break")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🔰 Chọn loại nghỉ:",
            reply_markup=reply_markup
        )

    async def handle_today_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị thống kê hôm nay"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền!")
            return
        
        now = datetime.now(VN_TIMEZONE)
        stats = f"📊 Thống kê ngày {now.strftime('%d/%m/%Y')}:\n\n"
        
        for state in self.user_states.values():
            if state.start_time and state.start_time.date() == now.date():
                stats += f"👤 {state.user_name}:\n"
                if state.is_working:
                    work_time = now - state.start_time
                    total_breaks = sum(state.breaks.values(), timedelta())
                    actual_work = work_time - total_breaks
                    stats += f"⏱ Đã làm: {str(actual_work).split('.')[0]}\n"
                    if state.current_break:
                        stats += f"🚽 Đang nghỉ: {state.current_break}\n"
                else:
                    stats += "🔴 Đã xuống ca\n"
                    if state.end_time:
                        work_time = state.end_time - state.start_time
                        total_breaks = sum(state.breaks.values(), timedelta())
                        actual_work = work_time - total_breaks
                        stats += f"⏱ Thời gian làm: {str(actual_work).split('.')[0]}\n"
                stats += "\n"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(stats)
        else:
            await update.message.reply_text(stats)

    async def handle_all_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị thống kê tổng"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền xem thống kê!")
            return
        
        stats = "📊 Thống kê tổng:\n\n"
        has_data = False
        
        for state in self.user_states.values():
            has_data = True
            stats += f"👤 {state.user_name}:\n"
            stats += f"🟢 Trạng thái: {'Đang làm' if state.is_working else 'Không làm'}\n"
            if state.current_break:
                stats += f"🚽 Đang nghỉ: {state.current_break}\n"
            if state.start_time:
                stats += f"⏰ Bắt đầu ca: {state.start_time.strftime('%H:%M:%S')}\n"
            stats += "\n"
        
        if not has_data:
            stats += "Chưa có dữ liệu"
        
        await update.message.reply_text(stats)

    async def handle_daily_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị báo cáo ngày"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền xem báo cáo!")
            return
        
        report = generate_daily_report(self.user_states)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(report)
        else:
            await update.message.reply_text(report)

    async def handle_weekly_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị báo cáo tuần"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền!")
            return
        
        now = datetime.now(VN_TIMEZONE)
        start_of_week = now - timedelta(days=now.weekday())
        report = f"📑 Báo cáo tuần {start_of_week.strftime('%d/%m')} - {now.strftime('%d/%m/%Y')}:\n\n"
        
        for state in self.user_states.values():
            if state.start_time and state.start_time.date() >= start_of_week.date():
                report += f"👤 {state.user_name}:\n"
                total_work = timedelta()
                total_breaks = timedelta()
                
                if state.end_time:
                    total_work = state.end_time - state.start_time
                    total_breaks = sum(state.breaks.values(), timedelta())
                    actual_work = total_work - total_breaks
                    report += f"⏱ Thời gian làm thực tế: {str(actual_work).split('.')[0]}\n"
                elif state.is_working:
                    total_work = now - state.start_time
                    total_breaks = sum(state.breaks.values(), timedelta())
                    actual_work = total_work - total_breaks
                    report += f"⏱ Đang làm: {str(actual_work).split('.')[0]}\n"
                
                report += f"🚽 Tổng thời gian nghỉ: {str(total_breaks).split('.')[0]}\n\n"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(report)
        else:
            await update.message.reply_text(report)

    async def handle_end_break(self, query):
        """Kết thúc giờ nghỉ cho nhân viên"""
        keyboard = []
        for break_type in BREAK_DURATIONS.keys():
            keyboard.append([InlineKeyboardButton(
                f"➖ {break_type}", 
                callback_data=f"end_{break_type}"
            )])
        keyboard.append([InlineKeyboardButton("⬅️ Quay lại", callback_data="admin_break")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🔰 Chọn loại nghỉ:",
            reply_markup=reply_markup
        )

    async def handle_force_break_type(self, query, break_type):
        """Xử l bắt đầu nghỉ theo loại"""
        count = 0
        for state in self.user_states.values():
            if state.is_working and check_break_frequency(state, break_type):
                state.break_start_time = datetime.now(VN_TIMEZONE)
                state.current_break = break_type
                count += 1
        save_user_states(self.user_states)
        await query.edit_message_text(f"✅ Đã cho {count} nhân viên bắt đầu {break_type}")

    async def handle_end_break_type(self, query, break_type):
        """Xử lý kết thúc nghỉ theo loại"""
        now = datetime.now(VN_TIMEZONE)
        count = 0
        for state in self.user_states.values():
            if state.is_working and state.current_break == break_type:
                break_duration = now - state.break_start_time
                state.breaks[break_type] += break_duration
                state.break_counts[break_type] += 1
                state.current_break = None
                state.break_start_time = None
                count += 1
        save_user_states(self.user_states)
        await query.edit_message_text(f"✅ Đã cho {count} nhân viên kết thúc {break_type}")

    async def handle_shift_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /shift"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền quản lý ca!")
            return
        help_text = (
            "🔰 Quản lý ca làm việc:\n\n"
            "/allstart - Cho tất cả lên ca\n"
            "/allend - Cho tất cả xuống ca"
        )
        await update.message.reply_text(help_text)

    async def handle_break_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /break"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền quản lý giờ nghỉ!")
            return
        help_text = (
            "🔰 Quản lý giờ nghỉ:\n\n"
            "Các loại nghỉ:\n"
            "- 🚻 Vệ sinh (厕所)\n"
            "- 🍱 Ăn trưa (午饭)\n"
            "- ☕️ Giải lao (休息)"
        )
        await update.message.reply_text(help_text)

    async def handle_stats_menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /stats"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền xem thống kê!")
            return
        keyboard = [
            [
                InlineKeyboardButton("📈 Thống kê hm nay", callback_data="today_stats"),
                InlineKeyboardButton("📊 Thống kê tổng", callback_data="all_stats")
            ],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="back_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(" Chọn loại thống kê:", reply_markup=reply_markup)

    async def handle_report_menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /report"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền xem báo cáo!")
            return
        keyboard = [
            [
                InlineKeyboardButton("📋 Báo cáo ngày", callback_data="daily_report"),
                InlineKeyboardButton("📑 Báo cáo tuần", callback_data="weekly_report")
            ],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="back_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("📝 Chọn loại báo cáo:", reply_markup=reply_markup)

    async def handle_shift_menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /shift"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền quản lý ca!")
            return
        keyboard = [
            [
                InlineKeyboardButton("🚀 Tất cả lên ca", callback_data="all_start_shift"),
                InlineKeyboardButton("🏁 Tất cả xuống ca", callback_data="all_end_shift")
            ],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="back_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🔰 Quản lý ca làm việc:", reply_markup=reply_markup)

    async def handle_break_menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /break"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền quản lý giờ nghỉ!")
            return
        keyboard = [
            [
                InlineKeyboardButton("➕ Bắt đầu nghỉ", callback_data="force_break"),
                InlineKeyboardButton("➖ Kết thúc nghỉ", callback_data="end_break")
            ],
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="back_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🔰 Quản lý giờ nghỉ:", reply_markup=reply_markup)

    async def handle_reset_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /reset - Reset toàn bộ dữ liệu"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền reset dữ liệu!")
            return
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Xác nhận", callback_data="confirm_reset"),
                InlineKeyboardButton("❌ Hủy", callback_data="cancel_reset")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ CẢNH BÁO: Hành động này sẽ:\n"
            "- Xóa toàn bộ dữ liệu chấm công\n"
            "- Reset trạng thái tất cả nhân viên\n"
            "- Xóa lịch sử vi phạm\n\n"
            "Bạn có chắc chắn muốn tiếp tục?",
            reply_markup=reply_markup
        )

    async def handle_reset_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý callback khi reset data"""
        query = update.callback_query
        
        if query.data == "confirm_reset":
            try:
                data_dir = BASE_DIR / 'data'
                data_dir.mkdir(exist_ok=True)
                
                # Reset user states
                for state in self.user_states.values():
                    state.is_working = False
                    state.start_time = None
                    state.end_time = None
                    state.breaks = {k: timedelta(0) for k in BREAK_DURATIONS.keys()}
                    state.break_counts = {k: 0 for k in BREAK_DURATIONS.keys()}
                    state.current_break = None
                    state.break_start_time = None
                
                # Xóa lịch sử chấm công
                attendance_file = data_dir / 'attendance_history.json'
                if attendance_file.exists():
                    with open(attendance_file, 'w', encoding='utf-8') as f:
                        json.dump({}, f, ensure_ascii=False, indent=4)
                
                # Xóa lịch sử vi phạm
                violations_file = data_dir / 'violations.json'
                if violations_file.exists():
                    with open(violations_file, 'w', encoding='utf-8') as f:
                        json.dump([], f, ensure_ascii=False, indent=4)
                
                # Lưu trạng thái đã reset
                save_user_states(self.user_states)
                
                await query.edit_message_text("✅ Đã reset toàn bộ dữ liệu thành công!")
                logger.info("Admin đã reset toàn bộ dữ liệu")
                
            except Exception as e:
                logger.error(f"Lỗi khi reset dữ liệu: {e}")
                await query.edit_message_text("❌ Đã xảy ra lỗi khi reset dữ liệu!")
                
        elif query.data == "cancel_reset":
            await query.edit_message_text("🚫 Đã hủy thao tác reset dữ liệu!")

    async def handle_callback_query(self, query: CallbackQuery):
        """X lý các callback query"""
        if query.data == "today_stats":
            stats = generate_today_stats(self.user_states)
            await query.edit_message_text(stats)
            
        elif query.data == "all_stats":
            stats = self.generate_all_stats()
            await query.edit_message_text(stats)
            
        elif query.data == "daily_report":
            report = self.generate_daily_report()
            await query.edit_message_text(report)
            
        elif query.data == "weekly_report":
            report = generate_weekly_report(self.user_states)
            await query.edit_message_text(report)

    def generate_all_stats(self):
        """Tạo thống kê tổng"""
        stats = "📊 Thống kê tổng:\n\n"
        for state in self.user_states.values():
            stats += f"👤 {state.user_name}:\n"
            if state.is_working:
                stats += "🟢 Đang làm việc\n"
                if state.current_break:
                    stats += f"🚽 Đang nghỉ: {state.current_break}\n"
            else:
                stats += "🔴 Không trong ca\n"
            stats += "\n"
        return stats

    async def handle_all_start_shift_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lệnh tắt: /as - Tất cả lên ca"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền!")
            return
        
        success_count = 0
        for state in self.user_states.values():
            if not state.is_working:
                state.start_shift()
                success_count += 1
        
        await update.message.reply_text(f"✅ Đã cho {success_count} người lên ca!")

    async def handle_all_end_shift_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lệnh tắt: /ae - Tất cả xuống ca"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền!")
            return
        
        success_count = 0
        for state in self.user_states.values():
            if state.is_working:
                state.end_shift()
                success_count += 1
        
        await update.message.reply_text(f"✅ Đã cho {success_count} người xuống ca!")

    async def handle_today_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lệnh tắt: /ts - Xem thống kê hôm nay"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền!")
            return
        
        stats = generate_today_stats(self.user_states)
        await update.message.reply_text(stats)

    async def handle_daily_report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lệnh tắt: /dr - Xem báo cáo ngày"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền xem báo cáo!")
            return
        
        report = generate_daily_report(self.user_states)
        await update.message.reply_text(report)

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị trợ giúp về các lệnh"""
        if update.effective_user.id not in ADMIN_ID:
            return
        
        help_text = """
🔰 *Các lệnh tắt cho Admin:*

*Quản lý ca:*
/as - Tất cả lên ca
/ae - Tất cả xuống ca

*Quản lý nghỉ:*
/fb - Bắt đầu nghỉ
/eb - Kết thúc nghỉ

*Thống kê & Báo cáo:*
/ts - Thống kê hôm nay
/st - Thống kê tổng
/dr - Báo cáo ngày
/wr - Báo cáo tuần

*Menu chính:*
/admin - Mở menu admin
/shift - Menu quản lý ca
/break - Menu quản lý nghỉ
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def handle_force_break_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lệnh tắt: /fb - Bắt đầu nghỉ cho nhân viên"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền!")
            return

        # Kiểm tra có argument không
        if not context.args:
            await update.message.reply_text("❌ Vui lòng cung cấp ID nhân viên!")
            return

        user_id = context.args[0]
        if user_id not in self.user_states:
            await update.message.reply_text("❌ Không tìm thấy nhân viên!")
            return

        state = self.user_states[user_id]
        if not state.is_working:
            await update.message.reply_text("❌ Nhân viên chưa bắt đầu ca làm việc!")
            return

        if state.current_break:
            await update.message.reply_text("❌ Nhân viên đang trong giờ nghỉ!")
            return

        # Bắt đầu nghỉ
        state.current_break = "break"  # hoặc loại nghỉ phù hợp
        state.break_start_time = datetime.now(VN_TIMEZONE)
        await update.message.reply_text(f"✅ Đã cho phép {state.user_name} bắt đầu nghỉ")

    async def handle_end_break_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lệnh tắt: /eb - Kết thúc nghỉ cho nhân viên"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền!")
            return

        if not context.args:
            await update.message.reply_text("❌ Vui lòng cung cấp ID nhân viên!")
            return

        user_id = context.args[0]
        if user_id not in self.user_states:
            await update.message.reply_text("❌ Không tìm thấy nhân viên!")
            return

        state = self.user_states[user_id]
        if not state.current_break:
            await update.message.reply_text("❌ Nhân viên không trong giờ nghỉ!")
            return

        # Kết thúc nghỉ
        now = datetime.now(VN_TIMEZONE)
        break_duration = now - state.break_start_time
        state.breaks[state.current_break] += break_duration
        state.current_break = None
        state.break_start_time = None

        await update.message.reply_text(
            f"✅ Đã kết thúc nghỉ cho {state.user_name}\n"
            f"⏱ Thời gian nghỉ: {str(break_duration).split('.')[0]}"
        )

    async def handle_all_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lệnh tắt: /st - Xem thống kê tổng"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền!")
            return
        
        stats = "📊 Thống kê tổng:\n\n"
        for state in self.user_states.values():
            stats += f"👤 {state.user_name}:\n"
            stats += f"🟢 Trạng thái: {'Đang làm' if state.is_working else 'Không làm'}\n"
            if state.current_break:
                stats += f"🚽 Đang nghỉ: {state.current_break}\n"
            stats += "\n"
        
        await update.message.reply_text(stats)

    async def handle_weekly_report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lệnh tắt: /wr - Xem báo cáo tuần"""
        if update.effective_user.id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền xem báo cáo!")
            return
        
        now = datetime.now(VN_TIMEZONE)
        start_of_week = now - timedelta(days=now.weekday())
        report = f"📊 Báo cáo tuần ({start_of_week.strftime('%d/%m')} - {now.strftime('%d/%m')}):\n\n"
        
        for state in self.user_states.values():
            if state.start_time and state.start_time.date() >= start_of_week.date():
                report += f"👤 {state.user_name}:\n"
                report += f"🕒 Tổng giờ làm: {calculate_work_hours(state)}\n"
                report += f"🚽 Tổng thời gian nghỉ: {sum(state.breaks.values(), timedelta())}\n\n"
        
        await update.message.reply_text(report)

def check_break_frequency(state, break_type):
    """Kiểm tra tần suất nghỉ"""
    try:
        current_count = state.break_counts.get(break_type, 0)
        max_count = BREAK_FREQUENCIES.get(break_type)
        
        if max_count is None:
            logger.error(f"Không tìm thấy cấu hình cho loại nghỉ: {break_type}")
            return False
            
        return current_count < max_count
    except Exception as e:
        logger.error(f"Lỗi khi kiểm tra tần suất nghỉ: {e}")
        return False