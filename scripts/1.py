import os
import shutil
import sys
import logging
from pathlib import Path
import codecs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProjectStructureManager:
    def __init__(self, source_dir='.'):
        self.source_dir = Path(source_dir)
        self.backup_dir = self.source_dir / 'backup'
        
        # Cấu trúc thư mục mới
        self.new_structure = {
            'src': {
                'main.py': None,  # None nghĩa là file sẽ được di chuyển từ file gốc
                'handlers': {},
                'models': {},
                'utils': {},
                'services': {}
            },
            'config': {
                'config.ini': None,
                'encryption_key.key': None
            },
            'data': {
                'attendance_history.json': None
            },
            'scripts': {
                'cleanup.py': None,
                'update_libraries.py': None,
                'watcher.py': None
            },
            'logs': {},
            'tests': {},
            'docs': {}
        }
        
        # Ánh xạ file cũ sang mới
        self.file_mapping = {
            'D1.py': 'src/main.py',
            'config.ini': 'config/config.ini',
            'encryption_key.key': 'config/encryption_key.key',
            'attendance_history.json': 'data/attendance_history.json',
            'loc.py': 'scripts/cleanup.py',
            'update_libraries.py': 'scripts/update_libraries.py',
            'watcher.py': 'scripts/watcher.py'
        }

    def create_backup(self):
        """Tạo backup trước khi tái cấu trúc"""
        logger.info("Đang tạo backup...")
        if not self.backup_dir.exists():
            self.backup_dir.mkdir()
        
        for src_file in self.file_mapping.keys():
            src_path = self.source_dir / src_file
            if src_path.exists():
                dst_path = self.backup_dir / src_file
                shutil.copy2(str(src_path), str(dst_path))
        logger.info(f"Đã tạo backup tại {self.backup_dir}")

    def create_structure(self):
        """Tạo cấu trúc thư mục mới"""
        logger.info("Đang tạo cấu trúc thư mục mới...")
        
        def create_dirs(base_path, structure):
            for name, content in structure.items():
                path = base_path / name
                if isinstance(content, dict):
                    path.mkdir(exist_ok=True)
                    create_dirs(path, content)
                    # Tạo __init__.py cho các package Python
                    if name not in ['config', 'data', 'logs', 'docs']:
                        init_file = path / '__init__.py'
                        if not init_file.exists():
                            init_file.touch()

        create_dirs(self.source_dir, self.new_structure)
        logger.info("Đã tạo xong cấu trúc thư mục")

    def move_files(self):
        """Di chuyển các file vào vị trí mới"""
        logger.info("Đang di chuyển các file...")
        for old_path, new_path in self.file_mapping.items():
            src = self.source_dir / old_path
            dst = self.source_dir / new_path
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
                logger.info(f"Đã di chuyển {old_path} -> {new_path}")
            else:
                logger.warning(f"Không tìm thấy file {old_path}")

    def create_gitignore(self):
        """Tạo file .gitignore"""
        gitignore_content = """
# Virtual Environment
venv/
env/
__pycache__/
*.py[cod]

# IDE
.vscode/
.idea/

# Logs
logs/
*.log

# Database
data/*.db
data/*.db-journal

# Config
config/encryption_key.key

# Environment variables
.env
.env.*

# Backup
backup/
"""
        with open(self.source_dir / '.gitignore', 'w', encoding='utf-8') as f:
            f.write(gitignore_content.strip())
        logger.info("Đã tạo .gitignore")

    def restructure(self):
        """Thực hiện tái cấu trúc dự án"""
        try:
            # Tạo backup
            self.create_backup()
            
            # Tạo cấu trúc mới
            self.create_structure()
            
            # Di chuyển files
            self.move_files()
            
            # Tạo .gitignore
            self.create_gitignore()
            
            logger.info("Tái cấu trúc dự án hoàn tất!")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khi tái cấu trúc: {str(e)}")
            return False

def main():
    if len(sys.argv) > 1:
        source_dir = sys.argv[1]
    else:
        source_dir = '.'
    
    manager = ProjectStructureManager(source_dir)
    if manager.restructure():
        print("\nTái cấu trúc dự án thành công!")
        print("\nCấu trúc mới:")
        os.system('tree' if os.name != 'nt' else 'tree /F')
    else:
        print("\nCó lỗi xảy ra trong quá trình tái cấu trúc!")
        print("Kiểm tra backup trong thư mục 'backup'")

if __name__ == "__main__":
    main()