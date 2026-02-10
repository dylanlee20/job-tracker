# 下一步操作指南

## 当前状态

✅ **已完成:**
- 系统架构搭建完成
- ChromeDriver 正常工作
- 数据库已初始化
- Web界面可以正常访问
- 定时任务已配置

⚠️ **需要调整:**
- CSS选择器不匹配实际网站结构
- 所有9个公司的爬虫都需要调整选择器

## 问题说明

金融公司的招聘网站都有独特的HTML结构，我使用的是通用模板选择器，所以无法提取到实际数据。每个网站都需要**根据其实际HTML结构定制选择器**。

## 如何修复

### 方法一：使用诊断工具（推荐）

我已经创建了一个诊断工具 `debug_selectors.py`，可以帮你找到正确的选择器。

**操作步骤：**

1. 运行诊断工具：
   ```bash
   cd ~/Desktop/job-tracker
   python3 debug_selectors.py
   ```

2. 选择模式：
   - 输入 `1` - 调试所有公司（耗时较长，约15-20分钟）
   - 输入 `2` - 调试单个公司（推荐先测试单个）

3. 查看输出：
   - 工具会自动尝试多种常见选择器
   - 保存HTML文件到 `data/debug/` 目录
   - 显示找到的选择器和元素数量
   - 显示第一个元素的内容示例

4. 根据输出结果修改爬虫：
   - 打开对应的爬虫文件（在 `scrapers/` 目录下）
   - 找到 `scrape_jobs()` 方法中的选择器
   - 替换为诊断工具推荐的选择器

### 方法二：手动检查（适合有HTML经验的用户）

1. 手动访问公司招聘网站
2. 在浏览器中按 F12 打开开发者工具
3. 使用"检查元素"功能查看HTML结构
4. 找到职位列表容器的CSS类名
5. 修改对应的爬虫文件

### 示例：修改 Citi 爬虫

假设诊断工具告诉你 Citi 网站使用的选择器是：
- 职位容器: `.jobs-list-item`
- 标题: `h3.job-title`
- 地点: `span.location`

那么你需要编辑 `scrapers/citi_scraper.py`:

```python
# 找到这一行
job_elements = self.driver.find_elements(By.CSS_SELECTOR, '.job, .vacancy, .posting')

# 改为
job_elements = self.driver.find_elements(By.CSS_SELECTOR, '.jobs-list-item')

# 然后修改提取逻辑
for job_element in job_elements:
    title = job_element.find_element(By.CSS_SELECTOR, 'h3.job-title').text.strip()
    location = job_element.find_element(By.CSS_SELECTOR, 'span.location').text.strip()
    # ... 其他字段
```

## 简化建议

如果你觉得调试9个网站太复杂，可以：

1. **先只调试1-2个最重要的公司**
   - 比如只修复 JPMorgan 和 Goldman Sachs
   - 其他暂时关闭

2. **使用简单网站替代**
   - 有些公司使用通用招聘平台（如 Workday, Greenhouse）
   - 这些平台的选择器通常比较标准

3. **暂时手动录入**
   - 先把系统的其他功能用起来（Excel导出、标记重点、备注等）
   - 手动添加职位到数据库
   - 后续再完善自动爬取

## 测试单个爬虫

修改完某个爬虫后，可以单独测试：

```bash
cd ~/Desktop/job-tracker
python3 -c "
from scrapers.citi_scraper import CitiScraper
scraper = CitiScraper()
jobs = scraper.scrape_with_retry()
print(f'爬取到 {len(jobs)} 个职位')
if jobs:
    print('第一个职位:')
    print(jobs[0])
"
```

## 需要帮助？

如果在调试过程中遇到问题：

1. 运行 `python3 debug_selectors.py` 选择单个公司
2. 查看保存的HTML文件（在 `data/debug/` 目录）
3. 把诊断输出和HTML文件发给我，我可以帮你找到正确的选择器

## 其他注意事项

1. **反爬虫限制**: 有些网站有严格的反爬虫机制，可能需要：
   - 增加延迟时间（在 `config.py` 中调整）
   - 使用代理IP
   - 添加更多的浏览器请求头

2. **动态加载**: 有些网站使用无限滚动或按钮加载更多，需要：
   - 添加滚动逻辑
   - 模拟点击"加载更多"按钮
   - 增加等待时间

3. **登录墙**: 部分公司网站需要登录才能查看职位，这种情况比较复杂，需要：
   - 添加自动登录逻辑
   - 或者使用API（如果有的话）
   - 或者手动维护该公司的职位

---

**总结**: 系统的基础框架已经完全搭建好了，只是需要为每个公司网站定制CSS选择器。你可以先从最重要的1-2个公司开始调试，不用一次性完成所有9个。
