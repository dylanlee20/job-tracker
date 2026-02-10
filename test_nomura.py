"""
测试 Nomura 爬虫
探索 Nomura 招聘网站的结构
"""

from scrapers.nomura_scraper import NomuraScraper
from selenium.webdriver.common.by import By
import time
import os


def test_nomura():
    print("="*70)
    print("Nomura 网站探索")
    print("="*70)

    # 使用用户提供的筛选URL
    url = 'https://nomuracampus.tal.net/vx/lang-en-GB/mobile-0/appcentre-ext/brand-4/xf-3348347fc789/candidate/jobboard/vacancy/1/adv/?f_Item_Opportunity_84825_lk=749&f_Item_Opportunity_408_lk=522954&f_Item_Opportunity_408_lk=522951&f_Item_Opportunity_408_lk=522952&f_Item_Opportunity_408_lk=522953'

    scraper = NomuraScraper()
    scraper.source_url = url  # 临时覆盖URL

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
        html_file = 'data/debug/nomura_initial.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(scraper.driver.page_source)
        print(f"   ✓ 初始HTML已保存: {html_file}")

        # 尝试找职位容器
        print("\n4. 搜索职位元素...")

        # Taleo 常见选择器
        selectors_to_try = [
            # Taleo 特定
            '[data-job-id]',
            '[id^="job"]',
            'tr[id^="job"]',
            'div[id^="job"]',
            'li[id^="job"]',
            '.job',
            '.job-item',
            '.job-result',
            'article',
            'li[role="listitem"]',
            'a[href*="/job/"]',
            'a[href*="vacancy"]',
        ]

        found_containers = []
        for selector in selectors_to_try:
            try:
                elements = scraper.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(elements) > 0:
                    # 检查是否有实际内容
                    has_content = False
                    for elem in elements[:3]:
                        if len(elem.text.strip()) > 30:
                            has_content = True
                            break
                    if has_content:
                        found_containers.append((selector, len(elements)))
                        print(f"   ✓ '{selector}' 找到 {len(elements)} 个元素")
            except:
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
                    print(f"   文本: {text[:200]}...")

                # 尝试找标题
                for ts in ['h3', 'h2', 'h4', 'a', '[class*="title"]', '[class*="Title"]', 'span']:
                    try:
                        title_elem = elem.find_element(By.CSS_SELECTOR, ts)
                        if title_elem.text.strip():
                            print(f"   标题 ({ts}): {title_elem.text.strip()}")
                            break
                    except:
                        pass

                # 尝试找链接
                try:
                    link = elem.find_element(By.TAG_NAME, 'a')
                    href = link.get_attribute('href')
                    if href:
                        print(f"   链接: {href}")
                except:
                    pass

                # 尝试找地点
                for ls in ['.location', '[class*="location"]', '[class*="Location"]', 'span', 'p']:
                    try:
                        loc_elem = elem.find_element(By.CSS_SELECTOR, ls)
                        loc_text = loc_elem.text.strip()
                        if loc_text and any(kw in loc_text for kw in ['United States', 'USA', 'New York', 'US']):
                            print(f"   地点 ({ls}): {loc_text}")
                            break
                    except:
                        pass

        # 查找分页
        print(f"\n6. 搜索分页元素...")
        pagination_selectors = [
            '[aria-label*="next"]',
            '[aria-label*="Next"]',
            'button[class*="next"]',
            'a[class*="next"]',
            '[class*="pagination"]',
            'button[aria-label*="page"]',
        ]

        for selector in pagination_selectors:
            try:
                elems = scraper.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(elems) > 0:
                    print(f"   ✓ 找到分页元素: '{selector}' ({len(elems)} 个)")
                    for elem in elems[:2]:
                        print(f"      文本: {elem.text.strip() if elem.text else '(无文本)'}")
                        print(f"      aria-label: {elem.get_attribute('aria-label')}")
            except:
                pass

        # 滚动查看是否有懒加载
        print(f"\n7. 测试滚动加载...")
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
        html_file2 = 'data/debug/nomura_after_scroll.html'
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
        print("\n8. 关闭浏览器...")
        try:
            scraper.close_driver()
            print("   ✓ 浏览器已关闭")
        except:
            pass


if __name__ == '__main__':
    test_nomura()
