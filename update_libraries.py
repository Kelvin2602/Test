import asyncio
import pkg_resources

async def check_and_update_modules():
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
            current_version = pkg_resources.get_distribution(module).version
            process = await asyncio.create_subprocess_shell(
                f"pip install --upgrade {module}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            updated_version = pkg_resources.get_distribution(module).version
            if current_version != updated_version:
                print(f"Đã cập nhật {module} từ {current_version} lên {updated_version}")
            else:
                print(f"{module} đã ở phiên bản mới nhất ({current_version})")
                
        except Exception as e:
            print(f"Lỗi khi cập nhật {module}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_and_update_modules())
