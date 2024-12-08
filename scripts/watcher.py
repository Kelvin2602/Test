import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import subprocess
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

class RestartHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.process = None
        
    def start_process(self):
        if self.process:
            self.process.terminate()
            time.sleep(1)
            
        cmd = [sys.executable, os.path.join(BASE_DIR, 'run.py')]
        self.process = subprocess.Popen(cmd)

    def on_any_event(self, event):
        if event.src_path.endswith(('user_states.db', 'user_states.db-journal')):
            return
        print(f"Phát hiện thay đổi trong {event.src_path}. Đang khởi động lại...")
        self.start_process()

if __name__ == "__main__":
    path = os.path.join(BASE_DIR, 'src')
    
    event_handler = RestartHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    
    # Khởi động process lần đầu
    event_handler.start_process()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        if event_handler.process:
            event_handler.process.terminate()
        observer.stop()
    observer.join()
