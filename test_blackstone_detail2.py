"""
详细测试 Blackstone 职位提取 - 第2版
"""

from scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
import time


def test_blackstone_detail2():
    print("="*70)
    print("Blackstone 职位详细提取测试 v2")
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

        # 直接查找所有职位标题链接
        print("\n查找所有职位标题链接...")
        title_links = scraper.driver.find_elements(By.CSS_SELECTOR, 'a[data-automation-id="jobTitle"]')
        print(f"找到 {len(title_links)} 个职位标题")

        print("\n分析前 3 个职位:")
        for i in range(min(3, len(title_links))):
            title_link = title_links[i]
            print(f"\n=== 职位 {i+1} ===")

            # 标题和链接
            title = title_link.text.strip()
            href = title_link.get_attribute('href')
            print(f"标题: {title}")
            print(f"链接: {href}")

            # 查找父级容器
            try:
                # 从标题向上查找包含完整职位信息的容器
                # 通常是 li 元素
                parent_li = title_link.find_element(By.XPATH, './ancestor::li')
                print(f"父容器标签: {parent_li.tag_name}")

                # 查找该容器内的所有 dd 元素（Workday 通常用 dt/dd 结构）
                dds = parent_li.find_elements(By.TAG_NAME, 'dd')
                print(f"找到 {len(dds)} 个 dd 元素:")
                for j, dd in enumerate(dds):
                    text = dd.text.strip()
                    if text:
                        print(f"  dd[{j}]: {text}")
                        # 尝试判断是否是地点
                        if any(keyword in text for keyword in ['United States', 'USA', 'New York', 'San Francisco', 'Chicago', 'Hong Kong']):
                            print(f"    ^ 可能是地点")

                # 查找 subtitles（Workday 常见结构）
                try:
                    subtitles = parent_li.find_elements(By.CSS_SELECTOR, '[data-automation-id*="subtitle"]')
                    if subtitles:
                        print(f"副标题元素: {len(subtitles)} 个")
                        for j, sub in enumerate(subtitles):
                            if sub.text.strip():
                                print(f"  subtitle[{j}]: {sub.text.strip()}")
                except:
                    pass

                # 查找所有 span 元素
                spans = parent_li.find_elements(By.TAG_NAME, 'span')
                print(f"找到 {len(spans)} 个 span 元素 (显示前5个有内容的):")
                span_count = 0
                for span in spans:
                    text = span.text.strip()
                    if text and span_count < 5:
                        print(f"  span: {text[:100]}")
                        span_count += 1

            except Exception as e:
                print(f"无法找到父容器: {e}")

        # 测试点击第一个职位看详情页结构
        print("\n\n测试打开第一个职位详情页...")
        if len(title_links) > 0:
            first_job_url = title_links[0].get_attribute('href')
            print(f"打开: {first_job_url}")

            scraper.driver.get(first_job_url)
            time.sleep(10)

            print(f"详情页标题: {scraper.driver.title}")

            # 查找职位描述
            desc_selectors = [
                '[data-automation-id="jobPostingDescription"]',
                '[class*="description"]',
                'div[role="main"]',
            ]

            for sel in desc_selectors:
                try:
                    desc_elem = scraper.driver.find_element(By.CSS_SELECTOR, sel)
                    desc_text = desc_elem.text.strip()
                    if desc_text:
                        print(f"\n描述 ({sel}): {desc_text[:200]}...")
                        break
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
    test_blackstone_detail2()
