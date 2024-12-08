import os
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import subprocess

class RestartHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.process = None
        
    def start_process(self):
        if self.process:
            self.process.terminate()
            time.sleep(1)
            
        cmd = [sys.executable, 'run.py']
        self.process = subprocess.Popen(cmd)

if __name__ == "__main__":
    path = Path(__file__).parent / 'src'
    event_handler = RestartHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    
    try:
        event_handler.start_process()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        if event_handler.process:
            event_handler.process.terminate()
        observer.stop()
    observer.join()
