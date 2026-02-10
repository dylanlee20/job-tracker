# Goldman Sachs爬虫已配置完成 ✅

## 配置摘要

你的Goldman Sachs职位追踪系统已经成功配置并运行！

### 筛选条件
- **部门**: Global Banking & Markets
- **职位类型**: Banker - Industry/Country Coverage
- **地点**: 美国所有主要城市（纽约、旧金山、芝加哥等）

### 当前数据
- **已爬取职位数**: 11个
- **数据库状态**: ✅ 已保存
- **Excel导出**: ✅ 已生成

## 如何使用系统

### 1. 启动Web界面

```bash
cd ~/Desktop/job-tracker
python3 app.py
```

然后在浏览器中访问: **http://127.0.0.1:5000**

### 2. Web界面功能

- 📋 **职位列表**: 查看所有爬取的职位
- 🔍 **搜索筛选**: 按公司、地点、关键词筛选
- ⭐ **标记重点**: 标记你感兴趣的职位
- 📝 **添加备注**: 为每个职位添加个人笔记
- 📊 **查看统计**: 本周新增、本月新增等

### 3. 查看Excel文件

Excel文件自动导出到:
```
~/Desktop/job-tracker/data/exports/jobs_export.xlsx
```

双击打开即可查看，包含:
- ✅ 自动筛选器
- ✅ 新职位高亮（绿色）
- ✅ 更新职位高亮（橙色）
- ✅ 可点击的职位链接

### 4. 手动触发爬取

如果想立即更新职位数据：

**方式1 - 通过Web界面:**
1. 访问 http://127.0.0.1:5000
2. 点击右上角"立即爬取"按钮

**方式2 - 通过命令行:**
```bash
python3 << 'EOF'
from services.scraper_service import ScraperService
from flask import Flask
from config import Config
from models.database import db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    scraper_service = ScraperService()
    result = scraper_service.run_single_scraper('Goldman Sachs')
    print(f"New jobs: {result.get('new_jobs', 0)}")
    print(f"Updated: {result.get('updated_jobs', 0)}")
EOF
```

### 5. 自动定时爬取

系统已配置为**每天早上9点**自动爬取。

如果想修改时间，编辑 `config.py`:
```python
SCHEDULE_HOUR = 9     # 修改为你想要的小时（0-23）
SCHEDULE_MINUTE = 0   # 修改为你想要的分钟（0-59）
```

## 当前爬取的职位示例

1. **GBM Private, Healthcare, Analyst, San Francisco**
   - 地点: San Francisco·United States
   - 链接: https://higher.gs.com/roles/154471

2. **GBM, Private, Banker - Industrials, Analyst - Chicago**
   - 地点: Chicago·United States
   - 链接: https://higher.gs.com/roles/157288

3. **GBM - Private Dept - Investment Banking, Classic, TMT Associate, New York**
   - 地点: New York·United States
   - 链接: https://higher.gs.com/roles/136400

... 共11个职位

## 如何修改筛选条件

如果想修改爬取条件（比如添加其他职位类型或地点），编辑文件:
```
~/Desktop/job-tracker/scrapers/goldman_scraper.py
```

修改第14行的URL参数。

## 添加其他公司

你的系统已经预配置了9个公司的爬虫框架：
- JPMorgan Chase
- Goldman Sachs ✅ (已配置)
- Morgan Stanley
- Citi
- Deutsche Bank
- UBS
- BNP Paribas
- Nomura
- Piper Sandler

如果需要配置其他公司，按照Goldman Sachs的方式：
1. 运行 `python3 test_goldman.py` 测试该公司网站
2. 根据输出的选择器修改对应的爬虫文件
3. 测试爬虫是否能提取数据

## 故障排除

### 爬取失败
- 检查网络连接
- 查看日志: `data/logs/scraper.log`
- Chrome浏览器可能需要更新

### 网站结构变化
如果Goldman Sachs网站更新了HTML结构，爬虫可能失效。此时:
1. 运行 `python3 test_goldman.py`
2. 查看新的HTML结构
3. 更新 `scrapers/goldman_scraper.py` 中的CSS选择器

## 数据文件位置

- **数据库**: `~/Desktop/job-tracker/data/jobs.db`
- **Excel**: `~/Desktop/job-tracker/data/exports/jobs_export.xlsx`
- **日志**: `~/Desktop/job-tracker/data/logs/scraper.log`
- **调试HTML**: `~/Desktop/job-tracker/data/debug/`

## 下一步建议

1. ✅ **Goldman Sachs爬虫已完成** - 正常运行中
2. 📅 **等待自动爬取** - 明天早上9点会自动更新
3. 🌐 **使用Web界面** - 启动app.py浏览职位
4. 📊 **查看Excel** - 用Excel分析和筛选职位
5. 🔧 **配置其他公司** - 如果需要其他公司，重复类似步骤

---

**系统状态**: ✅ 正常运行
**最后爬取**: 2026-01-26
**职位数量**: 11个Goldman Sachs职位
