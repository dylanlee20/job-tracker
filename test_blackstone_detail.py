"""
详细测试 Blackstone 职位提取
"""

from scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
import time


def test_blackstone_detail():
    print("="*70)
    print("Blackstone 职位详细提取测试")
    print("="*70)

    url = 'https://blackstone.wd1.myworkdayjobs.com/en-US/Blackstone_Campus_Careers?locations=ef375a2335bb0101284ca9065e1f6f2b&locations=9d4c631a9cd501ef51ff910af90138e3&locations=ef375a2335bb019369c586065e1f3d2b&locations=ef375a2335bb01d8c87897065e1f562b&locations=1bf5259d5ff60172b4ac9e926bdb60af&locations=ef375a2335bb01f2aacb0a075e1ff62b&locations=ef375a2335bb01d5993383065e1f382b'

    class TempScraper(BaseScraper):
        def __init__(self):
            super().__init__(company_name='Blackstone', source_url=url)
        def scrape_jobs(self):
            return []

    scraper = TempScraper()

    try:
        scraper.init_driver()
        print("\n正在加载页面...")
        scraper.driver.get(url)
        time.sleep(20)

        # 查找职位列表容器
        print("\n提取职位列表...")
        job_list_container = scraper.driver.find_elements(By.CSS_SELECTOR, 'ul[data-automation-id]')
        print(f"找到 {len(job_list_container)} 个 ul 容器")

        # 查找所有 li 元素
        job_items = scraper.driver.find_elements(By.CSS_SELECTOR, 'li[data-automation-id]')
        print(f"找到 {len(job_items)} 个 li 元素")

        print("\n分析前 3 个职位:")
        for i in range(min(3, len(job_items))):
            item = job_items[i]
            print(f"\n=== 职位 {i+1} ===")

            # 提取标题和链接
            try:
                title_link = item.find_element(By.CSS_SELECTOR, 'a[data-automation-id="jobTitle"]')
                title = title_link.text.strip()
                href = title_link.get_attribute('href')
                print(f"标题: {title}")
                print(f"链接: {href}")
            except Exception as e:
                print(f"无法提取标题: {e}")

            # 尝试提取地点 - 多种可能的选择器
            location_found = False
            location_selectors = [
                'dd[data-automation-id="location"]',
                'div[data-automation-id="location"]',
                'span[data-automation-id="location"]',
                '[class*="location"]',
            ]

            for loc_sel in location_selectors:
                try:
                    location_elem = item.find_element(By.CSS_SELECTOR, loc_sel)
                    location = location_elem.text.strip()
                    if location:
                        print(f"地点 ({loc_sel}): {location}")
                        location_found = True
                        break
                except:
                    pass

            if not location_found:
                # 打印所有 dd 元素
                print("  查找所有 dd 元素:")
                dds = item.find_elements(By.TAG_NAME, 'dd')
                for j, dd in enumerate(dds):
                    if dd.text.strip():
                        print(f"    dd[{j}]: {dd.text.strip()}")

            # 尝试提取发布日期
            date_selectors = [
                'dd[data-automation-id="postedOn"]',
                'time',
                'dd:nth-of-type(2)',
            ]

            for date_sel in date_selectors:
                try:
                    date_elem = item.find_element(By.CSS_SELECTOR, date_sel)
                    date_text = date_elem.text.strip()
                    if date_text:
                        print(f"发布日期 ({date_sel}): {date_text}")
                        break
                except:
                    pass

        # 测试分页
        print("\n\n测试分页:")
        try:
            next_button = scraper.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="next"]')
            print(f"  下一页按钮存在: {next_button.is_enabled()}")
            print(f"  按钮类: {next_button.get_attribute('class')}")
        except Exception as e:
            print(f"  未找到下一页按钮: {e}")

        # 查看分页导航
        try:
            pagination = scraper.driver.find_element(By.CSS_SELECTOR, 'nav[aria-label*="pagination"]')
            print(f"  分页导航文本: {pagination.text}")
        except:
            pass

        print("\n" + "="*70)
        print("测试完成！")
        print("="*70)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        scraper.close_driver()


if __name__ == '__main__':
    test_blackstone_detail()
