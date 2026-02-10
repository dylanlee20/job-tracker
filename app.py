from flask import Flask
from models.database import db, init_db
from models.job import Job
from models.job_snapshot import JobSnapshot
from routes.api import api_bp
from routes.web import web_bp
from scheduler.job_scheduler import JobScheduler
from config import Config
import logging
import os

# 配置日志
try:
    os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
    handlers = [
        logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
except (OSError, PermissionError):
    # Cloud environment - file logging may not work
    handlers = [logging.StreamHandler()]

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT,
    handlers=handlers
)

logger = logging.getLogger(__name__)


def create_app():
    """创建并配置 Flask 应用"""

    # 创建 Flask 应用
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(Config)

    # 确保数据目录存在
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(Config.EXCEL_EXPORT_PATH), exist_ok=True)

    # 初始化数据库
    init_db(app)

    # 注册蓝图
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)

    # 初始化并启动定时任务调度器
    scheduler = JobScheduler(app)

    # Only start scheduler if not disabled (cloud mode doesn't have Chrome for scraping)
    if os.environ.get('DISABLE_SCHEDULER', 'false').lower() != 'true':
        try:
            scheduler.start()
            logger.info("Job scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start job scheduler: {e}")
    else:
        logger.info("Scheduler disabled (cloud mode - set DISABLE_SCHEDULER=false to enable)")

    # 添加关闭时的清理
    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        try:
            scheduler.stop()
        except:
            pass

    # 添加错误处理
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        db.session.rollback()
        return {'error': 'Internal server error'}, 500

    logger.info("Flask application created successfully")

    return app, scheduler


if __name__ == '__main__':
    # 创建应用
    app, scheduler = create_app()

    # 运行应用
    logger.info(f"Starting Flask application on {Config.HOST}:{Config.PORT}")
    logger.info(f"Debug mode: {Config.DEBUG}")
    logger.info(f"Database: {Config.DATABASE_PATH}")
    logger.info(f"Excel export path: {Config.EXCEL_EXPORT_PATH}")

    try:
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG,
            use_reloader=False  # 禁用自动重载，避免调度器重复启动
        )
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
    finally:
        logger.info("Shutting down application...")
