"""
测试 Citi 筛选器
找到并应用 Country 和 Job Level 筛选
"""

from scrapers.citi_scraper import CitiScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def test_citi_filters():
    print("="*70)
    print("Citi 筛选器测试")
    print("="*70)

    scraper = CitiScraper()

    try:
        scraper.init_driver()
        print("\n1. 浏览器初始化成功")

        print(f"\n2. 加载页面: {scraper.source_url}")
        scraper.driver.get(scraper.source_url)
        time.sleep(10)

        # 关闭 cookie 提示
        print(f"\n3. 关闭 cookie 提示...")
        try:
            accept_button = scraper.driver.find_element(By.ID, 'system-ialert-button')
            accept_button.click()
            time.sleep(2)
            print(f"   ✓ Cookie 提示已关闭")
        except Exception as e:
            print(f"   Cookie 提示未找到或已关闭: {e}")

        # 查找所有职位数量（应用筛选前）
        initial_jobs = scraper.driver.find_elements(By.CSS_SELECTOR, '[data-job-id]')
        print(f"\n4. 初始职位数量: {len(initial_jobs)}")

        # 展开 "Country and Jurisdiction" 筛选器
        print(f"\n5. 展开 'Country and Jurisdiction' 筛选器...")
        try:
            country_toggle = scraper.driver.find_element(By.ID, 'country-toggle')
            print(f"   找到按钮: '{country_toggle.text.strip()}'")
            country_toggle.click()
            time.sleep(2)
            print(f"   ✓ 已展开")
        except Exception as e:
            print(f"   ✗ 展开失败: {e}")

        # 点击 "United States" 筛选
        print(f"\n6. 应用 'United States' 筛选...")
        try:
            us_checkbox = scraper.driver.find_element(By.ID, 'country-filter-56')
            label = scraper.driver.find_element(By.CSS_SELECTOR, 'label[for="country-filter-56"]')
            print(f"   找到筛选: '{label.text.strip()}'")

            # 点击checkbox
            us_checkbox.click()
            print(f"   ✓ 已选中 'United States'")

            # 等待页面更新
            print(f"   等待结果更新...")
            time.sleep(5)

            # 检查选中后的职位数量
            filtered_jobs = scraper.driver.find_elements(By.CSS_SELECTOR, '[data-job-id]')
            print(f"   筛选后职位数量: {len(filtered_jobs)}")
        except Exception as e:
            print(f"   ✗ 应用筛选失败: {e}")
            import traceback
            traceback.print_exc()

        # 展开 "Job Level" 筛选器
        print(f"\n7. 展开 'Job Level' 筛选器...")
        try:
            # 滚动到 Job Level 按钮
            job_level_toggle = scraper.driver.find_element(By.ID, 'custom_fields.cfcareerlevel-toggle')
            scraper.driver.execute_script("arguments[0].scrollIntoView(true);", job_level_toggle)
            time.sleep(1)

            print(f"   找到按钮: '{job_level_toggle.text.strip()}'")
            job_level_toggle.click()
            time.sleep(2)
            print(f"   ✓ 已展开")
        except Exception as e:
            print(f"   ✗ 展开失败: {e}")
            import traceback
            traceback.print_exc()

        # 点击 "Student and Grad Programs" 筛选
        print(f"\n8. 应用 'Student and Grad Programs' 筛选...")
        try:
            student_checkbox = scraper.driver.find_element(By.ID, 'custom_fields.cfcareerlevel-filter-3')
            label = scraper.driver.find_element(By.CSS_SELECTOR, 'label[for="custom_fields.cfcareerlevel-filter-3"]')
            print(f"   找到筛选: '{label.text.strip()}'")

            # 点击checkbox
            student_checkbox.click()
            print(f"   ✓ 已选中 'Student and Grad Programs'")

            # 等待页面更新
            print(f"   等待结果更新...")
            time.sleep(5)

            # 检查最终职位数量
            final_jobs = scraper.driver.find_elements(By.CSS_SELECTOR, '[data-job-id]')
            print(f"   最终筛选后职位数量: {len(final_jobs)}")
        except Exception as e:
            print(f"   ✗ 应用筛选失败: {e}")
            import traceback
            traceback.print_exc()

        # 保存筛选后的HTML
        print(f"\n9. 保存筛选后的HTML...")
        with open('data/debug/citi_filters_applied.html', 'w', encoding='utf-8') as f:
            f.write(scraper.driver.page_source)
        print(f"   ✓ HTML已保存到 data/debug/citi_filters_applied.html")

        # 检查是否有分页
        print(f"\n10. 检查分页...")
        try:
            next_buttons = scraper.driver.find_elements(By.CSS_SELECTOR, 'a[class*="next"]')
            print(f"   找到 {len(next_buttons)} 个 Next 按钮")
            for btn in next_buttons:
                print(f"   - Text: '{btn.text.strip()}', Enabled: {btn.is_enabled()}")
        except Exception as e:
            print(f"   检查分页出错: {e}")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print(f"\n11. 关闭浏览器...")
        scraper.close_driver()


if __name__ == '__main__':
    test_citi_filters()
