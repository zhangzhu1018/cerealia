"""
仪表盘数据路由
GET /dashboard/stats             - 核心统计（客户总数/A级/邮件数/打开率）
GET /dashboard/country-distribution - 客户国家分布
GET /dashboard/type-distribution   - 客户类型分布
"""
from flask import Blueprint, jsonify
from sqlalchemy import func
from ..models import db, Customer, EmailSentLog
from datetime import datetime, timedelta

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@bp.route('/stats', methods=['GET'])
def dashboard_stats():
    """
    GET /dashboard/stats
    返回仪表盘核心统计数据
    """
    # 客户总数
    total_customers = db.session.query(func.count(Customer.id)).scalar() or 0

    # A/B 级客户数（综合评分 >= 70）
    high_score_count = db.session.query(func.count(Customer.id)).filter(
        Customer.background_score >= 70
    ).scalar() or 0

    # 本月发送邮件数
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_emails = db.session.query(func.count(EmailSentLog.id)).filter(
        EmailSentLog.sent_at >= month_start,
        EmailSentLog.send_status.in_(['SENT', 'SENT_VIA_TASK'])
    ).scalar() or 0

    # 近30天邮件打开率（opened_at 非空 / 已发送）
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_sent = db.session.query(func.count(EmailSentLog.id)).filter(
        EmailSentLog.sent_at >= thirty_days_ago,
        EmailSentLog.send_status.in_(['SENT', 'SENT_VIA_TASK'])
    ).scalar() or 0
    recent_opened = db.session.query(func.count(EmailSentLog.id)).filter(
        EmailSentLog.sent_at >= thirty_days_ago,
        EmailSentLog.send_status.in_(['SENT', 'SENT_VIA_TASK']),
        EmailSentLog.opened_at.isnot(None)
    ).scalar() or 0

    email_open_rate = round(recent_opened / recent_sent * 100, 1) if recent_sent > 0 else 0

    return jsonify({
        'code': 0,
        'data': {
            'total_customers': total_customers,
            'high_score_count': high_score_count,
            'monthly_emails': monthly_emails,
            'email_open_rate': email_open_rate,
        }
    })


@bp.route('/country-distribution', methods=['GET'])
def country_distribution():
    """
    GET /dashboard/country-distribution
    返回按国家分组的客户数量
    """
    from ..models import Country
    results = db.session.query(
        Customer.country_id,
        Country.name_en,
        func.count(Customer.id).label('count')
    ).join(
        Country, Customer.country_id == Country.id
    ).group_by(
        Customer.country_id,
        Country.name_en
    ).order_by(
        func.count(Customer.id).desc()
    ).all()

    return jsonify({
        'code': 0,
        'data': [
            {'country': r.name_en or f"国家ID:{r.country_id}", 'count': r.count}
            for r in results
        ]
    })


@bp.route('/type-distribution', methods=['GET'])
def type_distribution():
    """
    GET /dashboard/type-distribution
    返回按客户类型分组的客户数量
    """
    from ..models import CustomerType

    results = db.session.query(
        Customer.customer_type_id,
        CustomerType.type_name_en,
        func.count(Customer.id).label('count')
    ).join(
        CustomerType, Customer.customer_type_id == CustomerType.id
    ).group_by(
        Customer.customer_type_id,
        CustomerType.type_name_en
    ).order_by(
        func.count(Customer.id).desc()
    ).all()

    return jsonify({
        'code': 0,
        'data': [
            {'type': r.type_name_en or f"类型ID:{r.customer_type_id}", 'count': r.count}
            for r in results
        ]
    })
