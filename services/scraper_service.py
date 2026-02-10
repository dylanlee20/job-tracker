from services.job_service import JobService
from scrapers.jpmorgan_scraper import JPMorganScraper
import threading
from datetime import datetime
from scrapers.jpmorgan_australia_scraper import JPMorganAustraliaScraper
from scrapers.jpmorgan_hongkong_scraper import JPMorganHongKongScraper
from scrapers.goldman_scraper import GoldmanSachsScraper
from scrapers.goldman_sachs_international_scraper import GoldmanSachsInternationalScraper
from scrapers.morgan_stanley_scraper import MorganStanleyScraper
from scrapers.citi_scraper import CitiScraper
from scrapers.deutsche_bank_scraper import DeutscheBankScraper
from scrapers.ubs_scraper import UBSScraper
from scrapers.bnp_paribas_scraper import BNPParibasScraper
from scrapers.nomura_scraper import NomuraScraper
from scrapers.evercore_scraper import EvercoreScraper
from scrapers.blackstone_scraper import BlackstoneScraper
from scrapers.piper_sandler_scraper import PiperSandlerScraper
from scrapers.jefferies_scraper import JefferiesScraper
from scrapers.mizuho_scraper import MizuhoScraper
from scrapers.barclays_scraper import BarclaysScraper
import logging

logger = logging.getLogger(__name__)


