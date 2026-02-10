"""
测试 JPMorgan URL 分页参数
"""

from scrapers.jpmorgan_scraper import JPMorganScraper
from selenium.webdriver.common.by import By
import time


def test_url_pagination():
    print("="*70)
    print("JPMorgan URL 分页测试")
    print("="*70)

    base_url = 'https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs?keyword=summer+analyst&lastSelectedFacet=CATEGORIES&location=United+States&locationId=300000000289738&locationLevel=country&mode=location&selectedCategoriesFacet=300000086153065'

    scraper = JPMorganScraper()

    try:
        scraper.init_driver()

        # 测试不同的分页参数
        pagination_params = [
            '',           # 第1页（默认）
            '&start=20',  # 第2页
            '&start=40',  # 第3页
        ]

        for i, param in enumerate(pagination_params):
            url = base_url + param
            page_num = i + 1

            print(f"\n{'='*70}")
            print(f"第 {page_num} 页")
            print(f"{'='*70}")
            print(f"URL: {url}")

            scraper.driver.get(url)
            time.sleep(10)

            # 统计职位数
            job_tiles = scraper.driver.find_elements(By.CSS_SELECTOR, 'div.job-tile')
            print(f"\n找到 {len(job_tiles)} 个职位")

            if len(job_tiles) > 0:
                # 显示前3个职位标题
                print(f"\n前3个职位:")
                for j, tile in enumerate(job_tiles[:3]):
                    try:
                        title_elem = tile.find_element(By.CSS_SELECTOR, 'span.job-tile__title')
                        print(f"  {j+1}. {title_elem.text}")
                    except:
                        pass
            else:
                print("  （没有找到职位）")
                break

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        scraper.close_driver()


if __name__ == '__main__':
    test_url_pagination()
