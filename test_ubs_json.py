"""
UBS JSON 数据提取测试
"""

from scrapers.ubs_scraper import UBSScraper
from selenium.webdriver.common.by import By
import time
import json
import html


def test_ubs_json():
    print("="*70)
    print("UBS JSON 数据提取")
    print("="*70)

    url = 'https://jobs.ubs.com/TGnewUI/Search/home/HomeWithPreLoad?partnerid=25008&siteid=5131&PageType=searchResults&SearchType=linkquery&LinkID=15700#keyWordSearch=&locationSearch=&City=Chicago_or_Hong%20Kong%20SAR_or_New%20York_or_San%20Francisco'

    scraper = UBSScraper()
    scraper.source_url = url

    try:
        scraper.init_driver()
        print("\n加载页面...")
        scraper.driver.get(url)
        time.sleep(30)

        # 查找 preLoadJSON 隐藏字段
        print("\n查找 preLoadJSON 元素...")
        try:
            json_input = scraper.driver.find_element(By.ID, 'preLoadJSON')
            json_value = json_input.get_attribute('value')

            print(f"✓ 找到 JSON 数据 (长度: {len(json_value)} 字符)")

            # 解码 HTML 实体
            decoded_json = html.unescape(json_value)

            # 解析 JSON
            data = json.loads(decoded_json)

            print(f"\n顶层键: {list(data.keys())}")

            # 检查 searchResultsResponse
            if 'searchResultsResponse' in data:
                search_results = data['searchResultsResponse']
                print(f"\nsearchResultsResponse 键: {list(search_results.keys())}")

                if 'Jobs' in search_results:
                    jobs = search_results['Jobs']
                    print(f"\nJobs 键: {list(jobs.keys())}")

                    if 'Job' in jobs:
                        job_list = jobs['Job']
                        print(f"\n共有 {len(job_list)} 个职位")

                        # 显示前3个职位的详细信息
                        for i, job in enumerate(job_list[:3]):
                            print(f"\n{'='*70}")
                            print(f"职位 {i+1}")
                            print(f"{'='*70}")

                            # 打印顶层键
                            print(f"顶层键: {list(job.keys())}")

                            # 提取关键信息
                            if 'Questions' in job:
                                questions = job['Questions']
                                print(f"\n共有 {len(questions)} 个 Questions")

                                # 创建字典方便查找
                                q_dict = {q['QuestionName']: q['Value'] for q in questions}

                                print(f"\nQuestion 名称:")
                                for q_name in list(q_dict.keys())[:15]:
                                    print(f"  - {q_name}: {q_dict[q_name]}")

                                # 提取常见字段
                                print(f"\n关键字段:")
                                if 'reqid' in q_dict:
                                    print(f"  Requisition ID: {q_dict['reqid']}")
                                if 'Job Title' in q_dict:
                                    print(f"  Title: {q_dict['Job Title']}")
                                if 'Primary Location' in q_dict:
                                    print(f"  Location: {q_dict['Primary Location']}")
                                if 'City' in q_dict:
                                    print(f"  City: {q_dict['City']}")
                                if 'State' in q_dict:
                                    print(f"  State: {q_dict['State']}")
                                if 'Job Description' in q_dict:
                                    desc = q_dict['Job Description']
                                    print(f"  Description: {desc[:200]}...")

                                # 构建职位URL
                                if 'reqid' in q_dict:
                                    req_id = q_dict['reqid']
                                    job_url = f"https://jobs.ubs.com/TGnewUI/Search/home/HomeWithPreLoad?partnerid=25008&siteid=5131&PageType=JobDetails&jobid={req_id}"
                                    print(f"  Job URL: {job_url}")

        except Exception as e:
            print(f"✗ 提取 JSON 失败: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        scraper.close_driver()


if __name__ == '__main__':
    test_ubs_json()
