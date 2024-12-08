import pickle
import os
from datetime import datetime, timedelta
from pathlib import Path
from src.utils.logger import logger

# Lấy đường dẫn thư mục gốc
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# File lưu trạng thái
STATE_FILE = BASE_DIR / 'data' / 'user_states.pkl'

def save_user_states(user_states):
    """Lưu trạng thái người dùng vào file"""
    try:
        # Đảm bảo thư mục data tồn tại
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        
        with open(STATE_FILE, 'wb') as f:
            pickle.dump(user_states, f)
        logger.info("Đã lưu trạng thái người dùng")
    except Exception as e:
        logger.error(f"Lỗi khi lưu user states: {e}")

def load_user_states():
    """Đọc trạng thái người dùng từ file"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Lỗi khi đọc user states: {e}")
    return {} 