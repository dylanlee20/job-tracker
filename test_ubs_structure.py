"""
UBS 结构分析 - 找到真实的职位链接
"""

from scrapers.ubs_scraper import UBSScraper
from selenium.webdriver.common.by import By
import time


def test_ubs_structure():
    print("="*70)
    print("UBS 结构分析")
    print("="*70)

    url = 'https://jobs.ubs.com/TGnewUI/Search/home/HomeWithPreLoad?partnerid=25008&siteid=5131&PageType=searchResults&SearchType=linkquery&LinkID=15700#keyWordSearch=&locationSearch=&City=Chicago_or_Hong%20Kong%20SAR_or_New%20York_or_San%20Francisco'

    scraper = UBSScraper()
    scraper.source_url = url

    try:
        scraper.init_driver()
        print("\n加载页面...")
        scraper.driver.get(url)
        time.sleep(30)

        print(f"找到 25 个结果\n")

        # 获取所有 tr 元素
        all_trs = scraper.driver.find_elements(By.TAG_NAME, 'tr')

        # 筛选包含职位信息的 tr
        job_trs = []
        for tr in all_trs:
            try:
                links = tr.find_elements(By.TAG_NAME, 'a')
                if links and len(tr.text.strip()) > 50:
                    job_trs.append(tr)
            except:
                pass

        print(f"找到 {len(job_trs)} 个职位行\n")

        # 分析前5个职位的详细结构
        for i, tr in enumerate(job_trs[:5]):
            print(f"{'='*70}")
            print(f"职位 {i+1}")
            print(f"{'='*70}")

            # 打印 HTML 结构
            print(f"HTML: {tr.get_attribute('outerHTML')[:500]}...")

            # 获取所有 td
            tds = tr.find_elements(By.TAG_NAME, 'td')
            print(f"\n共有 {len(tds)} 个 td 元素")

            for j, td in enumerate(tds):
                print(f"\nTD {j+1}:")
                print(f"  Class: {td.get_attribute('class')}")
                print(f"  文本: {td.text.strip()[:100]}")

                # 查找该 td 中的所有链接
                links = td.find_elements(By.TAG_NAME, 'a')
                if links:
                    print(f"  包含 {len(links)} 个链接:")
                    for k, link in enumerate(links):
                        href = link.get_attribute('href')
                        onclick = link.get_attribute('onclick')
                        print(f"    链接 {k+1}: {link.text.strip()[:50]}")
                        print(f"      href: {href}")
                        if onclick:
                            print(f"      onclick: {onclick[:100]}")

                # 查找 data-job-id 属性
                job_id = td.get_attribute('data-job-id')
                if job_id:
                    print(f"  data-job-id: {job_id}")

            # 尝试点击第一个职位，看会发生什么
            if i == 0:
                print(f"\n尝试点击第一个职位标题...")
                try:
                    # 查找职位标题链接（通常是第一个显著的链接）
                    title_links = tr.find_elements(By.CSS_SELECTOR, 'a[onclick], a[href*="job"]')
                    if title_links:
                        first_link = title_links[0]
                        print(f"点击: {first_link.text.strip()}")

                        # 获取当前窗口句柄
                        main_window = scraper.driver.current_window_handle

                        # 点击链接
                        first_link.click()
                        time.sleep(5)

                        # 检查是否打开了新窗口
                        all_windows = scraper.driver.window_handles
                        if len(all_windows) > 1:
                            scraper.driver.switch_to.window(all_windows[-1])
                            print(f"新窗口URL: {scraper.driver.current_url}")
                            scraper.driver.close()
                            scraper.driver.switch_to.window(main_window)
                        else:
                            print(f"当前URL: {scraper.driver.current_url}")
                            scraper.driver.back()
                            time.sleep(3)
                except Exception as e:
                    print(f"点击失败: {e}")

            print("\n")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        scraper.close_driver()


if __name__ == '__main__':
    test_ubs_structure()
