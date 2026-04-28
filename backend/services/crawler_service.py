"""
客户搜索爬虫服务 - 直接复用 crawler.py 的爬虫逻辑
"""
import time
import random
import re
from urllib.parse import quote
from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent


class CrawlerConfig:
    """爬虫配置"""
    PROXY = None
    REQUEST_DELAY = (2, 5)
    MAX_RETRIES = 3
    TIMEOUT = 30
    OUTPUT_DIR = './crawler_results/'


class BaseCrawler:
    """爬虫基类"""

    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        if CrawlerConfig.PROXY:
            self.session.proxies = {
                'http': CrawlerConfig.PROXY,
                'https': CrawlerConfig.PROXY
            }

    def _get_headers(self):
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

    def _delay(self):
        time.sleep(random.uniform(*CrawlerConfig.REQUEST_DELAY))

    def fetch(self, url):
        for attempt in range(CrawlerConfig.MAX_RETRIES):
            try:
                r = self.session.get(
                    url,
                    headers=self._get_headers(),
                    timeout=CrawlerConfig.TIMEOUT
                )
                if r.status_code == 200:
                    return r.text
            except Exception as e:
                print(f"请求失败 ({attempt + 1}/{CrawlerConfig.MAX_RETRIES}): {e}")
                time.sleep(5)
        return None


class GoogleSearchCrawler(BaseCrawler):
    """Google 搜索爬虫"""

    def build_search_url(self, keyword):
        return f"https://www.google.com/search?q={quote(keyword)}&num=20"

    def extract_results(self, html):
        if not html:
            return []
        soup = BeautifulSoup(html, 'lxml')
        results = []
        for g in soup.select('div.g'):
            title_el = g.select_one('h3')
            link_el = g.select_one('a')
            snippet_el = g.select_one('div[data-content]') or g.select_one('span')
            if title_el and link_el:
                href = link_el.get('href', '')
                if href.startswith('/url?q='):
                    href = href.split('/url?q=')[1].split('&')[0]
                if href and 'google' not in href and href.startswith('http'):
                    results.append({
                        'title': title_el.get_text(strip=True),
                        'url': href,
                        'snippet': snippet_el.get_text(strip=True) if snippet_el else ''
                    })
        return results

    def search(self, keyword, country):
        search_term = keyword.format(country=country)
        url = self.build_search_url(search_term)
        self._delay()
        html = self.fetch(url)
        if html:
            return self.extract_results(html)
        return []


class LinkedInSearchCrawler(BaseCrawler):
    """LinkedIn 搜索爬虫（框架，可扩展）"""

    def search_company(self, company_name):
        search_term = f"site:linkedin.com/company {company_name}"
        url = self.build_search_url(search_term)
        self._delay()
        html = self.fetch(url)
        if html:
            return self.extract_results(html)
        return []


class CustomerSearchController:
    """客户搜索控制器"""

    BASE_KEYWORDS = [
        'caviar importer',
        'caviar wholesale',
        'caviar distributor',
        'premium seafood supplier',
        'luxury food importer',
    ]

    def __init__(self):
        self.google_crawler = GoogleSearchCrawler()

    def _build_keywords(self, country, keyword_type, product_name=None, hs_code=None):
        """根据参数动态构建搜索关键词"""
        keywords = []

        # 确定产品关键词
        if product_name:
            product_kw = product_name.strip()
        elif hs_code:
            product_kw = f'HS {hs_code.strip()}'
        else:
            product_kw = 'caviar'

        # 确定类型关键词
        type_map = {
            'importer': 'importer',
            'wholesaler': 'wholesale distributor',
            'brand': 'caviar brand',
            'distributor': 'distributor',
            'retailer': 'boutique retailer',
            'restaurant': 'restaurant',
        }
        type_kw = type_map.get(keyword_type, 'importer')

        # 组合：{国家} + {产品} + {类型}
        kw = f'{country} {product_kw} {type_kw}'.strip()
        keywords.append(kw)

        # 备用关键词
        for base in self.BASE_KEYWORDS:
            kw2 = f'{country} {product_kw} {base}'.strip()
            if kw2 != kw:
                keywords.append(kw2)

        return keywords[:5]

    def search_by_country(self, country, keyword_type='importer', product_name=None, hs_code=None):
        """按国家 + 产品 + 类型搜索"""
        keywords = self._build_keywords(country, keyword_type, product_name, hs_code)
        results = []

        for kw in keywords:
            try:
                found = self.google_crawler.search(kw, country)
                for item in found:
                    results.append({
                        'company_name_en': item['title'],
                        'website': item['url'],
                        'country': country,
                        'source': 'google',
                        'snippet': item.get('snippet', ''),
                        'product_name': product_name,
                        'hs_code': hs_code,
                    })
                time.sleep(2)
            except Exception as e:
                print(f"关键词 [{kw}] 搜索出错: {e}")
        return results

    def search_by_company_name(self, company_name, country=None):
        """按公司名搜索"""
        kw = f'"{company_name}" caviar OR seafood OR gourmet'
        if country:
            kw += f' {country}'
        url = self.google_crawler.build_search_url(kw)
        google_crawler = GoogleSearchCrawler()
        google_crawler._delay()
        html = google_crawler.fetch(url)
        if html:
            results = google_crawler.extract_results(html)
            return [
                {
                    'company_name_en': r['title'],
                    'website': r['url'],
                    'country': country,
                    'source': 'google',
                    'snippet': r.get('snippet', '')
                }
                for r in results
            ]
        return []

    def run_full_search(self, countries=None, product_name=None, hs_code=None, progress_callback=None):
        """多国家全量搜索，支持按产品和 HS CODE 限定，支持进度回调"""
        if countries is None:
            countries = ['France', 'USA', 'Japan', 'Germany', 'UAE', 'Italy', 'Spain', 'Australia', 'UK']
        all_results = []
        total_countries = len(countries)

        for i, c in enumerate(countries):
            print(f"[Crawler] 搜索国家: {c} | 产品: {product_name or '鲟鱼子酱'} | HS: {hs_code or '无'}")
            results = self.search_by_country(c, keyword_type='importer', product_name=product_name, hs_code=hs_code)
            all_results.extend(results)
            print(f"[Crawler] {c} 完成，找到 {len(results)} 条结果")
            # 进度回调：报告当前国家序号和名称
            if progress_callback:
                progress_callback(i + 1, total_countries, c)
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
