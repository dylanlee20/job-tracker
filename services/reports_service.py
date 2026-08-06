"""
Reports generation service
Provides analytics and summary reports for job tracking
"""
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from models.job import Job
from models.database import db
import logging

logger = logging.getLogger(__name__)


class ReportsService:
    """职位报告生成服务"""

    @staticmethod
    def get_positions_summary(start_date=None, end_date=None, company=None, industry=None):
        """
        获取职位发布概况

        Args:
            start_date: 开始日期
            end_date: 结束日期
            company: 公司名称筛选
            industry: 行业筛选

        Returns:
            dict: 包含职位总数、按公司分组、按行业分组的统计信息
        """
        # Base query
        query = Job.query.filter(Job.status == 'active')

        if start_date:
            query = query.filter(Job.first_seen >= start_date)
        if end_date:
            query = query.filter(Job.first_seen <= end_date)
        if company:
            query = query.filter(Job.company == company)
        if industry:
            query = query.filter(Job.industry == industry)

        total = query.count()

        # Group by company
        by_company_query = db.session.query(
            Job.company,
            func.count(Job.id).label('count')
        ).filter(Job.status == 'active')

        if start_date:
            by_company_query = by_company_query.filter(Job.first_seen >= start_date)
        if end_date:
            by_company_query = by_company_query.filter(Job.first_seen <= end_date)
        if industry:
            by_company_query = by_company_query.filter(Job.industry == industry)

        by_company = by_company_query.group_by(Job.company).order_by(
            func.count(Job.id).desc()
        ).limit(20).all()  # Top 20 companies

        # Group by industry
        by_industry_query = db.session.query(
            Job.industry,
            func.count(Job.id).label('count')
        ).filter(and_(Job.status == 'active', Job.industry.isnot(None)))

        if start_date:
            by_industry_query = by_industry_query.filter(Job.first_seen >= start_date)
        if end_date:
            by_industry_query = by_industry_query.filter(Job.first_seen <= end_date)
        if company:
            by_industry_query = by_industry_query.filter(Job.company == company)

        by_industry = by_industry_query.group_by(Job.industry).order_by(
            func.count(Job.id).desc()
        ).all()

        return {
            'total_positions': total,
            'by_company': [{'name': c[0], 'count': c[1]} for c in by_company],
            'by_industry': [{'name': i[0], 'count': i[1]} for i in by_industry],
        }

    @staticmethod
    def get_application_summary():
        """
        获取申请追踪概况

        Returns:
            dict: 包含总申请数、各状态数量、成功率等统计信息
        """
        total_applications = Job.query.filter(
            Job.application_submitted == True
        ).count()

        # Count by result status
        result_counts = db.session.query(
            Job.application_result,
            func.count(Job.id)
        ).filter(Job.application_submitted == True).group_by(
            Job.application_result
        ).all()

        results = {(r[0] or 'pending'): r[1] for r in result_counts}

        # Calculate success rate
        accepted = results.get('accepted', 0)
        rejected = results.get('rejected', 0)
        no_response = results.get('no_response', 0)
        total_with_result = accepted + rejected + no_response

        success_rate = (accepted / total_with_result * 100) if total_with_result > 0 else 0

        return {
            'total_applications': total_applications,
            'pending': results.get('pending', 0) + results.get(None, 0),
            'accepted': accepted,
            'rejected': rejected,
            'no_response': no_response,
            'success_rate': round(success_rate, 2),
        }

    @staticmethod
    def get_industry_breakdown():
        """
        获取行业分布详情

        Returns:
            list: 行业统计列表，包含行业名称、职位数、申请数等
        """
        industry_stats = db.session.query(
            Job.industry,
            func.count(Job.id).label('total_jobs'),
            func.sum(func.cast(Job.application_submitted, db.Integer)).label('applications'),
            func.sum(
                func.case(
                    (Job.application_result == 'accepted', 1),
                    else_=0
                )
            ).label('accepted')
        ).filter(
            and_(Job.status == 'active', Job.industry.isnot(None))
        ).group_by(Job.industry).order_by(
            func.count(Job.id).desc()
        ).all()

        results = []
        for stat in industry_stats:
            results.append({
                'industry': stat[0],
                'total_jobs': stat[1],
                'applications': stat[2] or 0,
                'accepted': stat[3] or 0,
                'success_rate': round((stat[3] / stat[2] * 100) if stat[2] and stat[2] > 0 else 0, 2)
            })

        return results

    @staticmethod
    def get_company_application_stats():
        """
        获取各公司的申请统计

        Returns:
            list: 公司统计列表，包含公司名称、职位数、申请数、录取数等
        """
        company_stats = db.session.query(
            Job.company,
            func.count(Job.id).label('total_jobs'),
            func.sum(func.cast(Job.application_submitted, db.Integer)).label('applications'),
            func.sum(
                func.case(
                    (Job.application_result == 'accepted', 1),
                    else_=0
                )
            ).label('accepted')
        ).filter(
            Job.status == 'active'
        ).group_by(Job.company).order_by(
            func.count(Job.id).desc()
        ).limit(20).all()  # Top 20 companies

        results = []
        for stat in company_stats:
            results.append({
                'company': stat[0],
                'total_jobs': stat[1],
                'applications': stat[2] or 0,
                'accepted': stat[3] or 0,
                'success_rate': round((stat[3] / stat[2] * 100) if stat[2] and stat[2] > 0 else 0, 2)
            })

        return results

    @staticmethod
    def get_timeline_data(days=30):
        """
        获取时间线数据（职位发布趋势）

        Args:
            days: 查询的天数范围

        Returns:
            list: 按日期分组的职位数统计
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        timeline = db.session.query(
            func.date(Job.first_seen).label('date'),
            func.count(Job.id).label('count')
        ).filter(
            and_(Job.first_seen >= start_date, Job.status == 'active')
        ).group_by(
            func.date(Job.first_seen)
        ).order_by(
            func.date(Job.first_seen)
        ).all()

        return [
            {
                'date': t[0].isoformat() if hasattr(t[0], 'isoformat') else str(t[0]),
                'count': t[1]
            }
            for t in timeline
        ]
