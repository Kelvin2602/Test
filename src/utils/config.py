import pytz
import configparser
from pathlib import Path

config = configparser.ConfigParser()
config.read(Path(__file__).parent.parent.parent / 'config.ini', encoding='utf-8')

# Timezone
VN_TIMEZONE = pytz.timezone('Asia/Ho_Chi_Minh')

# Telegram config
BOT_TOKEN = config['telegram']['YOUR_BOT_TOKEN']
ADMIN_ID = [int(id.strip()) for id in config['telegram']['admin_id'].split(',')]
MAIN_ADMIN_ID = ADMIN_ID[0] if ADMIN_ID else None

# Break durations (minutes)
BREAK_DURATIONS = {
    "🚽 Vệ sinh (厕所)": int(config['break_durations']['ve_sinh']),
    "🚬 Hút thuốc (抽烟)": int(config['break_durations']['hut_thuoc']), 
    "🍚 Ăn cơm (吃饭)": int(config['break_durations']['an_com'])
}

# Break frequencies per shift
BREAK_FREQUENCIES = {
    "🚽 Vệ sinh (厕所)": int(config['break_frequencies']['ve_sinh']),
    "🚬 Hút thuốc (抽烟)": int(config['break_frequencies']['hut_thuoc']),
    "🍚 Ăn cơm (吃饭)": int(config['break_frequencies']['an_com'])
}

# Working hours
WORK_START = config['working_hours']['start_time']
WORK_END = config['working_hours']['end_time']

# Action permissions
AUTHORIZED_USERS = [int(id.strip()) for id in config['group_action_permissions']['authorized_users'].split(',')]
ALLOWED_ACTIONS = config['group_action_permissions']['allowed_actions'].split(',')

__all__ = [
    'BOT_TOKEN',
    'ADMIN_ID',
    'MAIN_ADMIN_ID',
    'BREAK_DURATIONS',
    'BREAK_FREQUENCIES',
    'WORK_START',
    'WORK_END',
    'AUTHORIZED_USERS',
    'ALLOWED_ACTIONS',
    'VN_TIMEZONE'
]