"""
邮件生成路由
POST /emails/generate  - 根据公司信息生成双语邮件
GET  /emails/templates - 获取邮件模板列表
POST /emails/templates  - 创建邮件模板
POST /emails/send      - 记录邮件发送
GET  /emails/logs/<customer_id> - 获取客户邮件发送历史
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from ..models import db, Customer, EmailTemplate, EmailSentLog, EmailAccount, EmailTask
from ..services.email_service import EmailGenerator
from ..services.activity_service import log_email_sent
from ..services.email_sender_service import get_sender

bp = Blueprint('emails', __name__, url_prefix='/emails')

# 全局邮件生成器实例
_email_gen = EmailGenerator()


@bp.route('/generate-batch-preview', methods=['POST'])
def generate_batch_preview():
    """
    POST /emails/generate-batch-preview
    批量生成邮件预览（DeepSeek AI，每家公司一封，不发送）

    Body: {
        customers: [{ company_name_en, country_name, email, contact_name }, ...],
        additional_context: str (可选)
    }

    返回: {
        previews: [{ company_name, country, email, subject, body_english, body_local, language }, ...],
        total: int
    }
    """
    data = request.get_json() or {}
    customers = data.get('customers', [])
    additional_context = data.get('additional_context')

    if not customers:
        return jsonify({'code': 400, 'message': '没有要生成的客户列表'}), 400

    if len(customers) > 500:
        return jsonify({'code': 400, 'message': '单次最多生成 500 封，请分批处理'}), 400

    previews = _email_gen.generate_batch_preview(
        companies=customers,
        additional_context=additional_context,
    )

    return jsonify({
        'code': 0,
        'data': {
            'previews': previews,
            'total': len(previews),
        }
    })


@bp.route('/confirm-batch-send', methods=['POST'])
def confirm_batch_send():
    """
    POST /emails/confirm-batch-send
    确认发送预览列表中的邮件（真实 SMTP 批量发送）

    Body: {
        previews: [{ company_name, email, subject, body_combined, language, customer_id }, ...],
        sender_account_id: int (可选，不填则自动选)
    }

    返回: {
        sent: int, failed: int, results: [...]
    }
    """
    data = request.get_json() or {}
    previews = data.get('previews', [])
    sender_account_id = data.get('sender_account_id')

    if not previews:
        return jsonify({'code': 400, 'message': '没有要发送的邮件'}), 400

    from ..models import Customer
    sender = get_sender()

    sent_count = 0
    failed_count = 0
    results = []

    for item in previews:
        email_addr = item.get('email', '').strip()
        if not email_addr or '@' not in email_addr:
            failed_count += 1
            results.append({
                'company_name': item.get('company_name', ''),
                'email': email_addr,
                'status': 'failed',
                'reason': '邮箱地址无效',
            })
            continue

        # 查找或关联客户
        customer_id = item.get('customer_id')
        if not customer_id:
            # 尝试按邮箱查找
            existing = Customer.query.filter(
                db.func.lower(Customer.email) == email_addr.lower()
            ).first()
            if existing:
                customer_id = existing.id

        # 真实发送
        success, err, acct_id = sender.send_one(
            to_email=email_addr,
            to_name=item.get('company_name', 'Partner'),
            subject=item.get('subject', 'Partnership: Cerealia Caviar'),
            body=item.get('body_combined', item.get('body_english', '')),
            account_id=sender_account_id,
        )

        # 记录发送日志
        log = EmailSentLog(
            customer_id=customer_id,
            sender_account_id=acct_id,
            recipient_email=email_addr,
            recipient_name=item.get('contact_name') or item.get('company_name', ''),
            subject=item.get('subject', ''),
            content=item.get('body_combined', item.get('body_english', '')),
            language=item.get('language', 'en'),
            send_status='SENT' if success else 'FAILED',
            error_message=err if not success else None,
            sent_at=datetime.utcnow() if success else None,
        )
        db.session.add(log)

        if customer_id:
            try:
                customer = Customer.query.get(customer_id)
                if customer:
                    log_email_sent(
                        customer_id=customer_id,
                        company_name=customer.company_name_en,
                        subject=item.get('subject', ''),
                        recipient=email_addr,
                    )
            except Exception:
                pass

        if success:
            sent_count += 1
        else:
            failed_count += 1

        results.append({
            'company_name': item.get('company_name', ''),
            'email': email_addr,
            'status': 'SENT' if success else 'FAILED',
            'reason': err if not success else None,
        })

    db.session.commit()

    return jsonify({
        'code': 0,
        'data': {
            'sent': sent_count,
            'failed': failed_count,
            'total': len(previews),
            'results': results,
        },
        'message': f'发送完成：成功 {sent_count} 封，失败 {failed_count} 封',
    })


@bp.route('/generate', methods=['POST'])
def generate_email():
    """
    POST /emails/generate
    兼容两种调用格式：
    1. 新格式（前端 EmailPage）：{ company_name, customer_type, target_language, additional_context }
    2. 旧格式（内部调用）：{ company: {...}, customer_type, preferred_language }
    """
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    # 兼容两种格式：检测是否使用了新格式的 flat 参数
    if 'company' not in data and 'company_name' in data:
        # 新格式：前端传来的 flat 参数
        company_name = data.get('company_name', '')
        company = {
            'company_name_en': company_name,
            'country_name': data.get('country'),
            'contact_name': data.get('contact_name'),
            'email': data.get('email'),
        }
        preferred_language = _language_code_to_locale(data.get('target_language'))
        customer_type = data.get('customer_type')
        additional_context = data.get('additional_context')
    elif 'company' in data:
        # 旧格式：直接传 company 对象
        company = data['company']
        preferred_language = data.get('preferred_language')
        customer_type = data.get('customer_type')
        additional_context = data.get('additional_context')
    else:
        return jsonify({'code': 400, 'message': '缺少 company 或 company_name 参数'}), 400

    result = _email_gen.generate_bilingual_email(
        company=company,
        customer_type=customer_type,
        preferred_language=preferred_language,
        additional_context=additional_context,
    )

    # 如果提供了 customer_id，自动创建邮件发送记录（待发送状态）
    if data.get('customer_id'):
        customer = Customer.query.get(data['customer_id'])
        if customer:
            log = EmailSentLog(
                customer_id=data['customer_id'],
                recipient_email=company.get('email', customer.email or ''),
                recipient_name=company.get('contact_name', 'Team'),
                subject=result['subject'],
                content=result['body_combined'],
                language=result.get('language_secondary') or result['language_primary'],
                send_status='PENDING'
            )
            db.session.add(log)
            db.session.commit()
            result['sent_log_id'] = log.id
            result['saved_to_log'] = True

    return jsonify({'code': 0, 'data': result})


def _language_code_to_locale(code):
    """将前端语言代码转换为邮件生成器期望的 locale 格式"""
    mapping = {
        'english': 'en', 'french': 'fr', 'german': 'de',
        'japanese': 'ja', 'spanish': 'es', 'arabic': 'ar',
    }
    return mapping.get(code, code or 'en')


@bp.route('/templates', methods=['GET'])
def list_templates():
    """GET /emails/templates - 获取邮件模板列表"""
    templates = EmailTemplate.query.filter_by(is_active=True).order_by(EmailTemplate.usage_count.desc()).all()
    return jsonify({
        'code': 0,
        'data': [{
            'id': t.id,
            'template_code': t.template_code,
            'template_name': t.template_name,
            'subject': t.subject,
            'language': t.language,
            'industry': t.industry,
            'usage_count': t.usage_count,
            'customer_type_name': t.customer_type.type_name_en if t.customer_type else None,
        } for t in templates]
    })


@bp.route('/templates', methods=['POST'])
def create_template():
    """POST /emails/templates - 创建邮件模板"""
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    required = ['template_code', 'template_name', 'subject', 'body_content']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({'code': 400, 'message': f'缺少必填字段: {", ".join(missing)}'}), 400

    # 检查模板编码唯一性
    existing = EmailTemplate.query.filter_by(template_code=data['template_code']).first()
    if existing:
        return jsonify({'code': 409, 'message': f'模板编码 {data["template_code"]} 已存在'}), 409

    template = EmailTemplate(
        template_code=data['template_code'],
        template_name=data['template_name'],
        customer_type_id=data.get('customer_type_id'),
        subject=data['subject'],
        body_content=data['body_content'],
        language=data.get('language', 'en'),
        variables=data.get('variables'),
        industry=data.get('industry', 'caviar'),
    )
    db.session.add(template)
    db.session.commit()
    return jsonify({'code': 0, 'data': {'id': template.id}, 'message': '模板创建成功'}), 201


@bp.route('/send', methods=['POST'])
def record_send():
    """
    POST /emails/send
    Body: {
        customer_id: int,
        template_id: int (可选),
        subject: str,
        content: str,
        recipient_email: str,
        recipient_name: str,
        language: str
    }
    """
    data = request.get_json()
    if not data or 'customer_id' not in data or 'recipient_email' not in data:
        return jsonify({'code': 400, 'message': '缺少 customer_id 或 recipient_email'}), 400

    log = EmailSentLog(
        customer_id=data['customer_id'],
        template_id=data.get('template_id'),
        recipient_email=data['recipient_email'],
        recipient_name=data.get('recipient_name'),
        subject=data.get('subject', ''),
        content=data.get('content', ''),
        language=data.get('language'),
        send_status=data.get('send_status', 'SENT'),
        sent_at=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()

    # 自动记录邮件发送日志
    customer = Customer.query.get(data['customer_id'])
    if customer:
        log_email_sent(
            customer_id=data['customer_id'],
            company_name=customer.company_name_en,
            subject=data.get('subject', ''),
            recipient=data['recipient_email']
        )

    return jsonify({'code': 0, 'data': {'log_id': log.id}, 'message': '发送记录已保存'})


@bp.route('/logs/<int:customer_id>', methods=['GET'])
def get_email_logs(customer_id):
    """GET /emails/logs/<customer_id> - 获取客户邮件发送历史"""
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'code': 404, 'message': '客户不存在'}), 404

    logs = EmailSentLog.query.filter_by(customer_id=customer_id).order_by(
        EmailSentLog.created_at.desc()
    ).limit(50).all()
    return jsonify({
        'code': 0,
        'data': [{
            'id': log.id,
            'template_id': log.template_id,
            'recipient_email': log.recipient_email,
            'recipient_name': log.recipient_name,
            'subject': log.subject,
            'language': log.language,
            'send_status': log.send_status,
            'sent_at': log.sent_at.isoformat() if log.sent_at else None,
            'opened_at': log.opened_at.isoformat() if log.opened_at else None,
            'replied_at': log.replied_at.isoformat() if log.replied_at else None,
            'follow_up_sent': log.follow_up_sent,
            'notes': log.notes,
        } for log in logs]
    })


# /emails/history/<customerId> - 前端 CustomerDetail 历史记录 Tab 专用
@bp.route('/history/<int:customer_id>', methods=['GET'])
def get_email_history(customer_id):
    """
    GET /emails/history/<customer_id>
    前端 CustomerDetail 页面邮件历史记录专用端点
    返回格式匹配前端期望的 { target_language, created_at, english_version }
    """
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'code': 404, 'message': '客户不存在'}), 404

    logs = EmailSentLog.query.filter_by(customer_id=customer_id).order_by(
        EmailSentLog.sent_at.desc()
    ).limit(50).all()

    # 返回前端期望的格式：{ target_language, created_at, english_version }
    return jsonify({
        'code': 0,
        'data': [{
            'id': log.id,
            'target_language': log.language or 'en',
            'created_at': (log.sent_at or log.created_at).isoformat() if (log.sent_at or log.created_at) else None,
            'english_version': log.content or '',
            'subject': log.subject,
            'send_status': log.send_status,
            'recipient_email': log.recipient_email,
        } for log in logs]
    })


@bp.route('/logs/<int:log_id>', methods=['PATCH'])
def update_log_status(log_id):
    """PATCH /emails/logs/<log_id> - 更新邮件状态（打开/回复等）"""
    log = EmailSentLog.query.get(log_id)
    if not log:
        return jsonify({'code': 404, 'message': '发送记录不存在'}), 404

    data = request.get_json()
    if data.get('opened') and not log.opened_at:
        log.opened_at = datetime.utcnow()
    if data.get('replied') and not log.replied_at:
        log.replied_at = datetime.utcnow()
    if 'send_status' in data:
        log.send_status = data['send_status']
    if 'notes' in data:
        log.notes = data['notes']

    db.session.commit()
    return jsonify({'code': 0, 'message': '状态已更新'})


# ══════════════════════════════════════════════════════════════════════════════
#  发件账号管理
# ══════════════════════════════════════════════════════════════════════════════

@bp.route('/accounts', methods=['GET'])
def list_accounts():
    """GET /emails/accounts - 获取发件账号列表"""
    accounts = EmailAccount.query.order_by(EmailAccount.priority.desc()).all()
    return jsonify({
        'code': 0,
        'data': [{
            'id': a.id,
            'account_name': a.account_name,
            'smtp_host': a.smtp_host,
            'smtp_port': a.smtp_port,
            'smtp_user': a.smtp_user,
            'from_name': a.from_name,
            'from_email': a.from_email,
            'use_tls': a.use_tls,
            'daily_limit': a.daily_limit,
            'daily_sent_count': a.daily_sent_count,
            'is_active': a.is_active,
            'priority': a.priority,
            'last_reset_date': a.last_reset_date.isoformat() if a.last_reset_date else None,
            'created_at': a.created_at.isoformat() if a.created_at else None,
        } for a in accounts]
    })


@bp.route('/accounts', methods=['POST'])
def create_account():
    """POST /emails/accounts - 添加发件账号"""
    data = request.get_json()
    required = ['account_name', 'smtp_host', 'smtp_user', 'smtp_password', 'from_email']
    missing = [f for f in required if f not in data or not data[f]]
    if missing:
        return jsonify({'code': 400, 'message': f'缺少必填字段: {", ".join(missing)}'}), 400

    account = EmailAccount(
        account_name=data['account_name'],
        smtp_host=data['smtp_host'],
        smtp_port=data.get('smtp_port', 587),
        smtp_user=data['smtp_user'],
        smtp_password=data['smtp_password'],      # 生产环境建议加密存储
        use_tls=data.get('use_tls', True),
        from_name=data.get('from_name', 'Cerealia Caviar'),
        from_email=data['from_email'],
        daily_limit=data.get('daily_limit', 200),
        is_active=data.get('is_active', True),
        priority=data.get('priority', 1),
    )
    db.session.add(account)
    db.session.commit()
    return jsonify({'code': 0, 'data': {'id': account.id}, 'message': '账号添加成功'}), 201


@bp.route('/accounts/<int:account_id>', methods=['PUT'])
def update_account(account_id):
    """PUT /emails/accounts/<id> - 更新发件账号"""
    account = EmailAccount.query.get_or_404(account_id)
    data = request.get_json()

    for field in ['account_name', 'smtp_host', 'smtp_port', 'smtp_user',
                  'use_tls', 'from_name', 'from_email', 'daily_limit', 'is_active', 'priority']:
        if field in data:
            setattr(account, field, data[field])

    if 'smtp_password' in data and data['smtp_password']:
        account.smtp_password = data['smtp_password']

    db.session.commit()
    return jsonify({'code': 0, 'message': '账号更新成功'})


@bp.route('/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    """DELETE /emails/accounts/<id> - 删除发件账号"""
    account = EmailAccount.query.get_or_404(account_id)
    db.session.delete(account)
    db.session.commit()
    return jsonify({'code': 0, 'message': '账号已删除'})


@bp.route('/accounts/<int:account_id>/test', methods=['POST'])
def test_account(account_id):
    """POST /emails/accounts/<id>/test - 测试账号连通性"""
    account = EmailAccount.query.get_or_404(account_id)
    data = request.get_json() or {}
    test_to = data.get('test_email')

    if not test_to:
        return jsonify({'code': 400, 'message': '缺少 test_email 参数'}), 400

    sender = get_sender()
    success, err, _ = sender.send_one(
        to_email=test_to,
        to_name='Test Recipient',
        subject='[Cerealia CRM] 邮件发送测试 / Email Send Test',
        body=f'<p>这是一封来自 Cerealia Caviar CRM 的测试邮件。</p><p>This is a test email from Cerealia Caviar CRM.</p><p>发送账号: {account.from_email}</p>',
        account_id=account.id,
    )

    if success:
        return jsonify({'code': 0, 'message': f'测试邮件发送成功，请检查 {test_to}'})
    else:
        return jsonify({'code': 500, 'message': f'发送失败: {err}'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  发送任务管理
# ══════════════════════════════════════════════════════════════════════════════

@bp.route('/tasks', methods=['GET'])
def list_tasks():
    """GET /emails/tasks - 获取发送任务列表"""
    tasks = EmailTask.query.order_by(EmailTask.created_at.desc()).limit(50).all()
    return jsonify({
        'code': 0,
        'data': [{
            'id': t.id,
            'task_name': t.task_name,
            'sender_account_id': t.sender_account_id,
            'sender_account_name': t.sender_account.account_name if t.sender_account else None,
            'status': t.status,
            'target_type': t.target_type,
            'total_count': t.total_count,
            'sent_count': t.sent_count,
            'failed_count': t.failed_count,
            'send_interval_seconds': t.send_interval_seconds,
            'language': t.language,
            'started_at': t.started_at.isoformat() if t.started_at else None,
            'finished_at': t.finished_at.isoformat() if t.finished_at else None,
            'created_at': t.created_at.isoformat() if t.created_at else None,
        } for t in tasks]
    })


@bp.route('/tasks', methods=['POST'])
def create_task():
    """
    POST /emails/tasks - 创建发送任务
    Body: {
        task_name, sender_account_id,
        target_type, target_customer_ids,
        subject_template, body_template,
        language, send_interval_seconds, created_by
    }
    """
    data = request.get_json()
    if not data or 'task_name' not in data:
        return jsonify({'code': 400, 'message': '缺少 task_name'}), 400

    task = EmailTask(
        task_name=data['task_name'],
        sender_account_id=data.get('sender_account_id'),
        target_type=data.get('target_type', 'MANUAL'),
        target_customer_ids=data.get('target_customer_ids'),
        subject_template=data.get('subject_template'),
        body_template=data.get('body_template'),
        language=data.get('language', 'en'),
        template_id=data.get('template_id'),
        send_interval_seconds=data.get('send_interval_seconds', 30),
        created_by=data.get('created_by', 'system'),
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({'code': 0, 'data': {'id': task.id}, 'message': '任务创建成功'}), 201


@bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """GET /emails/tasks/<id> - 获取任务详情 + 进度"""
    task = EmailTask.query.get_or_404(task_id)
    sender = get_sender()
    progress = sender.get_task_progress(task_id)
    return jsonify({
        'code': 0,
        'data': {
            'id': task.id,
            'task_name': task.task_name,
            'status': task.status,
            'target_type': task.target_type,
            'target_customer_ids': task.target_customer_ids,
            'subject_template': task.subject_template,
            'body_template': task.body_template,
            'language': task.language,
            'send_interval_seconds': task.send_interval_seconds,
            'total_count': task.total_count,
            'sent_count': task.sent_count,
            'failed_count': task.failed_count,
            'sender_account_name': task.sender_account.account_name if task.sender_account else None,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'finished_at': task.finished_at.isoformat() if task.finished_at else None,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            **progress,
        }
    })


@bp.route('/tasks/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """POST /emails/tasks/<id>/start - 启动任务"""
    sender = get_sender()
    ok = sender.start_task(task_id)
    if ok:
        return jsonify({'code': 0, 'message': '任务已启动'})
    return jsonify({'code': 400, 'message': '任务无法启动（可能已在运行或已完成）'}), 400


@bp.route('/tasks/<int:task_id>/pause', methods=['POST'])
def pause_task(task_id):
    """POST /emails/tasks/<id>/pause - 暂停任务"""
    sender = get_sender()
    ok = sender.pause_task(task_id)
    if ok:
        return jsonify({'code': 0, 'message': '任务已暂停'})
    return jsonify({'code': 400, 'message': '任务无法暂停'}), 400


@bp.route('/tasks/<int:task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """POST /emails/tasks/<id>/cancel - 取消任务"""
    sender = get_sender()
    ok = sender.cancel_task(task_id)
    if ok:
        return jsonify({'code': 0, 'message': '任务已取消'})
    return jsonify({'code': 400, 'message': '任务无法取消'}), 400


@bp.route('/tasks/<int:task_id>/progress', methods=['GET'])
def task_progress(task_id):
    """GET /emails/tasks/<id>/progress - 轮询任务进度"""
    sender = get_sender()
    progress = sender.get_task_progress(task_id)
    return jsonify({'code': 0, 'data': progress})


@bp.route('/tasks/<int:task_id>/logs', methods=['GET'])
def task_logs(task_id):
    """GET /emails/tasks/<id>/logs - 获取任务发送记录"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = EmailSentLog.query.filter_by(task_id=task_id).order_by(EmailSentLog.sent_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'code': 0,
        'data': [{
            'id': log.id,
            'customer_id': log.customer_id,
            'recipient_email': log.recipient_email,
            'recipient_name': log.recipient_name,
            'subject': log.subject,
            'send_status': log.send_status,
            'sent_at': log.sent_at.isoformat() if log.sent_at else None,
            'error_message': log.error_message,
            'sender_account_name': log.sender_account.account_name if log.sender_account else None,
        } for log in pagination.items],
        'pagination': {
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': per_page,
        }
    })


