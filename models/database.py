from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

# 初始化 SQLAlchemy
db = SQLAlchemy()


# 启用 SQLite 外键约束
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    if isinstance(dbapi_conn, sqlite3.Connection):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_db(app):
    """初始化数据库"""
    db.init_app(app)

    with app.app_context():
        # 创建所有表
        db.create_all()
        print("Database initialized successfully!")


def reset_db(app):
    """重置数据库（删除所有表并重新创建）"""
    db.init_app(app)

    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset successfully!")
