import os
import time
import logging

logger = logging.getLogger(__name__)

def find_unnecessary_files(directory):
    unnecessary_files = []
    try:
        for root, dirs, files in os.walk(directory):
            if '.git' in dirs:
                dirs.remove('.git')
            if 'venv' in dirs:
                dirs.remove('venv')
                
            for file in files:
                file_path = os.path.join(root, file)
                if any(file.endswith(ext) for ext in ['.tmp', '.bak', '.swp', '.pyc']):
                    unnecessary_files.append(file_path)
                elif file == '__pycache__':
                    unnecessary_files.append(file_path)
                elif file.endswith('.log') and time.time() - os.path.getmtime(file_path) > 30 * 24 * 60 * 60:
                    unnecessary_files.append(file_path)
    except Exception as e:
        logger.error(f"Lỗi khi tìm file: {e}")
    
    return unnecessary_files

# Sử dụng
project_directory = '.'  # Thay đổi thành đường dẫn thư mục dự án của bạn
files_to_remove = find_unnecessary_files(project_directory)

print("Các file có thể xóa:")
for file in files_to_remove:
    print(file)

# Xác nhận trước khi xóa
if input("Bạn có muốn xóa các file này không? (y/n): ").lower() == 'y':
    for file in files_to_remove:
        try:
            os.remove(file)
            print(f"Đã xóa: {file}")
        except Exception as e:
            print(f"Không thể xóa {file}: {e}")
else:
    print("Hủy thao tác xóa.")