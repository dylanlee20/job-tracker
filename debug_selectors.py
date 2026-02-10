"""
CSS选择器诊断工具
用于检查每个公司网站的实际HTML结构，帮助找到正确的CSS选择器
"""

from scrapers.jpmorgan_scraper import JPMorganScraper
from scrapers.goldman_scraper import GoldmanSachsScraper
from scrapers.morgan_stanley_scraper import MorganStanleyScraper
from scrapers.citi_scraper import CitiScraper
from scrapers.deutsche_bank_scraper import DeutscheBankScraper
from scrapers.ubs_scraper import UBSScraper
from scrapers.bnp_paribas_scraper import BNPParibasScraper
from scrapers.nomura_scraper import NomuraScraper
from scrapers.piper_sandler_scraper import PiperSandlerScraper

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time


def debug_scraper(scraper_class, company_name):
    """调试单个爬虫，保存HTML并打印关键信息"""
    print(f"\n{'='*60}")
    print(f"调试 {company_name}")
    print(f"{'='*60}")

    scraper = scraper_class()

    try:
        # 初始化WebDriver
        scraper.init_driver()
        print(f"✓ WebDriver初始化成功")

        # 加载页面
        print(f"正在加载: {scraper.source_url}")
        scraper.driver.get(scraper.source_url)

        # 等待页面加载
        time.sleep(5)

        # 保存完整HTML
        output_dir = "data/debug"
        os.makedirs(output_dir, exist_ok=True)

        html_file = os.path.join(output_dir, f"{company_name.replace(' ', '_').lower()}.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(scraper.driver.page_source)
        print(f"✓ HTML已保存到: {html_file}")

        # 尝试一些常见的职位容器选择器
        common_selectors = [
            # 通用
            '.job', '.job-item', '.job-card', '.job-listing', '.job-post',
            '.vacancy', '.position', '.opening', '.posting',
            # 列表项
            'li[class*="job"]', 'li[class*="vacancy"]', 'li[class*="position"]',
            # div容器
            'div[class*="job"]', 'div[class*="vacancy"]', 'div[class*="position"]',
            # 链接
            'a[href*="job"]', 'a[href*="career"]', 'a[href*="vacancy"]',
            # article
            'article',
            # 表格行
            'tr[class*="job"]', 'tr[class*="row"]',
            # Workday特定
            'div[data-automation-id*="job"]',
            # Oracle特定
            'div.job-tile', 'div.jobResultItem',
        ]

        print(f"\n尝试常见选择器:")
        found_selectors = []

        for selector in common_selectors:
            try:
                elements = scraper.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(elements) > 0:
                    found_selectors.append((selector, len(elements)))
                    print(f"  ✓ '{selector}' 找到 {len(elements)} 个元素")
            except Exception as e:
                pass

        if not found_selectors:
            print("  ✗ 未找到任何职位容器")
            print("\n建议:")
            print(f"  1. 打开HTML文件查看: {html_file}")
            print(f"  2. 搜索关键词: job, vacancy, position, career")
            print(f"  3. 查找职位标题所在的父容器")
        else:
            print(f"\n推荐选择器（按元素数量排序）:")
            found_selectors.sort(key=lambda x: x[1], reverse=True)
            for selector, count in found_selectors[:5]:
                print(f"  - '{selector}' ({count} 个元素)")

            # 尝试从第一个找到的选择器中提取信息
            best_selector = found_selectors[0][0]
            print(f"\n使用 '{best_selector}' 尝试提取数据:")
            try:
                elements = scraper.driver.find_elements(By.CSS_SELECTOR, best_selector)
                if len(elements) > 0:
                    first_elem = elements[0]
                    print(f"\n第一个元素的文本内容:")
                    print(f"{'-'*60}")
                    text = first_elem.text.strip()[:500]  # 限制500字符
                    print(text if text else "(无文本内容)")
                    print(f"{'-'*60}")

                    # 尝试找标题
                    title_selectors = ['h1', 'h2', 'h3', 'h4', 'a', '.title', '[class*="title"]']
                    for ts in title_selectors:
                        try:
                            title_elem = first_elem.find_element(By.CSS_SELECTOR, ts)
                            if title_elem.text.strip():
                                print(f"  可能的标题选择器: '{ts}' -> '{title_elem.text.strip()[:100]}'")
                                break
                        except:
                            pass

                    # 尝试找地点
                    location_selectors = ['.location', '[class*="location"]', '[class*="city"]', 'span']
                    for ls in location_selectors:
                        try:
                            loc_elem = first_elem.find_element(By.CSS_SELECTOR, ls)
                            if loc_elem.text.strip():
                                print(f"  可能的地点选择器: '{ls}' -> '{loc_elem.text.strip()[:100]}'")
                                break
                        except:
                            pass

                    # 尝试找链接
                    try:
                        link_elem = first_elem.find_element(By.TAG_NAME, 'a')
                        href = link_elem.get_attribute('href')
                        if href:
                            print(f"  可能的链接: {href[:100]}")
                    except:
                        pass
            except Exception as e:
                print(f"  提取失败: {e}")

        print(f"\n页面标题: {scraper.driver.title}")
        print(f"当前URL: {scraper.driver.current_url}")

    except Exception as e:
        print(f"✗ 错误: {e}")

    finally:
        try:
            scraper.close_driver()
        except:
            pass


def main():
    """调试所有爬虫"""
    scrapers = [
        (JPMorganScraper, "JPMorgan"),
        (GoldmanSachsScraper, "Goldman Sachs"),
        (MorganStanleyScraper, "Morgan Stanley"),
        (CitiScraper, "Citi"),
        (DeutscheBankScraper, "Deutsche Bank"),
        (UBSScraper, "UBS"),
        (BNPParibasScraper, "BNP Paribas"),
        (NomuraScraper, "Nomura"),
        (PiperSandlerScraper, "Piper Sandler"),
    ]

    print("CSS选择器诊断工具")
    print("这个工具会访问每个公司网站，保存HTML，并尝试找到正确的选择器\n")

    choice = input("选择模式:\n1. 调试所有公司\n2. 调试单个公司\n请输入 (1/2): ").strip()

    if choice == '2':
        print("\n可选公司:")
        for i, (_, name) in enumerate(scrapers, 1):
            print(f"{i}. {name}")
        idx = int(input("\n请输入公司编号: ").strip()) - 1
        if 0 <= idx < len(scrapers):
            debug_scraper(scrapers[idx][0], scrapers[idx][1])
    else:
        for scraper_class, company_name in scrapers:
            debug_scraper(scraper_class, company_name)
            time.sleep(2)  # 间隔2秒，避免请求过快

    print(f"\n{'='*60}")
    print("调试完成！")
    print("HTML文件保存在: data/debug/")
    print("请打开HTML文件查看页面结构，然后更新对应的爬虫文件")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
