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

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 创建复合索引（提高查询性能）
    __table_args__ = (
        Index('idx_company_location', 'company', 'location'),
        Index('idx_status_first_seen', 'status', 'first_seen'),
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
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<Job {self.company} - {self.title}>'
