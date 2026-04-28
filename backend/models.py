"""
SQLAlchemy ORM 模型 - 对照 database.sql 完整字段映射
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Country(db.Model):
    """国家字典表"""
    __tablename__ = 'countries'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name_en = db.Column(db.String(100), nullable=False)
    name_cn = db.Column(db.String(100))
    official_language = db.Column(db.String(50))
    priority = db.Column(db.Integer, default=0)
    trade_volume = db.Column(db.Numeric(12, 2))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    customers = db.relationship('Customer', backref='country', lazy='dynamic')


class CustomerType(db.Model):
    """客户类型字典表"""
    __tablename__ = 'customer_types'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type_code = db.Column(db.String(20), unique=True, nullable=False)
    type_name_en = db.Column(db.String(100), nullable=False)
    type_name_cn = db.Column(db.String(100), nullable=False)
    weight_score = db.Column(db.Integer, default=0)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联
    customers = db.relationship('Customer', backref='customer_type', lazy='dynamic')
    templates = db.relationship('EmailTemplate', backref='customer_type', lazy='dynamic')


class Customer(db.Model):
    """客户主表"""
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_name_en = db.Column(db.String(255), nullable=False)
    company_name_local = db.Column(db.String(255))
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=True)
    city = db.Column(db.String(100))
    website = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    linkedin_url = db.Column(db.String(500))          # 领英主页
    social_media = db.Column(db.JSON)                # 社交媒体 { facebook, instagram, twitter, youtube, tiktok, ... }
    contact_name = db.Column(db.String(100))          # 决策人/联系人
    address = db.Column(db.String(255))               # 公司地址
    customer_type_id = db.Column(db.Integer, db.ForeignKey('customer_types.id'))
    is_verified = db.Column(db.Boolean, default=False)
    background_score = db.Column(db.Numeric(5, 2), default=0)
    import_trade_score = db.Column(db.Integer, default=0)
    company_scale_score = db.Column(db.Integer, default=0)
    market_position_score = db.Column(db.Integer, default=0)
    qualification_score = db.Column(db.Integer, default=0)
    cooperation_potential_score = db.Column(db.Integer, default=0)
    social_media_score = db.Column(db.Integer, default=0)
    responsiveness_score = db.Column(db.Integer, default=0)
    country_rank = db.Column(db.Integer, default=999)
    is_collected = db.Column(db.Boolean, default=False)
    follow_up_status = db.Column(
        db.Enum('NEW', 'CONTACTED', 'NEGOTIATING', 'WON', 'LOST', 'INACTIVE', name='follow_up_status_enum'),
        default='NEW'
    )
    priority_level = db.Column(
        db.Enum('HIGH', 'MEDIUM', 'LOW', name='priority_level_enum'),
        default='MEDIUM'
    )
    notes = db.Column(db.Text)
    tags = db.Column(db.JSON)
    search_source = db.Column(db.String(100))
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_contact_date = db.Column(db.Date)

    # 关联
    background_check = db.relationship('BackgroundCheck', backref='customer', uselist=False, cascade='all, delete-orphan')
    email_logs = db.relationship('EmailSentLog', backref='customer', lazy='dynamic', cascade='all, delete-orphan')
    follow_up_tasks = db.relationship('FollowUpTask', backref='customer', lazy='dynamic', cascade='all, delete-orphan')
    products = db.relationship('Product', secondary='customer_products', back_populates='customers')


class BackgroundCheck(db.Model):
    """背调详细信息表"""
    __tablename__ = 'background_checks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False, unique=True)
    founded_year = db.Column(db.Integer)
    employee_count = db.Column(db.Integer)
    annual_revenue = db.Column(db.Numeric(15, 2))
    has_import_history = db.Column(db.Boolean, default=False)
    last_import_date = db.Column(db.Date)
    import_frequency = db.Column(db.String(20))
    typical_import_volume = db.Column(db.Numeric(10, 2))
    current_suppliers = db.Column(db.Text)
    has_cites_license = db.Column(db.Boolean, default=False)
    has_haccp_cert = db.Column(db.Boolean, default=False)
    other_certifications = db.Column(db.JSON)
    market_segment = db.Column(db.String(50))
    price_position = db.Column(db.String(20))
    distribution_channels = db.Column(db.JSON)
    linkedin_followers = db.Column(db.Integer)
    instagram_followers = db.Column(db.Integer)
    raw_data = db.Column(db.JSON)
    scrape_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmailTemplate(db.Model):
    """邮件模板表"""
    __tablename__ = 'email_templates'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    template_code = db.Column(db.String(50), unique=True, nullable=False)
    template_name = db.Column(db.String(100), nullable=False)
    customer_type_id = db.Column(db.Integer, db.ForeignKey('customer_types.id'))
    subject = db.Column(db.String(200), nullable=False)
    body_content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), default='en')
    variables = db.Column(db.JSON)
    industry = db.Column(db.String(50), default='caviar')
    is_active = db.Column(db.Boolean, default=True)
    usage_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    sent_logs = db.relationship('EmailSentLog', backref='template', lazy='dynamic')


class EmailSentLog(db.Model):
    """邮件发送记录表"""
    __tablename__ = 'email_sent_log'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('email_tasks.id', ondelete='SET NULL'), nullable=True)
    sender_account_id = db.Column(db.Integer, db.ForeignKey('email_accounts.id', ondelete='SET NULL'), nullable=True)
    recipient_email = db.Column(db.String(255), nullable=False)
    recipient_name = db.Column(db.String(100))
    subject = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10))
    send_status = db.Column(
        db.Enum('PENDING', 'SENT', 'FAILED', 'BOUNCED', name='send_status_enum'),
        default='PENDING'
    )
    error_message = db.Column(db.Text)
    opened_at = db.Column(db.DateTime)
    clicked_at = db.Column(db.DateTime)
    replied_at = db.Column(db.DateTime)
    follow_up_sent = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EmailAccount(db.Model):
    """发件邮箱账号表"""
    __tablename__ = 'email_accounts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account_name = db.Column(db.String(100), nullable=False)          # 账号昵称，如 "sales@cerealia.com"
    smtp_host = db.Column(db.String(200), nullable=False)             # SMTP 服务器
    smtp_port = db.Column(db.Integer, default=587)                   # SMTP 端口
    smtp_user = db.Column(db.String(200), nullable=False)              # 用户名
    smtp_password = db.Column(db.String(500), nullable=False)         # 密码/授权码（加密存储）
    use_tls = db.Column(db.Boolean, default=True)                    # 是否使用 TLS
    from_name = db.Column(db.String(100), default='Cerealia Caviar') # 发件人显示名
    from_email = db.Column(db.String(255), nullable=False)            # 发件地址
    daily_limit = db.Column(db.Integer, default=200)                  # 每日发送上限
    daily_sent_count = db.Column(db.Integer, default=0)               # 当日已发数
    last_reset_date = db.Column(db.Date)                             # 上次重置日期
    is_active = db.Column(db.Boolean, default=True)                  # 是否启用
    priority = db.Column(db.Integer, default=1)                       # 优先级（高→先发）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    sent_logs = db.relationship('EmailSentLog', backref='sender_account', lazy='dynamic')
    tasks = db.relationship('EmailTask', backref='sender_account', lazy='dynamic')


class EmailTask(db.Model):
    """批量邮件发送任务表"""
    __tablename__ = 'email_tasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_name = db.Column(db.String(200), nullable=False)             # 任务名称
    sender_account_id = db.Column(db.Integer, db.ForeignKey('email_accounts.id', ondelete='SET NULL'))
    status = db.Column(
        db.Enum('DRAFT', 'QUEUED', 'RUNNING', 'PAUSED', 'COMPLETED', 'CANCELLED', name='email_task_status_enum'),
        default='DRAFT'
    )
    # 发送目标
    target_type = db.Column(
        db.Enum('ALL_CUSTOMERS', 'BY_TYPE', 'BY_COUNTRY', 'BY_STATUS', 'BY_IDS', 'MANUAL', name='target_type_enum'),
        default='MANUAL'
    )
    target_customer_ids = db.Column(db.JSON)                          # 指定客户ID列表
    # 发送设置
    subject_template = db.Column(db.String(500))                       # 主题模板
    body_template = db.Column(db.Text)                                # 正文模板
    language = db.Column(db.String(10), default='en')
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'))
    # 调度配置
    send_interval_seconds = db.Column(db.Integer, default=30)          # 发送间隔（秒）
    start_time = db.Column(db.DateTime)                               # 开始时间
    end_time = db.Column(db.DateTime)                                 # 结束时间
    # 进度统计
    total_count = db.Column(db.Integer, default=0)                    # 总计应发
    sent_count = db.Column(db.Integer, default=0)                    # 已发送
    failed_count = db.Column(db.Integer, default=0)                   # 失败数
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    template = db.relationship('EmailTemplate', backref='email_tasks')
    sent_logs = db.relationship('EmailSentLog', backref='task', lazy='dynamic')


class FollowUpTask(db.Model):
    """跟进任务表"""
    __tablename__ = 'follow_up_tasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    contact_id = db.Column(db.Integer)
    task_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date, nullable=False)
    due_time = db.Column(db.Time)
    priority = db.Column(
        db.Enum('HIGH', 'MEDIUM', 'LOW', name='task_priority_enum'),
        default='MEDIUM'
    )
    status = db.Column(
        db.Enum('PENDING', 'COMPLETED', 'CANCELLED', 'OVERDUE', name='task_status_enum'),
        default='PENDING'
    )
    completed_at = db.Column(db.DateTime)
    completion_notes = db.Column(db.Text)
    assigned_to = db.Column(db.String(100))
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StatisticsDaily(db.Model):
    """每日统计表"""
    __tablename__ = 'statistics_daily'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stat_date = db.Column(db.Date, nullable=False, unique=True)
    total_customers = db.Column(db.Integer, default=0)
    new_customers = db.Column(db.Integer, default=0)
    high_score_customers = db.Column(db.Integer, default=0)
    countries_covered = db.Column(db.Integer, default=0)
    emails_sent = db.Column(db.Integer, default=0)
    emails_opened = db.Column(db.Integer, default=0)
    emails_replied = db.Column(db.Integer, default=0)
    open_rate = db.Column(db.Numeric(5, 2), default=0)
    reply_rate = db.Column(db.Numeric(5, 2), default=0)
    leads_converted = db.Column(db.Integer, default=0)
    total_potential_value = db.Column(db.Numeric(15, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ActivityLog(db.Model):
    """客户操作日志表 - 自动记录所有客户相关操作"""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(
        db.Enum(
            'CREATE',      # 新建客户
            'UPDATE',      # 更新客户
            'DELETE',      # 删除客户
            'SCORE',       # 背调评分
            'EMAIL_SENT',  # 发送邮件
            'STATUS_CHANGE',  # 状态变更
            'SCORE_TRIGGER', # 评分触发（搜索页）
            name='activity_action_enum'
        ),
        nullable=False
    )
    operator = db.Column(db.String(100), default='system')  # 操作者
    summary = db.Column(db.String(255), nullable=False)     # 操作摘要
    detail = db.Column(db.Text)                             # 详细信息（JSON）
    ip_address = db.Column(db.String(50))                  # IP 地址
    user_agent = db.Column(db.String(500))                 # 浏览器标识
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 关联
    customer = db.relationship('Customer', backref='activity_logs')


class User(db.Model):
    """管理员账号表"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(100))
    role = db.Column(db.String(20), default='admin')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── 产品 / HS CODE ────────────────────────────────────────────────────────────

class Product(db.Model):
    """产品字典表（鱼子酱品类）"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(100), nullable=False)          # 中文品名
    product_name_en = db.Column(db.String(100))                       # 英文品名
    hs_code = db.Column(db.String(20), nullable=False, unique=True)    # 海关HS编码
    hs_code_description = db.Column(db.String(255))                   # HS编码说明
    grade = db.Column(db.String(50))                                  # 等级（如：0级/1级）
    origin = db.Column(db.String(100))                                # 产地
    price_range = db.Column(db.String(100))                          # 参考价格区间
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    customers = db.relationship(
        'Customer',
        secondary='customer_products',
        back_populates='products'
    )


# 客户-产品关联表（多对多）
customer_products = db.Table(
    'customer_products',
    db.Column('customer_id', db.Integer, db.ForeignKey('customers.id', ondelete='CASCADE'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), primary_key=True),
    db.Column('typical_volume', db.Numeric(10, 2)),   # 典型进口量（kg）
    db.Column('notes', db.Text),
    db.Column('created_at', db.DateTime, default=datetime.utcnow),
)
