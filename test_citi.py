"""
测试 Citi 爬虫
探索 Citi 网站的动态加载和筛选机制
"""

from scrapers.citi_scraper import CitiScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os


def test_citi():
    print("="*70)
    print("Citi 网站探索")
    print("="*70)

    scraper = CitiScraper()

    try:
        # 初始化浏览器
        print("\n1. 正在初始化浏览器...")
        scraper.init_driver()
        print("   ✓ 浏览器初始化成功")

        # 加载页面
        print(f"\n2. 正在加载页面...")
        print(f"   URL: {scraper.source_url}")
        scraper.driver.get(scraper.source_url)

        # 等待页面加载
        print("\n3. 等待页面动态内容加载...")
        time.sleep(10)

        print(f"   页面标题: {scraper.driver.title}")
        print(f"   当前URL: {scraper.driver.current_url}")

        # 保存初始HTML
        os.makedirs('data/debug', exist_ok=True)
        html_file = 'data/debug/citi_initial.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(scraper.driver.page_source)
        print(f"   ✓ 初始HTML已保存: {html_file}")

        # 尝试找职位容器
        print("\n4. 搜索职位元素...")

        # 常见的职位容器选择器
        selectors_to_try = [
            'article',
            'li',
            '.job-card',
            '.job-item',
            '.job-result',
            '.search-result',
            '[data-job-id]',
            '[data-ph-id]',
            '[class*="job"]',
            '[class*="result"]',
            'div[class*="card"]',
            'a[href*="/job/"]',
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
                for ts in ['h1', 'h2', 'h3', 'a']:
                    try:
                        title_elem = elem.find_element(By.CSS_SELECTOR, ts)
                        if title_elem.text.strip():
                            print(f"   标题: {title_elem.text.strip()}")
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

        # 查找筛选器和分页按钮
        print(f"\n6. 搜索筛选器和分页元素...")

        # 查找可能的筛选按钮
        filter_elements = []
        for selector in ['button', '[role="button"]', 'select', 'input[type="checkbox"]']:
            try:
                elems = scraper.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(elems) > 0:
                    print(f"   找到 {len(elems)} 个 '{selector}' 元素")
                    filter_elements.extend(elems[:5])  # 只取前5个
            except:
                pass

        # 查找分页按钮
        pagination_selectors = [
            '[aria-label*="next"]',
            '[aria-label*="Next"]',
            'button[class*="next"]',
            'a[class*="next"]',
            '[class*="pagination"]',
            'button[aria-label*="page"]'
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
        time.sleep(3)

        after_scroll_count = len(scraper.driver.find_elements(By.CSS_SELECTOR, best_selector)) if found_containers else 0
        print(f"   滚动后: {after_scroll_count} 个职位")

        if after_scroll_count > initial_count:
            print(f"   ✓ 检测到懒加载：增加了 {after_scroll_count - initial_count} 个职位")

        # 保存滚动后的HTML
        html_file2 = 'data/debug/citi_after_scroll.html'
        with open(html_file2, 'w', encoding='utf-8') as f:
            f.write(scraper.driver.page_source)
        print(f"   ✓ 滚动后HTML已保存: {html_file2}")

        print("\n" + "="*70)
        print("探索完成！")
        print("="*70)
        if found_containers:
            print(f"\n建议：")
            print(f"1. 使用选择器: '{best_selector}'")
            print(f"2. 页面使用动态加载")
            print(f"3. 查看保存的HTML文件了解详细结构")

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
    test_citi()
