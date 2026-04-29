"""
客户搜索路由
POST /search/run          - 触发爬虫搜索（全球 150+ 国家，支持本地语言二次搜索）
POST /search/run-by-name  - 按公司名搜索
GET  /search/status/<task_id> - 查询搜索任务状态
GET  /search/countries    - 获取全球可搜索国家完整列表（按活跃度排序）
GET  /search/progress     - 查询搜索进度
POST /search/reset        - 重置搜索进度
"""
from flask import Blueprint, request, jsonify
from ..services.crawler_service import CustomerSearchController, _CAVIAR_COUNTRIES
import threading
import uuid
import time

bp = Blueprint('search', __name__, url_prefix='/search')

# 简单的内存任务存储（生产环境建议用 Redis）
_search_tasks = {}

# ─── 增量搜索：追踪哪些国家已被哪些关键词搜索过 ───────────────────────────────
# key = (product_name, hs_code)  →  set of completed_country_names
_country_search_completed = {}

# ─── 全部国家列表（Tier 1 高活跃 → Tier 2 → Tier 3 低活跃）──────────────────
_ALL_COUNTRIES = [c[0] for c in _CAVIAR_COUNTRIES]
# 映射：国家名 → tier
_COUNTRY_TIER_MAP = {c[0]: c[1] for c in _CAVIAR_COUNTRIES}
# 映射：国家名 → 本地语言关键词
_COUNTRY_LOCAL_MAP = {c[0]: c[2] for c in _CAVIAR_COUNTRIES}


def _run_search_async(task_id, countries, search_type, product_name=None, hs_code=None, local_search=True):
    """后台执行搜索任务"""
    try:
        _search_tasks[task_id]['status'] = 'running'
        _search_tasks[task_id]['current_country'] = None
        _search_tasks[task_id]['country_index'] = 0
        _search_tasks[task_id]['total_countries'] = len(countries) if countries else len(_ALL_COUNTRIES)

        session_key = _search_tasks[task_id].get('session_key', (product_name or '', hs_code or ''))

        def progress_callback(current, total, country_name):
            _search_tasks[task_id]['current_country'] = country_name
            _search_tasks[task_id]['country_index'] = current
            _search_tasks[task_id]['total_countries'] = total
            # 每搜完一个国家，立即写入已完成记录
            if session_key not in _country_search_completed:
                _country_search_completed[session_key] = set()
            _country_search_completed[session_key].add(country_name)

        controller = CustomerSearchController()
        results = controller.run_full_search(
            countries=countries,
            product_name=product_name,
            hs_code=hs_code,
            progress_callback=progress_callback,
            local_search=local_search,
        )
        unique_results = controller.deduplicate(results)
        _search_tasks[task_id].update({
            'status': 'completed',
            'current_country': '已完成',
            'results': unique_results,
            'total': len(unique_results),
            'completed_at': time.time()
        })
    except Exception as e:
        _search_tasks[task_id].update({
            'status': 'failed',
            'error': str(e)
        })


