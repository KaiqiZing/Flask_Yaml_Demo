from flask import Flask
from flask_socketio import SocketIO
import yaml
import os

from modules.file_handler import YamlFileHandler
from modules.file_monitor import YamlFileMonitor
from modules.business import YamlBusiness

def format_file_size(size):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'  # 请修改为安全的密钥
    
    # 注册Jinja2过滤器
    app.jinja_env.filters['format_size'] = format_file_size

    # 加载配置
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 初始化SocketIO
    socketio = SocketIO(app)
    
    # 初始化各个模块
    file_handler = YamlFileHandler(config)
    file_monitor = YamlFileMonitor(config, socketio)
    yaml_business = YamlBusiness(file_handler, file_monitor, config)
    
    # 注册蓝图
    app.register_blueprint(yaml_business.bp)
    
    # 启动文件监控
    file_monitor.start()
    
    @app.teardown_appcontext
    def cleanup(exception=None):
        """应用关闭时的清理工作"""
        file_monitor.stop()
    
    return app, socketio

# 创建全局应用实例，供Flask CLI使用
app, socketio = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 
