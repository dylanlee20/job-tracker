"""
运行 Evercore 爬虫并保存到数据库
"""

from scrapers.evercore_scraper import EvercoreScraper
from services.job_service import JobService
from services.excel_service import ExcelService
from app import create_app

def main():
    print("="*70)
    print("开始爬取 Evercore 职位...")
    print("="*70)

    # 创建爬虫实例
    scraper = EvercoreScraper()

    try:
        # 初始化浏览器
        scraper.init_driver()

        # 爬取职位
        print("\n正在爬取职位...")
        jobs = scraper.scrape_jobs()

        print(f"\n爬取完成！共爬取到 {len(jobs)} 个职位")

        # 显示前3个职位
        if len(jobs) > 0:
            print("\n前3个职位:")
            for i, job in enumerate(jobs[:3], 1):
                print(f"\n{i}. {job['title']}")
                print(f"   地点: {job['location']}")
                print(f"   截止日期: {job['deadline']}")
                print(f"   链接: {job['job_url'][:80]}...")

        # 保存到数据库
        print("\n" + "="*70)
        print("保存到数据库...")
        print("="*70)

        app, scheduler = create_app()

        with app.app_context():
            job_service = JobService()
            result = job_service.process_scraped_jobs(jobs, 'Evercore')

            print(f"\n数据库保存完成:")
            print(f"  新增职位: {result['new_jobs']}")
            print(f"  更新职位: {result['updated_jobs']}")
            print(f"  下线职位: {result['inactive_jobs']}")

            # 导出到 Excel
            print("\n" + "="*70)
            print("导出到 Excel...")
            print("="*70)

            excel_service = ExcelService()
            excel_path = excel_service.export_to_excel()

            print(f"\n✓ Excel 导出成功: {excel_path}")

        scheduler.stop()

        print("\n" + "="*70)
        print("全部完成！")
        print("="*70)

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        scraper.close_driver()


if __name__ == '__main__':
    main()
