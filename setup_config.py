import configparser
import os
from pathlib import Path

def create_config():
    config = configparser.ConfigParser()
    
    # Telegram Settings
    config['telegram'] = {
        'YOUR_BOT_TOKEN': '7704513962:AAEYU2Y6-PXJgMDwvA4YhI6JzG5kxFa6gXk',
        'admin_id': '7457185130'
    }
    
    # Group Action Permissions
    config['group_action_permissions'] = {
        'authorized_users': '7457185130',
        'allowed_actions': 'all_start_shift,all_end_shift,all_eat,reset_data'
    }
    
    # Working Hours
    config['working_hours'] = {
        'start_time': '06:30',
        'end_time': '23:10'
    }
    
    # Break Durations
    config['break_durations'] = {
        've_sinh': '10',
        'hut_thuoc': '5',
        'an_com': '45'
    }
    
    # Break Frequencies
    config['break_frequencies'] = {
        've_sinh': '3',
        'hut_thuoc': '3',
        'an_com': '2'
    }
    
    # Database
    config['database'] = {
        'url': 'your_database.db'
    }
    
    # Tạo thư mục config nếu chưa tồn tại
    config_dir = Path('config')
    config_dir.mkdir(exist_ok=True)
    
    # Lưu file config
    config_path = config_dir / 'config.ini'
    with open(config_path, 'w', encoding='utf-8') as configfile:
        config.write(configfile)
    
    print(f"Đã tạo file config tại: {config_path}")
    
    # Tạo các thư mục cần thiết khác
    directories = ['src', 'logs', 'data', 'backup']
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"Đã tạo thư mục: {dir_name}")

if __name__ == "__main__":
    try:
        create_config()
        print("\nTạo cấu hình thành công!")
        print("\nCấu trúc thư mục:")
        print("DD/")
        print("├── config/")
        print("│   └── config.ini")
        print("├── src/")
        print("├── logs/")
        print("├── data/")
        print("└── backup/")
    except Exception as e:
        print(f"Lỗi: {str(e)}") 