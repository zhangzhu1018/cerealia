"""
客户搜索服务 - 使用 AI 搜索替代 Google 爬虫
支持 DeepSeek / 智谱 / Volcengine Ark 等兼容 OpenAI 格式的 API
"""
import os
import json
import time
import re
import urllib.request
import urllib.error
from openai import OpenAI


def _verify_url(url: str, timeout: int = 3) -> bool:
    """验证 URL 是否可达（HEAD 请求，快速检查 AI 生成的网站是否真实存在）"""
    if not url or not url.startswith(('http://', 'https://')):
        return False
    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Cerealia-CRM/1.0')
        urllib.request.urlopen(req, timeout=timeout)
        return True
    except Exception:
        return False


# ── 网页爬虫：提取邮箱/电话 ──────────────────────────────────────────
_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
_PHONE_RE = re.compile(
    r'(?:\+?\d{1,4}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}',
)
_PHONE_BLACKLIST = frozenset({'0000000000', '1234567890', '0123456789', '1111111111'})
_CONTACT_PATHS = [
    '', '/contact', '/contact-us', '/about', '/contacts',
    '/contatti', '/contacto', '/kontakt', '/nous-contacter',
    '/impressum', '/imprint', '/pages/contact', '/pages/contact-us',
    '/en/contact', '/fr/contact', '/de/kontakt', '/es/contacto',
]

