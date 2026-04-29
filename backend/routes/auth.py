"""
认证路由 - 登录 / 登出 / 当前用户
"""
import hashlib
import secrets
import threading
from flask import Blueprint, request, jsonify
from ..models import db, User

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# 内存 token → user_id 映射（生产环境建议用 Redis）
_token_store: dict[str, int] = {}
_token_lock = threading.Lock()


def _make_token(uid: int) -> str:
    tok = secrets.token_hex(32)
    with _token_lock:
        _token_store[tok] = uid
    return tok


def _uid_from_token(token: str) -> int | None:
    with _token_lock:
        return _token_store.get(token)


def _revoke_token(token: str):
    with _token_lock:
        _token_store.pop(token, None)


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


def hash_password(password: str) -> str:
    """简单 SHA256 哈希（生产环境建议用 bcrypt）"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


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
