"""
测试 Evercore 爬虫
探索 Evercore 招聘网站的结构
"""

from scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
import time
import os


def test_evercore():
    print("="*70)
    print("Evercore 网站探索")
    print("="*70)

    # 使用用户提供的筛选URL
    url = 'https://evercore.tal.net/vx/lang-en-GB/mobile-0/channel-1/appcentre-ext/brand-6/candidate/jobboard/vacancy/2/adv/?f_Item_Opportunity_84825_lk=749'

    # 创建临时scraper
    class TempScraper(BaseScraper):
        def __init__(self):
            super().__init__(company_name='Evercore', source_url=url)
        def scrape_jobs(self):
            return []

    scraper = TempScraper()

    try:
        # 初始化浏览器
        print("\n1. 正在初始化浏览器...")
        scraper.init_driver()
        print("   ✓ 浏览器初始化成功")

        # 加载页面
        print(f"\n2. 正在加载页面...")
        print(f"   URL: {url}")
        scraper.driver.get(url)

        # 等待页面加载
        print("\n3. 等待页面动态内容加载...")
        print("   (等待15秒让页面加载)")
        time.sleep(15)

        print(f"   页面标题: {scraper.driver.title}")
        print(f"   当前URL: {scraper.driver.current_url}")

        # 保存初始HTML
        os.makedirs('data/debug', exist_ok=True)
        html_file = 'data/debug/evercore_initial.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(scraper.driver.page_source)
        print(f"   ✓ 初始HTML已保存: {html_file}")

        # 检查是否有结果表格
        print("\n4. 搜索职位表格...")
        try:
            # Taleo 表格选择器
            job_rows = scraper.driver.find_elements(By.CSS_SELECTOR, 'tr.search_res.details_row')
            print(f"   ✓ 找到 {len(job_rows)} 个职位行")

            if len(job_rows) > 0:
                print(f"\n5. 分析前3个职位...")
                for i, row in enumerate(job_rows[:3]):
                    print(f"\n   --- 职位 {i+1} ---")

                    # 提取标题
                    try:
                        link = row.find_element(By.CSS_SELECTOR, 'a.subject')
                        print(f"   标题: {link.text.strip()}")
                        print(f"   链接: {link.get_attribute('href')}")
                    except Exception as e:
                        print(f"   无法提取标题: {e}")

                    # 提取表格单元格
                    tds = row.find_elements(By.TAG_NAME, 'td')
                    print(f"   共有 {len(tds)} 个单元格")
                    for j, td in enumerate(tds):
                        if td.text.strip():
                            print(f"   单元格 {j+1}: {td.text.strip()}")
        except Exception as e:
            print(f"   ✗ 未找到职位表格: {e}")

        # 查找结果数量信息
        print(f"\n6. 查找结果数量...")
        try:
            body_text = scraper.driver.find_element(By.TAG_NAME, 'body').text
            lines = body_text.split('\n')
            for line in lines:
                if 'result' in line.lower() and any(char.isdigit() for char in line):
                    print(f"   {line.strip()}")
                    break
        except:
            pass

        print("\n" + "="*70)
        print("探索完成！")
        print("="*70)

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n7. 关闭浏览器...")
        try:
            scraper.close_driver()
            print("   ✓ 浏览器已关闭")
        except:
            pass


if __name__ == '__main__':
    test_evercore()
