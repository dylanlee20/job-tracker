from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from services.scraper_service import ScraperService
from services.excel_service import ExcelService
from services.snapshot_service import SnapshotService
from config import Config
import logging

logger = logging.getLogger(__name__)


class JobScheduler:
    """定时任务调度器"""

    def __init__(self, app):
        """
        初始化调度器

        Args:
            app: Flask 应用实例
        """
        self.app = app
        self.scheduler = BackgroundScheduler(timezone=Config.TIMEZONE)

    def scheduled_scrape_task(self):
        """定时执行的爬取任务"""
        with self.app.app_context():
            try:
                logger.info("Starting scheduled scraping task...")

                # 执行所有爬虫
                results = ScraperService.run_all_scrapers()

                # 自动导出 Excel
                try:
                    excel_path = ExcelService.auto_sync_excel()
                    logger.info(f"Excel file auto-synced to {excel_path}")
                except Exception as e:
                    logger.error(f"Error auto-syncing Excel: {e}")

                # 记录汇总结果
                summary = results['summary']
                logger.info(
                    f"Scheduled scraping completed. Summary: "
                    f"{summary['total_new']} new jobs, "
                    f"{summary['total_updated']} updated jobs, "
                    f"{summary['total_inactive']} inactive jobs, "
                    f"{summary['successful_companies']}/{len(results['companies'])} companies successful"
                )

            except Exception as e:
                logger.error(f"Error in scheduled scraping task: {e}")

    def weekly_snapshot_task(self):
        """Weekly snapshot capture for historical tracking"""
        with self.app.app_context():
            try:
                logger.info("Capturing weekly job market snapshot...")
                snapshot = SnapshotService.capture_weekly_snapshot()
                logger.info(
                    f"Weekly snapshot captured: {snapshot.total_active_jobs} jobs, "
                    f"{snapshot.new_jobs_this_week} new, {snapshot.closed_jobs_this_week} closed"
                )
            except Exception as e:
                logger.error(f"Error capturing weekly snapshot: {e}")

    def start(self):
        """启动定时任务调度器"""
        try:
            # 添加定时任务（每天指定时间执行）
            self.scheduler.add_job(
                func=self.scheduled_scrape_task,
                trigger=CronTrigger(
                    hour=Config.SCHEDULE_HOUR,
                    minute=Config.SCHEDULE_MINUTE,
                    timezone=Config.TIMEZONE
                ),
                id='daily_scrape',
                name='Daily job scraping task',
                replace_existing=True
            )

            # 添加周度快照任务（每周日凌晨2点执行）
            self.scheduler.add_job(
                func=self.weekly_snapshot_task,
                trigger=CronTrigger(
                    day_of_week='sun',
                    hour=2,
                    minute=0,
                    timezone=Config.TIMEZONE
                ),
                id='weekly_snapshot',
                name='Weekly job market snapshot',
                replace_existing=True
            )

            # 启动调度器
            self.scheduler.start()

            logger.info(
                f"Job scheduler started. Daily scraping scheduled at "
                f"{Config.SCHEDULE_HOUR:02d}:{Config.SCHEDULE_MINUTE:02d} {Config.TIMEZONE}"
            )
            logger.info("Weekly snapshots scheduled for Sundays at 02:00")

        except Exception as e:
            logger.error(f"Error starting job scheduler: {e}")
            raise

    def stop(self):
        """停止定时任务调度器"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Job scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping job scheduler: {e}")

    def run_now(self):
        """立即执行一次爬取任务"""
        logger.info("Running scrape task immediately...")
        self.scheduled_scrape_task()

    def get_next_run_time(self):
        """获取下次执行时间"""
        job = self.scheduler.get_job('daily_scrape')
        if job:
            return job.next_run_time
        return None

    def reschedule(self, hour=None, minute=None):
        """
        重新设置定时任务时间

        Args:
            hour: 小时 (0-23)
            minute: 分钟 (0-59)
        """
        if hour is None:
            hour = Config.SCHEDULE_HOUR
        if minute is None:
            minute = Config.SCHEDULE_MINUTE

        try:
            self.scheduler.reschedule_job(
                'daily_scrape',
                trigger=CronTrigger(
                    hour=hour,
                    minute=minute,
                    timezone=Config.TIMEZONE
                )
            )

            logger.info(f"Rescheduled daily scraping to {hour:02d}:{minute:02d} {Config.TIMEZONE}")

        except Exception as e:
            logger.error(f"Error rescheduling job: {e}")
            raise
