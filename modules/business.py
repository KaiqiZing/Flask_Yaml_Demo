from flask import Blueprint, render_template, request, jsonify, send_file
from datetime import datetime
import os
from pathlib import Path

class YamlBusiness:
    def __init__(self, file_handler, file_monitor, config):
        self.file_handler = file_handler
        self.file_monitor = file_monitor
        self.config = config
        
        # 创建Blueprint
        self.bp = Blueprint('yaml', __name__)
        self.register_routes()
    
    def register_routes(self):
        """注册所有路由"""
        # 主页
        self.bp.route('/')(self.index)
        # 查看文件
        self.bp.route('/view/<path:file_path>')(self.view_file)
        # 编辑文件
        self.bp.route('/edit/<path:file_path>')(self.edit_file)
        # 上传文件
        self.bp.route('/upload', methods=['GET', 'POST'])(self.upload_file)
        # API路由
        self.bp.route('/api/save', methods=['POST'])(self.save_file)
        self.bp.route('/api/update_value', methods=['POST'])(self.update_value)
        self.bp.route('/api/delete_key', methods=['POST'])(self.delete_key)
        self.bp.route('/api/add_key', methods=['POST'])(self.add_key)
        self.bp.route('/api/download/<path:file_path>')(self.download_file)
        self.bp.route('/api/update_values', methods=['POST'])(self.update_values)
    
    def index(self):
        """主页 - 显示YAML文件列表"""
        scan_dir = request.args.get('dir', self.config['app']['default_scan_dir'])
        if not os.path.exists(scan_dir):
            scan_dir = self.config['app']['default_scan_dir']
        
        yaml_files = self.file_handler.scan_yaml_files(scan_dir)
        return render_template('index.html', 
                             yaml_files=yaml_files,
                             current_dir=scan_dir)
    
    def view_file(self, file_path):
        """查看YAML文件内容"""
        try:
            file_path = os.path.normpath(file_path)
            yaml_data, content, error = self.file_handler.read_yaml_file(file_path)
            if error:
                return jsonify({'error': error}), 400
            
            return render_template('view.html',
                                 file_path=file_path,
                                 file_name=os.path.basename(file_path),
                                 yaml_data=yaml_data,
                                 raw_content=content)
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    def edit_file(self, file_path):
        """编辑YAML文件页面"""
        try:
            file_path = os.path.normpath(file_path)
            yaml_data, content, error = self.file_handler.read_yaml_file(file_path)
            if error:
                return jsonify({'error': error}), 400
            
            return render_template('edit.html',
                                 file_path=file_path,
                                 file_name=os.path.basename(file_path),
                                 yaml_data=yaml_data,
                                 raw_content=content)
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    def save_file(self):
        """保存YAML文件"""
        try:
            data = request.get_json()
            file_path = data.get('file_path')
            content = data.get('content')
            
            if not all([file_path, content]):
                return jsonify({'error': '缺少必要参数'}), 400
            
            success, error = self.file_handler.save_yaml_file(file_path, content)
            if not success:
                return jsonify({'error': error}), 400
            
            return jsonify({'message': '文件保存成功', 'status': 'success'})
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    def update_value(self):
        """更新YAML中的特定值"""
        try:
            data = request.get_json()
            file_path = data.get('file_path')
            key_path = data.get('key_path')
            new_value = data.get('value')
            
            if not all([file_path, key_path, new_value]):
                return jsonify({'error': '缺少必要参数'}), 400
            
            success, result = self.file_handler.update_yaml_value(file_path, key_path, new_value)
            if not success:
                return jsonify({'error': result}), 400
            
            return jsonify({'message': '值更新成功', 'data': result})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def delete_key(self):
        """删除YAML中的特定键"""
        try:
            data = request.get_json()
            file_path = data.get('file_path')
            key_path = data.get('key_path')
            
            if not all([file_path, key_path]):
                return jsonify({'error': '缺少必要参数'}), 400
            
            success, result = self.file_handler.delete_yaml_key(file_path, key_path)
            if not success:
                return jsonify({'error': result}), 400
            
            return jsonify({'message': '键删除成功', 'data': result})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def add_key(self):
        """添加新的键值对到YAML"""
        try:
            data = request.get_json()
            file_path = data.get('file_path')
            key_path = data.get('key_path')
            value = data.get('value')
            
            if not all([file_path, key_path, value]):
                return jsonify({'error': '缺少必要参数'}), 400
            
            success, result = self.file_handler.add_yaml_key(file_path, key_path, value)
            if not success:
                return jsonify({'error': result}), 400
            
            return jsonify({'message': '键值对添加成功', 'data': result})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def upload_file(self):
        """上传YAML文件"""
        if request.method == 'POST':
            if 'file' not in request.files:
                return jsonify({'error': '没有选择文件'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': '没有选择文件'}), 400
            
            if file and self.file_handler.allowed_file(file.filename):
                try:
                    filename = os.path.basename(file.filename)
                    file_path = os.path.join(self.config['app']['upload_folder'], filename)
                    file.save(file_path)
                    
                    # 验证YAML格式
                    success, error = self.file_handler.save_yaml_file(file_path, file.read().decode())
                    if not success:
                        os.remove(file_path)
                        return jsonify({'error': f'YAML格式错误: {error}'}), 400
                    
                    return jsonify({'message': '文件上传成功', 'filename': filename})
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            else:
                return jsonify({'error': '不支持的文件类型'}), 400
        
        return render_template('upload.html')
    
    def download_file(self, file_path):
        """下载YAML文件"""
        try:
            file_path = os.path.normpath(file_path)
            if os.path.exists(file_path):
                return send_file(file_path, as_attachment=True)
            else:
                return jsonify({'error': '文件不存在'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def update_values(self):
        """批量更新YAML中的多个值"""
        try:
            data = request.get_json()
            file_path = data.get('file_path')
            changes = data.get('changes', [])
            
            if not file_path or not changes:
                return jsonify({'error': '缺少必要参数'}), 400
            
            # 读取当前文件
            yaml_data, _, error = self.file_handler.read_yaml_file(file_path)
            if error:
                return jsonify({'error': f'读取文件失败: {error}'}), 500
            
            # 批量更新值
            for change in changes:
                key_path = change.get('key_path')
                new_value = change.get('value')
                
                if key_path and new_value is not None:
                    success, result = self.file_handler.update_yaml_value(file_path, key_path, new_value)
                    if not success:
                        return jsonify({'error': f'更新失败: {result}'}), 400
            
            # 读取更新后的文件
            yaml_data, _, error = self.file_handler.read_yaml_file(file_path)
            if error:
                return jsonify({'error': f'读取更新后的文件失败: {error}'}), 500
            
            return jsonify({'message': '批量更新成功', 'data': yaml_data})
        except Exception as e:
            return jsonify({'error': str(e)}), 500 