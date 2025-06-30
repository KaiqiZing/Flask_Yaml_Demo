# YAML管理工具

一个基于Flask的Web应用程序，用于管理和编辑YAML文件。

## 功能特性

- 🔍 **扫描YAML文件**: 自动扫描项目目录下的所有.yaml和.yml文件
- 📁 **指定扫描目录**: 支持指定任意目录进行YAML文件扫描
- 👀 **查看文件内容**: 以结构化和原始格式查看YAML文件
- ✏️ **编辑文件**: 支持直接编辑YAML文件内容
- ➕ **添加参数**: 支持添加新的键值对
- ✏️ **修改参数**: 支持修改现有的参数值
- 🗑️ **删除参数**: 支持删除指定的参数
- 💾 **保存功能**: 实时保存修改到文件
- 📤 **文件上传**: 支持上传新的YAML文件
- 📥 **文件下载**: 支持下载YAML文件

## 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置应用

编辑 `config.yaml` 文件来配置应用：

```yaml
app:
  # 默认扫描目录，支持相对路径和绝对路径
  default_scan_dir: "."
  
  # 上传文件配置
  upload_folder: "uploads"
  max_file_size: 16777216  # 16MB
  
  # 排除的目录（不会扫描这些目录中的YAML文件）
  exclude_dirs:
    - "uploads"
    - "__pycache__"
    - ".git"
    - "node_modules"
    - ".vscode"
  
  # 支持的文件扩展名
  allowed_extensions:
    - "yaml"
    - "yml"

server:
  host: "0.0.0.0"
  port: 5000
  debug: true
```

### 3. 运行应用

```bash
python app.py
```

### 4. 访问应用

打开浏览器访问: http://localhost:5000

## 使用说明

### 主页
- 显示指定目录下所有YAML文件的列表
- 支持通过界面切换扫描目录
- 每个文件显示名称、路径、大小和状态
- 支持查看、编辑、下载操作

### 指定扫描目录
- **通过URL参数**: 访问 `/?dir=你的目录路径`
- **通过界面**: 在主页的目录选择器中输入路径并点击扫描
- **配置文件**: 修改 `config.yaml` 中的 `default_scan_dir`

### 查看文件
- 左侧显示原始YAML内容
- 右侧显示结构化的数据树
- 支持展开/折叠嵌套结构

### 编辑文件
- 左侧提供YAML编辑器
- 右侧提供快速操作面板：
  - 添加新键值对
  - 修改现有值
  - 删除指定键
- 支持实时保存

### 上传文件
- 支持拖拽或选择文件
- 提供文件预览功能
- 自动验证YAML格式

## API接口

### 文件操作
- `GET /` - 主页，显示文件列表
- `GET /?dir=<directory>` - 指定目录扫描
- `GET /view/<file_path>` - 查看文件内容
- `GET /edit/<file_path>` - 编辑文件页面
- `GET /upload` - 上传文件页面

### API端点
- `POST /api/save` - 保存文件内容
- `POST /api/update_value` - 更新特定值
- `POST /api/delete_key` - 删除特定键
- `POST /api/add_key` - 添加新键值对
- `GET /api/scan` - 扫描YAML文件
- `GET /api/download/<file_path>` - 下载文件
- `POST /upload` - 上传文件

## 配置说明

### 扫描目录配置
- `default_scan_dir`: 默认扫描目录，支持相对路径和绝对路径
- `exclude_dirs`: 排除的目录列表，这些目录中的YAML文件不会被扫描
- `allowed_extensions`: 支持的文件扩展名

### 文件上传配置
- `upload_folder`: 上传文件保存目录
- `max_file_size`: 最大文件大小限制

### 服务器配置
- `host`: 服务器监听地址
- `port`: 服务器端口
- `debug`: 调试模式开关

## 支持的文件格式

- `.yaml`
- `.yml`

## 技术栈

- **后端**: Flask
- **前端**: Bootstrap 5, Font Awesome
- **YAML处理**: PyYAML
- **文件处理**: Werkzeug

## 注意事项

- 应用会自动排除配置文件中指定的目录
- 上传的文件会保存在配置的上传目录中
- 支持递归扫描子目录
- 自动验证YAML格式的正确性
- 支持通过URL参数或界面动态切换扫描目录

## 许可证

MIT License 