# 自动化职位追踪系统

一个完整的自动化职位爬取和管理系统，支持多个金融公司网站的职位追踪、去重、变更检测、Excel 导出和 Web 后台管理。

## 功能特性

- ✅ **自动爬取**：每天定时自动爬取 9 个金融公司的职位信息
- ✅ **智能去重**：基于公司+职位名+地点的 MD5 哈希自动去重
- ✅ **变更检测**：自动检测职位描述的更新并记录时间
- ✅ **状态追踪**：追踪新增、更新、下线的职位
- ✅ **Excel 导出**：自动同步到 Excel 文件，支持筛选和条件格式
- ✅ **Web 后台**：简洁的 Web 界面，支持搜索、筛选、标记重点
- ✅ **数据统计**：本周新增、本月新增、重点职位等统计信息

## 支持的公司

1. JPMorgan Chase
2. Goldman Sachs
3. Morgan Stanley
4. Citi
5. Deutsche Bank
6. UBS
7. BNP Paribas
8. Nomura
9. Piper Sandler

## 技术栈

- **后端**：Python 3.9+ + Flask
- **数据库**：SQLite + SQLAlchemy ORM
- **爬虫**：Selenium + BeautifulSoup
- **定时任务**：APScheduler
- **前端**：Bootstrap 5 + jQuery
- **Excel**：openpyxl

## 安装步骤

### 1. 克隆项目

```bash
# 项目已在 ~/Desktop/job-tracker 目录下
cd ~/Desktop/job-tracker
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 安装 ChromeDriver

系统使用 `webdriver-manager` 自动管理 ChromeDriver，但需要确保已安装 Chrome 浏览器。

**macOS**:
```bash
brew install --cask google-chrome
```

### 4. 初始化数据库

```bash
python -c "from models.database import init_db; from flask import Flask; from config import Config; app = Flask(__name__); app.config.from_object(Config); init_db(app)"
```

或者直接运行主程序（会自动初始化）：
```bash
python app.py
```

## 使用方法

### 启动应用

```bash
python app.py
```

应用将启动在 `http://127.0.0.1:5000`

### 首次使用

1. 启动应用后，访问 `http://127.0.0.1:5000`
2. 点击顶部导航栏的"立即爬取"按钮，执行首次爬取
3. 爬取完成后，职位列表会自动更新
4. Excel 文件会自动导出到 `data/exports/jobs_export.xlsx`

### Web 界面功能

#### 主页（职位列表）
- **筛选**：按公司、地点、时间范围、关键词筛选
- **查看**：点击职位标题查看详情
- **标记重点**：点击星标按钮标记重点职位
- **查看详情**：点击"查看"按钮在新标签页打开原始链接

#### 职位详情页
- 查看完整的职位信息
- 添加个人备注
- 标记/取消标记重点职位
- 在新标签页打开原始链接

#### 设置页面
- 查看系统配置
- 手动触发爬取
- 手动导出 Excel

### API 使用

#### 获取职位列表

```bash
GET /api/jobs?company=JPMorgan&time_range=this_week&page=1&per_page=20
```

#### 获取职位详情

```bash
GET /api/jobs/1
```

#### 标记重点职位

```bash
PUT /api/jobs/1/important
Content-Type: application/json

{
  "is_important": true
}
```

#### 添加备注

```bash
PUT /api/jobs/1/notes
Content-Type: application/json

{
  "note": "这是一个很好的职位机会"
}
```

#### 手动触发爬取

```bash
POST /api/scrape
Content-Type: application/json

{
  "company": "JPMorgan"  // 可选，不指定则爬取所有公司
}
```

#### 导出 Excel

```bash
GET /api/export
```

#### 获取统计信息

```bash
GET /api/stats
```

## 配置说明

配置文件位于 `config.py`，主要配置项：

```python
# 定时任务配置
SCHEDULE_HOUR = 9          # 每天执行的小时
SCHEDULE_MINUTE = 0        # 每天执行的分钟

# Excel 导出配置
EXCEL_EXPORT_PATH = 'data/exports/jobs_export.xlsx'

# 爬虫配置
SCRAPER_DELAY_MIN = 1      # 随机延迟最小值（秒）
SCRAPER_DELAY_MAX = 3      # 随机延迟最大值（秒）
HEADLESS_MODE = True       # 无头模式

# 新职位定义（天数）
NEW_JOB_DAYS = 7           # 7 天内的职位视为新职位
```

## 数据说明

### 数据库

数据存储在 SQLite 数据库中：`data/jobs.db`

