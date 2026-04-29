"""
邮件生成服务 - DeepSeek AI 生成双语开发信
支持全球 150+ 国家，自动推断目标语言，生成英文+本地语言双语邮件
"""
import os
import json
import re
from datetime import datetime
from openai import OpenAI


# ── DeepSeek 客户端 ───────────────────────────────────────────────────────────
def _get_ai_client():
    api_key = os.environ.get('DEEPSEEK_API_KEY') or os.environ.get('AI_SEARCH_API_KEY')
    base_url = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    model = os.environ.get('AI_SEARCH_MODEL', 'deepseek-chat')
    if not api_key:
        raise RuntimeError('未配置 DEEPSEEK_API_KEY 环境变量')
    return OpenAI(api_key=api_key, base_url=base_url), model


# ── 国家 → 语言映射（150+ 国家）───────────────────────────────────────────────
# 包含主要语言及对应国家/地区
_COUNTRY_LANGUAGE_MAP = {
    # Tier 1 高活跃市场
    'France': 'fr',
    'USA': 'en',
    'Italy': 'it',
    'Germany': 'de',
    'Spain': 'es',
    'Japan': 'ja',
    'United Kingdom': 'en',
    'Switzerland': 'de',
    'UAE': 'ar',
    'Netherlands': 'en',
    'Belgium': 'fr',
    'Australia': 'en',
    'Canada': 'en',
    'Singapore': 'en',
    'Hong Kong': 'zh',
    # Tier 2 中活跃市场
    'Russia': 'ru',
    'China': 'zh',
    'South Korea': 'ko',
    'Saudi Arabia': 'ar',
    'Qatar': 'ar',
    'Kuwait': 'ar',
    'Bahrain': 'ar',
    'Oman': 'ar',
    'Portugal': 'pt',
    'Greece': 'el',
    'Austria': 'de',
    'Sweden': 'sv',
    'Norway': 'no',
    'Denmark': 'da',
    'Finland': 'fi',
    'Poland': 'pl',
    'Czech Republic': 'cs',
    'Hungary': 'hu',
    'Ireland': 'en',
    'New Zealand': 'en',
    'Taiwan': 'zh',
    'Thailand': 'th',
    'Malaysia': 'ms',
    'Indonesia': 'id',
    'Philippines': 'en',
    'Vietnam': 'vi',
    'India': 'en',
    'Brazil': 'pt',
    'Mexico': 'es',
    'Argentina': 'es',
    'South Africa': 'en',
    'Morocco': 'ar',
    'Egypt': 'ar',
    'Turkey': 'tr',
    'Israel': 'he',
    'Lebanon': 'ar',
    'Jordan': 'ar',
    'Ukraine': 'uk',
    'Romania': 'ro',
    'Bulgaria': 'bg',
    'Croatia': 'hr',
    'Slovenia': 'sl',
    'Slovakia': 'sk',
    'Luxembourg': 'fr',
    # Tier 3（默认英文）
}

# 语言的本地名称（用于邮件签名和分隔线）
_LANGUAGE_NAMES = {
    'en': 'English', 'fr': 'Français', 'de': 'Deutsch', 'it': 'Italiano',
    'es': 'Español', 'ja': '日本語', 'ar': 'العربية', 'zh': '中文',
    'pt': 'Português', 'ru': 'Русский', 'ko': '한국어', 'el': 'Ελληνικά',
    'sv': 'Svenska', 'no': 'Norsk', 'da': 'Dansk', 'fi': 'Suomi',
    'pl': 'Polski', 'cs': 'Čeština', 'hu': 'Magyar', 'tr': 'Türkçe',
    'he': 'עברית', 'uk': 'Українська', 'ro': 'Română', 'bg': 'Български',
    'hr': 'Hrvatski', 'sl': 'Slovenščina', 'sk': 'Slovenčina',
    'th': 'ภาษาไทย', 'ms': 'Bahasa Melayu', 'id': 'Bahasa Indonesia',
    'vi': 'Tiếng Việt',
}