# ══════════════════════════════════════════════════════════════════════════════
#  实时发送（单封，不走任务队列）
# ══════════════════════════════════════════════════════════════════════════════

@bp.route('/send-now', methods=['POST'])
def send_email_now():
    """
    POST /emails/send-now - 实时发送一封邮件（真实 SMTP）
    Body: {
        customer_id, subject, content,
        sender_account_id (可选，不填则自动选)
    }
    """
    data = request.get_json()
    if not data or 'customer_id' not in data:
        return jsonify({'code': 400, 'message': '缺少 customer_id'}), 400

    customer = Customer.query.get(data['customer_id'])
    if not customer:
        return jsonify({'code': 404, 'message': '客户不存在'}), 404

    sender = get_sender()
    success, err, account_id = sender.send_one(
        to_email=customer.email or data.get('recipient_email', ''),
        to_name=customer.company_name_en,
        subject=data.get('subject', 'Partnership: Cerealia Caviar'),
        body=data.get('content', ''),
        account_id=data.get('sender_account_id'),
    )

    # 记录
    log = EmailSentLog(
        customer_id=customer.id,
        sender_account_id=account_id,
        recipient_email=customer.email or '',
        recipient_name=customer.company_name_en,
        subject=data.get('subject', ''),
        content=data.get('content', ''),
        send_status='SENT' if success else 'FAILED',
        error_message=err if not success else None,
        sent_at=datetime.utcnow() if success else None,
    )
    db.session.add(log)
    db.session.commit()

    if success:
        log_email_sent(
            customer_id=customer.id,
            company_name=customer.company_name_en,
            subject=data.get('subject', ''),
            recipient=customer.email or '',
        )
        return jsonify({'code': 0, 'message': '发送成功', 'data': {'log_id': log.id}})

    return jsonify({'code': 500, 'message': f'发送失败: {err}'}), 500


