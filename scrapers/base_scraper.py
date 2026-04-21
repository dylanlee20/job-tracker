from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import random
import logging
import os
from config import Config

# 配置日志
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class BaseScraper(ABC):
    """爬虫基类"""

    def __init__(self, company_name, source_url):
        self.company_name = company_name
        self.source_url = source_url
        self.driver = None
        self.logger = logging.getLogger(f"{__name__}.{company_name}")

    def init_driver(self):
        """初始化 Selenium WebDriver"""
        try:
            chrome_options = Options()

            if Config.HEADLESS_MODE:
                chrome_options.add_argument('--headless')

            # 添加常用选项
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')

            # 设置 User-Agent
            chrome_options.add_argument(
                'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )

            # 禁用自动化检测
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 使用 webdriver-manager 自动管理 ChromeDriver
            try:
                driver_path = ChromeDriverManager().install()

                # webdriver-manager 4.x 有时返回 THIRD_PARTY_NOTICES.chromedriver
                # 文件而不是 chromedriver 二进制。此时优先取同目录下的 chromedriver
                # 兄弟文件（就是刚下载好、版本匹配的那个），其次才按最高版本目录回退。
                if 'THIRD_PARTY_NOTICES' in driver_path or not os.path.exists(driver_path):
                    sibling = os.path.join(os.path.dirname(driver_path), 'chromedriver')
                    if os.path.exists(sibling) and os.path.getsize(sibling) > 1_000_000:
                        os.chmod(sibling, 0o755)
                        driver_path = sibling
                        self.logger.info(f"Corrected chromedriver path to sibling: {driver_path}")
                    else:
                        # 回退：按版本号降序扫描缓存，取最新版本，而不是 os.walk 的第一个结果
                        cache_base = os.path.expanduser('~/.wdm/drivers/chromedriver/mac64')
                        found = False
                        if os.path.isdir(cache_base):
                            def _ver_key(name):
                                try:
                                    return tuple(int(x) for x in name.split('.'))
                                except Exception:
                                    return (0,)
                            version_dirs = sorted(
                                (d for d in os.listdir(cache_base)
                                 if os.path.isdir(os.path.join(cache_base, d))),
                                key=_ver_key, reverse=True,
                            )
                            for vd in version_dirs:
                                candidate = os.path.join(
                                    cache_base, vd, 'chromedriver-mac-x64', 'chromedriver'
                                )
                                if os.path.exists(candidate) and os.path.getsize(candidate) > 1_000_000:
                                    os.chmod(candidate, 0o755)
                                    driver_path = candidate
                                    self.logger.info(f"Found chromedriver at: {driver_path}")
                                    found = True
                                    break
                        if not found:
                            raise Exception("Could not find valid chromedriver executable")

                service = Service(driver_path)
            except Exception as e:
                self.logger.error(f"ChromeDriver setup failed: {e}")
                raise
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # 设置页面加载超时
            self.driver.set_page_load_timeout(Config.SCRAPER_TIMEOUT)

            self.logger.info(f"WebDriver initialized for {self.company_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver for {self.company_name}: {e}")
            return False

    def close_driver(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info(f"WebDriver closed for {self.company_name}")
            except Exception as e:
                self.logger.error(f"Error closing WebDriver for {self.company_name}: {e}")

    def random_delay(self):
        """随机延迟，避免被反爬"""
        delay = random.uniform(Config.SCRAPER_DELAY_MIN, Config.SCRAPER_DELAY_MAX)
        time.sleep(delay)

    def wait_for_element(self, by, value, timeout=10):
        """等待元素出现"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            self.logger.warning(f"Element not found: {by}={value}, {e}")
            return None

    def scroll_to_bottom(self, pause_time=1):
        """滚动到页面底部（处理懒加载）"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            while True:
                # 滚动到底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(pause_time)

                # 计算新高度
                new_height = self.driver.execute_script("return document.body.scrollHeight")

                # 如果高度没有变化，说明已到底部
                if new_height == last_height:
                    break

                last_height = new_height

        except Exception as e:
            self.logger.warning(f"Error scrolling to bottom: {e}")

    @abstractmethod
    def scrape_jobs(self):
        """
        抓取职位列表（抽象方法，由子类实现）

        Returns:
            List[Dict]: 职位列表，每个职位包含以下字段：
                - company: 公司名称
                - title: 职位名称
                - location: 工作地点
                - description: 职位描述
                - post_date: 发布日期（可选）
                - deadline: 截止日期（可选）
                - source_website: 来源网站
                - job_url: 职位链接
        """
        pass

    def scrape_with_retry(self, max_retries=None):
        """
        带重试机制的爬取

        Args:
            max_retries: 最大重试次数，默认使用配置文件中的值

        Returns:
            List[Dict]: 职位列表
        """
        if max_retries is None:
            max_retries = Config.SCRAPER_RETRY_COUNT

        for attempt in range(max_retries):
            try:
                self.logger.info(
                    f"Starting scrape for {self.company_name} (attempt {attempt + 1}/{max_retries})"
                )

                # 初始化 WebDriver
                if not self.init_driver():
                    raise Exception("Failed to initialize WebDriver")

                # 执行爬取
                jobs = self.scrape_jobs()

                self.logger.info(
                    f"Successfully scraped {len(jobs)} jobs from {self.company_name}"
                )

                return jobs

            except Exception as e:
                self.logger.error(
                    f"Scrape failed for {self.company_name} (attempt {attempt + 1}/{max_retries}): {e}"
                )

                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    self.logger.error(f"All retry attempts failed for {self.company_name}")
                    return []

            finally:
                # 确保关闭浏览器
                self.close_driver()

        return []

    def get_page_source(self):
        """获取当前页面源代码"""
        return self.driver.page_source if self.driver else None

    def get_soup(self):
        """获取 BeautifulSoup 对象"""
        page_source = self.get_page_source()
        return BeautifulSoup(page_source, 'lxml') if page_source else None
