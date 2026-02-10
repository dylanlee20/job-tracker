#!/bin/bash

# 启动脚本 - 自动化职位追踪系统

echo "启动职位追踪系统..."
echo ""

# 检查数据库是否存在
if [ ! -f "data/jobs.db" ]; then
    echo "数据库未初始化，正在初始化..."
    python3 -c "from models.database import init_db; from flask import Flask; from config import Config; app = Flask(__name__); app.config.from_object(Config); init_db(app)"
fi

# 启动应用
python3 app.py
