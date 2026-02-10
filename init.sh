#!/bin/bash

# 初始化脚本 - 自动化职位追踪系统

echo "================================"
echo "自动化职位追踪系统 - 初始化脚本"
echo "================================"
echo ""

# 检查 Python 版本
echo "[1/5] 检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本: $python_version"

# 安装依赖
echo ""
echo "[2/5] 安装 Python 依赖..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "错误: 依赖安装失败"
    exit 1
fi

# 创建必要的目录
echo ""
echo "[3/5] 创建数据目录..."
mkdir -p data/exports
mkdir -p data/logs

# 初始化数据库
echo ""
echo "[4/5] 初始化数据库..."
python3 -c "from models.database import init_db; from flask import Flask; from config import Config; app = Flask(__name__); app.config.from_object(Config); init_db(app)"

if [ $? -ne 0 ]; then
    echo "错误: 数据库初始化失败"
    exit 1
fi

# 检查 Chrome 浏览器
echo ""
echo "[5/5] 检查 Chrome 浏览器..."
if [ -d "/Applications/Google Chrome.app" ]; then
    echo "✓ Chrome 浏览器已安装"
else
    echo "⚠ 警告: 未检测到 Chrome 浏览器"
    echo "请安装 Chrome 浏览器: brew install --cask google-chrome"
fi

# 完成
echo ""
echo "================================"
echo "✓ 初始化完成！"
echo "================================"
echo ""
echo "使用方法:"
echo "  1. 启动应用: python3 app.py"
echo "  2. 访问: http://127.0.0.1:5000"
echo "  3. 点击"立即爬取"开始首次爬取"
echo ""
echo "配置文件: config.py"
echo "数据库: data/jobs.db"
echo "Excel 导出: data/exports/jobs_export.xlsx"
echo "日志文件: data/logs/scraper.log"
echo ""
