from datetime import datetime, timedelta
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .utils.config import (
    ADMIN_ID, 
    MAIN_ADMIN_ID, 
    BREAK_DURATIONS,
    BREAK_FREQUENCIES,
    VN_TIMEZONE
)

logger = logging.getLogger(__name__)

class AdminCommands:
    def __init__(self, user_states):
        self.user_states = user_states

    async def admin_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị menu quản lý cho admin"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_ID:
            await update.message.reply_text("⛔️ Bạn không có quyền truy cập menu admin.")
            return

        keyboard = [
            [
                InlineKeyboardButton("👥 Quản lý ca", callback_data="admin_shift"),
                InlineKeyboardButton("⏰ Quản lý nghỉ", callback_data="admin_break")
            ],
            [
                InlineKeyboardButton("📊 Thống kê", callback_data="admin_stats"),
                InlineKeyboardButton("📋 Báo cáo", callback_data="admin_report")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🔰 Chào mừng đến với Menu Quản lý Admin!\nVui lòng chọn chức năng:",
            reply_markup=reply_markup
        )

    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý các callback từ menu admin"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if user_id not in ADMIN_ID:
            await query.answer("⛔️ Bạn không có quyền thực hiện hành động này!")
            return

        await query.answer()

        if query.data == "admin_shift":
            keyboard = [
                [
                    InlineKeyboardButton("🚀 Tất cả lên ca", callback_data="all_start_shift"),
                    InlineKeyboardButton("🏁 Tất cả xuống ca", callback_data="all_end_shift")
                ],
                [InlineKeyboardButton("⬅️ Quay lại", callback_data="back_admin")]
            ]
        
        elif query.data == "admin_break":
            keyboard = [
                [
                    InlineKeyboardButton("➕ Bắt đầu nghỉ", callback_data="force_break"),
                    InlineKeyboardButton("➖ Kết thúc nghỉ", callback_data="end_break")
                ],
                [InlineKeyboardButton("⬅️ Quay lại", callback_data="back_admin")]
            ]

        elif query.data == "admin_stats":
            keyboard = [
                [
                    InlineKeyboardButton("📈 Thống kê hôm nay", callback_data="today_stats"),
                    InlineKeyboardButton("📊 Thống kê tổng", callback_data="all_stats")
                ],
                [InlineKeyboardButton("⬅️ Quay lại", callback_data="back_admin")]
            ]

        elif query.data == "admin_report":
            keyboard = [
                [
                    InlineKeyboardButton("📋 Báo cáo ngày", callback_data="daily_report"),
                    InlineKeyboardButton("📑 Báo cáo tuần", callback_data="weekly_report")
                ],
                [InlineKeyboardButton("⬅️ Quay lại", callback_data="back_admin")]
            ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="🔰 Chọn chức năng chi tiết:",
            reply_markup=reply_markup
        )

    def generate_daily_report(self):
        """Tạo báo cáo ngày"""
        report = "📊 Báo cáo ngày:\n\n"
        for hashed_id, state in self.user_states.items():
            if state.start_time and state.start_time.date() == datetime.now(VN_TIMEZONE).date():
                report += f"👤 {state.user_name}:\n"
                report += f"⏰ Bắt đầu: {state.start_time.strftime('%H:%M:%S')}\n"
                if state.end_time:
                    report += f"🏁 Kết thúc: {state.end_time.strftime('%H:%M:%S')}\n"
                report += f"🚽 Tổng thời gian nghỉ: {sum(state.breaks.values(), timedelta())}\n\n"
        return report

    def generate_user_stats(self, hashed_id):
        """Tạo thống kê cho nhân viên cụ thể"""
        state = self.user_states[hashed_id]
        stats = f"📊 Thống kê nhân viên {state.user_name}:\n\n"
        stats += f"🚽 Số lần nghỉ hôm nay:\n"
        for break_type, count in state.break_counts.items():
            stats += f"{break_type}: {count}/{BREAK_FREQUENCIES[break_type]}\n"
        return stats 