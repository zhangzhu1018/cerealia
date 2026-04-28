"""
邮件生成服务 - 直接复用 email_templates.py 的 EmailGenerator
"""
from datetime import datetime


class EmailGenerator:
    """双语邮件生成器"""

    LANGUAGE_MAPPING = {
        'France': 'fr',
        'Germany': 'de',
        'Japan': 'ja',
        'UAE': 'ar',
        'Italy': 'it',
        'Spain': 'es',
        'USA': 'en',
        'UK': 'en',
        'Australia': 'en',
    }

    LOCAL_BODIES = {
        'fr': "Cher {contact},\n\nNous sommes un producteur de caviar certifié CITES en Chine. Nos produits sont présents dans les restaurants étoilés Michelin à travers le monde. Nous souhaiterions explorer une collaboration avec {name}.\n\nN'hésitez pas à nous contacter pour des échantillons et notre grille tarifaire.\n\nCordialement,\nÉquipe Commerciale",
        'de': "Sehr geehrte(r) {contact},\n\nWir sind ein CITES-zertifizierter Kaviarproduzent in China. Unsere Produkte werden in Michelin-Restaurants weltweit serviert. Wir möchten eine Zusammenarbeit mit {name} erkunden.\n\nBitte kontaktieren Sie uns für Muster und Preisinformationen.\n\nMit freundlichen Grüßen,\nVertriebsteam",
        'ja': "Dear {contact}様,\n\n私たちは中国初のCITES認証キャビア生産者です。ミシュラン星付きレストランに製品を提供しております。{name}との協業の可能性を探りたいと考えております。\n\nサンプルと価格のご案内をご希望の方は、お気軽にお問い合わせください。\n\nよろしくお願いいたします。",
        'ar': "عزيزي {contact}،\n\nنحن منتج رئيسي للكافيار حاصل على شهادة CITES في الصين. تُقدم منتجاتنا في مطاعم ميشلان حول العالم. نود استكشاف فرص التعاون مع {name}.\n\nيرجى التواصل معنا للحصول على عينات وأسعار.\n\nمع أطيب التحيات،\nفريق المبيعات",
        'it': "Gentile {contact},\n\nSiamo un produttore leader di caviale certificato CITES in Cina. I nostri prodotti sono serviti nei ristoranti Michelin in tutto il mondo. Vorremmo esplorare una collaborazione con {name}.\n\nNon esiti a contattarci per campioni e listino prezzi.\n\nCordiali saluti,\nTeam Vendite",
        'es': "Estimado/a {contact},\n\nSomos un productor líder de caviar certificado por CITES en China. Nuestros productos se sirven en restaurantes Michelin en todo el mundo. Nos gustaría explorar una colaboración con {name}.\n\nNo dude en contactarnos para muestras y precios.\n\nAtentamente,\nEquipo Comercial",
    }

    def get_country_language(self, country):
        return self.LANGUAGE_MAPPING.get(country, 'en')

    def generate_bilingual_email(self, company, customer_type=None, preferred_language=None):
        """
        生成双语邮件

        Args:
            company: dict，company_name_en, country_name, contact_name 等字段
            customer_type: 客户类型（可选）
            preferred_language: 优先语言（可选，默认按国家自动推断）

        Returns:
            dict，含 subject, body_english, body_local, body_combined 等字段
        """
        if not preferred_language:
            preferred_language = self.get_country_language(company.get('country_name', ''))

        name = company.get('company_name_en', 'Valued Partner')
        contact = company.get('contact_name', 'Team')

        subject = f"Partnership Opportunity: Premium Chinese Caviar for {name}"

        body_en = (
            f"Dear {contact},\n\n"
            f"We are a leading CITES-certified caviar producer in China. "
            f"Our products are proudly served in Michelin-starred restaurants worldwide. "
            f"We would like to explore a potential partnership with {name}.\n\n"
            f"Please feel free to contact us for complimentary samples and our current pricing.\n\n"
            f"Best regards,\n"
            f"Sales Team | Cerealia Caviar"
        )

        body_local = self.LOCAL_BODIES.get(preferred_language, '').format(
            contact=contact, name=name
        ) if preferred_language != 'en' else ''

        if body_local:
            combined = (
                body_en +
                f"\n\n─────────────────────────────────────\n"
                f"{preferred_language.upper()} VERSION / {preferred_language.upper()} 版本\n"
                f"─────────────────────────────────────\n\n" +
                body_local
            )
        else:
            combined = body_en

        return {
            'subject': subject,
            'body_english': body_en,
            'body_local': body_local or None,
            'body_combined': combined,
            'language_primary': 'en',
            'language_secondary': preferred_language if preferred_language != 'en' else None,
            'template_id': 'GEN-001',
            'generated_at': datetime.now().isoformat(),
            'company_name': name,
            'contact_name': contact,
            'customer_type': customer_type
        }

    def generate_by_template(self, template, variables):
        """根据数据库模板生成邮件"""
        subject = template.subject
        body = template.body_content
        for key, value in (variables or {}).items():
            body = body.replace(f'{{{key}}}', str(value))
            subject = subject.replace(f'{{{key}}}', str(value))
        return {'subject': subject, 'body': body}
