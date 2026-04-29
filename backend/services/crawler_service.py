"""
客户搜索服务 - 使用 AI 搜索替代 Google 爬虫
支持 DeepSeek / 智谱 / Volcengine Ark 等兼容 OpenAI 格式的 API
"""
import os
import json
import time
import re
from openai import OpenAI


# ─────────────────────────────────────────────────────────────────────────────
# 全球鱼子酱贸易国家完整列表
# Tier 1（高活跃/主要目标市场）：深度搜索，英文关键词 + 本地语言二次搜索
# Tier 2（中活跃）：标准搜索，英文关键词
# Tier 3（低活跃/偏远/内陆）：轻量搜索，仅英文关键词
# 每个国家含：本地语言关键词、英文关键词后缀、tier 等级
# ─────────────────────────────────────────────────────────────────────────────
# 格式：(国家英文名, tier, 本地语言 caviar 关键词, 英文类型后缀列表)
_CAVIAR_COUNTRIES = [
    # ── Tier 1: 高活跃市场 ────────────────────────────────────────────────────
    ('France',       1, 'caviar',           ['caviar importer','caviar wholesale','caviar distributor','premium seafood supplier','luxury food importer']),
    ('USA',          1, 'caviar',           ['caviar importer','caviar wholesale','caviar distributor','premium seafood supplier','luxury food importer']),
    ('Italy',        1, 'caviale',          ['caviale importer','caviale wholesale','caviale distributor','premium seafood supplier','luxury food importer']),
    ('Germany',      1, 'Kaviar',           ['Kaviar importer','Kaviar wholesale','Kaviar distributor','premium seafood supplier','luxury food importer']),
    ('Spain',        1, 'caviar',           ['caviar importer','caviar wholesale','caviar distributor','premium seafood supplier','luxury food importer']),
    ('Japan',        1, 'キャビア',         ['caviar importer','caviar wholesale','caviar distributor','premium seafood supplier','luxury food importer']),
    ('United Kingdom',1,'caviar',           ['caviar importer','caviar wholesale','caviar distributor','premium seafood supplier','luxury food importer']),
    ('Switzerland',  1, 'Kaviar',           ['caviar importer','caviar wholesale','caviar distributor','premium seafood supplier','luxury food importer']),
    ('UAE',          1, 'كافيار',           ['caviar importer','caviar wholesale','caviar distributor','premium seafood supplier','luxury food importer']),
    ('Netherlands',  1, 'kaviaar',          ['caviar importer','caviar wholesale','caviar distributor','premium seafood supplier','luxury food importer']),
    ('Belgium',      1, 'kaviaar',          ['caviar importer','caviar wholesale','caviar distributor','premium seafood supplier','luxury food importer']),
    ('Australia',    1, 'caviar',           ['caviar importer','caviar wholesale','caviar distributor','premium seafood supplier','luxury food importer']),
    ('Canada',       1, 'caviar',           ['caviar importer','caviar wholesale','caviar distributor','premium seafood supplier','luxury food importer']),
    ('Singapore',    1, 'caviar',           ['caviar importer','caviar wholesale','caviar distributor','premium seafood supplier','luxury food importer']),
    ('Hong Kong',    1, '魚子醬',           ['caviar importer','caviar wholesale','caviar distributor','premium seafood supplier','luxury food importer']),

    # ── Tier 2: 中活跃市场 ────────────────────────────────────────────────────
    ('Russia',       2, 'икра',             ['caviar importer','caviar wholesale','caviar distributor']),
    ('China',        2, '魚子醬',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('South Korea',  2, '캐비어',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Saudi Arabia', 2, 'كافيار',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Qatar',        2, 'كافيار',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Kuwait',       2, 'كافيار',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Bahrain',      2, 'كافيار',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Oman',         2, 'كافيار',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Portugal',     2, 'caviar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Greece',       2, 'αβγατος',         ['caviar importer','caviar wholesale','caviar distributor']),
    ('Austria',      2, 'Kaviar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Sweden',       2, 'kaviar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Norway',       2, 'kaviar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Denmark',      2, 'kaviar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Finland',      2, 'kaviaari',         ['caviar importer','caviar wholesale','caviar distributor']),
    ('Poland',       2, 'kawior',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Czech Republic',2,'kaviár',          ['caviar importer','caviar wholesale','caviar distributor']),
    ('Hungary',      2, 'kaviár',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Ireland',      2, 'caviar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('New Zealand',  2, 'caviar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Taiwan',       2, '魚子醬',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Thailand',     2, 'คาวิอาร์',         ['caviar importer','caviar wholesale','caviar distributor']),
    ('Malaysia',     2, 'kaviar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Indonesia',    2, 'kaviar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Philippines',  2, 'caviar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Vietnam',      2, 'trứng cá tầm',    ['caviar importer','caviar wholesale','caviar distributor']),
    ('India',        2, 'कैवियार',          ['caviar importer','caviar wholesale','caviar distributor']),
    ('Brazil',       2, 'caviar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Mexico',       2, 'caviar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Argentina',    2, 'caviar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('South Africa', 2, 'caviar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Morocco',      2, 'كافيار',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Egypt',        2, 'كافيار',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Turkey',       2, 'havyar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Israel',       2, 'קוויאר',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Lebanon',      2, 'كافيار',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Jordan',       2, 'كافيار',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Ukraine',      2, 'ікра',             ['caviar importer','caviar wholesale','caviar distributor']),
    ('Romania',      2, 'caviar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Bulgaria',     2, 'caviar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Croatia',      2, 'kavijar',          ['caviar importer','caviar wholesale','caviar distributor']),
    ('Slovenia',     2, 'kaviar',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Slovakia',     2, 'kaviár',           ['caviar importer','caviar wholesale','caviar distributor']),
    ('Luxembourg',   2, 'caviar',           ['caviar importer','caviar wholesale','caviar distributor']),

    # ── Tier 3: 低活跃 / 偏远 / 内陆国家 ──────────────────────────────────────
    ('Kazakhstan',   3, 'қавиар',           ['caviar importer']),
    ('Uzbekistan',   3, 'кавиар',           ['caviar importer']),
    ('Turkmenistan', 3, 'kawiar',           ['caviar importer']),
    ('Azerbaijan',   3, 'kalsium',          ['caviar importer']),
    ('Georgia',      3, 'კავიარი',          ['caviar importer']),
    ('Armenia',      3, 'կավիար',          ['caviar importer']),
    ('Belarus',      3, 'ікра',             ['caviar importer']),
    ('Moldova',      3, 'caviar',           ['caviar importer']),
    ('Albania',      3, 'kaviar',           ['caviar importer']),
    ('Serbia',       3, 'kavijar',          ['caviar importer']),
    ('Bosnia and Herzegovina', 3, 'kavijar', ['caviar importer']),
    ('Montenegro',   3, 'kavijar',          ['caviar importer']),
    ('North Macedonia', 3, 'кавијар',      ['caviar importer']),
    ('Latvia',       3, 'kaviārs',          ['caviar importer']),
    ('Lithuania',    3, 'kaviaras',         ['caviar importer']),
    ('Estonia',      3, 'kalamari',         ['caviar importer']),
    ('Iceland',      3, 'kavíar',           ['caviar importer']),
    ('Malta',        3, 'caviar',           ['caviar importer']),
    ('Cyprus',       3, 'καβούρι',          ['caviar importer']),
    ('Andorra',      3, 'caviar',           ['caviar importer']),
    ('Monaco',       3, 'caviar',           ['caviar importer']),
    ('Liechtenstein',3, 'Kaviar',           ['caviar importer']),
    ('San Marino',   3, 'caviar',           ['caviar importer']),
    ('Vatican City', 3, 'caviar',           ['caviar importer']),
    ('Gibraltar',    3, 'caviar',           ['caviar importer']),
    ('Greenland',    3, 'caviar',           ['caviar importer']),
    ('Faroe Islands',3, 'kaviar',           ['caviar importer']),
    ('Jersey',       3, 'caviar',           ['caviar importer']),
    ('Guernsey',     3, 'caviar',           ['caviar importer']),
    ('Isle of Man', 3, 'caviar',           ['caviar importer']),
    ('Pakistan',     3, 'کیویار',           ['caviar importer']),
    ('Bangladesh',   3, 'ক্যাভিয়ার',        ['caviar importer']),
    ('Sri Lanka',    3, 'කැවියර්',         ['caviar importer']),
    ('Nepal',        3, 'क्याभियार',         ['caviar importer']),
    ('Bhutan',       3, 'caviar',           ['caviar importer']),
    ('Maldives',     3, 'caviar',           ['caviar importer']),
    ('Afghanistan',  3, 'caviar',           ['caviar importer']),
    ('Iran',         3, 'کلم مار',           ['caviar importer']),
    ('Iraq',         3, 'كافيار',           ['caviar importer']),
    ('Syria',        3, 'كافيار',           ['caviar importer']),
    ('Yemen',        3, 'كافيار',           ['caviar importer']),
    ('Libya',        3, 'كافيار',           ['caviar importer']),
    ('Tunisia',      3, 'كافيار',           ['caviar importer']),
    ('Algeria',      3, 'كافيار',           ['caviar importer']),
    ('Sudan',        3, 'كافيار',           ['caviar importer']),
    ('Ethiopia',     3, 'ካቪያር',             ['caviar importer']),
    ('Kenya',        3, 'caviar',           ['caviar importer']),
    ('Uganda',       3, 'caviar',           ['caviar importer']),
    ('Tanzania',      3, 'caviar',           ['caviar importer']),
    ('Rwanda',       3, 'caviar',           ['caviar importer']),
    ('Burundi',      3, 'caviar',           ['caviar importer']),
    ('Democratic Republic of the Congo', 3, 'caviar', ['caviar importer']),
    ('Republic of the Congo', 3, 'caviar',  ['caviar importer']),
    ('Gabon',        3, 'caviar',           ['caviar importer']),
    ('Cameroon',     3, 'caviar',           ['caviar importer']),
    ('Nigeria',      3, 'caviar',           ['caviar importer']),
    ('Ghana',        3, 'caviar',           ['caviar importer']),
    ('Ivory Coast',  3, 'caviar',           ['caviar importer']),
    ('Senegal',      3, 'caviar',           ['caviar importer']),
    ('Mali',         3, 'caviar',           ['caviar importer']),
    ('Niger',        3, 'caviar',           ['caviar importer']),
    ('Burkina Faso', 3, 'caviar',           ['caviar importer']),
    ('Angola',       3, 'caviar',           ['caviar importer']),
    ('Zambia',       3, 'caviar',           ['caviar importer']),
    ('Zimbabwe',     3, 'caviar',           ['caviar importer']),
    ('Mozambique',   3, 'caviar',           ['caviar importer']),
    ('Madagascar',   3, 'caviar',           ['caviar importer']),
    ('Mauritius',    3, 'caviar',           ['caviar importer']),
    ('Seychelles',   3, 'caviar',           ['caviar importer']),
    ('Namibia',      3, 'caviar',           ['caviar importer']),
    ('Botswana',     3, 'caviar',           ['caviar importer']),
    ('Lesotho',      3, 'caviar',           ['caviar importer']),
    ('Eswatini',     3, 'caviar',           ['caviar importer']),
    ('Malawi',       3, 'caviar',           ['caviar importer']),
    ('Jamaica',      3, 'caviar',           ['caviar importer']),
    ('Trinidad and Tobago', 3, 'caviar',   ['caviar importer']),
    ('Barbados',     3, 'caviar',           ['caviar importer']),
    ('Bahamas',      3, 'caviar',           ['caviar importer']),
    ('Cuba',         3, 'caviar',           ['caviar importer']),
    ('Dominican Republic', 3, 'caviar',   ['caviar importer']),
    ('Puerto Rico',  3, 'caviar',           ['caviar importer']),
    ('Costa Rica',   3, 'caviar',           ['caviar importer']),
    ('Panama',       3, 'caviar',           ['caviar importer']),
    ('Guatemala',    3, 'caviar',           ['caviar importer']),
    ('Honduras',     3, 'caviar',           ['caviar importer']),
    ('El Salvador',  3, 'caviar',           ['caviar importer']),
    ('Nicaragua',    3, 'caviar',           ['caviar importer']),
    ('Colombia',     3, 'caviar',           ['caviar importer']),
    ('Venezuela',    3, 'caviar',           ['caviar importer']),
    ('Ecuador',      3, 'caviar',           ['caviar importer']),
    ('Peru',         3, 'caviar',           ['caviar importer']),
    ('Bolivia',      3, 'caviar',           ['caviar importer']),
    ('Paraguay',     3, 'caviar',           ['caviar importer']),
    ('Uruguay',      3, 'caviar',           ['caviar importer']),
    ('Chile',        3, 'caviar',           ['caviar importer']),
    ('Myanmar',      3, 'caviar',           ['caviar importer']),
    ('Cambodia',     3, 'caviar',           ['caviar importer']),
    ('Laos',         3, 'caviar',           ['caviar importer']),
    ('Mongolia',     3, 'caviar',           ['caviar importer']),
    ('North Korea',  3, '캐비어',            ['caviar importer']),
    ('Brunei',       3, 'caviar',           ['caviar importer']),
    ('Timor-Leste',  3, 'caviar',           ['caviar importer']),
    ('Papua New Guinea', 3, 'caviar',      ['caviar importer']),
    ('Fiji',         3, 'caviar',           ['caviar importer']),
    ('Samoa',        3, 'caviar',           ['caviar importer']),
    ('Tonga',        3, 'caviar',           ['caviar importer']),
    ('Vanuatu',      3, 'caviar',           ['caviar importer']),
    ('Solomon Islands', 3, 'caviar',        ['caviar importer']),
    ('Micronesia',   3, 'caviar',           ['caviar importer']),
    ('Palau',        3, 'caviar',           ['caviar importer']),
    ('Marshall Islands', 3, 'caviar',       ['caviar importer']),
    ('Nauru',        3, 'caviar',           ['caviar importer']),
    ('Tuvalu',       3, 'caviar',           ['caviar importer']),
    ('Kyrgyzstan',   3, 'кызыл балык',      ['caviar importer']),
    ('Tajikistan',   3, 'кавиар',           ['caviar importer']),
]


# ── AI 客户端配置 ─────────────────────────────────────────────────────────────
def _get_ai_client():
    """按优先级自动选择可用的 AI API"""
    # 优先用 DeepSeek
    api_key = os.environ.get('DEEPSEEK_API_KEY') or os.environ.get('AI_SEARCH_API_KEY')
    base_url = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    model = os.environ.get('AI_SEARCH_MODEL', 'deepseek-chat')

    if not api_key:
        raise RuntimeError(
            '未配置 AI API Key。请设置环境变量 DEEPSEEK_API_KEY 或 AI_SEARCH_API_KEY。'
        )
    return OpenAI(api_key=api_key, base_url=base_url), model


# ── AI 搜索核心 ───────────────────────────────────────────────────────────────
def _ai_search_companies(query: str, country: str, max_results: int = 10) -> list:
    """
    用 AI 直接生成目标企业列表。
    返回: [{'company_name_en': ..., 'website': ..., 'snippet': ...}, ...]
    """
    client, model = _get_ai_client()

    system_prompt = (
        "You are a B2B business intelligence assistant specializing in the global food trade industry. "
        "When given a search query about caviar/sturgeon roe importers, distributors, or wholesalers, "
        "you return REAL, VERIFIABLE companies that match the query. "
        "Format your response as a JSON array ONLY, no markdown, no explanation. "
        "Each element: {\"company_name_en\": \"...\", \"website\": \"...\", \"snippet\": \"...\", \"country\": \"...\"}. "
        "If you are unsure about a website, set it to empty string. "
        "Return up to " + str(max_results) + " companies."
    )

    user_prompt = (
        f"Find real companies in {country} that match this search: \"{query}\". "
        f"Focus on businesses that import, distribute, wholesale or retail caviar/sturgeon roe. "
        f"Include their official website if known. Return JSON array only."
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        content = resp.choices[0].message.content.strip()

        # 提取 JSON（兼容 AI 可能包裹在 ```json 中的情况）
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            companies = json.loads(match.group())
            return companies if isinstance(companies, list) else []
        return []
    except Exception as e:
        print(f'[AISearch] 搜索失败 ({query}): {e}')
        return []


# ── 控制器（保持与原有接口完全兼容）────────────────────────────────────────────
class CustomerSearchController:
    """客户搜索控制器（AI 搜索版，支持全球 150+ 国家 + 本地语言二次搜索）"""

    BASE_KEYWORDS = [
        'caviar importer',
        'caviar wholesale',
        'caviar distributor',
        'premium seafood supplier',
        'luxury food importer',
    ]

    # tier 1 最大关键词数，tier 2 中等，tier 3 精简
    _KW_COUNTS = {1: 5, 2: 3, 3: 1}

    def __init__(self):
        pass

    def get_all_countries(self) -> list:
        """返回全部国家英文名列表（Tier 1 → Tier 2 → Tier 3）"""
        return [c[0] for c in _CAVIAR_COUNTRIES]

    def _find_country_info(self, country_name: str):
        """根据国家名查找完整信息"""
        for c_info in _CAVIAR_COUNTRIES:
            if c_info[0].lower() == country_name.lower():
                return c_info
        return None  # 未知国家，降级到 tier3

    def _build_keywords(
        self, country_name: str, tier: int, local_kw: str,
        product_name=None, hs_code=None, use_local: bool = False
    ) -> list:
        """
        构建搜索关键词列表。
        - tier 1: 最多 5 个英文关键词 + 本地语言二次搜索
        - tier 2: 最多 3 个英文关键词 + 本地语言二次搜索
        - tier 3: 仅 1 个英文关键词（轻量）
        - use_local=True 时：追加本地语言关键词
        """
        if product_name:
            product_en = product_name.strip()
        elif hs_code:
            product_en = f'HS {hs_code.strip()}'
        else:
            product_en = 'caviar'

        max_kw = self._KW_COUNTS.get(tier, 1)
        keywords = []

        # 英文关键词
        for base in self.BASE_KEYWORDS[:max_kw]:
            kw = f'{country_name} {product_en} {base}'.strip()
            keywords.append(kw)

        # 本地语言关键词（tier 1/2 二次搜索）
        if use_local and local_kw and local_kw.lower() != 'caviar':
            for base in self.BASE_KEYWORDS[:2]:  # 本地语言只取 2 个变体
                kw_local = f'{local_kw} {base}'.strip()
                keywords.append(kw_local)

        return keywords

    def search_by_country(
        self, country, keyword_type='importer',
        product_name=None, hs_code=None, use_local: bool = False
    ):
        """按国家 + 产品 + 类型搜索；use_local=True 时追加本地语言二次搜索"""
        c_info = self._find_country_info(country)
        if c_info:
            tier = c_info[1]
            local_kw = c_info[2]
        else:
            tier = 3
            local_kw = 'caviar'

        keywords = self._build_keywords(
            country, tier, local_kw, product_name, hs_code, use_local=use_local
        )
        results = []

        for kw in keywords:
            try:
                found = _ai_search_companies(kw, country)
                for item in found:
                    results.append({
                        'company_name_en': item.get('company_name_en', ''),
                        'website': item.get('website', ''),
                        'country': item.get('country', country),
                        'source': 'ai_search',
                        'snippet': item.get('snippet', ''),
                        'product_name': product_name,
                        'hs_code': hs_code,
                        'tier': tier,
                    })
                time.sleep(1)
            except Exception as e:
                print(f'关键词 [{kw}] 搜索出错: {e}')

        return results

    def search_by_company_name(self, company_name, country=None):
        """按公司名搜索"""
        query = f'"{company_name}" caviar OR seafood OR gourmet'
        target_country = country or 'global'
        found = _ai_search_companies(query, target_country)
        return [
            {
                'company_name_en': r.get('company_name_en', ''),
                'website': r.get('website', ''),
                'country': r.get('country', country or ''),
                'source': 'ai_search',
                'snippet': r.get('snippet', ''),
            }
            for r in found
        ]

    def run_full_search(
        self, countries=None, product_name=None, hs_code=None,
        progress_callback=None, local_search: bool = True
    ):
        """
        多国家全量搜索，支持进度回调。
        - countries: 国家英文名列表，默认全部 150+ 国家
        - local_search: True = tier 1/2 国家追加本地语言二次搜索
        - tier 3 国家不进行本地语言搜索（轻量原则）
        """
        if countries is None:
            countries = self.get_all_countries()

        all_results = []
        total_countries = len(countries)

        for i, c in enumerate(countries):
            # 统一处理：c 可能是 dict({"code":"FR","name":"France"}) 或 string
            country_name = c.get('name') if isinstance(c, dict) else str(c)
            c_info = self._find_country_info(country_name)
            tier = c_info[1] if c_info else 3

            # tier 3 只用英文；tier 1/2 本地语言 + tier 1 用更多关键词
            use_local = local_search and tier <= 2

            print(f'[AISearch] [{i+1}/{total_countries}] 国家: {country_name} | Tier: {tier} | '
                  f'本地搜索: {"✓" if use_local else "✗"} | '
                  f'产品: {product_name or "鲟鱼子酱"} | HS: {hs_code or "无"}')

            results = self.search_by_country(
                country_name, keyword_type='importer',
                product_name=product_name, hs_code=hs_code,
                use_local=use_local
            )
            all_results.extend(results)
            print(f'[AISearch]   → {country_name} 完成，找到 {len(results)} 条结果')

            if progress_callback:
                progress_callback(i + 1, total_countries, country_name, country_results=results)

        return all_results

    def deduplicate(self, results):
        """去重"""
        seen = set()
        unique = []
        for r in results:
            key = r.get('website', '') or r.get('company_name_en', '')
            if key and key not in seen:
                seen.add(key)
                unique.append(r)
        return unique
