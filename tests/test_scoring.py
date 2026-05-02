"""pytest: 评分引擎单元测试"""
import sys
sys.path.insert(0, '.')
from backend.services.scoring_service import BackgroundScoringEngine


def test_empty_company_min_score():
    engine = BackgroundScoringEngine()
    score = engine.calculate_as_dict({})
    assert 0 <= score['total_score'] <= 100
    assert score['total_score'] < 20  # 无数据应极低分


def test_perfect_company():
    engine = BackgroundScoringEngine()
    data = {
        'company_name_en': 'Petrossian',
        'has_import_history': True,
        'import_frequency': 12,
        'import_volume': 5000,
        'employee_count': 200,
        'annual_revenue': 50_000_000,
        'description': 'Premium caviar, established 1920, global distribution',
        'has_cites_license': True,
        'has_haccp_cert': True,
        'other_certifications': ['BRC', 'ISO22000'],
        'current_suppliers': 'Iranian, Russian farms',
        'has_previous_contact': True,
        'social_followers': 50000,
        'social_links': True,
    }
    score = engine.calculate_as_dict(data)
    assert score['total_score'] >= 60  # 高数据应有高分
    assert score['grade'] in ('A', 'B', 'C', 'D', 'E')
    assert len(score['scores']) == 7  # 7 维度


def test_grade_boundaries():
    engine = BackgroundScoringEngine()
    # 验证评分区间映射
    assert engine._grade(85) == 'A'
    assert engine._grade(84) == 'B'
    assert engine._grade(70) == 'B'
    assert engine._grade(55) == 'C'
    assert engine._grade(40) == 'D'
    assert engine._grade(39) == 'E'


def test_all_grades():
    """验证所有常见输入都返回有效分数"""
    engine = BackgroundScoringEngine()
    cases = [
        {'company_name_en': 'Test A', 'has_import_history': True, 'annual_revenue': 10_000_000},
        {'company_name_en': 'Test B', 'has_import_history': False},
        {'company_name_en': 'Test C', 'has_cites_license': True},
    ]
    for data in cases:
        score = engine.calculate_as_dict(data)
        assert isinstance(score['total_score'], (int, float))
        assert 0 <= score['total_score'] <= 100
