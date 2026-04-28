"""
客户 CRUD 路由
GET  /customers          - 分页+筛选列表
POST /customers           - 新建客户
GET  /customers/<id>      - 获取单个客户
PUT  /customers/<id>      - 更新客户
DELETE /customers/<id>     - 删除客户
POST /customers/import    - 批量导入 Excel/CSV
GET  /customers/import/preview - 预览文件
"""
from flask import Blueprint, request, jsonify
from ..models import db, Customer, Country, CustomerType, BackgroundCheck, Product
from ..services.activity_service import (
    log_customer_created, log_customer_updated,
    log_customer_deleted, log_status_changed
)
from ..services.import_service import import_customers, preview_file

bp = Blueprint('customers', __name__, url_prefix='/customers')


@bp.route('', methods=['GET'])
def list_customers():
    """
    GET /customers
    Query params:
      page, page_size,
      country_id, customer_type_id,
      follow_up_status, priority_level,
      is_verified, min_score, max_score,
      keyword (搜索公司名)
    """
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)

    query = Customer.query

    # 筛选条件
    if request.args.get('country_id'):
        query = query.filter(Customer.country_id == request.args['country_id'])
    if request.args.get('customer_type_id'):
        query = query.filter(Customer.customer_type_id == request.args['customer_type_id'])
    if request.args.get('follow_up_status'):
        query = query.filter(Customer.follow_up_status == request.args['follow_up_status'])
    if request.args.get('priority_level'):
        query = query.filter(Customer.priority_level == request.args['priority_level'])
    if request.args.get('is_verified') is not None:
        query = query.filter(Customer.is_verified == (request.args['is_verified'] == 'true'))
    if request.args.get('min_score'):
        query = query.filter(Customer.background_score >= float(request.args['min_score']))
    if request.args.get('max_score'):
        query = query.filter(Customer.background_score <= float(request.args['max_score']))
    if request.args.get('keyword'):
        kw = f"%{request.args['keyword']}%"
        query = query.filter(
            Customer.company_name_en.ilike(kw) |
            Customer.company_name_local.ilike(kw)
        )

    # 按产品名或 HS CODE 搜索
    if request.args.get('product_name'):
        kw = f"%{request.args['product_name']}%"
        query = query.join(Product, Customer.products).filter(
            Product.product_name.ilike(kw) | Product.product_name_en.ilike(kw)
        )
    if request.args.get('hs_code'):
        kw = f"%{request.args['hs_code']}%"
        query = query.join(Product, Customer.products).filter(
            Product.hs_code.ilike(kw)
        )

    query = query.order_by(Customer.background_score.desc(), Customer.created_at.desc())
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)

    return jsonify({
        'code': 0,
        'data': {
            'items': [_customer_to_dict(c) for c in pagination.items],
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'pages': pagination.pages
        }
    })


@bp.route('', methods=['POST'])
def create_customer():
    """POST /customers - 新建客户"""
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    required_fields = ['company_name_en']
    missing = [f for f in required_fields if f not in data or not data[f]]
    if missing:
        return jsonify({'code': 400, 'message': f'缺少必填字段: {", ".join(missing)}'}), 400

    # country_name 解析为 country_id
    country_id = data.get('country_id')
    country_name = data.get('country_name')
    if not country_id and country_name:
        c = Country.query.filter(
            db.or_(
                db.func.lower(Country.name_en) == country_name.strip().lower(),
                db.func.lower(Country.name_cn) == country_name.strip().lower(),
                db.func.lower(Country.code) == country_name.strip().lower(),
            )
        ).first()
        country_id = c.id if c else None

    customer = Customer(
        company_name_en=data['company_name_en'],
        company_name_local=data.get('company_name_local'),
        country_id=country_id,
        city=data.get('city'),
        website=data.get('website'),
        email=data.get('email'),
        phone=data.get('phone'),
        linkedin_url=data.get('linkedin_url'),
        social_media=data.get('social_media'),
        contact_name=data.get('contact_name'),
        address=data.get('address'),
        customer_type_id=data.get('customer_type_id'),
        follow_up_status=data.get('follow_up_status', 'NEW'),
        priority_level=data.get('priority_level', 'MEDIUM'),
        notes=data.get('notes'),
        tags=data.get('tags'),
        search_source=data.get('search_source'),
        created_by=data.get('created_by'),
        is_collected=data.get('is_collected', False),
    )
    db.session.add(customer)
    db.session.commit()

    # 自动记录操作日志
    log_customer_created(
        customer,
        operator=request.headers.get('X-Operator', 'system'),
        ip=request.remote_addr,
        ua=request.headers.get('User-Agent')
    )

    return jsonify({'code': 0, 'data': _customer_to_dict(customer), 'message': '创建成功'}), 201


