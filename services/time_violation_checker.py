from datetime import datetime, timedelta
import configparser
import logging
from telegram import Bot
from src.utils.config import BOT_TOKEN, ADMIN_ID

class TimeViolationChecker:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.bot = Bot(BOT_TOKEN)
        
        # Đọc thời gian từ config
        self.start_time = datetime.strptime(self.config['working_hours']['start_time'], '%H:%M').time()
        self.end_time = datetime.strptime(self.config['working_hours']['end_time'], '%H:%M').time()
        
        # Đọc thời gian break
        self.break_durations = {
            've_sinh': int(self.config['break_durations']['ve_sinh']),
            'hut_thuoc': int(self.config['break_durations']['hut_thuoc']),
            'an_com': int(self.config['break_durations']['an_com'])
        }
        
    async def check_violation(self, user_id, action_type, action_time):
        violations = []
        
        if action_type == 'start_shift':
            # Kiểm tra đi trễ
            if action_time.time() > self.start_time:
                minutes_late = (action_time - datetime.combine(action_time.date(), self.start_time)).total_seconds() / 60
                violations.append({
                    'type': 'late_arrival',
                    'minutes': int(minutes_late),
                    'scheduled_time': self.start_time.strftime('%H:%M'),
                    'actual_time': action_time.strftime('%H:%M')
                })

        elif action_type == 'end_shift':
            # Kiểm tra về sớm
            if action_time.time() < self.end_time:
                minutes_early = (datetime.combine(action_time.date(), self.end_time) - action_time).total_seconds() / 60
                violations.append({
                    'type': 'early_departure',
                    'minutes': int(minutes_early),
                    'scheduled_time': self.end_time.strftime('%H:%M'),
                    'actual_time': action_time.strftime('%H:%M')
                })

        elif action_type in ['ve_sinh', 'hut_thuoc', 'an_com']:
            # Kiểm tra thời gian break vượt quá quy định
            allowed_duration = self.break_durations[action_type]
            actual_duration = self.get_break_duration(user_id, action_type, action_time)
            
            if actual_duration > allowed_duration:
                violations.append({
                    'type': f'break_overtime_{action_type}',
                    'minutes': int(actual_duration - allowed_duration),
                    'allowed_duration': allowed_duration,
                    'actual_duration': actual_duration
                })

        return violations

    async def notify_admin(self, user_id, violations):
        """Gửi thông báo vi phạm tới admin"""
        try:
            for violation in violations:
                message = self._format_violation_message(user_id, violation)
                
                # Gửi thông báo cho tất cả admin
                for admin_id in ADMIN_ID:
                    try:
                        await self.bot.send_message(
                            chat_id=admin_id,
                            text=message,
                            parse_mode='HTML'
                        )
                        logging.info(f"Đã gửi thông báo vi phạm tới admin {admin_id}")
                    except Exception as e:
                        logging.error(f"Lỗi khi gửi thông báo tới admin {admin_id}: {e}")
                        
        except Exception as e:
            logging.error(f"Lỗi khi thông báo vi phạm: {e}")

    def _format_violation_message(self, user_id, violation):
        """Format tin nhắn thông báo vi phạm với user_id"""
        messages = {
            'late_arrival': (
                f"⚠️ <b>VI PHẠM: ĐI TRỄ</b>\n\n"
                f"🆔 User ID: <code>{user_id}</code>\n"
                f"👤 Tên: {violation.get('user_name', 'Không xác định')}\n"
                f"⏰ Giờ quy định: {violation['scheduled_time']}\n" 
                f"⏰ Giờ thực tế: {violation['actual_time']}\n"
                f"⏱ Số phút trễ: <b>{violation['minutes']}</b> phút\n\n"
                f"📅 Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            ),
            'early_departure': (
                f"⚠️ <b>VI PHẠM: VỀ SỚM</b>\n\n"
                f"🆔 User ID: <code>{user_id}</code>\n"
                f"👤 Tên: {violation.get('user_name', 'Không xác định')}\n"
                f"⏰ Giờ quy định: {violation['scheduled_time']}\n"
                f"⏰ Giờ thực tế: {violation['actual_time']}\n"
                f"⏱ Số phút về sớm: <b>{violation['minutes']}</b> phút\n\n"
                f"📅 Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            ),
            'break_overtime': (
                f"⚠️ <b>VI PHẠM: NGHỈ QUÁ GIỜ</b>\n\n"
                f"🆔 User ID: <code>{user_id}</code>\n"
                f"👤 Tên: {violation.get('user_name', 'Không xác định')}\n"
                f"🔄 Loại nghỉ: {violation['break_type']}\n"
                f"⏰ Thời gian cho phép: {violation['allowed_duration']} phút\n"
                f"⏰ Thời gian thực tế: {violation['actual_duration']} phút\n"
                f"⏱ Số phút vượt quá: <b>{violation['minutes']}</b> phút\n\n"
                f"📅 Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            ),
            'break_frequency': (
                f"⚠️ <b>VI PHẠM: NGHỈ QUÁ SỐ LẦN CHO PHÉP</b>\n\n"
                f"🆔 User ID: <code>{user_id}</code>\n"
                f"👤 Tên: {violation.get('user_name', 'Không xác định')}\n"
                f"🔄 Loại nghỉ: {violation['break_type']}\n"
                f"⏰ Số lần cho phép: {violation['allowed_count']}\n"
                f"⏰ Số lần đã nghỉ: <b>{violation['actual_count']}</b>\n\n"
                f"📅 Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            )
        }
        
        return messages.get(violation['type'], (
            f"⚠️ <b>VI PHẠM: KHÔNG XÁC ĐỊNH</b>\n\n"
            f"🆔 User ID: <code>{user_id}</code>\n"
            f"👤 Tên: {violation.get('user_name', 'Không xác định')}\n"
            f"❓ Loại vi phạm: Không xác định\n\n"
            f"📅 Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )) 