class ScraperService:
    """爬虫调度服务"""

    # Progress tracking
    _progress = {
        'is_running': False,
        'current_company': None,
        'current_index': 0,
        'total_companies': 0,
        'completed_companies': [],
        'failed_companies': [],
        'start_time': None,
        'results': None
    }
    _lock = threading.Lock()

    @classmethod
    def get_progress(cls):
        """Get current scraping progress"""
        with cls._lock:
            # Deep copy to avoid race conditions with lists
            return {
                'is_running': cls._progress['is_running'],
                'current_company': cls._progress['current_company'],
                'current_index': cls._progress['current_index'],
                'total_companies': cls._progress['total_companies'],
                'completed_companies': list(cls._progress['completed_companies']),
                'failed_companies': list(cls._progress['failed_companies']),
                'start_time': cls._progress['start_time'],
                'results': cls._progress['results']
            }

    @classmethod
    def is_running(cls):
        """Check if scraping is in progress"""
        with cls._lock:
            return cls._progress['is_running']

    @classmethod
    def _update_progress(cls, **kwargs):
        """Update progress state"""
        with cls._lock:
            cls._progress.update(kwargs)

    @classmethod
    def _add_completed(cls, company_name):
        """Thread-safe add to completed list"""
        with cls._lock:
            cls._progress['completed_companies'].append(company_name)

    @classmethod
    def _add_failed(cls, company_name):
        """Thread-safe add to failed list"""
        with cls._lock:
            cls._progress['failed_companies'].append(company_name)

    @classmethod
    def _reset_progress(cls):
        """Reset progress state"""
        with cls._lock:
            cls._progress = {
                'is_running': False,
                'current_company': None,
                'current_index': 0,
                'total_companies': 0,
                'completed_companies': [],
                'failed_companies': [],
                'start_time': None,
                'results': None
            }

    # 所有爬虫类的映射
    SCRAPERS = {
        'JPMorgan - US': JPMorganScraper,
        'JPMorgan - Australia': JPMorganAustraliaScraper,
        'JPMorgan - Hong Kong': JPMorganHongKongScraper,
        'Goldman Sachs - US': GoldmanSachsScraper,
        'Goldman Sachs - International': GoldmanSachsInternationalScraper,
        'Morgan Stanley': MorganStanleyScraper,
        'Citi': CitiScraper,
        'Deutsche Bank': DeutscheBankScraper,
        'UBS': UBSScraper,
        'BNP Paribas': BNPParibasScraper,
        'Nomura': NomuraScraper,
        'Evercore': EvercoreScraper,
        'Blackstone': BlackstoneScraper,
        'Piper Sandler': PiperSandlerScraper,
        'Jefferies': JefferiesScraper,
        'Mizuho': MizuhoScraper,
        'Barclays': BarclaysScraper
    }

    @classmethod
    def run_all_scrapers(cls, with_progress=False):
        """
        执行所有爬虫

        Args:
            with_progress: If True, update progress tracking

        Returns:
            dict: 包含每个公司爬取结果的字典
        """
        overall_results = {
            'companies': {},
            'summary': {
                'total_new': 0,
                'total_updated': 0,
                'total_inactive': 0,
                'total_scraped': 0,
                'successful_companies': 0,
                'failed_companies': 0
            }
        }

        company_list = list(cls.SCRAPERS.keys())
        total = len(company_list)

        if with_progress:
            cls._update_progress(
                is_running=True,
                total_companies=total,
                current_index=0,
                start_time=datetime.now().isoformat(),
                completed_companies=[],
                failed_companies=[]
            )

        logger.info("Starting scraping for all companies...")

        for idx, company_name in enumerate(company_list):
            scraper_class = cls.SCRAPERS[company_name]

            if with_progress:
                cls._update_progress(
                    current_company=company_name,
                    current_index=idx + 1
                )

            try:
                logger.info(f"Running scraper for {company_name}...")

                # 创建爬虫实例
                scraper = scraper_class()

                # 执行爬取（带重试机制）
                jobs = scraper.scrape_with_retry()

                if jobs:
                    # 处理爬取的职位数据
                    stats = JobService.process_scraped_jobs(jobs, company_name)

                    overall_results['companies'][company_name] = {
                        'success': True,
                        'stats': stats
                    }

                    # 更新总体统计
                    overall_results['summary']['total_new'] += stats['new_jobs']
                    overall_results['summary']['total_updated'] += stats['updated_jobs']
                    overall_results['summary']['total_inactive'] += stats['inactive_jobs']
                    overall_results['summary']['total_scraped'] += stats['total_scraped']
                    overall_results['summary']['successful_companies'] += 1

                    if with_progress:
                        cls._add_completed(company_name)

                    logger.info(
                        f"{company_name}: Scraped {stats['total_scraped']} jobs, "
                        f"{stats['new_jobs']} new, {stats['updated_jobs']} updated, "
                        f"{stats['inactive_jobs']} inactive"
                    )
                else:
                    overall_results['companies'][company_name] = {
                        'success': False,
                        'error': 'No jobs scraped'
                    }
                    overall_results['summary']['failed_companies'] += 1

                    if with_progress:
                        cls._add_failed(company_name)

                    logger.warning(f"{company_name}: No jobs scraped")

            except Exception as e:
                logger.error(f"Error scraping {company_name}: {e}")

                overall_results['companies'][company_name] = {
                    'success': False,
                    'error': str(e)
                }
                overall_results['summary']['failed_companies'] += 1

                if with_progress:
                    cls._add_failed(company_name)

        if with_progress:
            cls._update_progress(
                is_running=False,
                current_company=None,
                results=overall_results
            )

        logger.info(
            f"Scraping completed. Summary: "
            f"{overall_results['summary']['total_new']} new jobs, "
            f"{overall_results['summary']['total_updated']} updated, "
            f"{overall_results['summary']['total_inactive']} inactive, "
            f"{overall_results['summary']['successful_companies']} companies successful, "
            f"{overall_results['summary']['failed_companies']} failed"
        )

        return overall_results

    @classmethod
    def run_all_scrapers_async(cls, app=None):
        """Run all scrapers in a background thread with progress tracking"""
        if cls.is_running():
            logger.warning("Scraping already in progress, resetting...")
            cls._reset_progress()

        # Initialize progress immediately
        total = len(cls.SCRAPERS)
        cls._update_progress(
            is_running=True,
            total_companies=total,
            current_index=0,
            current_company='Initializing...',
            start_time=datetime.now().isoformat(),
            completed_companies=[],
            failed_companies=[],
            results=None
        )
        logger.info(f"Progress initialized: {total} companies")

        def run():
            try:
                logger.info("Background scraping thread started")
                cls.run_all_scrapers(with_progress=True)
                # Auto export Excel after scraping
                try:
                    from services.excel_service import ExcelService
                    ExcelService.auto_sync_excel()
                    logger.info("Excel auto-sync completed")
                except Exception as e:
                    logger.warning(f"Error auto-syncing Excel after scrape: {e}")
            except Exception as e:
                logger.error(f"Error in async scraping: {e}")
                import traceback
                traceback.print_exc()
                cls._update_progress(is_running=False, current_company=None)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        logger.info("Background thread started successfully")
        return True

    @staticmethod
    def run_single_scraper(company_name):
        """
        执行单个公司的爬虫

        Args:
            company_name: 公司名称

        Returns:
            dict: 爬取结果
        """
        if company_name not in ScraperService.SCRAPERS:
            return {
                'success': False,
                'error': f'Unknown company: {company_name}'
            }

        try:
            logger.info(f"Running scraper for {company_name}...")

            scraper_class = ScraperService.SCRAPERS[company_name]
            scraper = scraper_class()

            # 执行爬取
            jobs = scraper.scrape_with_retry()

            if jobs:
                # 处理爬取的职位数据
                stats = JobService.process_scraped_jobs(jobs, company_name)

                logger.info(
                    f"{company_name}: Scraped {stats['total_scraped']} jobs, "
                    f"{stats['new_jobs']} new, {stats['updated_jobs']} updated, "
                    f"{stats['inactive_jobs']} inactive"
                )

                return {
                    'success': True,
                    'stats': stats
                }
            else:
                return {
                    'success': False,
                    'error': 'No jobs scraped'
                }

        except Exception as e:
            logger.error(f"Error scraping {company_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def get_available_companies():
        """获取所有可用的公司列表"""
        return list(ScraperService.SCRAPERS.keys())