def _scrape_website_contacts(website_url, timeout=10):
    """访问企业网站提取邮箱和电话。返回 {'email':'','phone':'','emails':[...],'phones':[...]}"""
    if not website_url:
        return {}
    all_emails, all_phones = set(), set()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8,de;q=0.7,es;q=0.6',
    }
    skip_domains = frozenset({'example.com', 'domain.com', 'test.com', 'email.com', 'mail.com', 'gmail.com', 'outlook.com', 'yahoo.com'})
    url = website_url.rstrip('/')
    bases = [f'https://{url}', f'http://{url}'] if not url.startswith('http') else [url]

    for base in bases:
        for path in _CONTACT_PATHS[:10]:
            try:
                target = f'{base}{path}' if path else base
                req = urllib.request.Request(target, headers=headers)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')[:300000]
                    for e in _EMAIL_RE.findall(html):
                        e_low = e.lower()
                        parts = e_low.split('@')
                        if len(parts) == 2 and parts[1] not in skip_domains and 'example' not in e_low and '.png' not in e_low and '.jpg' not in e_low:
                            all_emails.add(e)
                    for m in re.findall(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', html, re.IGNORECASE):
                        all_emails.add(m)
                    for p in _PHONE_RE.findall(html):
                        digits = re.sub(r'\D', '', p)
                        if 8 <= len(digits) <= 15 and digits not in _PHONE_BLACKLIST:
                            all_phones.add(p)
                if len(all_emails) >= 2:
                    break
            except Exception:
                continue
        if all_emails:
            break

    prefix = ['info@', 'sales@', 'contact@', 'export@', 'office@', 'hello@', 'mail@']
    es = sorted(all_emails, key=lambda e: next((i for i, p in enumerate(prefix) if e.startswith(p.lower())), 99))
    ps = sorted(all_phones, key=lambda p: (not p.startswith('+')), reverse=True)
    return {'email': es[0] if es else '', 'emails': es, 'phone': ps[0] if ps else '', 'phones': ps}


# ── 邮箱域名猜解 + SMTP 验证 ─────────────────────────────────────
_COMMON_LOCAL_PARTS = [
    'info', 'sales', 'contact', 'export', 'office', 'hello',
    'mail', 'admin', 'support', 'enquiry', 'inquiry', 'orders',
    'customerservice', 'management', 'general', 'team',
]

def _guess_and_verify_email(domain, company_name=''):
    """
    根据域名猜解常用邮箱地址。
    返回: {'email': str, 'verified': bool}  已验证成功的邮箱优先
    """
    emails = []
    # 从域名猜
    for lp in _COMMON_LOCAL_PARTS:
        emails.append(f'{lp}@{domain}')
    # 从公司名猜
    if company_name:
        words = re.sub(r'[^a-z0-9\s]', '', company_name.lower()).split()
        if len(words) >= 2:
            emails.append(f'{words[0]}@{domain}')
            emails.append(f'{words[0]}.{words[-1]}@{domain}')

    # 尝试 SMTP 验证
    import smtplib
    for email in emails[:8]:
        try:
            # 简单尝试直连
            with smtplib.SMTP(domain, 25, timeout=6) as smtp:
                smtp.helo('verify.local')
                smtp.mail('test@cerealia-caviar.com')
                code, _ = smtp.rcpt(email)
                if 200 <= code < 300:
                    return {'email': email, 'verified': True}
        except Exception:
            continue

    # SMTP 没验证成功的，返回第一个 info@ 作为候选
    return {'email': emails[0] if emails else '', 'verified': False}


# ── 批量邮箱猜解 ─────────────────────────────────────────────────
def batch_guess_emails(limit=200, skip_existing=True):
    """为没有邮箱的客户猜解邮箱地址。"""
    from ..models import db, Customer
    from urllib.parse import urlparse

    query = Customer.query.filter(Customer.website != '', Customer.website.isnot(None))
    if skip_existing:
        query = query.filter(db.or_(Customer.email == '', Customer.email.is_(None)))
    customers = query.order_by(Customer.background_score.desc()).limit(limit).all()
    filled = 0

    for c in customers:
        try:
            domain = urlparse(c.website or '').netloc
            if not domain or '.' not in domain:
                raw = ((c.website or '').replace('https://', '').replace('http://', '')).split('/')[0]
                domain = raw.replace('www.', '').strip()
            if not domain or '.' not in domain:
                continue
            result = _guess_and_verify_email(domain, c.company_name_en or '')
            if result.get('email'):
                c.email = result['email']
                db.session.commit()
                filled += 1
                print(f'[Guess] {c.company_name_en[:30]} → {result["email"]} (verified={result.get("verified")})')
            time.sleep(0.1)
        except Exception as e:
            db.session.rollback()
            print(f'[Guess] Error {c.company_name_en[:20]}: {e}')

    print(f'[Guess] Done: {filled}/{limit}')
    return filled
def batch_scrape_contacts(limit=100, skip_existing=True):
    """批量爬取现有客户网站，提取邮箱电话。"""
    from ..models import db, Customer
    query = Customer.query.filter(Customer.website != '', Customer.website.isnot(None))
    if skip_existing:
        query = query.filter(db.or_(Customer.email == '', Customer.email.is_(None)))
    customers = query.order_by(Customer.background_score.desc()).limit(limit).all()
    enriched = 0
    for c in customers:
        try:
            contacts = _scrape_website_contacts(c.website)
            if contacts.get('email'):
                c.email = contacts['email']; enriched += 1
            if contacts.get('phone'):
                c.phone = contacts['phone']
            db.session.commit()
            print(f'[Scrape] {c.company_name_en[:30]} → email={bool(contacts.get("email"))} phone={bool(contacts.get("phone"))}')
            time.sleep(0.5)
        except Exception as e:
            db.session.rollback()
            print(f'[Scrape] Error {c.company_name_en[:20]}: {e}')
    print(f'[Scrape] Done: {enriched}/{limit}')
    return enriched


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
    """按优先级自动选择可用的 AI API（DeepSeek > GROK > 通用 OPENAI_FORMAT_KEY）"""
    # 1. DeepSeek
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if api_key:
        base_url = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
        model = os.environ.get('AI_SEARCH_MODEL', 'deepseek-chat')
        return OpenAI(api_key=api_key, base_url=base_url), model

    # 2. GROK (xAI) — 兼容 OpenAI 格式
    api_key = os.environ.get('GROK_API_KEY')
    if api_key:
        base_url = os.environ.get('GROK_BASE_URL', 'https://api.x.ai/v1')
        model = os.environ.get('GROK_MODEL', 'grok-2-latest')
        return OpenAI(api_key=api_key, base_url=base_url), model

    # 3. 通用兜底
    api_key = os.environ.get('AI_SEARCH_API_KEY')
    base_url = os.environ.get('AI_SEARCH_BASE_URL', 'https://api.deepseek.com/v1')
    model = os.environ.get('AI_SEARCH_MODEL', 'deepseek-chat')
    if not api_key:
        raise RuntimeError(
            '未配置 AI API Key。请设置 DEEPSEEK_API_KEY、GROK_API_KEY 或 AI_SEARCH_API_KEY。'
        )
    return OpenAI(api_key=api_key, base_url=base_url), model


# ── AI 搜索核心 ───────────────────────────────────────────────────────────────
def _ai_search_companies(query: str, country: str, local_lang: str = None, max_results: int = 15) -> list:
    """
    用 AI 直接生成目标企业列表。
    支持本地语言（local_lang 非空时用本地语言提问）。
    返回: [{'company_name_en': ..., 'website': ..., 'snippet': ..., 'country': ..., 'type': ...}, ...]
    """
    client, model = _get_ai_client()

    lang_instruction = ""
    if local_lang and local_lang not in ('caviar', 'Caviar'):
        lang_instruction = f"Also search using the local term \"{local_lang}\" (the local word for caviar). "

    system_prompt = (
        "You are a B2B business intelligence database of VERIFIED companies in the global gourmet food industry. "
        "You have factual knowledge of real companies that actually exist and operate today. "
        "ONLY return companies you know for certain are real. If you are unsure, return fewer results. "
        "Format: JSON array only, no markdown, no explanation. "
        "Each element: {\"company_name_en\": \"...\", \"website\": \"...\", \"snippet\": \"25-word description\", \"country\": \"...\", \"type\": \"importer|distributor|retailer|producer\"}. "
        "Website must be a real domain you know exists, or empty string \"\" if unsure. "
        "Return exactly " + str(max_results) + " companies if possible. Prioritize companies with known websites."
    )

    user_prompt = (
        f"List REAL, VERIFIABLE companies in {country} that are involved in the caviar/sturgeon roe trade. "
        + lang_instruction +
        f"Search context: \"{query}\". "
        f"Include ALL types — restaurants, importers, distributors, retailers, producers, farms. "
        f"If you know their official website, include it. Otherwise leave website empty. "
        f"If you find fewer than {max_results} real companies, return only what you know. "
        f"Return JSON array only."
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


def _ai_enrich_contact(company_name, website, country):
    """
    用 AI 搜索企业关键联系人信息。
    返回: {'email': str, 'phone': str, 'contact_name': str}
    """
    client, model = _get_ai_client()
    prompt = (
        f"You are searching the web for contact information of: {company_name}. "
        f"Website: {website or 'unknown'}. Country: {country}. "
        f"Look for their official website, LinkedIn page, business directories (Kompass, Europages, etc.) "
        f"to find: 1) A working business email address, 2) A phone number with country code, "
        f"3) The name of a key person (CEO, founder, export/sales manager, procurement director). "
        f"Return ONLY a JSON object: {{\"email\":\"...\",\"phone\":\"...\",\"contact_name\":\"...\"}}. "
        f"For email, prefer general addresses like info@, sales@, contact@, export@. "
        f"If the website domain is known (e.g. example.com), use the domain to construct likely emails. "
        f"If you cannot confirm any piece of information, use empty string for that field. "
        f"Do not make up data. Only return what you can verify."
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': 'You are a business contact finder with web search capability. Return only valid JSON.'},
                {'role': 'user', 'content': prompt},
            ],
            temperature=0.3,
            max_tokens=400,
        )
        content = resp.choices[0].message.content.strip()
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            result = json.loads(match.group())
            # Validate email contains @
            if result.get('email') and '@' not in str(result['email']):
                result['email'] = ''
            return result
        return {}
    except Exception as e:
        print(f'[ContactEnrich] failed for {company_name}: {e}')
        return {}


# ── 批量联系人补全 ────────────────────────────────────────────────
def batch_enrich_contacts(limit=50, skip_existing=True):
    """
    批量补全现有客户中缺失的联系信息。
    返回补全数量。
    """
    from ..models import db, Customer

    query = Customer.query.filter(Customer.website != '', Customer.website.isnot(None))
    if skip_existing:
        query = query.filter(
            db.or_(
                Customer.email == '',
                Customer.email.is_(None),
                Customer.phone == '',
                Customer.phone.is_(None),
                Customer.contact_name == '',
                Customer.contact_name.is_(None),
            )
        )
    customers = query.order_by(Customer.background_score.desc()).limit(limit).all()
    enriched = 0

    for c in customers:
        try:
            contact = _ai_enrich_contact(
                c.company_name_en or '',
                c.website or '',
                c.country.name_en if c.country else ''
            )
            if contact.get('email'):
                c.email = contact['email']
                enriched += 1
            if contact.get('phone'):
                c.phone = contact['phone']
            if contact.get('contact_name'):
                c.contact_name = contact['contact_name']
            db.session.commit()
            print(f'[Enrich] {c.company_name_en[:30]} → email={bool(contact.get("email"))} phone={bool(contact.get("phone"))}')
            time.sleep(0.3)
        except Exception as e:
            db.session.rollback()
            print(f'[Enrich] Error {c.company_name_en[:20]}: {e}')

    print(f'[Enrich] Batch done: {enriched}/{limit} enriched')
    return enriched

# ── 控制器（保持与原有接口完全兼容）────────────────────────────────────────────
class CustomerSearchController:
    """客户搜索控制器（AI 搜索版，支持全球 150+ 国家 + 本地语言二次搜索）"""

    BASE_KEYWORDS = [
        'caviar importer distributor',
        'caviar wholesale supplier',
        'sturgeon caviar buyer',
        'premium gourmet food distributor',
        'luxury seafood importer',
        'caviar trade import',
        'caviar food distributor',
        'gourmet seafood wholesale',
        'fine food importer caviar',
        'caviar export international trade',
    ]

    # tier 1 最大关键词数，tier 2 中等，tier 3 精简
    _KW_COUNTS = {1: 10, 2: 7, 3: 3}

    def __init__(self):
        pass

    def get_all_countries(self) -> list:
        """返回全部国家英文名列表（Tier 1 → Tier 2 → Tier 3），排除中国"""
        return [c[0] for c in _CAVIAR_COUNTRIES if c[0].lower() != 'china']

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
            for base in self.BASE_KEYWORDS[:4]:  # 本地语言取 4 个变体
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
                found = _ai_search_companies(kw, country, local_lang=local_kw)
                for item in found:
                    url = item.get('website', '')
                    website_verified = _verify_url(url) if url else False
                    # ── 联系人信息 AI 采集 ──
                    company_name = item.get('company_name_en', '')
                    contact = {}
                    if company_name and url:
                        try:
                            contact = _ai_enrich_contact(company_name, url, country)
                            time.sleep(0.5)
                        except Exception:
                            pass
                    results.append({
                        'company_name_en': company_name,
                        'website': url,
                        'country': item.get('country', country),
                        'source': 'ai_search',
                        'snippet': item.get('snippet', ''),
                        'product_name': product_name,
                        'hs_code': hs_code,
                        'tier': tier,
                        'website_verified': website_verified,
                        'email': contact.get('email', ''),
                        'phone': contact.get('phone', ''),
                        'contact_name': contact.get('contact_name', ''),
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
        """去重：按 website + 公司名前3词模糊匹配（跨语言去重）"""
        import re
        seen = set()
        seen_names = set()
        unique = []
        for r in results:
            url = (r.get('website', '') or '').strip().lower()
            name = (r.get('company_name_en', '') or '').strip()
            
            # 1. 相同 URL → 直接去重
            if url and url in seen:
                continue
                
            # 2. 公司名前 3 词作为指纹（处理 "Caviar de France" vs "Caviar De France"）
            name_fingerprint = ' '.join(name.lower().split()[:3])
            # 降级：用前 2 词
            name_fp2 = ' '.join(name.lower().split()[:2])
            
            if name_fingerprint in seen_names or name_fp2 in seen_names:
                # 保留有 website 的版本
                for existing in unique:
                    existing_name = (existing.get('company_name_en', '') or '').strip()
                    existing_fp = ' '.join(existing_name.lower().split()[:3])
                    if existing_fp == name_fingerprint or existing_fp == name_fp2:
                        if url and not existing.get('website'):
                            existing['website'] = r.get('website')
                            existing['snippet'] = r.get('snippet', existing.get('snippet', ''))
                        break
                continue
            
            if url:
                seen.add(url)
            seen_names.add(name_fingerprint)
            seen_names.add(name_fp2)
            unique.append(r)
        return unique
