 #!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yaml
import os

def test_yaml_edit():
    """测试YAML文件编辑功能"""
    file_path = r"C:\Users\z3744\Desktop\cursor_project\RY_PytestDemo\data\auth_data.yaml"
    
    print(f"测试文件: {file_path}")
    print(f"文件存在: {os.path.exists(file_path)}")
    print(f"文件可写: {os.access(file_path, os.W_OK)}")
    
    # 读取文件
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"文件内容长度: {len(content)}")
            print("文件内容前100字符:")
            print(content[:100])
            
            yaml_data = yaml.safe_load(content)
            print(f"YAML解析成功: {type(yaml_data)}")
            
            # 测试修改值
            if 'login' in yaml_data and 'success' in yaml_data['login']:
                old_value = yaml_data['login']['success'].get('username', '')
                print(f"当前username值: {old_value}")
                
                # 修改值
                yaml_data['login']['success']['username'] = 'test_user_modified'
                
                # 保存文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)
                
                print("文件修改成功!")
                
                # 验证修改
                with open(file_path, 'r', encoding='utf-8') as f:
                    new_data = yaml.safe_load(f)
                    new_value = new_data['login']['success'].get('username', '')
                    print(f"修改后username值: {new_value}")
                    
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_yaml_edit()