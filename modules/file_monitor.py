from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from pathlib import Path
from flask_socketio import SocketIO
from datetime import datetime

class YamlFileMonitor:
    def __init__(self, config, socketio):
        self.config = config
        self.socketio = socketio
        self.observer = Observer()
        self.watch_paths = []
        self.event_handler = YamlEventHandler(self)
    
    def start(self, paths=None):
        """启动文件监控"""
        if paths:
            self.watch_paths = paths
        else:
            self.watch_paths = [self.config['app']['default_scan_dir']]
        
        for path in self.watch_paths:
            if os.path.exists(path):
                self.observer.schedule(self.event_handler, path, recursive=True)
        
        self.observer.start()
    
    def stop(self):
        """停止文件监控"""
        self.observer.stop()
        self.observer.join()
    
    def notify_clients(self, event_type, file_path):
        """通知客户端文件变化"""
        # 检查是否是YAML文件
        if not any(file_path.endswith(ext) for ext in self.config['app']['allowed_extensions']):
            return
        
        # 检查是否在排除目录中
        if any(exclude_dir in file_path for exclude_dir in self.config['app']['exclude_dirs']):
            return
        
        # 发送WebSocket通知
        self.socketio.emit('file_change', {
            'type': event_type,
            'file': file_path,
            'timestamp': str(datetime.now())
        })

class YamlEventHandler(FileSystemEventHandler):
    def __init__(self, monitor):
        self.monitor = monitor
    
    def on_created(self, event):
        if not event.is_directory:
            self.monitor.notify_clients('created', event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            self.monitor.notify_clients('modified', event.src_path)
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.monitor.notify_clients('deleted', event.src_path)
    
    def on_moved(self, event):
        if not event.is_directory:
            self.monitor.notify_clients('moved', {
                'src': event.src_path,
                'dest': event.dest_path
            }) 