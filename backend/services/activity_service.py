"""
活动日志服务 - 记录客户所有操作
"""
import json
from ..models import db, ActivityLog


def log_activity(
    action: str,
    summary: str,
    customer_id: int = None,
    detail: dict = None,
    operator: str = 'system',
    ip_address: str = None,
    user_agent: str = None
):
    """
    记录一条操作日志

    Args:
        action: 操作类型（CREATE/UPDATE/DELETE/SCORE/EMAIL_SENT/STATUS_CHANGE/SCORE_TRIGGER）
        summary: 操作摘要文本
        customer_id: 关联的客户ID
        detail: 详细信息（字典，会序列化为 JSON）
        operator: 操作者标识
        ip_address: 请求来源IP
        user_agent: 浏览器标识
    """
    log = ActivityLog(
        action=action,
        summary=summary,
        customer_id=customer_id,
        detail=json.dumps(detail, ensure_ascii=False) if detail else None,
        operator=operator,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.session.add(log)
    db.session.commit()
    return log


def log_customer_created(customer, operator='system', ip=None, ua=None):
    """新建客户"""
    return log_activity(
        action='CREATE',
        summary=f'新增客户: {customer.company_name_en}',
        customer_id=customer.id,
        detail={
            'company_name_en': customer.company_name_en,
            'country_id': customer.country_id,
            'customer_type_id': customer.customer_type_id,
            'priority_level': customer.priority_level,
        },
        operator=operator,
        ip_address=ip,
        user_agent=ua,
    )


def log_customer_updated(customer, changes: dict, operator='system', ip=None, ua=None):
    """更新客户"""
    return log_activity(
        action='UPDATE',
        summary=f'更新客户: {customer.company_name_en}',
        customer_id=customer.id,
        detail={'changes': changes},
        operator=operator,
        ip_address=ip,
        user_agent=ua,
    )


def log_customer_deleted(customer_name: str, customer_id: int, operator='system', ip=None, ua=None):
    """删除客户"""
    return log_activity(
        action='DELETE',
        summary=f'删除客户: {customer_name}',
        customer_id=customer_id,
        detail={'deleted_customer_id': customer_id},
        operator=operator,
        ip_address=ip,
        user_agent=ua,
    )


def log_score_calculated(customer_id: int, company_name: str, score: float, detail: dict = None):
    """背调评分"""
    return log_activity(
        action='SCORE',
        summary=f'背调评分 [{company_name}]: {score}分',
        customer_id=customer_id,
        detail={'score': score, 'company_name': company_name, **detail} if detail else {'score': score},
    )


def log_email_sent(customer_id: int, company_name: str, subject: str, recipient: str):
    """发送邮件"""
    return log_activity(
        action='EMAIL_SENT',
        summary=f'发送邮件 [{company_name}]: {subject}',
        customer_id=customer_id,
        detail={'subject': subject, 'recipient': recipient},
    )


def log_status_changed(customer_id: int, company_name: str, old_status: str, new_status: str):
    """状态变更"""
    return log_activity(
        action='STATUS_CHANGE',
        summary=f'状态变更 [{company_name}]: {old_status} → {new_status}',
        customer_id=customer_id,
        detail={'old_status': old_status, 'new_status': new_status},
    )


def log_score_trigger(customer_id: int, company_name: str, triggered_by: str = 'auto'):
    """搜索页触发评分"""
    return log_activity(
        action='SCORE_TRIGGER',
        summary=f'{"自动" if triggered_by == "auto" else "手动"}触发评分 [{company_name}]',
        customer_id=customer_id,
        detail={'triggered_by': triggered_by},
    )
