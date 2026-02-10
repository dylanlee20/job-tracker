"""
BNP Paribas 结构详细分析
"""

from scrapers.bnp_paribas_scraper import BNPParibasScraper
from selenium.webdriver.common.by import By
import time


def test_bnp_structure():
    print("="*70)
    print("BNP Paribas 结构分析")
    print("="*70)

    url = 'https://group.bnpparibas/en/careers/all-job-offers?page=1&type=28%7C2134&rh_entity=94&country=10'

    scraper = BNPParibasScraper()
    scraper.source_url = url

    try:
        scraper.init_driver()
        print("\n加载页面...")
        scraper.driver.get(url)
        time.sleep(15)

        # 获取所有 offer 元素
        offer_divs = scraper.driver.find_elements(By.CSS_SELECTOR, 'div[class*="offer"]')
        print(f"\n找到 {len(offer_divs)} 个 offer 元素")

        # 筛选真正的职位卡片（包含足够信息）
        job_cards = []
        for div in offer_divs:
            try:
                # 看是否有链接
                links = div.find_elements(By.TAG_NAME, 'a')
                if links and len(div.text.strip()) > 20:
                    job_cards.append(div)
            except:
                pass

        print(f"其中可能是职位卡片的: {len(job_cards)} 个")

        # 分析前5个职位的详细结构
        for i, card in enumerate(job_cards[:5]):
            print(f"\n{'='*70}")
            print(f"职位 {i+1}")
            print(f"{'='*70}")

            print(f"Class: {card.get_attribute('class')}")
            print(f"文本: {card.text[:300]}...")

            # 查找所有子元素
            print(f"\n子元素:")

            # 标题
            for title_sel in ['h3', 'h2', 'h4', '.title', '[class*="title"]', 'a']:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, title_sel)
                    if title_elem.text.strip():
                        print(f"  标题 ({title_sel}): {title_elem.text.strip()}")
                        break
                except:
                    pass

            # 地点
            for loc_sel in ['.location', '[class*="location"]', 'span', 'p']:
                try:
                    loc_elem = card.find_element(By.CSS_SELECTOR, loc_sel)
                    loc_text = loc_elem.text.strip()
                    if loc_text and ('UNITED STATES' in loc_text.upper() or 'NEW YORK' in loc_text.upper()):
                        print(f"  地点 ({loc_sel}): {loc_text}")
                        break
                except:
                    pass

            # 链接
            try:
                links = card.find_elements(By.TAG_NAME, 'a')
                if links:
                    for link in links:
                        href = link.get_attribute('href')
                        if href and 'job' in href.lower():
                            print(f"  链接: {href}")
                            print(f"  链接文本: {link.text.strip()}")
                            break
            except:
                pass

            # 职位类型
            for type_sel in ['.type', '[class*="type"]', 'span', 'div']:
                try:
                    type_elem = card.find_element(By.CSS_SELECTOR, type_sel)
                    type_text = type_elem.text.strip()
                    if type_text and ('INTERNSHIP' in type_text.upper() or 'TRAINEE' in type_text.upper()):
                        print(f"  类型 ({type_sel}): {type_text}")
                        break
                except:
                    pass

        # 检查分页信息
        print(f"\n{'='*70}")
        print("分页信息")
        print(f"{'='*70}")

        try:
            # 查找总页数或总结果数
            body_text = scraper.driver.find_element(By.TAG_NAME, 'body').text
            lines = body_text.split('\n')
            for line in lines:
                if 'result' in line.lower() or 'offer' in line.lower():
                    if any(char.isdigit() for char in line):
                        print(f"  {line.strip()}")
        except:
            pass

        # 查找 next 按钮
        try:
            next_button = scraper.driver.find_element(By.CSS_SELECTOR, '[aria-label*="next"]')
            print(f"\n找到 Next 按钮:")
            print(f"  Tag: {next_button.tag_name}")
            print(f"  Text: {next_button.text}")
            print(f"  Enabled: {next_button.is_enabled()}")
            print(f"  href: {next_button.get_attribute('href')}")
        except Exception as e:
            print(f"\n未找到 Next 按钮: {e}")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        scraper.close_driver()


if __name__ == '__main__':
    test_bnp_structure()
