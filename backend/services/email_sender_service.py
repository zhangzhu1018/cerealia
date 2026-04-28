"""
邮件发送服务 - 真实 SMTP 发送 + 任务调度
支持多账号轮询、发送间隔控制、每日上限保护
"""
import time
import json
import smtplib
import threading
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

from flask import current_app
from ..models import db, EmailAccount, EmailTask, EmailSentLog


class EmailSender:
    """
    真实邮件发送器
    支持多账号轮询 + 每日限额 + 发送间隔
    """

    def __init__(self, app=None):
        self.app = app
        self._scheduler = None
        self._scheduler_thread = None
        self._running_task_id = None  # 当前正在运行的任务ID
        self._lock = threading.Lock()

    def init_app(self, app):
        self.app = app

    # ── SMTP 发送 ─────────────────────────────────────────────────────────────

    def _build_message(self, to_email: str, to_name: str, subject: str, body: str,
                       from_name: str, from_email: str) -> MIMEMultipart:
        """构建 MIME 邮件"""
        msg = MIMEMultipart('alternative')
        msg['From'] = f'"{from_name}" <{from_email}>'
        msg['To'] = f'"{to_name}" <{to_email}>'
        msg['Subject'] = Header(subject, 'utf-8')
        # 支持 HTML 邮件
        plain = MIMEText(body.replace('\n', '<br>'), 'html', 'utf-8')
        msg.attach(plain)
        return msg

    def _get_ready_account(self) -> EmailAccount | None:
        """获取一个可用的发件账号（有配额）"""
        accounts = EmailAccount.query.filter_by(is_active=True).order_by(
            EmailAccount.priority.desc()
        ).all()
        today = date.today()
        for acc in accounts:
            # 重置每日计数
            if acc.last_reset_date != today:
                acc.daily_sent_count = 0
                acc.last_reset_date = today
                db.session.commit()
            if acc.daily_sent_count < acc.daily_limit:
                return acc
        return None

    def _send_via_smtp(self, account: EmailAccount, to_email: str, to_name: str,
                       subject: str, body: str) -> tuple[bool, str]:
        """
        通过 SMTP 发送一封邮件
        Returns: (success, error_message)
        """
        try:
            msg = self._build_message(
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                body=body,
                from_name=account.from_name,
                from_email=account.from_email,
            )

            if account.use_tls:
                server = smtplib.SMTP(account.smtp_host, account.smtp_port, timeout=30)
                server.starttls()
            else:
                server = smtplib.SMTP(account.smtp_host, account.smtp_port, timeout=30)

            server.login(account.smtp_user, account.smtp_password)
            server.sendmail(account.from_email, [to_email], msg.as_string())
            server.quit()
            return True, ''
        except Exception as e:
            return False, str(e)

    def send_one(self, to_email: str, to_name: str, subject: str, body: str,
                 account_id: int = None) -> tuple[bool, str, int | None]:
        """
        发送一封邮件（使用指定账号或自动选一个）
        Returns: (success, error, account_id)
        """
        if account_id:
            account = EmailAccount.query.get(account_id)
        else:
            account = self._get_ready_account()

        if not account:
            return False, '没有可用的发件账号', None

        success, err = self._send_via_smtp(account, to_email, to_name, subject, body)

        if success:
            account.daily_sent_count = (account.daily_sent_count or 0) + 1
            db.session.commit()

        return success, err, account.id

    # ── 调度器 ───────────────────────────────────────────────────────────────

    def _dispatch_task(self, task_id: int):
        """在新线程中执行任务（每批次发一封）"""
        def _run():
            with self.app.app_context():
                self._execute_task(task_id)

        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def _execute_task(self, task_id: int):
        """执行一个发送任务（持续循环直到完成/暂停/取消）"""
        task = EmailTask.query.get(task_id)
        if not task:
            return

        task.status = 'RUNNING'
        task.started_at = datetime.utcnow()
        db.session.commit()

        # 确定要发送的客户列表
        from ..models import Customer
        query = Customer.query

        if task.target_type == 'ALL_CUSTOMERS':
            pass
        elif task.target_type == 'BY_STATUS' and task.target_customer_ids:
            status_filter = task.target_customer_ids.get('status')
            if status_filter:
                query = query.filter(Customer.follow_up_status == status_filter)
        elif task.target_type == 'BY_COUNTRY' and task.target_customer_ids:
            country_ids = task.target_customer_ids.get('country_ids', [])
            if country_ids:
                query = query.filter(Customer.country_id.in_(country_ids))
        elif task.target_type == 'BY_IDS' and task.target_customer_ids:
            ids = task.target_customer_ids.get('ids', [])
            if ids:
                query = query.filter(Customer.id.in_(ids))
            else:
                query = query.filter(db.text('1=0'))
        else:
            # 过滤无邮箱客户
            query = query.filter(Customer.email.isnot(None)).filter(Customer.email != '')

        # 排除已有最近发送记录的
        recent = db.session.query(EmailSentLog.customer_id).filter(
            EmailSentLog.sent_at.isnot(None)
        ).order_by(EmailSentLog.sent_at.desc()).limit(500).subquery()

        customers = query.filter(~Customer.id.in_(recent)).all()
        task.total_count = len(customers)

        interval = task.send_interval_seconds or 30
        total = task.total_count
        idx = 0

        while idx < total and task.status == 'RUNNING':
            customer = customers[idx]
            account = self._get_ready_account()

            if not account:
                task.status = 'PAUSED'
                task.notes = (task.notes or '') + f'\n[{datetime.now()}] 暂停：所有账号配额已用完'
                db.session.commit()
                break

            # 查找已有待发记录或新建
            log = EmailSentLog.query.filter_by(
                task_id=task_id,
                customer_id=customer.id,
                send_status='PENDING'
            ).first()

            if not log:
                log = EmailSentLog(
                    task_id=task_id,
                    customer_id=customer.id,
                    sender_account_id=account.id,
                    recipient_email=customer.email or '',
                    recipient_name=customer.company_name_en,
                    subject=task.subject_template or f'Partnership: Cerealia Caviar',
                    content=task.body_template or '',
                    language=task.language,
                    send_status='PENDING',
                )
                db.session.add(log)
                db.session.commit()

            # 实际发送
            success, err = self._send_via_smtp(
                account=account,
                to_email=log.recipient_email,
                to_name=log.recipient_name,
                subject=log.subject,
                body=log.content,
            )

            if success:
                log.send_status = 'SENT'
                log.sent_at = datetime.utcnow()
                task.sent_count += 1
                account.daily_sent_count = (account.daily_sent_count or 0) + 1
            else:
                log.send_status = 'FAILED'
                log.error_message = err
                task.failed_count += 1

            db.session.commit()
            idx += 1

            # 间隔等待
            time.sleep(interval)

        # 任务结束
        if task.status == 'RUNNING':
            task.status = 'COMPLETED'
            task.finished_at = datetime.utcnow()

        db.session.commit()

    def start_task(self, task_id: int):
        """启动一个发送任务（异步）"""
        with self._lock:
            task = EmailTask.query.get(task_id)
            if task and task.status in ('DRAFT', 'PAUSED'):
                task.status = 'QUEUED'
                db.session.commit()
                self._dispatch_task(task_id)
                return True
        return False

    def pause_task(self, task_id: int):
        """暂停任务"""
        task = EmailTask.query.get(task_id)
        if task and task.status == 'RUNNING':
            task.status = 'PAUSED'
            db.session.commit()
            return True
        return False

    def cancel_task(self, task_id: int):
        """取消任务"""
        task = EmailTask.query.get(task_id)
        if task and task.status in ('RUNNING', 'QUEUED', 'PAUSED'):
            task.status = 'CANCELLED'
            task.finished_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

    def get_task_progress(self, task_id: int) -> dict:
        """获取任务进度"""
        task = EmailTask.query.get(task_id)
        if not task:
            return {}
        total = task.total_count or 0
        done = task.sent_count + task.failed_count
        return {
            'id': task.id,
            'status': task.status,
            'total': total,
            'sent': task.sent_count,
            'failed': task.failed_count,
            'pending': max(0, total - done),
            'progress_pct': round(done / total * 100, 1) if total > 0 else 0,
        }


# 全局单例（在 app.py 中通过 init_app 初始化）
_email_sender = EmailSender()


def get_sender() -> EmailSender:
    return _email_sender


def init_sender(app):
    """由 app.py 调用，将 Flask app 注入 sender"""
    _email_sender.init_app(app)
