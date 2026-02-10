"""
数据迁移脚本
- 添加 category 列到数据库
- 规范化现有职位的地点名称
- 对现有职位进行分类
"""

from app import create_app
from models.database import db
from models.job import Job
from utils.job_utils import normalize_location, categorize_job
from sqlalchemy import text

def migrate_data():
    print("="*70)
    print("开始数据迁移...")
    print("="*70)

    app, scheduler = create_app()
    scheduler.stop()

    with app.app_context():
        # Step 1: 添加 category 列（如果不存在）
        print("\n1. 检查并添加 category 列...")
        try:
            # 检查列是否存在
            result = db.session.execute(text("PRAGMA table_info(jobs)"))
            columns = [row[1] for row in result]

            if 'category' not in columns:
                print("   添加 category 列...")
                db.session.execute(text("ALTER TABLE jobs ADD COLUMN category VARCHAR(50)"))
                db.session.commit()
                print("   ✓ category 列已添加")
            else:
                print("   ✓ category 列已存在")
        except Exception as e:
            print(f"   错误: {e}")
            db.session.rollback()
            return

        # Step 2: 规范化地点名称
        print("\n2. 规范化地点名称...")
        try:
            all_jobs = Job.query.all()
            total_jobs = len(all_jobs)
            print(f"   处理 {total_jobs} 个职位...")

            location_changes = {}
            for job in all_jobs:
                old_location = job.location
                new_location = normalize_location(old_location)

                if old_location != new_location:
                    if old_location not in location_changes:
                        location_changes[old_location] = new_location
                    job.location = new_location

            if location_changes:
                print(f"\n   地点名称变更:")
                for old, new in sorted(location_changes.items()):
                    print(f"     '{old}' -> '{new}'")

            db.session.commit()
            print(f"\n   ✓ 地点规范化完成，共 {len(location_changes)} 个不同地点被规范化")
        except Exception as e:
            print(f"   错误: {e}")
            db.session.rollback()
            return

        # Step 3: 对职位进行分类
        print("\n3. 对职位进行分类...")
        try:
            all_jobs = Job.query.all()
            category_stats = {}

            for job in all_jobs:
                category = categorize_job(job.title, job.description or '')
                job.category = category

                if category not in category_stats:
                    category_stats[category] = 0
                category_stats[category] += 1

            db.session.commit()

            print(f"\n   分类统计:")
            for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"     {category}: {count} 个职位")

            print(f"\n   ✓ 职位分类完成")
        except Exception as e:
            print(f"   错误: {e}")
            db.session.rollback()
            return

        # Step 4: 验证结果
        print("\n4. 验证迁移结果...")
        try:
            total = Job.query.count()
            unique_locations = db.session.query(Job.location).distinct().count()
            unique_categories = db.session.query(Job.category).distinct().count()

            print(f"   总职位数: {total}")
            print(f"   唯一地点数: {unique_locations}")
            print(f"   唯一类别数: {unique_categories}")

            print("\n   前10个地点:")
            top_locations = db.session.query(Job.location, db.func.count(Job.id))\
                .group_by(Job.location)\
                .order_by(db.func.count(Job.id).desc())\
                .limit(10).all()

            for loc, count in top_locations:
                print(f"     {loc}: {count} 个职位")

        except Exception as e:
            print(f"   错误: {e}")

    print("\n" + "="*70)
    print("数据迁移完成！")
    print("="*70)


if __name__ == '__main__':
    migrate_data()
