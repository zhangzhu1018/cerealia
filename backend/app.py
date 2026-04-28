"""
Flask 主应用入口
支持 CORS，挂载所有路由蓝图
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from .models import db
from .config import config_by_name, Config


def create_app(config_name=None):
    """工厂函数：创建并配置 Flask 应用"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # 初始化数据库
    db.init_app(app)

    # 启用 CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', '*'),
            "supports_credentials": True
        }
    })

    # 注册蓝图
    from .routes.customers import bp as customers_bp
    from .routes.scoring import bp as scoring_bp
    from .routes.emails import bp as emails_bp
    from .routes.search import bp as search_bp
    from .routes.activities import bp as activities_bp
    from .routes.dashboard import bp as dashboard_bp
    from .routes.auth import bp as auth_bp

    app.register_blueprint(customers_bp, url_prefix='/api/customers')
    app.register_blueprint(scoring_bp, url_prefix='/api/scoring')
    app.register_blueprint(emails_bp, url_prefix='/api/emails')
    app.register_blueprint(search_bp, url_prefix='/api/search')
    app.register_blueprint(activities_bp, url_prefix='/api/activities')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # 初始化邮件发送服务（调度器）
    from .services.email_sender_service import init_sender
    init_sender(app)

    # 健康检查
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'ok', 'service': 'caviar-crm-backend'})

    # 全局错误处理
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'code': 400, 'message': '请求参数错误'}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'code': 404, 'message': '资源不存在'}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

    # 创建数据库表 + 确保 admin 账号存在
    with app.app_context():
        try:
            db.create_all()
            from .routes.auth import ensure_admin
            ensure_admin()
        except Exception as e:
            print(f"[WARNING] 数据库操作失败: {e}")

    return app


# WSGI 入口（gunicorn 使用）
app = create_app()
