from telegram import Update
from telegram.ext import ContextTypes
from src.utils.config import config

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Đọc thông tin từ config
    start_time = config['working_hours']['start_time']
    end_time = config['working_hours']['end_time']
    
    ve_sinh_duration = config['break_durations']['ve_sinh']
    hut_thuoc_duration = config['break_durations']['hut_thuoc']
    an_com_duration = config['break_durations']['an_com']
    
    ve_sinh_freq = config['break_frequencies']['ve_sinh']
    hut_thuoc_freq = config['break_frequencies']['hut_thuoc']
    an_com_freq = config['break_frequencies']['an_com']

    help_text = f"""
🕒 *THỜI GIAN LÀM VIỆC VÀ NGHỈ NGƠI*

⏰ *Ca làm việc:*
• Bắt đầu ca: {start_time}
• Kết thúc ca: {end_time}

🚻 *Thời gian vệ sinh:*
• Thời lượng: {ve_sinh_duration} phút/lần
• Số lần cho phép: {ve_sinh_freq} lần/ca

🚬 *Thời gian hút thuốc:*
• Thời lượng: {hut_thuoc_duration} phút/lần
• Số lần cho phép: {hut_thuoc_freq} lần/ca

🍚 *Thời gian ăn cơm:*
• Thời lượng: {an_com_duration} phút/lần
• Số lần cho phép: {an_com_freq} lần/ca

📝 *Lưu ý:*
• Vui lòng tuân thủ thời gian quy định
• Báo cáo trước khi bắt đầu nghỉ
• Báo cáo khi trở lại làm việc
• Không tự ý kéo dài thời gian nghỉ

💡 *Các lệnh cơ bản:*
/start - Bắt đầu sử dụng bot
/help - Xem hướng dẫn này
"""

    await update.message.reply_text(help_text, parse_mode='Markdown') 