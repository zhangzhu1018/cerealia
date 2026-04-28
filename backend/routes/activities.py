"""
操作日志路由
GET  /activities              - 分页查询日志（全局）
GET  /activities/<customer_id> - 客户专属日志
GET  /activities/stats         - 日志统计
"""
from flask import Blueprint, request, jsonify
from ..models import db, ActivityLog

bp = Blueprint('activities', __name__, url_prefix='/activities')


@bp.route('', methods=['GET'])
def list_activities():
    """
    GET /activities
    Query params:
        page, page_size,
        customer_id, action,
        operator, keyword, start_date, end_date
    """
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)

    query = ActivityLog.query

    if request.args.get('customer_id'):
        query = query.filter(ActivityLog.customer_id == int(request.args['customer_id']))
    if request.args.get('action'):
        query = query.filter(ActivityLog.action == request.args['action'].upper())
    if request.args.get('operator'):
        query = query.filter(ActivityLog.operator == request.args['operator'])
    if request.args.get('keyword'):
        kw = f"%{request.args['keyword']}%"
        query = query.filter(ActivityLog.summary.ilike(kw))
    if request.args.get('start_date'):
        from datetime import datetime
        query = query.filter(ActivityLog.created_at >= datetime.fromisoformat(request.args['start_date']))
    if request.args.get('end_date'):
        from datetime import datetime
        query = query.filter(ActivityLog.created_at <= datetime.fromisoformat(request.args['end_date']))

    query = query.order_by(ActivityLog.created_at.desc())
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)

    return jsonify({
        'code': 0,
        'data': {
            'items': [_log_to_dict(l) for l in pagination.items],
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'pages': pagination.pages
        }
    })


@bp.route('/stats', methods=['GET'])
def activity_stats():
    """
    GET /activities/stats
    返回各操作类型的统计
    """
    from sqlalchemy import func
    results = db.session.query(
        ActivityLog.action,
        func.count(ActivityLog.id).label('count')
    ).group_by(ActivityLog.action).all()

    # 最近7天趋势
    from datetime import datetime, timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    trend = db.session.query(
        func.date(ActivityLog.created_at).label('date'),
        func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.created_at >= seven_days_ago
    ).group_by(func.date(ActivityLog.created_at)).order_by('date').all()

    return jsonify({
        'code': 0,
        'data': {
            'by_action': {r.action: r.count for r in results},
            'trend_7d': [{'date': str(r.date), 'count': r.count} for r in trend],
            'total': sum(r.count for r in results),
        }
    })


def _log_to_dict(log: ActivityLog):
    return {
        'id': log.id,
        'customer_id': log.customer_id,
        'customer_name': log.customer.company_name_en if log.customer else None,
        'action': log.action,
        'operator': log.operator,
        'summary': log.summary,
        'detail': log.detail,
        'ip_address': log.ip_address,
        'user_agent': log.user_agent,
        'created_at': log.created_at.isoformat() if log.created_at else None,
    }