# 硬编码备用模板（AI 不可用时的 fallback）
_FALLBACK_TEMPLATES = {
    'en': ("Dear {contact},\n\n"
           "We are a leading CITES-certified caviar producer in China. "
           "Our products are proudly served in Michelin-starred restaurants worldwide. "
           "We would like to explore a potential partnership with {name}.\n\n"
           "Please feel free to contact us for complimentary samples and our current pricing.\n\n"
           "Best regards,\nSales Team | Cerealia Caviar"),
    'fr': ("Cher/Chère {contact},\n\n"
           "Nous sommes un producteur de caviar certifié CITES en Chine. "
           "Nos produits sont présents dans les restaurants étoilés Michelin à travers le monde. "
           "Nous souhaiterions explorer une collaboration avec {name}.\n\n"
           "N'hésitez pas à nous contacter pour des échantillons gratuits et notre grille tarifaire.\n\n"
           "Cordialement,\nÉquipe Commerciale | Cerealia Caviar"),
    'de': ("Sehr geehrte(r) {contact},\n\n"
           "Wir sind ein CITES-zertifizierter Kaviarproduzent in China. "
           "Unsere Produkte werden in Michelin-Restaurants weltweit serviert. "
           "Wir möchten eine Zusammenarbeit mit {name} erkunden.\n\n"
           "Bitte kontaktieren Sie uns für kostenlose Muster und aktuelle Preisinformationen.\n\n"
           "Mit freundlichen Grüßen,\nVertriebsteam | Cerealia Caviar"),
    'it': ("Gentile {contact},\n\n"
           "Siamo un produttore leader di caviale certificato CITES in Cina. "
           "I nostri prodotti sono serviti nei ristoranti Michelin in tutto il mondo. "
           "Vorremmo esplorare una collaborazione con {name}.\n\n"
           "Non esiti a contattarci per campioni gratuiti e listino prezzi.\n\n"
           "Cordiali saluti,\nTeam Vendite | Cerealia Caviar"),
    'es': ("Estimado/a {contact},\n\n"
           "Somos un productor líder de caviar certificado por CITES en China. "
           "Nuestros productos se sirven en restaurantes Michelin en todo el mundo. "
           "Nos gustaría explorar una colaboración con {name}.\n\n"
           "No dude en contactarnos para muestras gratuitas y precios actualizados.\n\n"
           "Atentamente,\nEquipo Comercial | Cerealia Caviar"),
    'ja': ("{contact}様\n\n"
           "私たちは中国初のCITES認証キャビア生産者です。\n"
           "ミシュラン星付きレストランに製品を提供しており、世界中でご評価いただいています。\n"
           "{name}との協業の可能性を探りたいと考えております。\n\n"
           "無料サンプルと料金のご案内をご希望の方は、お気軽にお問い合わせください。\n\n"
           "よろしくお願いいたします。\nCerealia Caviar 営業チーム"),
    'ar': ("عزيزي/عزيزتي {contact}،\n\n"
           "نحن مُنتج رائد للكافيار حاصل على شهادة CITES في الصين. "
           "تُقدَّم منتجاتنا في مطاعم ميشلان حول العالم. "
           "نود استكشاف فرص التعاون مع {name}.\n\n"
           "يُرجى التواصل معنا للحصول على عينات مجانية وأسعارنا الحالية.\n\n"
           "مع أطيب التحيات،\nفريق المبيعات | Cerealia Caviar"),
    'zh': ("尊敬的 {contact}，\n\n"
           "我们是来自中国的领先 CITES 认证鲟鱼子酱生产商，"
           "产品已供应全球米其林餐厅。我们希望与 {name} 探讨合作可能。\n\n"
           "欢迎联系我们获取免费样品和最新报价。\n\n"
           "此致\nCerealia Caviar 销售团队"),
}

# 通用英文主题
_DEFAULT_SUBJECT = "Partnership Inquiry: Premium Chinese Caviar for {name}"


