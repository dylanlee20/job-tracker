import os

class Config:
    """应用配置类"""

    # 项目根目录
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # 数据库配置
    DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'jobs.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 爬虫配置
    SCRAPER_DELAY_MIN = 1  # 随机延迟最小值（秒）
    SCRAPER_DELAY_MAX = 3  # 随机延迟最大值（秒）
    SCRAPER_TIMEOUT = 30   # 页面加载超时（秒）
    SCRAPER_RETRY_COUNT = 3  # 失败重试次数

    # Chrome Driver 配置
    CHROME_DRIVER_PATH = None  # None 表示使用 webdriver-manager 自动管理
    HEADLESS_MODE = True       # 无头模式

    # 定时任务配置
    SCHEDULE_HOUR = 9          # 每天执行的小时
    SCHEDULE_MINUTE = 0        # 每天执行的分钟
    TIMEZONE = 'Asia/Shanghai' # 时区

    # Excel 导出配置
    EXCEL_EXPORT_PATH = os.path.join(BASE_DIR, 'data', 'exports', 'jobs_export.xlsx')

    # 日志配置
    LOG_FILE = os.path.join(BASE_DIR, 'data', 'logs', 'scraper.log')
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Flask 配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')  # 0.0.0.0 for cloud deployment
    PORT = int(os.environ.get('PORT', os.environ.get('FLASK_PORT', 5000)))  # Railway uses PORT

    # 新职位定义（天数）
    NEW_JOB_DAYS = 7  # 7 天内的职位视为新职位
    UPDATED_JOB_DAYS = 3  # 3 天内更新的职位视为最近更新

    # 公司网站配置
    COMPANY_WEBSITES = {
        'JPMorgan - US': 'https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs?keyword=CIB&mode=location',
        'JPMorgan - Australia': 'https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs?keyword=CIB&location=Sydney%2C+NSW%2C+Australia&locationId=300000024729598&locationLevel=city&mode=location&radius=25&radiusUnit=KM',
        'JPMorgan - Hong Kong': 'https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs?location=Hong+Kong&locationId=300000000289330&locationLevel=country&mode=location',
        'Goldman Sachs - US': 'https://higher.gs.com/results?DIVISION=Global%20Banking%20%26%20Markets&JOB_FUNCTION=&LOCATION=Albany|New%20York|Atlanta|Boston|Chicago|Dallas|Houston|Richardson|Detroit|Jersey%20City|Los%20Angeles|Menlo%20Park|Newport%20Beach|San%20Francisco|Miami|West%20Palm%20Beach|Philadelphia|Pittsburgh|Salt%20Lake%20City|Seattle|Washington|Wilmington&page=1&sort=RELEVANCE',
        'Goldman Sachs - International': 'https://higher.gs.com/results?LOCATION=Hong%20Kong|Melbourne|Sydney|Sydney|Calgary|Toronto|Beijing|Shanghai|Shenzhen|Minato-Ku|Seoul|Auckland|Singapore|Dubai|Birmingham|London&page=1&sort=RELEVANCE',
        'Morgan Stanley': 'https://www.morganstanley.com/careers/career-opportunities-search?opportunity=sg#',
        'Citi': 'https://jobs.citi.com/search-jobs?utm_source=chatgpt.com',
        'Deutsche Bank': 'https://careers.db.com/students-graduates/index?language_id=1#/graduate/',
        'UBS': 'https://www.ubs.com/global/en/careers/professional-careers/investment-bank.html#join',
        'BNP Paribas': 'https://usa.bnpparibas/en/homepage/join-us/our-opportunities/students-graduates/',
        'Nomura': 'https://nomuracampus.tal.net/vx/lang-en-GB/mobile-0/appcentre-ext/brand-4/xf-3348347fc789/candidate/jobboard/vacancy/1/adv/',
        'Piper Sandler': 'https://pipersandler.wd501.myworkdayjobs.com/Piper_Sandler_Careers'
    }
