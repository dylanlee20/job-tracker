"""
测试 Goldman Sachs 爬虫
帮助找到正确的CSS选择器
"""

from scrapers.goldman_scraper import GoldmanSachsScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os


def test_goldman():
    print("="*70)
    print("Goldman Sachs 爬虫测试")
    print("="*70)

    scraper = GoldmanSachsScraper()

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
        print("   (等待20秒让JavaScript加载职位列表)")
        time.sleep(20)

        print(f"\n   页面标题: {scraper.driver.title}")
        print(f"   当前URL: {scraper.driver.current_url}")

        # 滚动页面以触发懒加载
        print("\n4. 滚动页面以触发内容加载...")
        scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        scraper.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        # 保存HTML
        os.makedirs('data/debug', exist_ok=True)
        html_file = 'data/debug/goldman_sachs.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(scraper.driver.page_source)
        print(f"   ✓ HTML已保存到: {html_file}")

        # 尝试找职位容器
        print("\n5. 正在搜索职位元素...")

        selectors_to_try = [
            # 通用卡片/列表
            '[role="listitem"]',
            'li[role="listitem"]',
            '[data-testid*="job"]',
            '[data-testid*="card"]',
            '[data-testid*="result"]',
            # 常见容器
            '.job-card',
            '.job-item',
            '.job-result',
            '.result-item',
            '.search-result',
            '[data-job-id]',
            '[data-job]',
            # higher.gs.com 特定
            '.job-listing',
            '.position',
            '.opportunity',
            '[class*="OpportunityCard"]',
            '[class*="SearchResultCard"]',
            # 通用
            'article',
            'li',
            'div[class*="card"]',
            'a[href*="/job/"]',
            'a[href*="/opportunity/"]',
        ]

        found = []
        for selector in selectors_to_try:
            try:
                elements = scraper.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(elements) > 0:
                    # 检查元素是否包含实际内容
                    has_content = False
                    for elem in elements[:3]:  # 检查前3个
                        if len(elem.text.strip()) > 20:  # 至少20个字符
                            has_content = True
                            break
                    if has_content:
                        found.append((selector, len(elements)))
                        print(f"   ✓ '{selector}' 找到 {len(elements)} 个元素（有内容）")
            except:
                pass

        if not found:
            print("   ✗ 未找到职位容器元素")
            print("\n   可能的原因：")
            print("   1. 页面还在加载中")
            print("   2. 筛选条件导致没有匹配的职位")
            print("   3. 网站需要登录或有其他访问限制")
            print(f"\n   请手动访问查看: {scraper.source_url}")
        else:
            # 使用找到最多元素的选择器
            found.sort(key=lambda x: x[1], reverse=True)
            best_selector = found[0][0]
            best_count = found[0][1]

            print(f"\n6. 使用最佳选择器提取数据: '{best_selector}' ({best_count} 个)")

            elements = scraper.driver.find_elements(By.CSS_SELECTOR, best_selector)

            # 分析前3个元素
            for i in range(min(3, len(elements))):
                print(f"\n   --- 元素 {i+1} ---")
                elem = elements[i]

                # 显示文本内容
                text = elem.text.strip()
                if text:
                    # 只显示前300个字符
                    preview = text[:300] + ("..." if len(text) > 300 else "")
                    print(f"   文本内容:\n   {preview}")
                else:
                    print(f"   (无文本内容)")

                # 尝试找标题
                title_selectors = ['h1', 'h2', 'h3', 'h4', 'h5', 'a', '.title', '[class*="title"]', '[class*="Title"]', '[data-testid*="title"]']
                for ts in title_selectors:
                    try:
                        title_elem = elem.find_element(By.CSS_SELECTOR, ts)
                        if title_elem.text.strip():
                            print(f"   ✓ 标题 ('{ts}'): {title_elem.text.strip()}")
                            break
                    except:
                        pass

                # 尝试找地点
                location_selectors = ['.location', '[class*="location"]', '[class*="Location"]', '[class*="city"]', '[data-testid*="location"]', 'span', 'p']
                for ls in location_selectors:
                    try:
                        loc_elems = elem.find_elements(By.CSS_SELECTOR, ls)
                        for loc_elem in loc_elems:
                            loc_text = loc_elem.text.strip()
                            # 检查是否像地点（包含常见地点关键词）
                            if loc_text and any(keyword in loc_text for keyword in ['New York', 'San Francisco', 'Chicago', 'Boston', 'Los Angeles', 'USA', 'United States']):
                                print(f"   ✓ 地点 ('{ls}'): {loc_text}")
                                break
                    except:
                        pass

                # 尝试找链接
                try:
                    links = elem.find_elements(By.TAG_NAME, 'a')
                    for link in links:
                        href = link.get_attribute('href')
                        if href and ('/job/' in href or '/opportunity/' in href):
                            print(f"   ✓ 链接: {href}")
                            break
                except:
                    pass

            print("\n" + "="*70)
            print("推荐配置:")
            print("="*70)
            print(f"职位容器选择器: '{best_selector}'")
            print("\n在 scrapers/goldman_scraper.py 中修改:")
            print(f"    job_elements = self.driver.find_elements(By.CSS_SELECTOR, '{best_selector}')")
            print("\n然后根据上面显示的标题、地点选择器，修改提取逻辑")

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

    print("\n完成！")


if __name__ == '__main__':
    test_goldman()
