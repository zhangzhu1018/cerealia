"""
Flask 主应用入口
支持 CORS，挂载所有路由蓝图
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate

from .models import db
from .config import config_by_name, Config


def create_app(config_name=None):
    """工厂函数：创建并配置 Flask 应用"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # 初始化数据库 + 迁移
    db.init_app(app)
    migrate = Migrate(app, db)  # Alembic 数据库迁移

    # 启用 CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', '*'),
            "supports_credentials": True
        }
    })

    # API 限流（保护 DeepSeek API 不被打爆）
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per hour", "50 per minute"],
        storage_uri="memory://",
    )
    limiter.init_app(app)

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

    # ── 对所有业务 Blueprint 添加登录验证 ──────────────────────────────────
    from .routes.auth import _uid_from_token
    from flask import request as _req
    from flask import jsonify as _json

    _protected_prefixes = (
        '/api/customers', '/api/scoring', '/api/emails',
        '/api/search', '/api/activities', '/api/dashboard'
    )
    _public_paths = ('/api/search/countries',)

    @app.before_request
    def _guard_all():
        # CORS 预检请求（OPTIONS）直接放行，否则浏览器报 Network Error
        if _req.method == 'OPTIONS':
            return None
        path = _req.path
        if not any(path.startswith(p) for p in _protected_prefixes):
            return None
        if path in _public_paths:
            return None
        auth = _req.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return _json({'code': 401, 'message': '请先登录'}), 401
        uid = _uid_from_token(auth[7:])
        if uid is None:
            return _json({'code': 401, 'message': '登录已过期'}), 401
        return None

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

    # 数据库初始化
    with app.app_context():
        try:
            if os.getenv('SKIP_MIGRATIONS'):
                db.create_all()
            else:
                from flask_migrate import upgrade as _upgrade
                _upgrade()
            from .routes.auth import ensure_admin as _ensure_admin
            _ensure_admin()
            _seed_countries()
        except Exception as e:
            print(f"[WARNING] DB初始化: {e}, 重试create_all")
            try:
                db.create_all()
                from .routes.auth import ensure_admin as _ensure_admin
                _ensure_admin()
                _seed_countries()
            except Exception as e2:
                print(f"[ERROR] 数据库失败: {e2}")

    return app


