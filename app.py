from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_socketio import SocketIO, emit
import os
import yaml
import json
import math
from werkzeug.utils import secure_filename
import glob
from pathlib import Path
import tempfile
import shutil
from file_monitor import FileMonitor
from datetime import datetime

# 读取配置文件
def load_config():
    """加载配置文件"""
    config_file = 'config.yaml'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                print(f"配置文件加载成功: {config_file}")
                print(f"默认扫描目录: {config_data.get('app', {}).get('default_scan_dir', '未设置')}")
                return config_data
        except Exception as e:
            print(f"配置文件读取失败: {e}")
    else:
        print(f"配置文件不存在: {config_file}")
    
    # 返回默认配置
    print("使用默认配置")
    return {
        'app': {
            'default_scan_dir': '.',
            'upload_folder': 'uploads',
            'max_file_size': 16 * 1024 * 1024,
            'exclude_dirs': ['uploads', '__pycache__', '.git', 'node_modules', '.vscode'],
            'allowed_extensions': ['yaml', 'yml']
        },
        'server': {
            'host': '0.0.0.0',
            'port': 5000,
            'debug': True
        }
    }

# 加载配置
config = load_config()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = config['app']['upload_folder']
app.config['MAX_CONTENT_LENGTH'] = config['app']['max_file_size']
app.config['DEFAULT_SCAN_DIR'] = config['app']['default_scan_dir']

# 初始化SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# 初始化文件监控器
file_monitor = FileMonitor(app.config['DEFAULT_SCAN_DIR'])

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = set(config['app']['allowed_extensions'])

# 排除的目录
EXCLUDE_DIRS = config['app']['exclude_dirs']

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_file_size(bytes):
    """格式化文件大小显示"""
    if bytes == 0:
        return '0 Bytes'
    k = 1024
    sizes = ['Bytes', 'KB', 'MB', 'GB']
    i = int(math.floor(math.log(bytes) / math.log(k)))
    return f"{bytes / math.pow(k, i):.2f} {sizes[i]}"

def scan_yaml_files(directory='.'):
    """扫描指定目录下的所有YAML文件"""
    yaml_files = []
    
    # 支持多种YAML文件扩展名
    patterns = [f'**/*.{ext}' for ext in ALLOWED_EXTENSIONS]
    
    for pattern in patterns:
        files = glob.glob(os.path.join(directory, pattern), recursive=True)
        for file_path in files:
            # 检查是否在排除目录中
            should_exclude = False
            for exclude_dir in EXCLUDE_DIRS:
                if exclude_dir in file_path:
                    should_exclude = True
                    break
            
            if not should_exclude:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        yaml_data = yaml.safe_load(content)
                        
                        yaml_files.append({
                            'path': file_path,
                            'name': os.path.basename(file_path),
                            'size': os.path.getsize(file_path),
                            'content': yaml_data,
                            'raw_content': content
                        })
                except Exception as e:
                    yaml_files.append({
                        'path': file_path,
                        'name': os.path.basename(file_path),
                        'size': os.path.getsize(file_path),
                        'error': str(e),
                        'content': None,
                        'raw_content': None
                    })
    
    return yaml_files

@app.route('/')
def index():
    """主页 - 显示YAML文件列表"""
    # 从URL参数获取扫描目录，默认为配置的默认目录
    scan_dir = request.args.get('dir', app.config['DEFAULT_SCAN_DIR'])
    
    # 验证目录是否存在
    if not os.path.exists(scan_dir):
        scan_dir = app.config['DEFAULT_SCAN_DIR']
    
    yaml_files = scan_yaml_files(scan_dir)
    return render_template('index.html', 
                         yaml_files=yaml_files, 
                         formatFileSize=format_file_size,
                         current_dir=scan_dir)

