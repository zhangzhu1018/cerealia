"""
认证路由 - 登录 / 登出 / 当前用户
"""
import hashlib
import secrets
from flask import Blueprint, request, jsonify
from ..models import db, User

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


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

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400

    user = User.query.filter_by(username=username, is_active=True).first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401

    # 生成简单 session token
    token = secrets.token_hex(32)
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
    return jsonify({'code': 200, 'message': '已登出'})


@bp.route('/me', methods=['GET'])
def me():
    """获取当前登录用户（前端 header 传 Authorization: Bearer <token>）"""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'code': 401, 'message': '未登录'}), 401
    # 简化版：只要有 token 就返回 admin 信息
    # 生产版应验证 token 有效性
    return jsonify({
        'code': 200,
        'data': {
            'id': 1,
            'username': 'admin',
            'nickname': 'Administrator',
            'role': 'admin'
        }
    })


def ensure_admin():
    """启动时确保存在 admin 账号"""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password_hash=hash_password('caviar2024'),
            nickname='Administrator',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("[Auth] 默认管理员账号已创建: admin / caviar2024")
    else:
        print("[Auth] 管理员账号已存在")
