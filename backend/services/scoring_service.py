"""
背调打分服务 - 直接复用 scoring.py 的 BackgroundScoringEngine
"""
from dataclasses import dataclass


@dataclass
class BackgroundScore:
    """背调打分结果数据类"""
    total_score: float
    import_trade_score: int
    company_scale_score: int
    market_position_score: int
    qualification_score: int
    cooperation_potential: int
    social_media_score: int
    responsiveness_score: int
    grade: str
    recommendation: str
    details: dict


class BackgroundScoringEngine:
    """背景打分算法引擎（直接复用 scoring.py）"""

    def calculate_import_trade_score(self, data):
        score = 0
        details = {}
        if data.get('has_import_history'):
            score += 10
            details['has_import_history'] = '有进口历史+10'
            freq = data.get('import_frequency', 0)
            if freq >= 12:
                score += 10
                details['frequency'] = '高频(月) +10'
            elif freq >= 4:
                score += 8
                details['frequency'] = '中频(季) +8'
            elif freq >= 1:
                score += 5
                details['frequency'] = '低频(年) +5'
            volume = data.get('import_volume', 0)
            if volume >= 10000:
                score += 3
            elif volume >= 1000:
                score += 2
            elif volume > 0:
                score += 1
        else:
            details['has_import_history'] = '无进口历史'
        return min(score, 25), details

    def calculate_company_scale_score(self, data):
        emp = data.get('employee_count', 0)
        rev = data.get('annual_revenue', 0)
        if emp >= 500 and rev >= 5e7:
            score, desc = 20, '大型企业'
        elif emp >= 100 and rev >= 1e7:
            score, desc = 16, '中型企业'
        elif emp >= 50 and rev >= 5e6:
            score, desc = 13, '中大型'
        elif emp >= 20 and rev >= 1e6:
            score, desc = 10, '中小型'
        elif emp >= 5 or rev >= 1e5:
            score, desc = 6, '小型'
        else:
            score, desc = 3, '微型/未知'
        return min(score, 20), {'scale': desc}

    def calculate_market_position_score(self, data):
        text = (data.get('description', '') + data.get('company_name_en', '')).lower()
        keywords = {'luxury': 4, 'premium': 4, 'gourmet': 3, 'michelin': 5, 'fine dining': 4}
        total = 0
        for kw, w in keywords.items():
            if kw in text:
                total += w
        score = min(total, 20) if total > 0 else 8
        return score, {'matched_keywords': total}

    def calculate_qualification_score(self, data):
        score = 0
        if data.get('has_cites_license'):
            score += 8
        if data.get('has_haccp_cert'):
            score += 5
        other = data.get('other_certifications', [])
        score += min(len(other) * 2, 4)
        return min(score, 15), {}

    def calculate_cooperation_potential(self, data):
        score = 5
        suppliers = data.get('current_suppliers', '').lower()
        if 'china' not in suppliers and suppliers:
            score += 2
        if data.get('has_previous_contact'):
            score += 1
        return min(score, 10), {}

    def calculate_social_media_score(self, data):
        score = 0
        followers = data.get('social_followers', 0)
        if followers >= 50000:
            score = 5
        elif followers >= 10000:
            score = 4
        elif followers >= 1000:
            score = 2
        elif data.get('social_links'):
            score = 1
        return min(score, 5), {}

    def calculate_responsiveness_score(self, data):
        return 2, {}

    def get_grade_and_recommendation(self, score):
        if score >= 85:
            return 'A', '强烈推荐优先跟进'
        if score >= 70:
            return 'B', '推荐跟进'
        if score >= 55:
            return 'C', '可考虑跟进'
        if score >= 40:
            return 'D', '暂缓跟进'
        return 'E', '不推荐跟进'

    def calculate_full_score(self, company_data):
        import_score, import_details = self.calculate_import_trade_score(company_data)
        scale_score, scale_details = self.calculate_company_scale_score(company_data)
        market_score, market_details = self.calculate_market_position_score(company_data)
        qual_score, _ = self.calculate_qualification_score(company_data)
        coop_score, _ = self.calculate_cooperation_potential(company_data)
        social_score, _ = self.calculate_social_media_score(company_data)
        resp_score, _ = self.calculate_responsiveness_score(company_data)
        total = import_score + scale_score + market_score + qual_score + coop_score + social_score + resp_score
        grade, rec = self.get_grade_and_recommendation(total)
        return BackgroundScore(
            total_score=round(total, 2),
            import_trade_score=import_score,
            company_scale_score=scale_score,
            market_position_score=market_score,
            qualification_score=qual_score,
            cooperation_potential=coop_score,
            social_media_score=social_score,
            responsiveness_score=resp_score,
            grade=grade,
            recommendation=rec,
            details={'import': import_details, 'scale': scale_details, 'market': market_details}
        )

    def calculate_as_dict(self, company_data):
        """计算打分并以 dict 格式返回，适合直接 JSON 序列化"""
        result = self.calculate_full_score(company_data)
        return {
            'total_score': result.total_score,
            'import_trade_score': result.import_trade_score,
            'company_scale_score': result.company_scale_score,
            'market_position_score': result.market_position_score,
            'qualification_score': result.qualification_score,
            'cooperation_potential_score': result.cooperation_potential,
            'social_media_score': result.social_media_score,
            'responsiveness_score': result.responsiveness_score,
            'grade': result.grade,
            'recommendation': result.recommendation,
            'details': result.details
        }


class BatchScoringProcessor:
    """批量打分处理器"""
    def __init__(self):
        self.engine = BackgroundScoringEngine()

    def process_company(self, company):
        return self.engine.calculate_full_score(company)

    def process_batch(self, companies):
        return [self.process_company(c) for c in companies]