# ── DeepSeek AI 生成 ──────────────────────────────────────────────────────────
def _ai_generate_email(
    company_name: str,
    country: str,
    contact_name: str,
    language: str,
    additional_context: str = None,
) -> dict:
    """
    用 DeepSeek 生成一封地道双语开发信（英文 + 本地语言）。
    如果 AI 不可用，降级到硬编码模板。
    返回 { subject, body_english, body_local, body_combined }
    """
    name = company_name or 'Valued Partner'
    contact = contact_name or 'Team'
    lang_name = _LANGUAGE_NAMES.get(language, language.upper())
    subject = _DEFAULT_SUBJECT.format(name=name)

    extra = f"\n\nAdditional context from sender: {additional_context}" if additional_context else ""

    system_prompt = (
        "You are a professional B2B cold outreach copywriter specializing in premium food and seafood. "
        "You write compelling, personalized cold emails that feel human — not generic template filler. "
        "Rules:\n"
        "1. Each email should be 100-150 words in the target language.\n"
        "2. Start with a personalized hook mentioning the company name or their likely business.\n"
        "3. Briefly establish credibility (CITES-certified, served in Michelin-starred restaurants, HACCP/ISO certified).\n"
        "4. State a clear, low-friction ask (complimentary samples + pricing).\n"
        "5. End with a warm professional sign-off.\n"
        "6. NEVER use overly salesy language. Keep it elegant and professional.\n"
        "7. Always write in proper grammar — do not translate literally from English.\n"
        "8. If the target language uses a non-Latin script, write in that script ONLY (no transliteration).\n"
        "9. Output JSON only: {\"body\": \"...\"} — no markdown, no explanation."
    )

    user_prompt_en = (
        f"Write a bilingual cold outreach email in English. "
        f"This is the English version.\n\n"
        f"Recipient company: {name}\n"
        f"Contact person: {contact}\n"
        f"Country: {country}\n"
        f"Company context: Cerealia Caviar — CITES-certified sturgeon caviar producer from Dujiangyan, China. "
        f"0 additives, 0 preservatives, 48-hour hand-crafted, HACCP/ISO certified. "
        f"Currently serving Michelin-starred restaurants in Europe, Dubai, Japan, Australia.{extra}\n\n"
        f"Write the English version now."
    )

    user_prompt_local = (
        f"Write a cold outreach email in {lang_name}. "
        f"Write ONLY the body text in {lang_name} — do NOT translate from English.\n\n"
        f"Recipient company: {name}\n"
        f"Contact person: {contact}\n"
        f"Country: {country}\n"
        f"Company context: Cerealia Caviar — CITES-certified sturgeon caviar producer from Dujiangyan, China. "
        f"0 additives, 0 preservatives, 48-hour hand-crafted, HACCP/ISO certified. "
        f"Currently serving Michelin-starred restaurants in Europe, Dubai, Japan, Australia.{extra}\n\n"
        f"Write in {lang_name} only."
    )

    try:
        client, model = _get_ai_client()

        # 并发生成英文和本地语言版
        resp_en = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt_en},
            ],
            temperature=0.7,
            max_tokens=800,
        )
        body_english = _extract_json_or_text(resp_en.choices[0].message.content.strip())

        # 如果本地语言不是英文，也生成本地语言版
        if language != 'en':
            resp_local = client.chat.completions.create(
                model=model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt_local},
                ],
                temperature=0.7,
                max_tokens=800,
            )
            body_local = _extract_json_or_text(resp_local.choices[0].message.content.strip())
        else:
            body_local = ''

        return {
            'subject': subject,
            'body_english': body_english,
            'body_local': body_local,
            'ai_generated': True,
        }

    except Exception as e:
        print(f'[EmailGenerator] AI 生成失败，降级到模板: {e}')
        body_english = _FALLBACK_TEMPLATES.get('en', _FALLBACK_TEMPLATES['en']).format(
            contact=contact, name=name
        )
        body_local = _FALLBACK_TEMPLATES.get(language, _FALLBACK_TEMPLATES['en']).format(
            contact=contact, name=name
        ) if language != 'en' else ''
        return {
            'subject': subject,
            'body_english': body_english,
            'body_local': body_local,
            'ai_generated': False,
        }


