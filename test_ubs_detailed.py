"""
UBS 详细测试 - 等待更长时间并尝试多种方法
"""

from scrapers.ubs_scraper import UBSScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def test_ubs_detailed():
    print("="*70)
    print("UBS 详细测试")
    print("="*70)

    url = 'https://jobs.ubs.com/TGnewUI/Search/home/HomeWithPreLoad?partnerid=25008&siteid=5131&PageType=searchResults&SearchType=linkquery&LinkID=15700#keyWordSearch=&locationSearch=&City=Chicago_or_Hong%20Kong%20SAR_or_New%20York_or_San%20Francisco'

    scraper = UBSScraper()
    scraper.source_url = url

    try:
        scraper.init_driver()
        print("\n1. 加载页面...")
        scraper.driver.get(url)

        # 等待更长时间
        print("\n2. 等待30秒让页面完全加载...")
        time.sleep(30)

        print(f"   页面标题: {scraper.driver.title}")
        print(f"   当前URL: {scraper.driver.current_url}")

        # 尝试查找 searchResultsShell (Taleo 常见元素)
        print("\n3. 查找 searchResultsShell...")
        try:
            shell = scraper.driver.find_element(By.CLASS_NAME, 'searchResultsShell')
            print(f"   ✓ 找到 searchResultsShell")
            print(f"   内容长度: {len(shell.text)} 字符")
            if shell.text:
                print(f"   前200字符: {shell.text[:200]}")
        except Exception as e:
            print(f"   ✗ 未找到: {e}")

        # 查找所有 table
        print("\n4. 查找所有 table 元素...")
        tables = scraper.driver.find_elements(By.TAG_NAME, 'table')
        print(f"   找到 {len(tables)} 个 table")
        for i, table in enumerate(tables[:3]):
            print(f"   Table {i+1}: {table.get_attribute('class')} / {table.get_attribute('id')}")

        # 查找 data-row 类
        print("\n5. 查找 data-row 元素...")
        data_rows = scraper.driver.find_elements(By.CLASS_NAME, 'data-row')
        print(f"   找到 {len(data_rows)} 个 data-row")

        # 查找所有 tr 元素
        print("\n6. 查找所有 tr 元素...")
        all_trs = scraper.driver.find_elements(By.TAG_NAME, 'tr')
        print(f"   总共 {len(all_trs)} 个 tr 元素")

        # 筛选出可能是职位的 tr（包含链接）
        job_trs = []
        for tr in all_trs:
            try:
                links = tr.find_elements(By.TAG_NAME, 'a')
                if links and len(tr.text.strip()) > 30:
                    job_trs.append(tr)
            except:
                pass

        print(f"   其中可能是职位的: {len(job_trs)} 个")

        # 显示前3个可能的职位
        if len(job_trs) > 0:
            print("\n7. 前3个可能的职位:")
            for i, tr in enumerate(job_trs[:3]):
                print(f"\n   职位 {i+1}:")
                print(f"   ID: {tr.get_attribute('id')}")
                print(f"   Class: {tr.get_attribute('class')}")
                print(f"   文本: {tr.text[:200]}...")

                # 尝试找链接
                try:
                    link = tr.find_element(By.TAG_NAME, 'a')
                    print(f"   链接: {link.get_attribute('href')}")
                    print(f"   链接文本: {link.text}")
                except:
                    pass

        # 查找 span 中包含 "jobs found" 或 "results" 的文本
        print("\n8. 查找结果数量信息...")
        try:
            all_text = scraper.driver.find_element(By.TAG_NAME, 'body').text
            if 'jobs found' in all_text.lower() or 'results' in all_text.lower():
                # 找包含这些关键词的行
                lines = all_text.split('\n')
                for line in lines:
                    if 'jobs found' in line.lower() or 'results' in line.lower():
                        print(f"   {line.strip()}")
        except:
            pass

        # 尝试点击"显示所有"按钮（如果有的话）
        print("\n9. 查找'Show All'或分页按钮...")
        button_texts = ['Show All', 'Show all', 'View All', 'Load More']
        for btn_text in button_texts:
            try:
                buttons = scraper.driver.find_elements(By.XPATH, f"//button[contains(text(), '{btn_text}')] | //a[contains(text(), '{btn_text}')]")
                if buttons:
                    print(f"   找到按钮: '{btn_text}' ({len(buttons)} 个)")
            except:
                pass

        # 检查 Angular 是否加载完成
        print("\n10. 检查页面加载状态...")
        try:
            ng_binding = scraper.driver.find_elements(By.CSS_SELECTOR, '[ng-binding]')
            print(f"   Angular绑定元素: {len(ng_binding)} 个")
        except:
            pass

        # 保存调试信息
        print("\n11. 保存完整HTML...")
        with open('data/debug/ubs_detailed.html', 'w', encoding='utf-8') as f:
            f.write(scraper.driver.page_source)
        print("   ✓ 已保存到 data/debug/ubs_detailed.html")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        scraper.close_driver()


if __name__ == '__main__':
    test_ubs_detailed()
