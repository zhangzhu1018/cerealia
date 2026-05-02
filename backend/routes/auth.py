"""
认证路由 - 登录 / 登出 / 当前用户
Token 持久化到 DB（auth_tokens 表），支持 gunicorn 多 worker
"""
import hashlib
import secrets
from flask import Blueprint, request, jsonify
from ..models import db, User, AuthToken

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _make_token(uid: int) -> str:
    tok = secrets.token_hex(32)
    db.session.add(AuthToken(token=tok, user_id=uid))
    db.session.commit()
    return tok


def _uid_from_token(token: str) -> int | None:
    at = AuthToken.query.filter_by(token=token).first()
    return at.user_id if at else None


def _revoke_token(token: str):
    AuthToken.query.filter_by(token=token).delete()
    db.session.commit()


# ── login_required 装饰器 ──────────────────────────────────────────────────
import functools

def login_required(f):
    """装饰器：要求请求携带有效的 Authorization: Bearer <token>"""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '请先登录'}), 401
        uid = _uid_from_token(auth[7:])
        if uid is None:
            return jsonify({'code': 401, 'message': '登录已过期，请重新登录'}), 401
        # 将 user_id 注入请求上下文
        request._current_user_id = uid
        return f(*args, **kwargs)
    return wrapper


import bcrypt

def hash_password(password: str) -> str:
    """bcrypt 加密（安全替代 SHA256）"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码：bcrypt 优先，兼容旧 SHA256 哈希"""
    # bcrypt 哈希以 $2b$ 开头
    if password_hash.startswith('$2') and len(password_hash) >= 50:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    # 旧 SHA256 fallback（迁移后移除）
    return hashlib.sha256(password.encode()).hexdigest() == password_hash


def ensure_compatible_password(user) -> None:
    """如果用户密码仍是 SHA256，自动迁移到 bcrypt"""
    from ..models import db
    if user.password_hash and not user.password_hash.startswith('$2'):
        user.password_hash = bcrypt.hashpw(user.password_hash.encode(), bcrypt.gensalt()).decode()
        db.session.commit()


@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求格式错误'}), 400

    # 支持 email 或 username 登录
    identifier = data.get('email', '').strip() or data.get('username', '').strip()
    password = data.get('password', '')

    if not identifier or not password:
        return jsonify({'code': 400, 'message': '邮箱和密码不能为空'}), 400

    user = User.query.filter_by(username=identifier, is_active=True).first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({'code': 401, 'message': '邮箱或密码错误'}), 401

    token = _make_token(user.id)
    return jsonify({
        'code': 200,
        'data': {
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'nickname': user.nickname,
                'role': user.role
            }
        }
    })


@bp.route('/logout', methods=['POST'])
def logout():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        _revoke_token(auth[7:])
    return jsonify({'code': 200, 'message': '已登出'})


@bp.route('/me', methods=['GET'])
def me():
    """获取当前登录用户（前端 header 传 Authorization: Bearer <token>）"""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'code': 401, 'message': '未登录'}), 401

    uid = _uid_from_token(auth[7:])
    if uid is None:
        return jsonify({'code': 401, 'message': '登录已过期，请重新登录'}), 401

    user = db.session.get(User, uid)
    if not user or not user.is_active:
        return jsonify({'code': 401, 'message': '用户不存在或已禁用'}), 401

    return jsonify({
        'code': 200,
        'data': {
            'id': user.id,
            'username': user.username,
            'nickname': user.nickname,
            'role': user.role
        }
    })


def ensure_admin():
    """启动时确保存在管理员账号（邮箱格式）"""
    admin_email = 'JooCerealiaCaviar@gmail.com'
    admin = User.query.filter_by(username=admin_email).first()
    if not admin:
        admin = User(
            username=admin_email,
            password_hash=hash_password('caviar2024'),
            nickname='Administrator',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print(f"[Auth] 默认管理员账号已创建: {admin_email} / caviar2024")
    else:
        print("[Auth] 管理员账号已存在")
