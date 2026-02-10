"""
测试 Blackstone 爬虫
探索 Blackstone 招聘网站的结构（Workday 平台）
"""

from scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
import time
import os


def test_blackstone():
    print("="*70)
    print("Blackstone 网站探索 (Workday 平台)")
    print("="*70)

    url = 'https://blackstone.wd1.myworkdayjobs.com/en-US/Blackstone_Campus_Careers?locations=ef375a2335bb0101284ca9065e1f6f2b&locations=9d4c631a9cd501ef51ff910af90138e3&locations=ef375a2335bb019369c586065e1f3d2b&locations=ef375a2335bb01d8c87897065e1f562b&locations=1bf5259d5ff60172b4ac9e926bdb60af&locations=ef375a2335bb01f2aacb0a075e1ff62b&locations=ef375a2335bb01d5993383065e1f382b'

    # 创建临时scraper
    class TempScraper(BaseScraper):
        def __init__(self):
            super().__init__(company_name='Blackstone', source_url=url)
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
        print(f"   URL: {url[:100]}...")
        scraper.driver.get(url)

        # 等待页面加载
        print("\n3. 等待页面动态内容加载...")
        print("   (等待20秒让 Workday 页面加载)")
        time.sleep(20)

        print(f"   页面标题: {scraper.driver.title}")
        print(f"   当前URL: {scraper.driver.current_url[:100]}...")

        # 保存初始HTML
        os.makedirs('data/debug', exist_ok=True)
        html_file = 'data/debug/blackstone_initial.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(scraper.driver.page_source)
        print(f"   ✓ 初始HTML已保存: {html_file}")

        # Workday 常见选择器
        print("\n4. 搜索职位元素...")

        selectors_to_try = [
            # Workday 特定选择器
            'li[data-automation-id="compositeContainer"]',
            'div[data-automation-id="jobPostingItem"]',
            'div[data-automation-id="compositeContainer"]',
            'ul[aria-label*="Search Results"] li',
            '[data-automation-id="jobTitle"]',
            'a[data-automation-id="jobTitle"]',
            '.css-19uc56f',  # Workday 常见类名
            '[role="listitem"]',
        ]

        found_containers = []
        for selector in selectors_to_try:
            try:
                elements = scraper.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(elements) > 0:
                    # 检查是否有实际内容
                    has_content = False
                    for elem in elements[:3]:
                        if len(elem.text.strip()) > 20:
                            has_content = True
                            break
                    if has_content:
                        found_containers.append((selector, len(elements)))
                        print(f"   ✓ '{selector}' 找到 {len(elements)} 个元素")
            except Exception as e:
                pass

        if found_containers:
            found_containers.sort(key=lambda x: x[1], reverse=True)
            best_selector = found_containers[0][0]
            print(f"\n   推荐选择器: '{best_selector}'")

            # 分析前3个元素
            elements = scraper.driver.find_elements(By.CSS_SELECTOR, best_selector)
            print(f"\n5. 分析前3个职位元素...")

            for i in range(min(3, len(elements))):
                elem = elements[i]
                print(f"\n   --- 元素 {i+1} ---")
                text = elem.text.strip()
                if text:
                    print(f"   文本: {text[:300]}...")

                # 尝试找标题
                title_selectors = [
                    'a[data-automation-id="jobTitle"]',
                    '[data-automation-id="jobTitle"]',
                    'h3',
                    'h4',
                    'a',
                    '[class*="title"]',
                ]
                for ts in title_selectors:
                    try:
                        title_elem = elem.find_element(By.CSS_SELECTOR, ts)
                        if title_elem.text.strip():
                            print(f"   标题 ({ts}): {title_elem.text.strip()}")
                            # 尝试获取链接
                            if title_elem.tag_name == 'a':
                                href = title_elem.get_attribute('href')
                                print(f"   链接: {href}")
                            break
                    except:
                        pass

                # 尝试找地点
                location_selectors = [
                    '[data-automation-id="location"]',
                    'dd[data-automation-id="location"]',
                    '.css-1dimb5e',
                    'span[class*="location"]',
                ]
                for ls in location_selectors:
                    try:
                        loc_elem = elem.find_element(By.CSS_SELECTOR, ls)
                        loc_text = loc_elem.text.strip()
                        if loc_text:
                            print(f"   地点 ({ls}): {loc_text}")
                            break
                    except:
                        pass

                # 尝试找发布日期
                date_selectors = [
                    '[data-automation-id="postedOn"]',
                    'dd[data-automation-id="postedOn"]',
                    'time',
                ]
                for ds in date_selectors:
                    try:
                        date_elem = elem.find_element(By.CSS_SELECTOR, ds)
                        date_text = date_elem.text.strip()
                        if date_text:
                            print(f"   发布日期 ({ds}): {date_text}")
                            break
                    except:
                        pass

        # 查找结果数量
        print(f"\n6. 查找结果数量...")
        count_selectors = [
            'h2[data-automation-id="searchResultsHeading"]',
            '[class*="result"][class*="count"]',
            'span[data-automation-id="searchResultsCount"]',
        ]
        for cs in count_selectors:
            try:
                count_elem = scraper.driver.find_element(By.CSS_SELECTOR, cs)
                print(f"   结果数: {count_elem.text.strip()}")
                break
            except:
                pass

        # 查找分页
        print(f"\n7. 搜索分页元素...")
        pagination_selectors = [
            'button[data-uxi-widget-type="nextButton"]',
            'button[aria-label*="next"]',
            'button[aria-label*="Next"]',
            '[data-automation-id="pageNavigation"]',
            'nav[aria-label*="pagination"]',
        ]

        for selector in pagination_selectors:
            try:
                elems = scraper.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(elems) > 0:
                    print(f"   ✓ 找到分页元素: '{selector}' ({len(elems)} 个)")
                    for elem in elems[:2]:
                        print(f"      文本: {elem.text.strip() if elem.text else '(无文本)'}")
                        print(f"      aria-label: {elem.get_attribute('aria-label')}")
                        print(f"      enabled: {elem.is_enabled()}")
            except Exception as e:
                pass

        # 滚动测试
        print(f"\n8. 测试滚动加载...")
        initial_count = len(scraper.driver.find_elements(By.CSS_SELECTOR, best_selector)) if found_containers else 0
        print(f"   滚动前: {initial_count} 个职位")

        scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)

        after_scroll_count = len(scraper.driver.find_elements(By.CSS_SELECTOR, best_selector)) if found_containers else 0
        print(f"   滚动后: {after_scroll_count} 个职位")

        if after_scroll_count > initial_count:
            print(f"   ✓ 检测到懒加载：增加了 {after_scroll_count - initial_count} 个职位")
        else:
            print(f"   未检测到懒加载")

        # 保存滚动后的HTML
        html_file2 = 'data/debug/blackstone_after_scroll.html'
        with open(html_file2, 'w', encoding='utf-8') as f:
            f.write(scraper.driver.page_source)
        print(f"   ✓ 滚动后HTML已保存: {html_file2}")

        print("\n" + "="*70)
        print("探索完成！")
        print("="*70)

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n9. 关闭浏览器...")
        try:
            scraper.close_driver()
            print("   ✓ 浏览器已关闭")
        except:
            pass


if __name__ == '__main__':
    test_blackstone()