主要字段：
- `job_hash`：唯一标识（MD5 哈希）
- `company`：公司名称
- `title`：职位名称
- `location`：工作地点
- `description`：职位描述
- `status`：状态（active/inactive）
- `first_seen`：首次发现时间
- `last_seen`：最后看到时间
- `last_updated`：最后更新时间
- `is_important`：是否重点
- `user_notes`：用户备注

### Excel 文件

导出的 Excel 文件包含：
- 自动筛选器
- 冻结首行
- 新职位高亮（浅绿色）
- 更新职位高亮（浅橙色）
- 重点职位标注（星号）
- 超链接可点击

## 爬虫说明

### 爬虫结构

每个公司都有独立的爬虫类，继承自 `BaseScraper` 基类。

### 自定义爬虫

如果需要调整某个公司的爬虫，请编辑对应的文件：

```
scrapers/
├── jpmorgan_scraper.py
├── goldman_scraper.py
├── morgan_stanley_scraper.py
└── ...
```

**注意**：由于目标网站可能使用动态加载，爬虫中使用了通用的选择器模板。首次运行时，可能需要根据实际网站结构调整 CSS 选择器。

### 调整选择器

在每个爬虫文件中，找到以下位置并根据实际页面结构调整：

```python
# 职位标题
title_element = job_element.find_element(By.CSS_SELECTOR, 'h3, .job-title, a.title')

# 职位链接
link_element = job_element.find_element(By.CSS_SELECTOR, 'a[href*="job"]')

# 地点
location_element = job_element.find_element(By.CSS_SELECTOR, '.location, .job-location')
```

### 测试爬虫

可以单独测试某个公司的爬虫：

```python
from scrapers.jpmorgan_scraper import JPMorganScraper

scraper = JPMorganScraper()
jobs = scraper.scrape_with_retry()
print(f"Scraped {len(jobs)} jobs")
```

## 常见问题

### 1. ChromeDriver 错误

**问题**：启动时提示 ChromeDriver 错误

**解决**：确保已安装 Chrome 浏览器，`webdriver-manager` 会自动下载匹配的 ChromeDriver

### 2. 爬取失败

**问题**：某些网站爬取失败

**解决**：
- 检查网络连接
- 查看日志文件 `data/logs/scraper.log`
- 根据实际网站结构调整爬虫选择器
- 某些网站可能有反爬虫机制，需要调整延迟时间

### 3. 数据库锁定

**问题**：SQLite database is locked

**解决**：确保只有一个应用实例在运行

### 4. Excel 导出失败

**问题**：Excel 文件导出失败

**解决**：
- 确保 `data/exports` 目录存在并有写入权限
- 关闭已打开的 Excel 文件

## 目录结构

```
job-tracker/
├── app.py                    # Flask 主应用
├── config.py                 # 配置文件
├── requirements.txt          # Python 依赖
├── README.md                 # 项目文档
├── scrapers/                 # 爬虫模块
│   ├── base_scraper.py
│   └── *_scraper.py
├── models/                   # 数据模型
│   ├── database.py
│   └── job.py
├── services/                 # 业务逻辑
│   ├── scraper_service.py
│   ├── job_service.py
│   └── excel_service.py
├── scheduler/                # 定时任务
│   └── job_scheduler.py
├── routes/                   # 路由
│   ├── api.py
│   └── web.py
├── templates/                # HTML 模板
│   ├── layout.html
│   ├── index.html
│   ├── job_detail.html
│   └── settings.html
├── static/                   # 静态文件
│   ├── css/style.css
│   └── js/main.js
└── data/                     # 数据存储
    ├── jobs.db
    ├── exports/
    └── logs/
```

## 维护建议

1. **定期备份数据库**：`data/jobs.db`
2. **查看日志**：定期检查 `data/logs/scraper.log`
3. **更新爬虫**：目标网站结构变化时，及时更新对应的爬虫
4. **清理旧数据**：定期清理 inactive 状态的职位

## 后续扩展

可以考虑的扩展方向：

1. ✨ 邮件通知：每次爬取完成后发送邮件摘要
2. ✨ 职位推荐：基于关键词匹配推荐符合条件的职位
3. ✨ 申请追踪：添加"已申请"状态，记录申请进度
4. ✨ 数据分析：统计职位数量趋势、热门地点等
5. ✨ 云部署：部署到云服务器，支持远程访问

## 许可证

本项目仅供个人学习和求职使用，请勿用于商业用途。

## 作者

自动化职位追踪系统 - 2026

---

如有问题，请查看日志文件或修改配置文件。