@bp.route('/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """GET /customers/<id> - 获取单个客户"""
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'code': 404, 'message': '客户不存在'}), 404

    result = _customer_to_dict(customer)
    # 附加背调信息
    if customer.background_check:
        result['background_check'] = _bg_check_to_dict(customer.background_check)
    return jsonify({'code': 0, 'data': result})


@bp.route('/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """PUT /customers/<id> - 更新客户"""
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'code': 404, 'message': '客户不存在'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    # 允许更新的字段
    updatable = [
        'company_name_en', 'company_name_local', 'country_id', 'city',
        'website', 'email', 'phone', 'linkedin_url', 'social_media',
        'contact_name', 'address',
        'customer_type_id', 'is_verified',
        'background_score', 'import_trade_score', 'company_scale_score',
        'market_position_score', 'qualification_score', 'cooperation_potential_score',
        'social_media_score', 'responsiveness_score', 'country_rank',
        'is_collected', 'follow_up_status', 'priority_level', 'notes',
        'tags', 'search_source', 'last_contact_date'
    ]

    old_status = customer.follow_up_status
    changes = {}
    for field in updatable:
        if field in data:
            old_val = getattr(customer, field, None)
            new_val = data[field]
            if str(old_val) != str(new_val):
                changes[field] = {'from': old_val, 'to': new_val}
            setattr(customer, field, new_val)

    db.session.commit()

    # 自动记录操作日志
    log_customer_updated(
        customer,
        changes=changes,
        operator=request.headers.get('X-Operator', 'system'),
        ip=request.remote_addr,
        ua=request.headers.get('User-Agent')
    )

    # 单独记录状态变更
    if 'follow_up_status' in changes:
        log_status_changed(
            customer_id=customer.id,
            company_name=customer.company_name_en,
            old_status=changes['follow_up_status']['from'],
            new_status=changes['follow_up_status']['to']
        )

    return jsonify({'code': 0, 'data': _customer_to_dict(customer), 'message': '更新成功'})


@bp.route('/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """DELETE /customers/<id> - 删除客户"""
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'code': 404, 'message': '客户不存在'}), 404

    customer_name = customer.company_name_en
    db.session.delete(customer)
    db.session.commit()

    # 自动记录操作日志
    log_customer_deleted(
        customer_name=customer_name,
        customer_id=customer_id,
        operator=request.headers.get('X-Operator', 'system'),
        ip=request.remote_addr,
        ua=request.headers.get('User-Agent')
    )

    return jsonify({'code': 0, 'message': '删除成功'})


# ─── 辅助序列化函数 ───────────────────────────────────────────────────────────

def _customer_to_dict(c: Customer):
    return {
        'id': c.id,
        'company_name_en': c.company_name_en,
        'company_name_local': c.company_name_local,
        'country_id': c.country_id,
        'country_name': c.country.name_en if c.country else None,
        'city': c.city,
        'website': c.website,
        'email': c.email,
        'phone': c.phone,
        'linkedin_url': c.linkedin_url,
        'social_media': c.social_media,
        'contact_name': c.contact_name,
        'address': c.address,
        'city': c.city,
        'customer_type_id': c.customer_type_id,
        'customer_type_name': c.customer_type.type_name_en if c.customer_type else None,
        'is_verified': c.is_verified,
        'background_score': float(c.background_score) if c.background_score else 0,
        'import_trade_score': c.import_trade_score,
        'company_scale_score': c.company_scale_score,
        'market_position_score': c.market_position_score,
        'qualification_score': c.qualification_score,
        'cooperation_potential_score': c.cooperation_potential_score,
        'social_media_score': c.social_media_score,
        'responsiveness_score': c.responsiveness_score,
        'country_rank': c.country_rank,
        'is_collected': c.is_collected,
        'follow_up_status': c.follow_up_status,
        'priority_level': c.priority_level,
        'notes': c.notes,
        'tags': c.tags,
        'search_source': c.search_source,
        'created_by': c.created_by,
        'created_at': c.created_at.isoformat() if c.created_at else None,
        'updated_at': c.updated_at.isoformat() if c.updated_at else None,
        'last_contact_date': c.last_contact_date.isoformat() if c.last_contact_date else None,
        'products': [
            {'id': p.id, 'product_name': p.product_name, 'product_name_en': p.product_name_en, 'hs_code': p.hs_code}
            for p in c.products
        ] if hasattr(c, 'products') else [],
    }


