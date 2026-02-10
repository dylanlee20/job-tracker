"""
测试 JPMorgan 分页/加载更多机制
"""

from scrapers.jpmorgan_scraper import JPMorganScraper
from selenium.webdriver.common.by import By
import time


def test_jpmorgan_load_all():
    print("="*70)
    print("JPMorgan 加载测试")
    print("="*70)

    url = 'https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs?keyword=summer+analyst&lastSelectedFacet=CATEGORIES&location=United+States&locationId=300000000289738&locationLevel=country&mode=location&selectedCategoriesFacet=300000086153065'

    scraper = JPMorganScraper()
    scraper.source_url = url

    try:
        scraper.init_driver()
        print("\n1. 加载页面...")
        scraper.driver.get(url)
        time.sleep(15)

        print(f"\n2. 初始职位数量...")
        job_tiles = scraper.driver.find_elements(By.CSS_SELECTOR, 'div.job-tile')
        print(f"   找到 {len(job_tiles)} 个职位卡片")

        # 查找"Load More"或"Show More"按钮
        print(f"\n3. 搜索加载更多按钮...")
        load_more_selectors = [
            'button[aria-label*="more"]',
            'button[aria-label*="More"]',
            'button[class*="load"]',
            'button[class*="show-more"]',
            'button:has-text("Load More")',
            'button:has-text("Show More")',
        ]

        found_button = False
        for selector in load_more_selectors:
            try:
                buttons = scraper.driver.find_elements(By.CSS_SELECTOR, selector)
                if buttons:
                    print(f"   找到按钮: {selector} ({len(buttons)} 个)")
                    for btn in buttons[:3]:
                        print(f"      文本: '{btn.text}'")
                        print(f"      aria-label: '{btn.get_attribute('aria-label')}'")
                    found_button = True
            except:
                pass

        # 尝试滚动加载多次
        print(f"\n4. 尝试多次滚动加载...")
        previous_count = len(job_tiles)

        for i in range(5):
            # 滚动到底部
            scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            # 检查是否有新职位加载
            job_tiles = scraper.driver.find_elements(By.CSS_SELECTOR, 'div.job-tile')
            current_count = len(job_tiles)

            print(f"   第 {i+1} 次滚动: {current_count} 个职位")

            if current_count > previous_count:
                print(f"      ✓ 新增 {current_count - previous_count} 个职位")
                previous_count = current_count
            else:
                print(f"      未增加新职位")
                break

        # 最终统计
        print(f"\n5. 最终结果:")
        job_tiles = scraper.driver.find_elements(By.CSS_SELECTOR, 'div.job-tile')
        print(f"   总共加载了 {len(job_tiles)} 个职位")

        # 显示前5个职位
        print(f"\n6. 前5个职位:")
        for i, tile in enumerate(job_tiles[:5]):
            try:
                title_elem = tile.find_element(By.CSS_SELECTOR, 'span.job-tile__title')
                link_elem = tile.find_element(By.CSS_SELECTOR, 'a.job-grid-item__link')

                print(f"\n   {i+1}. {title_elem.text}")
                print(f"      URL: {link_elem.get_attribute('href')}")
            except:
                pass

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        scraper.close_driver()


if __name__ == '__main__':
    test_jpmorgan_load_all()