def _seed_countries():
    """启动时自动从 crawler_service 种子国家数据到数据库"""
    import hashlib
    from .models import Country
    from .services.crawler_service import _CAVIAR_COUNTRIES

    # 国家名 → ISO 代码 & 中文名 映射（完整版）
    _COUNTRY_META = {
        # Tier 1
        'France':          {'code': 'FR', 'name_cn': '法国',       'lang': 'french'},
        'USA':             {'code': 'US', 'name_cn': '美国',       'lang': 'english'},
        'Italy':           {'code': 'IT', 'name_cn': '意大利',     'lang': 'italian'},
        'Germany':         {'code': 'DE', 'name_cn': '德国',       'lang': 'german'},
        'Spain':           {'code': 'ES', 'name_cn': '西班牙',     'lang': 'spanish'},
        'Japan':           {'code': 'JP', 'name_cn': '日本',       'lang': 'japanese'},
        'United Kingdom':  {'code': 'GB', 'name_cn': '英国',       'lang': 'english'},
        'Switzerland':     {'code': 'CH', 'name_cn': '瑞士',       'lang': 'german'},
        'UAE':             {'code': 'AE', 'name_cn': '阿联酋',     'lang': 'arabic'},
        'Netherlands':     {'code': 'NL', 'name_cn': '荷兰',       'lang': 'dutch'},
        'Belgium':         {'code': 'BE', 'name_cn': '比利时',     'lang': 'french'},
        'Australia':       {'code': 'AU', 'name_cn': '澳大利亚',   'lang': 'english'},
        'Canada':          {'code': 'CA', 'name_cn': '加拿大',     'lang': 'english'},
        'Singapore':       {'code': 'SG', 'name_cn': '新加坡',     'lang': 'english'},
        'Hong Kong':       {'code': 'HK', 'name_cn': '香港',       'lang': 'chinese'},
        # Tier 2
        'Russia':          {'code': 'RU', 'name_cn': '俄罗斯',     'lang': 'russian'},
        'China':           {'code': 'CN', 'name_cn': '中国',       'lang': 'chinese'},
        'South Korea':     {'code': 'KR', 'name_cn': '韩国',       'lang': 'korean'},
        'Saudi Arabia':    {'code': 'SA', 'name_cn': '沙特阿拉伯',  'lang': 'arabic'},
        'Qatar':           {'code': 'QA', 'name_cn': '卡塔尔',     'lang': 'arabic'},
        'Kuwait':          {'code': 'KW', 'name_cn': '科威特',     'lang': 'arabic'},
        'Bahrain':         {'code': 'BH', 'name_cn': '巴林',       'lang': 'arabic'},
        'Oman':            {'code': 'OM', 'name_cn': '阿曼',       'lang': 'arabic'},
        'Portugal':        {'code': 'PT', 'name_cn': '葡萄牙',     'lang': 'portuguese'},
        'Greece':          {'code': 'GR', 'name_cn': '希腊',       'lang': 'greek'},
        'Austria':         {'code': 'AT', 'name_cn': '奥地利',     'lang': 'german'},
        'Sweden':          {'code': 'SE', 'name_cn': '瑞典',       'lang': 'swedish'},
        'Norway':          {'code': 'NO', 'name_cn': '挪威',       'lang': 'norwegian'},
        'Denmark':         {'code': 'DK', 'name_cn': '丹麦',       'lang': 'danish'},
        'Finland':         {'code': 'FI', 'name_cn': '芬兰',       'lang': 'finnish'},
        'Ireland':         {'code': 'IE', 'name_cn': '爱尔兰',    'lang': 'english'},
        'Poland':          {'code': 'PL', 'name_cn': '波兰',       'lang': 'polish'},
        'Czech Republic':  {'code': 'CZ', 'name_cn': '捷克',       'lang': 'czech'},
        'Hungary':         {'code': 'HU', 'name_cn': '匈牙利',     'lang': 'hungarian'},
        'Romania':         {'code': 'RO', 'name_cn': '罗马尼亚',   'lang': 'romanian'},
        'Bulgaria':        {'code': 'BG', 'name_cn': '保加利亚',   'lang': 'bulgarian'},
        'Croatia':         {'code': 'HR', 'name_cn': '克罗地亚',   'lang': 'croatian'},
        'Serbia':          {'code': 'RS', 'name_cn': '塞尔维亚',   'lang': 'serbian'},
        'Turkey':          {'code': 'TR', 'name_cn': '土耳其',     'lang': 'turkish'},
        'India':           {'code': 'IN', 'name_cn': '印度',       'lang': 'hindi'},
        'Thailand':        {'code': 'TH', 'name_cn': '泰国',       'lang': 'thai'},
        'Vietnam':         {'code': 'VN', 'name_cn': '越南',       'lang': 'vietnamese'},
        'Malaysia':        {'code': 'MY', 'name_cn': '马来西亚',   'lang': 'malay'},
        'Indonesia':       {'code': 'ID', 'name_cn': '印尼',       'lang': 'indonesian'},
        'Philippines':     {'code': 'PH', 'name_cn': '菲律宾',     'lang': 'filipino'},
        'Brazil':          {'code': 'BR', 'name_cn': '巴西',       'lang': 'portuguese'},
        'Argentina':       {'code': 'AR', 'name_cn': '阿根廷',     'lang': 'spanish'},
        'Mexico':          {'code': 'MX', 'name_cn': '墨西哥',     'lang': 'spanish'},
        'Chile':           {'code': 'CL', 'name_cn': '智利',       'lang': 'spanish'},
        'South Africa':    {'code': 'ZA', 'name_cn': '南非',       'lang': 'english'},
        'Egypt':           {'code': 'EG', 'name_cn': '埃及',       'lang': 'arabic'},
        'Israel':          {'code': 'IL', 'name_cn': '以色列',     'lang': 'hebrew'},
        'New Zealand':     {'code': 'NZ', 'name_cn': '新西兰',     'lang': 'english'},
        'Taiwan':          {'code': 'TW', 'name_cn': '台湾',       'lang': 'chinese'},
        'Morocco':         {'code': 'MA', 'name_cn': '摩洛哥',     'lang': 'arabic'},
        'Luxembourg':      {'code': 'LU', 'name_cn': '卢森堡',     'lang': 'french'},
        'Lebanon':         {'code': 'LB', 'name_cn': '黎巴嫩',     'lang': 'arabic'},
        'Jordan':          {'code': 'JO', 'name_cn': '约旦',       'lang': 'arabic'},
        'Ukraine':         {'code': 'UA', 'name_cn': '乌克兰',     'lang': 'ukrainian'},
        'Slovenia':        {'code': 'SI', 'name_cn': '斯洛文尼亚', 'lang': 'slovenian'},
        'Slovakia':        {'code': 'SK', 'name_cn': '斯洛伐克',   'lang': 'slovak'},
        # Tier 3
        'Kazakhstan':      {'code': 'KZ', 'name_cn': '哈萨克斯坦', 'lang': 'kazakh'},
        'Uzbekistan':      {'code': 'UZ', 'name_cn': '乌兹别克斯坦', 'lang': 'uzbek'},
        'Turkmenistan':    {'code': 'TM', 'name_cn': '土库曼斯坦', 'lang': 'turkmen'},
        'Azerbaijan':      {'code': 'AZ', 'name_cn': '阿塞拜疆',  'lang': 'azerbaijani'},
        'Georgia':         {'code': 'GE', 'name_cn': '格鲁吉亚',   'lang': 'georgian'},
        'Armenia':         {'code': 'AM', 'name_cn': '亚美尼亚',   'lang': 'armenian'},
        'Belarus':         {'code': 'BY', 'name_cn': '白俄罗斯',   'lang': 'belarusian'},
        'Moldova':         {'code': 'MD', 'name_cn': '摩尔多瓦',   'lang': 'romanian'},
        'Albania':         {'code': 'AL', 'name_cn': '阿尔巴尼亚', 'lang': 'albanian'},
        'Bosnia and Herzegovina': {'code': 'BA', 'name_cn': '波黑', 'lang': 'bosnian'},
        'Montenegro':      {'code': 'ME', 'name_cn': '黑山',       'lang': 'montenegrin'},
        'North Macedonia': {'code': 'MK', 'name_cn': '北马其顿',  'lang': 'macedonian'},
        'Latvia':          {'code': 'LV', 'name_cn': '拉脱维亚',   'lang': 'latvian'},
        'Lithuania':       {'code': 'LT', 'name_cn': '立陶宛',    'lang': 'lithuanian'},
        'Estonia':         {'code': 'EE', 'name_cn': '爱沙尼亚',  'lang': 'estonian'},
        'Iceland':         {'code': 'IS', 'name_cn': '冰岛',       'lang': 'icelandic'},
        'Malta':           {'code': 'MT', 'name_cn': '马耳他',    'lang': 'maltese'},
        'Cyprus':          {'code': 'CY', 'name_cn': '塞浦路斯',  'lang': 'greek'},
        'Andorra':         {'code': 'AD', 'name_cn': '安道尔',    'lang': 'catalan'},
        'Monaco':          {'code': 'MC', 'name_cn': '摩纳哥',    'lang': 'french'},
        'Liechtenstein':    {'code': 'LI', 'name_cn': '列支敦士登', 'lang': 'german'},
        'San Marino':      {'code': 'SM', 'name_cn': '圣马力诺',  'lang': 'italian'},
        'Vatican City':    {'code': 'VA', 'name_cn': '梵蒂冈',    'lang': 'italian'},
        'Gibraltar':       {'code': 'GI', 'name_cn': '直布罗陀',  'lang': 'english'},
        'Greenland':       {'code': 'GL', 'name_cn': '格陵兰',    'lang': 'danish'},
        'Faroe Islands':   {'code': 'FO', 'name_cn': '法罗群岛',  'lang': 'faroese'},
        'Jersey':          {'code': 'JE', 'name_cn': '泽西岛',    'lang': 'english'},
        'Guernsey':        {'code': 'GG', 'name_cn': '根西岛',    'lang': 'english'},
        'Isle of Man':     {'code': 'IM', 'name_cn': '马恩岛',    'lang': 'english'},
        'Pakistan':        {'code': 'PK', 'name_cn': '巴基斯坦',  'lang': 'urdu'},
        'Bangladesh':      {'code': 'BD', 'name_cn': '孟加拉国',  'lang': 'bengali'},
        'Sri Lanka':       {'code': 'LK', 'name_cn': '斯里兰卡',  'lang': 'sinhala'},
        'Nepal':           {'code': 'NP', 'name_cn': '尼泊尔',    'lang': 'nepali'},
        'Bhutan':          {'code': 'BT', 'name_cn': '不丹',       'lang': 'dzongkha'},
        'Maldives':        {'code': 'MV', 'name_cn': '马尔代夫',  'lang': 'dhivehi'},
        'Afghanistan':     {'code': 'AF', 'name_cn': '阿富汗',    'lang': 'pashto'},
        'Iran':            {'code': 'IR', 'name_cn': '伊朗',       'lang': 'persian'},
        'Iraq':            {'code': 'IQ', 'name_cn': '伊拉克',    'lang': 'arabic'},
        'Syria':           {'code': 'SY', 'name_cn': '叙利亚',   'lang': 'arabic'},
        'Yemen':           {'code': 'YE', 'name_cn': '也门',       'lang': 'arabic'},
        'Libya':           {'code': 'LY', 'name_cn': '利比亚',   'lang': 'arabic'},
        'Tunisia':         {'code': 'TN', 'name_cn': '突尼斯',   'lang': 'arabic'},
        'Algeria':         {'code': 'DZ', 'name_cn': '阿尔及利亚', 'lang': 'arabic'},
        'Sudan':           {'code': 'SD', 'name_cn': '苏丹',      'lang': 'arabic'},
        'Ethiopia':        {'code': 'ET', 'name_cn': '埃塞俄比亚', 'lang': 'amharic'},
        'Kenya':           {'code': 'KE', 'name_cn': '肯尼亚',   'lang': 'swahili'},
        'Uganda':          {'code': 'UG', 'name_cn': '乌干达',   'lang': 'swahili'},
        'Tanzania':        {'code': 'TZ', 'name_cn': '坦桑尼亚', 'lang': 'swahili'},
        'Rwanda':          {'code': 'RW', 'name_cn': '卢旺达',   'lang': 'kinyarwanda'},
        'Burundi':         {'code': 'BI', 'name_cn': '布隆迪',   'lang': 'kirundi'},
        'Democratic Republic of the Congo': {'code': 'CD', 'name_cn': '刚果民主共和国', 'lang': 'french'},
        'Republic of the Congo': {'code': 'CG', 'name_cn': '刚果共和国', 'lang': 'french'},
        'Gabon':           {'code': 'GA', 'name_cn': '加蓬',      'lang': 'french'},
        'Cameroon':        {'code': 'CM', 'name_cn': '喀麦隆',   'lang': 'french'},
        'Nigeria':         {'code': 'NG', 'name_cn': '尼日利亚', 'lang': 'english'},
        'Ghana':           {'code': 'GH', 'name_cn': '加纳',      'lang': 'english'},
        'Ivory Coast':     {'code': 'CI', 'name_cn': '科特迪瓦', 'lang': 'french'},
        'Senegal':         {'code': 'SN', 'name_cn': '塞内加尔', 'lang': 'french'},
        'Mali':            {'code': 'ML', 'name_cn': '马里',      'lang': 'french'},
        'Niger':           {'code': 'NE', 'name_cn': '尼日尔',   'lang': 'french'},
        'Burkina Faso':    {'code': 'BF', 'name_cn': '布基纳法索', 'lang': 'french'},
        'Angola':          {'code': 'AO', 'name_cn': '安哥拉',   'lang': 'portuguese'},
        'Zambia':          {'code': 'ZM', 'name_cn': '赞比亚',   'lang': 'english'},
        'Zimbabwe':        {'code': 'ZW', 'name_cn': '津巴布韦', 'lang': 'english'},
        'Mozambique':      {'code': 'MZ', 'name_cn': '莫桑比克', 'lang': 'portuguese'},
        'Madagascar':      {'code': 'MG', 'name_cn': '马达加斯加', 'lang': 'malagasy'},
        'Mauritius':       {'code': 'MU', 'name_cn': '毛里求斯', 'lang': 'english'},
        'Seychelles':      {'code': 'SC', 'name_cn': '塞舌尔',   'lang': 'english'},
        'Namibia':         {'code': 'NA', 'name_cn': '纳米比亚', 'lang': 'english'},
        'Botswana':        {'code': 'BW', 'name_cn': '博茨瓦纳', 'lang': 'english'},
        'Lesotho':         {'code': 'LS', 'name_cn': '莱索托',   'lang': 'english'},
        'Eswatini':        {'code': 'SZ', 'name_cn': '斯威士兰', 'lang': 'swazi'},
        'Malawi':          {'code': 'MW', 'name_cn': '马拉维',   'lang': 'english'},
        'Jamaica':         {'code': 'JM', 'name_cn': '牙买加',   'lang': 'english'},
        'Trinidad and Tobago': {'code': 'TT', 'name_cn': '特立尼达和多巴哥', 'lang': 'english'},
        'Barbados':        {'code': 'BB', 'name_cn': '巴巴多斯', 'lang': 'english'},
        'Bahamas':         {'code': 'BS', 'name_cn': '巴哈马',   'lang': 'english'},
        'Cuba':            {'code': 'CU', 'name_cn': '古巴',      'lang': 'spanish'},
        'Dominican Republic': {'code': 'DO', 'name_cn': '多米尼加', 'lang': 'spanish'},
        'Puerto Rico':     {'code': 'PR', 'name_cn': '波多黎各', 'lang': 'spanish'},
        'Costa Rica':      {'code': 'CR', 'name_cn': '哥斯达黎加', 'lang': 'spanish'},
        'Panama':          {'code': 'PA', 'name_cn': '巴拿马',   'lang': 'spanish'},
        'Guatemala':       {'code': 'GT', 'name_cn': '危地马拉', 'lang': 'spanish'},
        'Honduras':        {'code': 'HN', 'name_cn': '洪都拉斯', 'lang': 'spanish'},
        'El Salvador':     {'code': 'SV', 'name_cn': '萨尔瓦多', 'lang': 'spanish'},
        'Nicaragua':       {'code': 'NI', 'name_cn': '尼加拉瓜', 'lang': 'spanish'},
        'Colombia':        {'code': 'CO', 'name_cn': '哥伦比亚', 'lang': 'spanish'},
        'Venezuela':        {'code': 'VE', 'name_cn': '委内瑞拉', 'lang': 'spanish'},
        'Ecuador':         {'code': 'EC', 'name_cn': '厄瓜多尔', 'lang': 'spanish'},
        'Peru':            {'code': 'PE', 'name_cn': '秘鲁',      'lang': 'spanish'},
        'Bolivia':         {'code': 'BO', 'name_cn': '玻利维亚', 'lang': 'spanish'},
        'Paraguay':        {'code': 'PY', 'name_cn': '巴拉圭',   'lang': 'spanish'},
        'Uruguay':         {'code': 'UY', 'name_cn': '乌拉圭',   'lang': 'spanish'},
        'Myanmar':         {'code': 'MM', 'name_cn': '缅甸',      'lang': 'burmese'},
        'Cambodia':        {'code': 'KH', 'name_cn': '柬埔寨',   'lang': 'khmer'},
        'Laos':            {'code': 'LA', 'name_cn': '老挝',      'lang': 'lao'},
        'Mongolia':        {'code': 'MN', 'name_cn': '蒙古',      'lang': 'mongolian'},
        'North Korea':     {'code': 'KP', 'name_cn': '朝鲜',      'lang': 'korean'},
        'Brunei':          {'code': 'BN', 'name_cn': '文莱',      'lang': 'malay'},
        'Timor-Leste':     {'code': 'TL', 'name_cn': '东帝汶',   'lang': 'portuguese'},
        'Papua New Guinea': {'code': 'PG', 'name_cn': '巴布亚新几内亚', 'lang': 'english'},
        'Fiji':            {'code': 'FJ', 'name_cn': '斐济',      'lang': 'english'},
        'Samoa':           {'code': 'WS', 'name_cn': '萨摩亚',   'lang': 'samoan'},
        'Tonga':           {'code': 'TO', 'name_cn': '汤加',      'lang': 'tongan'},
        'Vanuatu':         {'code': 'VU', 'name_cn': '瓦努阿图', 'lang': 'bislama'},
        'Solomon Islands': {'code': 'SB', 'name_cn': '所罗门群岛', 'lang': 'english'},
        'Micronesia':      {'code': 'FM', 'name_cn': '密克罗尼西亚', 'lang': 'english'},
        'Palau':           {'code': 'PW', 'name_cn': '帕劳',      'lang': 'english'},
        'Marshall Islands': {'code': 'MH', 'name_cn': '马绍尔群岛', 'lang': 'english'},
        'Nauru':           {'code': 'NR', 'name_cn': '瑙鲁',      'lang': 'nauran'},
        'Tuvalu':          {'code': 'TV', 'name_cn': '图瓦卢',   'lang': 'tuvaluan'},
        'Kyrgyzstan':      {'code': 'KG', 'name_cn': '吉尔吉斯斯坦', 'lang': 'kyrgyz'},
        'Tajikistan':      {'code': 'TJ', 'name_cn': '塔吉克斯坦', 'lang': 'tajik'},
        'Macau':           {'code': 'MO', 'name_cn': '澳门',      'lang': 'chinese'},
    }

    all_country_names = [c[0] for c in _CAVIAR_COUNTRIES]
    tier_map = {c[0]: c[1] for c in _CAVIAR_COUNTRIES}

    existing = {c.name_en for c in Country.query.all()}
    existing_codes = {c.code for c in Country.query.all()}

    added = 0
    for name in all_country_names:
        if name in existing:
            continue
        meta = _COUNTRY_META.get(name, {})
        code = meta.get('code')
        if not code or code in existing_codes:
            # 兜底：用 country name 前缀 + hash 生成唯一代码
            code = name[:3].upper()[:2] + format(hash(name) % 900 + 100, '03d')
            if code in existing_codes:
                code = name[:2].upper() + 'X'
            if code in existing_codes:
                code = name[:4].upper()[:4]
        country = Country(
            code=code,
            name_en=name,
            name_cn=meta.get('name_cn', name),
            official_language=meta.get('lang', 'english'),
            priority=11 - tier_map.get(name, 3),
        )
        db.session.add(country)
        existing_codes.add(code)
        added += 1

    if added > 0:
        db.session.commit()
        print(f"[Countries] 已自动种子 {added} 个国家数据到数据库")


# WSGI 入口（gunicorn 使用）
app = create_app()
