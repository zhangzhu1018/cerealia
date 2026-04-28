"""
背调评分路由
POST /scoring/calculate  - 计算单个公司背调评分
POST /scoring/batch      - 批量计算
GET  /scoring/history/<customer_id> - 查询客户评分历史
"""
from flask import Blueprint, request, jsonify
from ..models import db, Customer, BackgroundCheck
from ..services.scoring_service import BackgroundScoringEngine, BatchScoringProcessor
from ..services.activity_service import log_score_calculated

bp = Blueprint('scoring', __name__, url_prefix='/scoring')


@bp.route('/calculate', methods=['POST'])
def calculate_score():
    """
    POST /scoring/calculate
    Body: {
        company_data: {
            has_import_history: bool,
            import_frequency: int,
            import_volume: float,
            employee_count: int,
            annual_revenue: float,
            description: str,
            company_name_en: str,
            has_cites_license: bool,
            has_haccp_cert: bool,
            other_certifications: list,
            current_suppliers: str,
            has_previous_contact: bool,
            social_followers: int,
            social_links: bool
        },
        customer_id: int (optional, 关联到已有客户)
    }
    """
    data = request.get_json()
    if not data or 'company_data' not in data:
        return jsonify({'code': 400, 'message': '缺少 company_data 参数'}), 400

    company_data = data['company_data']
    customer_id = data.get('customer_id')

    engine = BackgroundScoringEngine()
    result = engine.calculate_as_dict(company_data)

    # 如果关联了客户，同步更新客户表评分字段并保存背调数据
    if customer_id:
        customer = Customer.query.get(customer_id)
        if customer:
            customer.background_score = result['total_score']
            customer.import_trade_score = result['import_trade_score']
            customer.company_scale_score = result['company_scale_score']
            customer.market_position_score = result['market_position_score']
            customer.qualification_score = result['qualification_score']
            customer.cooperation_potential_score = result['cooperation_potential_score']
            customer.social_media_score = result['social_media_score']
            customer.responsiveness_score = result['responsiveness_score']

            # 保存/更新背调记录
            bg = BackgroundCheck.query.filter_by(customer_id=customer_id).first()
            if bg:
                _update_bg_from_data(bg, company_data)
            else:
                bg = BackgroundCheck(customer_id=customer_id)
                _update_bg_from_data(bg, company_data)
                db.session.add(bg)

            db.session.commit()
            result['customer_id'] = customer_id
            result['synced'] = True

            # 自动记录评分日志
            log_score_calculated(
                customer_id=customer_id,
                company_name=customer.company_name_en,
                score=result['total_score'],
                detail={
                    'import_trade_score': result['import_trade_score'],
                    'company_scale_score': result['company_scale_score'],
                    'market_position_score': result['market_position_score'],
                }
            )

    return jsonify({'code': 0, 'data': result})


@bp.route('/batch', methods=['POST'])
def batch_calculate():
    """
    POST /scoring/batch
    Body: { companies: [company_data, ...] }
    """
    data = request.get_json()
    if not data or 'companies' not in data:
        return jsonify({'code': 400, 'message': '缺少 companies 参数'}), 400

    processor = BatchScoringProcessor()
    results = []
    for i, company in enumerate(data['companies']):
        r = processor.engine.calculate_as_dict(company)
        r['index'] = i
        results.append(r)

    return jsonify({
        'code': 0,
        'data': {
            'results': results,
            'total': len(results),
            'average_score': round(sum(r['total_score'] for r in results) / len(results), 2) if results else 0
        }
    })


@bp.route('/history/<int:customer_id>', methods=['GET'])
def get_score_history(customer_id):
    """
    GET /scoring/history/<customer_id> - 获取客户评分历史
    返回格式兼容前端 CustomerDetail：
    [{ grade, total_score, created_at, import_trade_score, ... }, ...]
    """
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'code': 404, 'message': '客户不存在'}), 404

    bg = BackgroundCheck.query.filter_by(customer_id=customer_id).first()

    # 计算当前等级
    def _calc_grade(score):
        if score is None or score < 40:
            return 'E'
        elif score < 55:
            return 'D'
        elif score < 70:
            return 'C'
        elif score < 85:
            return 'B'
        else:
            return 'A'

    current_score = float(customer.background_score) if customer.background_score else 0

    # 构建评分历史数组（包含当前评分 + 背景检查数据）
    score_records = [{
        'id': bg.id if bg else None,
        'customer_id': customer_id,
        'total_score': current_score,
        'grade': _calc_grade(current_score),
        'import_trade_score': customer.import_trade_score,
        'company_scale_score': customer.company_scale_score,
        'market_position_score': customer.market_position_score,
        'qualification_score': customer.qualification_score,
        'cooperation_potential_score': customer.cooperation_potential_score,
        'social_media_score': customer.social_media_score,
        'responsiveness_score': customer.responsiveness_score,
        'created_at': (bg.scrape_date if bg else customer.updated_at).isoformat()
                       if (bg.scrape_date if bg else customer.updated_at) else None,
    }]

    return jsonify({
        'code': 0,
        'data': {
            'customer_id': customer_id,
            'current_score': current_score,
            'current_grade': _calc_grade(current_score),
            'scores': score_records,
            'background_check': {
                'founded_year': bg.founded_year if bg else None,
                'employee_count': bg.employee_count if bg else None,
                'annual_revenue': float(bg.annual_revenue) if bg and bg.annual_revenue else None,
                'has_import_history': bg.has_import_history if bg else None,
                'has_cites_license': bg.has_cites_license if bg else None,
                'has_haccp_cert': bg.has_haccp_cert if bg else None,
                'scrape_date': bg.scrape_date.isoformat() if bg and bg.scrape_date else None,
            } if bg else None
        }
    })


def _update_bg_from_data(bg: BackgroundCheck, data: dict):
    """将 company_data 字典更新到 BackgroundCheck 模型"""
    bg.founded_year = data.get('founded_year')
    bg.employee_count = data.get('employee_count')
    bg.annual_revenue = data.get('annual_revenue')
    bg.has_import_history = data.get('has_import_history', False)
    bg.last_import_date = data.get('last_import_date')
    bg.import_frequency = str(data.get('import_frequency', ''))
    bg.typical_import_volume = data.get('import_volume')
    bg.current_suppliers = data.get('current_suppliers', '')
    bg.has_cites_license = data.get('has_cites_license', False)
    bg.has_haccp_cert = data.get('has_haccp_cert', False)
    bg.other_certifications = data.get('other_certifications', [])
    bg.market_segment = data.get('market_segment', '')
    bg.price_position = data.get('price_position', '')
    bg.distribution_channels = data.get('distribution_channels', [])
    bg.linkedin_followers = data.get('linkedin_followers', 0)
    bg.instagram_followers = data.get('instagram_followers', 0)
    bg.raw_data = data.get('raw_data')
    bg.scrape_date = data.get('scrape_date')
