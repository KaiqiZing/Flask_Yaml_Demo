import os
import yaml
from pathlib import Path
from werkzeug.utils import secure_filename

class YamlFileHandler:
    """YAML文件处理类"""
    
    def __init__(self, config):
        self.config = config
        self.upload_folder = config['app']['upload_folder']
        self.allowed_extensions = set(config['app']['allowed_extensions'])
        self.exclude_dirs = config['app']['exclude_dirs']
        
        # 确保上传目录存在
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def allowed_file(self, filename):
        """检查文件扩展名是否允许"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def scan_yaml_files(self, directory='.'):
        """扫描指定目录下的所有YAML文件"""
        yaml_files = []
        patterns = [f'**/*.{ext}' for ext in self.allowed_extensions]
        
        for pattern in patterns:
            for file_path in Path(directory).glob(pattern):
                # 检查是否在排除目录中
                if not any(exclude_dir in str(file_path) for exclude_dir in self.exclude_dirs):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            yaml_data = yaml.safe_load(content)
                            
                            yaml_files.append({
                                'path': str(file_path),
                                'name': file_path.name,
                                'size': file_path.stat().st_size,
                                'content': yaml_data,
                                'raw_content': content
                            })
                    except Exception as e:
                        yaml_files.append({
                            'path': str(file_path),
                            'name': file_path.name,
                            'size': file_path.stat().st_size,
                            'error': str(e),
                            'content': None,
                            'raw_content': None
                        })
        return yaml_files
    
    def save_yaml_file(self, file_path, content):
        """保存YAML文件"""
        try:
            # 验证YAML格式
            yaml.safe_load(content)
            
            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, None
        except Exception as e:
            return False, str(e)
    
    def read_yaml_file(self, file_path):
        """读取YAML文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                yaml_data = yaml.safe_load(content)
                return yaml_data, content, None
        except Exception as e:
            return None, None, str(e)
    
    def update_yaml_value(self, file_path, key_path, new_value):
        """更新YAML中的特定值"""
        try:
            # 读取当前文件
            yaml_data, _, error = self.read_yaml_file(file_path)
            if error:
                return False, error
            
            # 更新值
            current = yaml_data
            keys = key_path.split('.')
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = new_value
            
            # 保存文件
            content = yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True)
            success, error = self.save_yaml_file(file_path, content)
            if not success:
                return False, error
            
            return True, yaml_data
        except Exception as e:
            return False, str(e)
    
    def delete_yaml_key(self, file_path, key_path):
        """删除YAML中的特定键"""
        try:
            # 读取当前文件
            yaml_data, _, error = self.read_yaml_file(file_path)
            if error:
                return False, error
            
            # 删除键
            current = yaml_data
            keys = key_path.split('.')
            for key in keys[:-1]:
                if key not in current:
                    return False, "键路径不存在"
                current = current[key]
            
            if keys[-1] in current:
                del current[keys[-1]]
            else:
                return False, "键不存在"
            
            # 保存文件
            content = yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True)
            success, error = self.save_yaml_file(file_path, content)
            if not success:
                return False, error
            
            return True, yaml_data
        except Exception as e:
            return False, str(e)
    
    def add_yaml_key(self, file_path, key_path, value):
        """添加新的键值对到YAML"""
        try:
            # 读取当前文件
            yaml_data, _, error = self.read_yaml_file(file_path)
            if error:
                yaml_data = {}
            
            # 添加键值对
            current = yaml_data
            keys = key_path.split('.')
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = value
            
            # 保存文件
            content = yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True)
            success, error = self.save_yaml_file(file_path, content)
            if not success:
                return False, error
            
            return True, yaml_data
        except Exception as e:
            return False, str(e) 