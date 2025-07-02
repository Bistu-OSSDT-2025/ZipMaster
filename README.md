# ZipMaster


🗜️ **ZipMaster** - 开源压缩包管理工具 (Python 版本)

一个功能强大、易于使用的压缩包管理工具，支持多种压缩格式的创建、解压、查看和管理。

## ✨ 特性

- 🎯 **多格式支持**: 支持 7z、ZIP、RAR、TAR、GZ、BZ2、XZ 等主流压缩格式
- 🔍 **智能搜索**: 快速搜索和过滤压缩包文件
- 📊 **详细信息**: 查看压缩包内容、文件数量、压缩比等详细信息
- 🖥️ **现代化界面**: 基于 Tkinter 的直观用户界面
- 📁 **批量操作**: 支持批量扫描、解压和创建压缩包
- 💾 **数据库存储**: 使用 SQLite 数据库管理压缩包索引
- ⚡ **高性能**: 多线程处理，提升操作效率
- 🔧 **易于扩展**: 模块化设计，便于功能扩展

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Windows / macOS / Linux

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/your-username/zipmaster.git
cd zipmaster

# 创建虚拟环境（推荐）
python -m venv zipmaster_env

# 激活虚拟环境
# Windows:
zipmaster_env\Scripts\activate
# macOS/Linux:
source zipmaster_env/bin/activate

# 安装依赖
pip install -r requirements.txt```