def _extract_json_or_text(content: str) -> str:
    """提取 AI 返回的 JSON body 或纯文本"""
    try:
        data = json.loads(content)
        if isinstance(data, dict) and 'body' in data:
            return data['body'].strip()
        if isinstance(data, dict) and 'text' in data:
            return data['text'].strip()
    except json.JSONDecodeError:
        pass
    # 去掉可能包裹的 markdown
    match = re.search(r'\{[^}]*"body"[^}]*\}', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())['body'].strip()
        except Exception:
            pass
    return content.strip()


# ── 主生成器 ──────────────────────────────────────────────────────────────────
class EmailGenerator:
    """双语开发信生成器（DeepSeek AI 驱动）"""

    def get_country_language(self, country: str) -> str:
        """根据国家名推断语言"""
        if not country:
            return 'en'
        # 精确匹配
        if country in _COUNTRY_LANGUAGE_MAP:
            return _COUNTRY_LANGUAGE_MAP[country]
        # 部分匹配（如 "France" vs "France metropolitan"）
        for key in _COUNTRY_LANGUAGE_MAP:
            if key.lower() in country.lower() or country.lower() in key.lower():
                return _COUNTRY_LANGUAGE_MAP[key]
        return 'en'

    def generate_bilingual_email(
        self,
        company: dict,
        customer_type: str = None,
        preferred_language: str = None,
        additional_context: str = None,
    ) -> dict:
        """
        生成一封双语开发信。

        Args:
            company: dict，字段包含 company_name_en, country_name, contact_name, email 等
            customer_type: 客户类型（可选）
            preferred_language: 优先语言（可选，默认按国家自动推断）
            additional_context: 补充上下文（可选）

        Returns:
            {
                subject, body_english, body_local, body_combined,
                language_primary, language_secondary,
                template_id, generated_at, company_name, contact_name,
                ai_generated
            }
        """
        company_name = company.get('company_name_en', company.get('company_name', 'Valued Partner'))
        country_name = company.get('country_name', company.get('country', ''))
        contact_name = company.get('contact_name', 'Team')

        # 自动推断语言
        lang = preferred_language or self.get_country_language(country_name)

        result = _ai_generate_email(
            company_name=company_name,
            country=country_name,
            contact_name=contact_name,
            language=lang,
            additional_context=additional_context,
        )

        # 构建合并正文（英文 + 本地语言）
        if result['body_local']:
            body_combined = (
                result['body_english']
                + f"\n\n{'─' * 45}\n"
                + f"{lang.upper()} VERSION\n"
                + f"{'─' * 45}\n\n"
                + result['body_local']
            )
        else:
            body_combined = result['body_english']

        return {
            'subject': result['subject'],
            'body_english': result['body_english'],
            'body_local': result['body_local'],
            'body_combined': body_combined,
            'language_primary': 'en',
            'language_secondary': lang if lang != 'en' else None,
            'template_id': 'DEEPSEEK-AI' if result.get('ai_generated') else 'FALLBACK',
            'generated_at': datetime.now().isoformat(),
            'company_name': company_name,
            'contact_name': contact_name,
            'customer_type': customer_type,
            'ai_generated': result.get('ai_generated', False),
        }

    def generate_batch_preview(
        self,
        companies: list,
        additional_context: str = None,
    ) -> list:
        """
        批量生成预览（不发送）。
        传入公司列表，返回每家公司的邮件预览。
        每个元素包含：company_name, country, email, subject, body_english, body_local
        """
        results = []
        for company in companies:
            email_data = self.generate_bilingual_email(
                company=company,
                preferred_language=None,
                additional_context=additional_context,
            )
            results.append({
                'company_name': email_data['company_name'],
                'country': company.get('country_name', company.get('country', '')),
                'email': company.get('email', ''),
                'contact_name': email_data['contact_name'],
                'subject': email_data['subject'],
                'body_english': email_data['body_english'],
                'body_local': email_data['body_local'],
                'language': email_data['language_secondary'] or email_data['language_primary'],
                'ai_generated': email_data.get('ai_generated', False),
            })
        return results

    def generate_by_template(self, template, variables):
        """根据数据库模板生成邮件"""
        subject = template.subject
        body = template.body_content
        for key, value in (variables or {}).items():
            body = body.replace(f'{{{key}}}', str(value))
            subject = subject.replace(f'{{{key}}}', str(value))
        return {'subject': subject, 'body': body}