@bp.route('/send-test', methods=['POST'])
def send_test():
    """
    POST /emails/send-test - 发送测试邮件到指定邮箱
    Body: { to_email, subject, content, sender_account_id }
    """
    data = request.get_json()
    if not data or 'to_email' not in data:
        return jsonify({'code': 400, 'message': '缺少 to_email'}), 400

    sender = get_sender()
    success, err, _ = sender.send_one(
        to_email=data['to_email'],
        to_name=data.get('to_name', 'Test'),
        subject=data.get('subject', '[Cerealia CRM] Test Email'),
        body=data.get('content', '<p>Test email from Cerealia Caviar CRM.</p>'),
        account_id=data.get('sender_account_id'),
    )

    if success:
        return jsonify({'code': 0, 'message': f'测试邮件已发送至 {data["to_email"]}'})
    return jsonify({'code': 500, 'message': f'发送失败: {err}'}), 500


@bp.route('/track/<log_id>', methods=['GET'])
def track_open(log_id):
    """邮件打开追踪像素：嵌入式1x1透明GIF"""
    from ..models import EmailSentLog, db
    log = EmailSentLog.query.get(log_id)
    if log and not log.opened_at:
        log.opened_at = datetime.utcnow()
        db.session.commit()
    pixel = b'GIF89a...'  # 1x1透明像素
    return b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b', 200, {'Content-Type': 'image/gif', 'Cache-Control': 'no-cache'}