@bp.route('/run', methods=['POST'])
def run_search():
    """
    POST /search/run
    Body: {
        countries: ["France", "USA"],       (可选，默认全球全部 150+ 国家)
        task_id: str,                       (可选，提供则复用已有任务)
        product_name: str,
        hs_code: str,
        local_search: bool,                 (可选，默认 True；是否对 tier 1/2 国家进行本地语言二次搜索)
    }

    增量搜索逻辑：
    - 若前端传来 task_id，则复用已有任务（返回当前状态）
    - 若不传 task_id，则根据 (product_name, hs_code) 判断哪些国家已搜过，
      只对未搜过的国家启动新任务
    """
    data = request.get_json() or {}
    countries = data.get('countries')
    task_id = data.get('task_id')
    product_name = data.get('product_name') or ''
    hs_code = data.get('hs_code') or ''
    local_search = data.get('local_search', True)  # 默认开启本地语言二次搜索

    # 复用已有任务
    if task_id and task_id in _search_tasks:
        task = _search_tasks[task_id]
        return jsonify({
            'code': 0,
            'data': {
                'task_id': task_id,
                'status': task['status'],
                'total': task.get('total'),
                'completed_at': task.get('completed_at')
            }
        })

    # ── 增量搜索：过滤掉已搜过的国家 ──────────────────────────────────────
    session_key = (product_name.strip(), hs_code.strip())
    completed = _country_search_completed.get(session_key, set())
    # 默认全部国家（Tier 1 → Tier 2 → Tier 3）
    all_countries = countries if (countries and len(countries) > 0) else list(_ALL_COUNTRIES)
    pending_countries = [c for c in all_countries if c not in completed]

    if not pending_countries:
        return jsonify({
            'code': 0,
            'data': {
                'task_id': None,
                'status': 'all_completed',
                'message': f'该关键词已在所有 {len(completed)} 个国家搜索完毕（含本地语言二次搜索）',
                'completed_countries': sorted(completed),
                'pending_countries': [],
                'total_countries': len(all_countries),
            }
        }), 200

    skipped_count = len(all_countries) - len(pending_countries)

    # 创建新任务
    task_id = str(uuid.uuid4())[:8]
    _search_tasks[task_id] = {
        'status': 'pending',
        'countries': pending_countries,
        'all_countries': all_countries,
        'search_type': 'incremental',
        'product_name': product_name,
        'hs_code': hs_code,
        'local_search': local_search,
        'session_key': session_key,
        'created_at': time.time(),
    }

    # 后台线程执行
    thread = threading.Thread(
        target=_run_search_async,
        args=(task_id, pending_countries, 'incremental', product_name, hs_code, local_search),
        daemon=True
    )
    thread.start()

    return jsonify({
        'code': 0,
        'data': {
            'task_id': task_id,
            'status': 'pending',
            'message': (
                f'全球搜索任务已创建：{len(pending_countries)} 个待搜国家，'
                f'跳过 {skipped_count} 个已搜国家'
                f'{"" if local_search else "（本地语言搜索已关闭）"}'
            ),
            'pending_countries': pending_countries,
            'skipped_countries': sorted(completed),
            'skipped_count': skipped_count,
            'total_countries': len(all_countries),
            'local_search_enabled': local_search,
        }
    }), 202


