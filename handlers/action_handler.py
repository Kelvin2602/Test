from datetime import datetime
from services.time_violation_checker import TimeViolationChecker
import logging

time_checker = TimeViolationChecker()

async def handle_action(user_id, action_type):
    current_time = datetime.now()
    
    # Kiểm tra vi phạm
    violations = await time_checker.check_violation(user_id, action_type, current_time)
    
    # Nếu có vi phạm, thông báo cho admin
    if violations:
        try:
            await time_checker.notify_admin(user_id, violations)
            logging.info(f"Đã gửi thông báo vi phạm cho user {user_id}")
        except Exception as e:
            logging.error(f"Lỗi khi xử lý thông báo vi phạm: {e}") 