@app.route('/view/<path:file_path>')
def view_file(file_path):
    """查看YAML文件内容"""
    try:
        # 规范化文件路径
        file_path = os.path.normpath(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            yaml_data = yaml.safe_load(content)
        
        return render_template('view.html', 
                             file_path=file_path, 
                             file_name=os.path.basename(file_path),
                             yaml_data=yaml_data,
                             raw_content=content)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/edit/<path:file_path>')
def edit_file(file_path):
    """编辑YAML文件页面"""
    try:
        # 规范化文件路径
        file_path = os.path.normpath(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            yaml_data = yaml.safe_load(content)
        
        return render_template('edit.html', 
                             file_path=file_path, 
                             file_name=os.path.basename(file_path),
                             yaml_data=yaml_data,
                             raw_content=content)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/save', methods=['POST'])
def save_file():
    """保存YAML文件"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        # 从URL路径中提取正确的文件名
        if '\\' in file_path or '/' in file_path:
            file_name = os.path.basename(file_path)
        else:
            return jsonify({'error': '无效的文件路径'}), 400
        
        # 构建新的文件路径，保存到default_scan_dir
        new_file_path = os.path.join(app.config['DEFAULT_SCAN_DIR'], file_name)
        new_file_path = Path(new_file_path).resolve()
        
        content = data.get('content')
        
        if not new_file_path or not content:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 验证YAML格式
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            return jsonify({'error': f'YAML格式错误: {str(e)}'}), 400
        
        # 保存文件
        with open(new_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 通过WebSocket发送通知
        socketio.emit('file_changed', {
            'type': 'modified',
            'path': str(new_file_path),
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        return jsonify({'message': '文件保存成功', 'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/update_value', methods=['POST'])
def update_value():
    """更新YAML中的特定值"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        print(f"原始file_path: {file_path}")
        
        # 从URL路径中提取正确的文件名
        # 原始URL路径格式: /edit/C:/Users/z3744/Desktop/cursor_project/RY_PytestDemo/data/example.yaml
        # 需要从URL中提取实际的文件路径
        if '\\' in file_path or '/' in file_path:
            # 如果路径包含分隔符，说明是完整路径
            file_name = os.path.basename(file_path)
        else:
            return jsonify({'error': '无效的文件路径'}), 400
        
        print(f"提取的文件名: {file_name}")
        
        # 构建新的文件路径，保存到default_scan_dir
        new_file_path = os.path.join(app.config['DEFAULT_SCAN_DIR'], file_name)
        print(f"新文件路径: {new_file_path}")
        
        # 规范化文件路径
        new_file_path = Path(new_file_path).resolve()
        print(f"规范化后file_path: {new_file_path}")
        
        key_path = data.get('key_path')
        new_value = data.get('value')
        
        print(f"更新值请求: file_path={new_file_path}, key_path={key_path}, value={new_value}")
        
        if not all([new_file_path, key_path, new_value]):
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 检查文件是否存在
        if not new_file_path.exists():
            print(f"文件不存在: {new_file_path}")
            print(f"当前工作目录: {os.getcwd()}")
            return jsonify({'error': f'文件不存在: {new_file_path}'}), 400
        
        # 检查文件是否可写
        if not os.access(new_file_path, os.W_OK):
            return jsonify({'error': f'文件不可写: {new_file_path}'}), 400
        
        # 读取当前文件
        try:
            with open(new_file_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
                print(f"成功读取YAML文件: {new_file_path}")
        except Exception as e:
            print(f"读取YAML文件失败: {e}")
            return jsonify({'error': f'读取文件失败: {str(e)}'}), 500
        
        # 更新值
        keys = key_path.split('.')
        current = yaml_data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        old_value = current.get(keys[-1])
        current[keys[-1]] = new_value
        print(f"更新值: {key_path} = {old_value} -> {new_value}")
        
        # 保存文件
        try:
            with open(new_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)
            print(f"成功保存文件: {new_file_path}")
        except Exception as e:
            print(f"保存文件失败: {e}")
            return jsonify({'error': f'保存文件失败: {str(e)}'}), 500
        
        return jsonify({'message': '值更新成功', 'data': yaml_data})
    except Exception as e:
        print(f"更新值异常: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_key', methods=['POST'])
def delete_key():
    """删除YAML中的特定键"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        # 从URL路径中提取正确的文件名
        if '\\' in file_path or '/' in file_path:
            file_name = os.path.basename(file_path)
        else:
            return jsonify({'error': '无效的文件路径'}), 400
        
        # 构建新的文件路径，保存到default_scan_dir
        new_file_path = os.path.join(app.config['DEFAULT_SCAN_DIR'], file_name)
        new_file_path = Path(new_file_path).resolve()
        
        key_path = data.get('key_path')
        
        if not all([new_file_path, key_path]):
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 读取当前文件
        with open(new_file_path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
        
        # 删除键
        keys = key_path.split('.')
        current = yaml_data
        for key in keys[:-1]:
            if key not in current:
                return jsonify({'error': '键路径不存在'}), 400
            current = current[key]
        
        if keys[-1] in current:
            del current[keys[-1]]
        else:
            return jsonify({'error': '键不存在'}), 400
        
        # 保存文件
        with open(new_file_path, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)
        
        return jsonify({'message': '键删除成功', 'data': yaml_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add_key', methods=['POST'])
def add_key():
    """添加新的键值对到YAML"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        # 从URL路径中提取正确的文件名
        if '\\' in file_path or '/' in file_path:
            file_name = os.path.basename(file_path)
        else:
            return jsonify({'error': '无效的文件路径'}), 400
        
        # 构建新的文件路径，保存到default_scan_dir
        new_file_path = os.path.join(app.config['DEFAULT_SCAN_DIR'], file_name)
        new_file_path = Path(new_file_path).resolve()
        
        key_path = data.get('key_path')
        value = data.get('value')
        
        if not all([new_file_path, key_path, value]):
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 读取当前文件
        with open(new_file_path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f) or {}
        
        # 添加键值对
        keys = key_path.split('.')
        current = yaml_data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
        
        # 保存文件
        with open(new_file_path, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)
        
        return jsonify({'message': '键值对添加成功', 'data': yaml_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """上传YAML文件"""
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # 验证YAML格式
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
                return jsonify({'message': '文件上传成功', 'filename': filename})
            except yaml.YAMLError as e:
                os.remove(file_path)  # 删除无效文件
                return jsonify({'error': f'YAML格式错误: {str(e)}'}), 400
        else:
            return jsonify({'error': '不支持的文件类型'}), 400
    
    return render_template('upload.html')

@app.route('/api/config')
def get_config():
    """获取当前配置"""
    return jsonify({
        'config': config,
        'app_config': {
            'default_scan_dir': app.config['DEFAULT_SCAN_DIR'],
            'upload_folder': app.config['UPLOAD_FOLDER'],
            'max_file_size': app.config['MAX_CONTENT_LENGTH']
        }
    })

@app.route('/api/scan')
def api_scan():
    """API端点：扫描YAML文件"""
    try:
        directory = request.args.get('directory', '.')
        yaml_files = scan_yaml_files(directory)
        return jsonify({
            'files': yaml_files,
            'directory': directory,
            'count': len(yaml_files)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<path:file_path>')
def download_file(file_path):
    """下载YAML文件"""
    try:
        file_path = os.path.normpath(file_path)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_values', methods=['POST'])
def update_values():
    """批量更新YAML中的多个值"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        # 从URL路径中提取正确的文件名
        if '\\' in file_path or '/' in file_path:
            file_name = os.path.basename(file_path)
        else:
            return jsonify({'error': '无效的文件路径'}), 400
        
        # 构建新的文件路径，保存到default_scan_dir
        new_file_path = os.path.join(app.config['DEFAULT_SCAN_DIR'], file_name)
        new_file_path = Path(new_file_path).resolve()
        
        changes = data.get('changes', [])
        
        if not new_file_path or not changes:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 读取当前文件
        try:
            with open(new_file_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
                print(f"成功读取YAML文件: {new_file_path}")
        except Exception as e:
            print(f"读取YAML文件失败: {e}")
            return jsonify({'error': f'读取文件失败: {str(e)}'}), 500
        
        # 批量更新值
        for change in changes:
            key_path = change.get('key_path')
            new_value = change.get('value')
            
            if key_path and new_value is not None:
                keys = key_path.split('.')
                current = yaml_data
                for key in keys[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # 尝试转换值的类型
                original_value = current.get(keys[-1])
                if original_value is not None:
                    if isinstance(original_value, (int, float)):
                        try:
                            new_value = float(new_value) if isinstance(original_value, float) else int(new_value)
                        except ValueError:
                            pass
                    elif isinstance(original_value, bool):
                        new_value = str(new_value).lower() == 'true'
                    elif isinstance(original_value, list):
                        try:
                            new_value = json.loads(new_value)
                        except (json.JSONDecodeError, TypeError):
                            new_value = [item.strip() for item in str(new_value).split(',')]
                
                current[keys[-1]] = new_value
                print(f"更新值: {key_path} = {new_value}")
        
        # 保存文件
        try:
            with open(new_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)
            print(f"成功保存文件: {new_file_path}")
        except Exception as e:
            print(f"保存文件失败: {e}")
            return jsonify({'error': f'保存文件失败: {str(e)}'}), 500
        
        return jsonify({'message': '批量更新成功', 'data': yaml_data})
    except Exception as e:
        print(f"批量更新异常: {e}")
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """处理WebSocket连接"""
    print('Client connected')
    
@socketio.on('disconnect')
def handle_disconnect():
    """处理WebSocket断开连接"""
    print('Client disconnected')

def start_file_monitor():
    """启动文件监控"""
    try:
        file_monitor.start()
    except Exception as e:
        print(f"启动文件监控失败: {e}")

if __name__ == '__main__':
    # 启动文件监控
    start_file_monitor()
    
    # 启动Flask应用
    server_config = config['server']
    socketio.run(
        app,
        host=server_config['host'],
        port=server_config['port'],
        debug=server_config['debug']
    ) 
