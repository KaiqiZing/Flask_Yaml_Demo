from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import time
from datetime import datetime

class YamlFileHandler(FileSystemEventHandler):
    """YAML文件变化处理器"""
    
    def __init__(self):
        self.last_modified = {}
        
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(('.yaml', '.yml')):
            # 获取文件的最后修改时间
            current_time = time.time()
            last_time = self.last_modified.get(event.src_path, 0)
            
            # 防止重复触发（文件系统可能会多次触发同一事件）
            if current_time - last_time > 1:  # 1秒内的修改视为同一次修改
                self.last_modified[event.src_path] = current_time
                print(f"文件变化: {event.src_path} 在 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                return {
                    'type': 'modified',
                    'path': event.src_path,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(('.yaml', '.yml')):
            print(f"新文件创建: {event.src_path} 在 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return {
                'type': 'created',
                'path': event.src_path,
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith(('.yaml', '.yml')):
            print(f"文件删除: {event.src_path} 在 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return {
                'type': 'deleted',
                'path': event.src_path,
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

class FileMonitor:
    """文件监控器"""
    
    def __init__(self, watch_path):
        self.watch_path = watch_path
        self.observer = None
        self.handler = YamlFileHandler()
    
    def start(self):
        """启动监控"""
        if self.observer is None:
            self.observer = Observer()
            self.observer.schedule(self.handler, self.watch_path, recursive=True)
            self.observer.start()
            print(f"开始监控目录: {self.watch_path}")
    
    def stop(self):
        """停止监控"""
        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            print(f"停止监控目录: {self.watch_path}")
    
    def is_running(self):
        """检查监控是否运行中"""
        return self.observer is not None and self.observer.is_alive() 