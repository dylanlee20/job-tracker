from datetime import datetime, timedelta
from models.database import db
from sqlalchemy import Index
import hashlib


class Job(db.Model):
    """职位模型"""

    __tablename__ = 'jobs'

    # 主键
    id = db.Column(db.Integer, primary_key=True)

    # 唯一标识（用于去重）
    job_hash = db.Column(db.String(32), unique=True, nullable=False, index=True)

    # 基本信息
    company = db.Column(db.String(100), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=True, index=True)  # Job category
    description = db.Column(db.Text, nullable=True)
    description_hash = db.Column(db.String(32), nullable=True)

    # 日期信息
    post_date = db.Column(db.DateTime, nullable=True)
    deadline = db.Column(db.DateTime, nullable=True)

    # 来源信息
    source_website = db.Column(db.String(200), nullable=False)
    job_url = db.Column(db.String(500), nullable=False)

    # 状态追踪
    status = db.Column(db.String(20), default='active', nullable=False, index=True)  # active/inactive
    first_seen = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 用户交互字段
    is_important = db.Column(db.Boolean, default=False, nullable=False, index=True)
    user_notes = db.Column(db.Text, nullable=True)

    # 行业分类
    industry = db.Column(db.String(100), nullable=True, index=True)

    # 申请状态追踪
    application_submitted = db.Column(db.Boolean, default=False, nullable=False)
    application_date = db.Column(db.DateTime, nullable=True)
    application_result = db.Column(db.String(20), nullable=True)  # 'pending', 'accepted', 'rejected', 'no_response'
    result_date = db.Column(db.DateTime, nullable=True)
    result_notes = db.Column(db.Text, nullable=True)

    # 工作签证赞助
    sponsorship_required = db.Column(db.Boolean, nullable=True)  # NULL = unknown, False = no sponsorship, True = sponsorship required

    # Megasheet（精选全职项目清单）字段
    external_id = db.Column(db.String(30), nullable=True, index=True)  # 来源 megasheet 的职位编号，例如 "24764"
    is_rolling = db.Column(db.Boolean, default=False, nullable=False)  # "Rolling ASAP" 滚动招聘（无固定截止日）
    recruiting_window = db.Column(db.String(120), nullable=True)  # 该公司该岗位每年通常开放的时间窗口

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 创建复合索引（提高查询性能）
    __table_args__ = (
        Index('idx_company_location', 'company', 'location'),
        Index('idx_status_first_seen', 'status', 'first_seen'),
        Index('idx_industry', 'industry'),
    )

    @property
    def is_new(self):
        """判断是否为新职位（7天内）"""
        from config import Config
        return (datetime.utcnow() - self.first_seen).days < Config.NEW_JOB_DAYS

    @property
    def is_updated(self):
        """判断是否最近更新过（3天内）"""
        from config import Config
        return (datetime.utcnow() - self.last_updated).days < Config.UPDATED_JOB_DAYS

    @property
    def deadline_status(self):
        """职位截止状态：'rolling' / 'open' / 'closing_soon'(<=14天) / 'expired'。"""
        if self.is_rolling:
            return 'rolling'
        if not self.deadline:
            return 'open'
        days_left = (self.deadline - datetime.utcnow()).days
        if days_left < 0:
            return 'expired'
        if days_left <= 14:
            return 'closing_soon'
        return 'open'

    @property
    def days_until_deadline(self):
        """距离截止日的天数；rolling 或无截止日返回 None。"""
        if self.is_rolling or not self.deadline:
            return None
        return (self.deadline - datetime.utcnow()).days

    @staticmethod
    def generate_job_hash(company, title, location):
        """生成职位唯一哈希"""
        data = f"{company}{title}{location}".lower().strip()
        return hashlib.md5(data.encode('utf-8')).hexdigest()

    @staticmethod
    def generate_description_hash(description):
        """生成描述哈希"""
        if not description:
            return None
        return hashlib.md5(description.encode('utf-8')).hexdigest()

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'company': self.company,
            'title': self.title,
            'location': self.location,
            'category': self.category,
            'description': self.description,
            'post_date': self.post_date.isoformat() if self.post_date else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'source_website': self.source_website,
            'job_url': self.job_url,
            'status': self.status,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'is_new': self.is_new,
            'is_updated': self.is_updated,
            'is_important': self.is_important,
            'user_notes': self.user_notes,
            'industry': self.industry,
            'application_submitted': self.application_submitted,
            'application_date': self.application_date.isoformat() if self.application_date else None,
            'application_result': self.application_result,
            'result_date': self.result_date.isoformat() if self.result_date else None,
            'result_notes': self.result_notes,
            'sponsorship_required': self.sponsorship_required,
            'external_id': self.external_id,
            'is_rolling': self.is_rolling,
            'recruiting_window': self.recruiting_window,
            'deadline_status': self.deadline_status,
            'days_until_deadline': self.days_until_deadline,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<Job {self.company} - {self.title}>'