@bp.route('/run-by-name', methods=['POST'])
def search_by_name():
    """
    POST /search/run-by-name
    Body: {
        company_name: str,
        country: str (可选)
    }
    """
    data = request.get_json()
    if not data or 'company_name' not in data:
        return jsonify({'code': 400, 'message': '缺少 company_name 参数'}), 400

    company_name = data['company_name']
    country = data.get('country')
    task_id = str(uuid.uuid4())[:8]

    try:
        controller = CustomerSearchController()
        results = controller.search_by_company_name(company_name, country=country)
        unique = controller.deduplicate(results)
        return jsonify({
            'code': 0,
            'data': {
                'task_id': task_id,
                'status': 'completed',
                'results': unique,
                'total': len(unique),
                'keyword': company_name,
                'country': country
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': f'搜索失败: {str(e)}'}), 500


@bp.route('/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """GET /search/status/<task_id> - 查询任务状态"""
    if task_id not in _search_tasks:
        return jsonify({'code': 404, 'message': '任务不存在'}), 404

    task = _search_tasks[task_id]
    response = {
        'task_id': task_id,
        'status': task['status'],
        'created_at': task.get('created_at'),
        'current_country': task.get('current_country'),
        'country_index': task.get('country_index'),
        'total_countries': task.get('total_countries'),
    }
    if task['status'] == 'completed':
        response['total'] = task.get('total')
        response['completed_at'] = task.get('completed_at')
        response['results'] = task.get('results', [])
    elif task['status'] == 'failed':
        response['error'] = task.get('error')
    return jsonify({'code': 0, 'data': response})


@bp.route('/countries', methods=['GET'])
def list_searchable_countries():
    """
    GET /search/countries - 获取全球可搜索国家完整列表
    返回全部 150+ 国家，按鱼子酱活跃度 Tier 1 → Tier 2 → Tier 3 排序
    """
    countries_data = [
        {
            'name': c[0],
            'tier': c[1],
            'tier_label': '高活跃市场' if c[1] == 1 else ('中活跃市场' if c[1] == 2 else '低活跃/偏远'),
            'local_keyword': c[2],
        }
        for c in _CAVIAR_COUNTRIES
    ]
    tier1 = [c for c in countries_data if c['tier'] == 1]
    tier2 = [c for c in countries_data if c['tier'] == 2]
    tier3 = [c for c in countries_data if c['tier'] == 3]
    return jsonify({
        'code': 0,
        'data': {
            'total': len(countries_data),
            'tier1_count': len(tier1),
            'tier2_count': len(tier2),
            'tier3_count': len(tier3),
            'tier1': [c['name'] for c in tier1],
            'tier2': [c['name'] for c in tier2],
            'tier3': [c['name'] for c in tier3],
            'detail': countries_data,
        }
    })


@bp.route('/progress', methods=['GET'])
def get_search_progress():
    """
    GET /search/progress?product_name=...&hs_code=...
    返回指定关键词下各国家的搜索完成状态（全球 150+ 国家）
    """
    product_name = request.args.get('product_name', '').strip()
    hs_code = request.args.get('hs_code', '').strip()
    session_key = (product_name, hs_code)
    completed = _country_search_completed.get(session_key, set())

    all_countries = list(_ALL_COUNTRIES)
    pending = [c for c in all_countries if c not in completed]

    # tier 统计
    tier1_total = sum(1 for c in all_countries if _COUNTRY_TIER_MAP.get(c) == 1)
    tier1_done = sum(1 for c in completed if _COUNTRY_TIER_MAP.get(c) == 1)
    tier2_total = sum(1 for c in all_countries if _COUNTRY_TIER_MAP.get(c) == 2)
    tier2_done = sum(1 for c in completed if _COUNTRY_TIER_MAP.get(c) == 2)
    tier3_total = sum(1 for c in all_countries if _COUNTRY_TIER_MAP.get(c) == 3)
    tier3_done = sum(1 for c in completed if _COUNTRY_TIER_MAP.get(c) == 3)

    return jsonify({
        'code': 0,
        'data': {
            'product_name': product_name,
            'hs_code': hs_code,
            'completed_countries': sorted(completed),
            'pending_countries': pending,
            'total': len(all_countries),
            'completed_count': len(completed),
            'pending_count': len(pending),
            'tier_summary': {
                'tier1': {'total': tier1_total, 'done': tier1_done},
                'tier2': {'total': tier2_total, 'done': tier2_done},
                'tier3': {'total': tier3_total, 'done': tier3_done},
            }
        }
    })


@bp.route('/reset', methods=['POST'])
def reset_search_progress():
    """
    POST /search/reset
    重置指定关键词的搜索进度（清除已完成记录，可重新从头搜索）

    Body: {
        product_name: str,
        hs_code: str
    }
    """
    data = request.get_json() or {}
    product_name = data.get('product_name', '').strip()
    hs_code = data.get('hs_code', '').strip()
    session_key = (product_name, hs_code)

    if session_key in _country_search_completed:
        count = len(_country_search_completed[session_key])
        del _country_search_completed[session_key]
        return jsonify({
            'code': 0,
            'data': {'message': f'已重置，删除了 {count} 个国家的搜索记录'}
        })
    return jsonify({
        'code': 0,
        'data': {'message': '该关键词暂无搜索记录，无需重置'}
    })


# ══════════════════════════════════════════════════════════════════════════════
#  批量导入搜索结果 → 客户池
# ══════════════════════════════════════════════════════════════════════════════

@bp.route('/import-batch', methods=['POST'])
def import_search_results():
    """
    POST /search/import-batch
    将搜索结果批量导入客户池

    Body: {
        items: [{
            company_name_en: str,   # 公司英文名
            website: str,           # 官网
            country: str,            # 国家名称
            source: str,            # 来源（google）
            snippet: str,           # 描述
            product_name: str,      # 产品名
            hs_code: str,           # HS CODE
        }]
    }

    返回: {
        imported: int,             # 成功导入数
        skipped: int,              # 跳过数（重复/缺必填）
        failed: int,               # 失败数
        results: [{company_name_en, country, status, reason, customer_id}],
    }
    """
    from ..models import db, Customer, Country

    data = request.get_json() or {}
    items = data.get('items', [])
    if not items:
        return jsonify({'code': 400, 'message': '没有要导入的数据'}), 400

    # 构建已存在客户名集合（用于快速去重）
    all_names = [item.get('company_name_en') or item.get('company_name', '') for item in items]
    all_names_lower = {n.strip().lower() for n in all_names if n.strip()}

    existing = set()
    if all_names_lower:
        rows = db.session.query(
            Customer.company_name_en, Customer.country_id, Customer.id
        ).filter(
            db.func.lower(Customer.company_name_en).in_(all_names_lower)
        ).all()
        for r in rows:
            existing.add((r.company_name_en.strip().lower(), r.country_id, r.id))

    # 国家名缓存
    country_cache = {}
    def _resolve_country(name: str):
        if not name:
            return None
        name_lower = name.strip().lower()
        if name_lower in country_cache:
            return country_cache[name_lower]
        c = Country.query.filter(
            db.or_(
                db.func.lower(Country.name_en) == name_lower,
                db.func.lower(Country.name_cn) == name_lower,
                db.func.lower(Country.code) == name_lower,
            )
        ).first()
        country_cache[name_lower] = c.id if c else None
        return country_cache[name_lower]

    imported = 0
    skipped = 0
    failed = 0
    results = []

    for item in items:
        company_name = (item.get('company_name_en') or item.get('company_name') or '').strip()
        country_str = item.get('country', '')
        website = item.get('website') or ''
        source = item.get('source', 'google')
        snippet = item.get('snippet') or item.get('description') or ''
        product_name = item.get('product_name')
        hs_code = item.get('hs_code')

        # 必填校验
        if not company_name:
            skipped += 1
            results.append({
                'company_name_en': '(空)',
                'country': country_str,
                'status': 'skipped',
                'reason': '公司名称为空',
            })
            continue

        # 国家解析
        country_id = _resolve_country(country_str)

        # 去重检查（只看公司名，不强制要求国家相同）
        dup_found = False
        dup_id = None
        for (exist_name_lower, exist_country_id, exist_id) in existing:
            if exist_name_lower == company_name.lower():
                dup_found = True
                dup_id = exist_id
                break
        if dup_found:
            skipped += 1
            results.append({
                'company_name_en': company_name,
                'country': country_str,
                'status': 'skipped',
                'reason': '客户已在库中',
                'customer_id': dup_id,
            })
            continue

        # 写入数据库
        try:
            customer = Customer(
                company_name_en=company_name,
                country_id=country_id if country_id else None,
                website=website,
                follow_up_status='NEW',
                priority_level='MEDIUM',
                notes=f'来源：客户搜索（{source}）\n描述：{snippet}',
                search_source=f'search_{source}',
                is_collected=True,  # 批量导入 → 直接入客户池
            )
            db.session.add(customer)
            db.session.flush()  # 获取 ID

            # 关联产品
            if product_name or hs_code:
                from ..models import Product
                query = Product.query
                if hs_code:
                    query = query.filter(Product.hs_code.ilike(f'%{hs_code}%'))
                if product_name:
                    query = query.filter(
                        db.or_(
                            Product.product_name.ilike(f'%{product_name}%'),
                            Product.product_name_en.ilike(f'%{product_name}%'),
                        )
                    )
                product = query.first()
                if product and customer not in product.customers:
                    product.customers.append(customer)

            db.session.commit()

            imported += 1
            existing.add((company_name.lower(), country_id, customer.id))
            results.append({
                'company_name_en': company_name,
                'country': country_str,
                'status': 'imported',
                'customer_id': customer.id,
            })
        except Exception as e:
            db.session.rollback()
            failed += 1
            results.append({
                'company_name_en': company_name,
                'country': country_str,
                'status': 'failed',
                'reason': str(e)[:80],
            })

    return jsonify({
        'code': 0,
        'data': {
            'imported': imported,
            'skipped': skipped,
            'failed': failed,
            'total': len(items),
            'results': results,
        },
        'message': f'导入完成：成功 {imported} 条，跳过 {skipped} 条，失败 {failed} 条',
    })


# ══════════════════════════════════════════════════════════════════════════════
#  搜索历史
# ══════════════════════════════════════════════════════════════════════════════

@bp.route('/history', methods=['GET'])
def search_history():
    """
    GET /search/history
    返回最近的搜索任务历史
    Query params:
        limit: int (默认10, 最大50)
    """
    limit = min(request.args.get('limit', 10, type=int), 50)

    history = []
    for task_id, task in _search_tasks.items():
        status = task.get('status', 'unknown')
        if status in ('completed', 'failed'):
            history.append({
                'task_id': task_id,
                'status': status,
                'countries': task.get('countries'),
                'product_name': task.get('product_name'),
                'hs_code': task.get('hs_code'),
                'total_results': task.get('total', 0),
                'created_at': task.get('created_at'),
                'completed_at': task.get('completed_at'),
                'error': task.get('error'),
            })

    history.sort(key=lambda x: x.get('created_at') or 0, reverse=True)
    return jsonify({
        'code': 0,
        'data': history[:limit]
    })