def _bg_check_to_dict(bc: BackgroundCheck):
    return {
        'id': bc.id,
        'customer_id': bc.customer_id,
        'founded_year': bc.founded_year,
        'employee_count': bc.employee_count,
        'annual_revenue': float(bc.annual_revenue) if bc.annual_revenue else None,
        'has_import_history': bc.has_import_history,
        'last_import_date': bc.last_import_date.isoformat() if bc.last_import_date else None,
        'import_frequency': bc.import_frequency,
        'typical_import_volume': float(bc.typical_import_volume) if bc.typical_import_volume else None,
        'current_suppliers': bc.current_suppliers,
        'has_cites_license': bc.has_cites_license,
        'has_haccp_cert': bc.has_haccp_cert,
        'other_certifications': bc.other_certifications,
        'market_segment': bc.market_segment,
        'price_position': bc.price_position,
        'distribution_channels': bc.distribution_channels,
        'linkedin_followers': bc.linkedin_followers,
        'instagram_followers': bc.instagram_followers,
        'raw_data': bc.raw_data,
        'scrape_date': bc.scrape_date.isoformat() if bc.scrape_date else None,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  批量导入（Excel / CSV）
# ══════════════════════════════════════════════════════════════════════════════

@bp.route('/import/preview', methods=['POST'])
def import_preview():
    """
    POST /customers/import/preview
    上传文件 → 返回前5行预览 + 自动列映射结果
    """
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '请上传文件'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'code': 400, 'message': '未选择文件'}), 400

    ext = file.filename.lower().split('.')[-1]
    if ext not in ('xlsx', 'xls', 'csv'):
        return jsonify({'code': 400, 'message': '仅支持 .xlsx / .xls / .csv 文件'}), 400

    try:
        result = preview_file(file.read(), file.filename)
        return jsonify({'code': 0, 'data': result})
    except ValueError as e:
        return jsonify({'code': 400, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 500, 'message': f'预览失败: {e}'}), 500


@bp.route('/import', methods=['POST'])
def import_customers_endpoint():
    """
    POST /customers/import
    批量导入客户（支持 Excel / CSV）
    Body (multipart/form-data):
      file: 文件
      run_background_check: 是否自动评分 (默认 true)
      skip_duplicates: 是否跳过重复 (默认 true)
    """
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '请上传文件'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'code': 400, 'message': '未选择文件'}), 400

    ext = file.filename.lower().split('.')[-1]
    if ext not in ('xlsx', 'xls', 'csv'):
        return jsonify({'code': 400, 'message': '仅支持 .xlsx / .xls / .csv 文件'}), 400

    run_bg = request.form.get('run_background_check', 'true').lower() in ('true', '1', 'yes')
    skip_dup = request.form.get('skip_duplicates', 'true').lower() in ('true', '1', 'yes')
    created_by = request.form.get('created_by', 'import')

    try:
        result = import_customers(
            file_content=file.read(),
            filename=file.filename,
            run_background_check=run_bg,
            skip_duplicates=skip_dup,
            created_by=created_by,
        )
        return jsonify({
            'code': 0,
            'message': f"导入完成：成功 {result['imported']} 条，跳过 {result['skipped']} 条，失败 {result['failed']} 条",
            'data': result,
        })
    except ValueError as e:
        return jsonify({'code': 400, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 500, 'message': f'导入失败: {e}'}), 500
