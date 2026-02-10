from models.database import db
from models.job import Job
from datetime import datetime, timedelta
from sqlalchemy import or_, and_
from utils.job_utils import normalize_location, categorize_job
import logging

logger = logging.getLogger(__name__)


class JobService:
    """职位管理服务"""

    @staticmethod
    def process_scraped_jobs(scraped_jobs, company):
        """
        处理爬取的职位数据

        Args:
            scraped_jobs: 爬取的职位列表
            company: 公司名称

        Returns:
            dict: 包含新增、更新、下线职位统计的字典
        """
        stats = {
            'new_jobs': 0,
            'updated_jobs': 0,
            'inactive_jobs': 0,
            'total_scraped': len(scraped_jobs)
        }

        try:
            # 获取该批次的 source_website（从第一个job获取）
            source_website = scraped_jobs[0]['source_website'] if scraped_jobs else None

            # 获取该公司和来源的所有活跃职位的哈希值
            # 只管理来自同一source_website的职位，避免不同区域互相影响
            if source_website:
                existing_jobs = Job.query.filter_by(
                    company=company,
                    source_website=source_website,
                    status='active'
                ).all()
            else:
                existing_jobs = Job.query.filter_by(company=company, status='active').all()

            existing_hashes = {job.job_hash: job for job in existing_jobs}

            # 当前爬取到的职位哈希集合
            scraped_hashes = set()

            # 处理每个爬取的职位
            for job_data in scraped_jobs:
                try:
                    # Normalize location and categorize job
                    normalized_location = normalize_location(job_data.get('location', ''))
                    job_category = categorize_job(job_data.get('title', ''), job_data.get('description', ''))

                    # Update job_data with normalized values
                    job_data['location'] = normalized_location
                    job_data['category'] = job_category

                    # 生成职位哈希
                    job_hash = Job.generate_job_hash(
                        job_data['company'],
                        job_data['title'],
                        job_data['location']
                    )

                    # 检查是否在本批次中已经处理过（去重）
                    if job_hash in scraped_hashes:
                        logger.debug(f"Duplicate job in batch, skipping: {job_data['title']}")
                        continue

                    scraped_hashes.add(job_hash)

                    # 生成描述哈希
                    description_hash = Job.generate_description_hash(job_data.get('description', ''))

                    # 检查职位是否已存在
                    if job_hash in existing_hashes:
                        # 职位已存在，检查是否需要更新
                        existing_job = existing_hashes[job_hash]

                        # 更新 last_seen 时间
                        existing_job.last_seen = datetime.utcnow()

                        # 检查描述是否有变化
                        if description_hash and existing_job.description_hash != description_hash:
                            existing_job.description = job_data.get('description', '')
                            existing_job.description_hash = description_hash
                            existing_job.last_updated = datetime.utcnow()
                            stats['updated_jobs'] += 1

                            logger.info(f"Updated job: {job_data['title']} at {job_data['company']}")

                    else:
                        # 新职位，插入数据库
                        new_job = Job(
                            job_hash=job_hash,
                            company=job_data['company'],
                            title=job_data['title'],
                            location=job_data['location'],
                            category=job_data.get('category', 'Other'),
                            description=job_data.get('description', ''),
                            description_hash=description_hash,
                            post_date=job_data.get('post_date'),
                            deadline=job_data.get('deadline'),
                            source_website=job_data['source_website'],
                            job_url=job_data['job_url'],
                            status='active',
                            first_seen=datetime.utcnow(),
                            last_seen=datetime.utcnow(),
                            last_updated=datetime.utcnow()
                        )

                        db.session.add(new_job)
                        stats['new_jobs'] += 1

                        logger.info(f"Added new job: {job_data['title']} at {job_data['company']}")

                except Exception as e:
                    logger.error(f"Error processing job data: {e}")
                    continue

            # 标记未爬取到的职位为 inactive
            for job_hash, job in existing_hashes.items():
                if job_hash not in scraped_hashes:
                    job.status = 'inactive'
                    stats['inactive_jobs'] += 1

                    logger.info(f"Marked as inactive: {job.title} at {job.company}")

            # 提交数据库更改
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in process_scraped_jobs: {e}")
            raise

        return stats

    @staticmethod
    def get_jobs(filters=None, page=1, per_page=50):
        """
        获取职位列表（支持筛选和分页）

        Args:
            filters: 筛选条件字典
                - company: 公司名称
                - location: 地点
                - keyword: 关键词搜索
                - is_important: 是否只显示重点职位
                - time_range: 时间范围 (this_week, this_month, all)
                - status: 状态 (active, inactive)
            page: 页码
            per_page: 每页数量

        Returns:
            dict: 包含 jobs 和 pagination 信息的字典
        """
        query = Job.query

        if filters:
            # 公司筛选
            if filters.get('company'):
                query = query.filter(Job.company == filters['company'])

            # 地点筛选
            if filters.get('location'):
                query = query.filter(Job.location.like(f"%{filters['location']}%"))

            # 类别筛选
            if filters.get('category'):
                query = query.filter(Job.category == filters['category'])

            # 关键词搜索（搜索标题和描述）
            if filters.get('keyword'):
                keyword = f"%{filters['keyword']}%"
                query = query.filter(
                    or_(
                        Job.title.like(keyword),
                        Job.description.like(keyword)
                    )
                )

            # 重点职位筛选
            if filters.get('is_important'):
                query = query.filter(Job.is_important == True)

            # 时间范围筛选
            if filters.get('time_range'):
                time_range = filters['time_range']
                now = datetime.utcnow()

                if time_range == 'this_week':
                    week_ago = now - timedelta(days=7)
                    query = query.filter(Job.first_seen >= week_ago)
                elif time_range == 'this_month':
                    month_ago = now - timedelta(days=30)
                    query = query.filter(Job.first_seen >= month_ago)

            # 状态筛选（默认只显示 active）
            status = filters.get('status', 'active')
            if status:
                query = query.filter(Job.status == status)

        # 按首次发现时间倒序排序
        query = query.order_by(Job.first_seen.desc())

        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            'jobs': [job.to_dict() for job in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }

    @staticmethod
    def get_job_by_id(job_id):
        """获取单个职位详情"""
        job = Job.query.get(job_id)
        return job.to_dict() if job else None

    @staticmethod
    def mark_job_important(job_id, is_important):
        """标记/取消标记重点职位"""
        try:
            job = Job.query.get(job_id)
            if job:
                job.is_important = is_important
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error marking job important: {e}")
            return False

    @staticmethod
    def add_user_note(job_id, note):
        """添加/更新用户备注"""
        try:
            job = Job.query.get(job_id)
            if job:
                job.user_notes = note
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding user note: {e}")
            return False

    @staticmethod
    def get_statistics():
        """获取统计信息"""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Calculate how many weeks we've been tracking
        from models.job_snapshot import JobSnapshot
        first_snapshot = JobSnapshot.query.order_by(JobSnapshot.snapshot_date.asc()).first()
        tracking_weeks = 0
        if first_snapshot:
            days_tracking = (now - first_snapshot.snapshot_date).days
            tracking_weeks = max(1, days_tracking // 7)

        stats = {
            'total_active_jobs': Job.query.filter_by(status='active').count(),
            'total_inactive_jobs': Job.query.filter_by(status='inactive').count(),
            'new_this_week': Job.query.filter(
                and_(Job.first_seen >= week_ago, Job.status == 'active')
            ).count(),
            'new_this_month': Job.query.filter(
                and_(Job.first_seen >= month_ago, Job.status == 'active')
            ).count(),
            'important_jobs': Job.query.filter_by(is_important=True, status='active').count(),
            'companies': db.session.query(Job.company).filter_by(status='active').distinct().count(),
            'tracking_weeks': tracking_weeks
        }

        return stats

    @staticmethod
    def get_all_companies():
        """获取所有公司列表"""
        companies = db.session.query(Job.company).filter_by(status='active').distinct().all()
        return [c[0] for c in companies]

    @staticmethod
    def get_all_locations():
        """获取所有地点列表"""
        locations = db.session.query(Job.location).filter_by(status='active').distinct().all()
        return sorted([l[0] for l in locations if l[0]])

    @staticmethod
    def get_all_categories():
        """获取所有职位类别列表"""
        categories = db.session.query(Job.category).filter_by(status='active').distinct().all()
        return sorted([c[0] for c in categories if c[0]])
