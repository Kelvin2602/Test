import subprocess

def check_and_update_modules():
    modules_to_check = [
        'python-telegram-bot',
        'pytz',
        'configparser',
        'asyncio',
        'python-dotenv',
        'watchdog',
        'coloredlogs',
        'tabulate',
        'emoji'
    ]
    
    for module in modules_to_check:
        try:
            result = subprocess.run(
                f"pip install --upgrade {module}",
                shell=True,
                capture_output=True,
                text=True
            )
            print(f"Cập nhật {module}: {result.stdout}")
        except Exception as e:
            print(f"Lỗi khi cập nhật {module}: {str(e)}")

if __name__ == "__main__":
    check_and_update_modules()
