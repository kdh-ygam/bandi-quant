"""
법원 전자경매 크롤러
courtauction.go.kr 데이터 수집

사용법:
    from scraper.court_auction_scraper import CourtAuctionScraper
    
    scraper = CourtAuctionScraper()
    auctions = scraper.search_auctions(
        sido="서울",           # 시/도
        gungu="마포구",       # 구/군
        min_price=100000000,  # 최소 1억
        max_price=500000000   # 최대 5억
    )
"""

import urllib.request
import urllib.parse
import urllib.error
import ssl
import json
from pathlib import Path
from datetime import datetime
import re


class CourtAuctionScraper:
    """
    법원 전자경매 크롤러
    
    공식 사이트: https://www.courtauction.go.kr/
    """
    
    BASE_URL = "https://www.courtauction.go.kr"
    SEARCH_URL = f"{BASE_URL}/RetrieveRealEstMulDetailList.laf"
    
    # 지역 코드 매핑 (법원 코드)
    COURT_CODES = {
        "서울": "서울중앙지방법원",
        "부산": "부산지방법원", 
        "대구": "대구지방법원",
        "인천": "인천지방법원",
        "광주": "광주지방법원",
        "대전": "대전지방법원",
        "울산": "울산지방법원",
        "수원": "수원지방법원",
        "창원": "창원지방법원",
        "청주": "청주지방법원",
        "전주": "전주지방법원",
        "춘천": "춘천지방법원",
        "제주": "제주지방법원"
    }
    
    def __init__(self):
        print("🏛️ 법원 전자경매 크롤러 준비!")
        print("   https://www.courtauction.go.kr/")
        self.session_id = None
        self.cookies = {}
    
    def _create_ssl_context(self):
        """SSL 인증 무시 (테스트용, 프로덕션에서는 제거)"""
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
    
    def _make_request(self, url, data=None, headers=None):
        """
        HTTP 요청 (urllib)
        """
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive'
        }
        
        if headers:
            default_headers.update(headers)
        
        # 쿠키 추가
        if self.cookies:
            cookie_str = '; '.join([f"{k}={v}" for k, v in self.cookies.items()])
            default_headers['Cookie'] = cookie_str
        
        try:
            req = urllib.request.Request(
                url,
                data=data.encode('utf-8') if data else None,
                headers=default_headers,
                method='POST' if data else 'GET'
            )
            
            context = self._create_ssl_context()
            response = urllib.request.urlopen(req, context=context, timeout=30)
            
            # 쿠키 저장
            if 'Set-Cookie' in response.headers:
                cookies = response.headers.get('Set-Cookie')
                self._parse_cookies(cookies)
            
            html = response.read().decode('utf-8')
            return html
            
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP 오류: {e.code} - {e.reason}")
            return None
        except Exception as e:
            print(f"❌ 요청 오류: {e}")
            return None
    
    def _parse_cookies(self, cookie_header):
        """쿠키 파싱"""
        if not cookie_header:
            return
        
        # JSESSIONID 등 추출
        for cookie in cookie_header.split(','):
            parts = cookie.strip().split(';')
            if parts:
                key_val = parts[0].strip().split('=')
                if len(key_val) == 2:
                    self.cookies[key_val[0]] = key_val[1]
    
    def get_initial_page(self):
        """
        처음 페이지 접속 (세션 생성)
        """
        print("🔌 법원 사이트 연결 중...")
        url = f"{self.BASE_URL}/index.html"
        html = self._make_request(url)
        
        if html:
            print("✅ 연결 성공!")
            return True
        else:
            print("❌ 연결 실패")
            return False
    
    def search_auctions(self, sido="서울", gungu=None, 
                       building_type="아파트", 
                       min_price=None, max_price=None,
                       page=1):
        """
        경매 물건 검색
        
        Args:
            sido: 시/도 (서울, 부산 등)
            gungu: 구/군 (마포구, 강남구 등)
            building_type: 아파트, 주택, 상가, 토지 등
            min_price: 최소 가격 (원)
            max_price: 최대 가격 (원)
            page: 페이지 번호
        
        Returns:
            list: 검색 결과 목록
        """
        print(f"\n🔍 검색: {sido} {gungu or ''} {building_type}")
        
        # 먼저 세션 생성
        if not self.session_id:
            self.get_initial_page()
        
        # POST 데이터 구성
        # 법원 사이트 실제 파라미터 (변경될 수 있음)
        post_data = {
            'page': str(page),
            'daepyosu': '',
            'realJiwonNm': self.COURT_CODES.get(sido, '서울중앙지방법원'),
            'jipreResult': '',
            'ipchalGbak': '',
            'hangilGbak': '',
            'minbeob': '',
            'maxbeob': '',
            'minYear': '',
            'maxYear': '',
            'dongs': gungu if gungu else '',
            'jibeon': '',
            'saedaeil': '',
            'gamriil': ''
        }
        
        # 가격 필터
        if min_price:
            post_data['minbeob'] = str(min_price)
        if max_price:
            post_data['maxbeob'] = str(max_price)
        
        # URL 인코딩
        encoded_data = urllib.parse.urlencode(post_data)
        
        # 요청
        print("📡 데이터 요청 중...")
        html = self._make_request(self.SEARCH_URL, data=encoded_data)
        
        if html:
            print("✅ 데이터 받기 성공!")
            # 파싱 (간단한 예시)
            return self._parse_auction_list(html)
        else:
            print("❌ 데이터 받기 실패")
            return []
    
    def _parse_auction_list(self, html):
        """
        HTML에서 경매 목록 파싱
        """
        auctions = []
        
        # 간단한 파싱 (실제 구현 시 정규식/BeautifulSoup 필요)
        # 여기서는 샘플 데이터 반환
        
        print("🔍 HTML 파싱 중...")
        
        # 실제 법원 사이트 구조는 복잡해서
        # 여기서는 테스트용 샘플 반환
        sample_auctions = [
            {
                "court": "서울중앙지방법원",
                "case_no": "2024타경12345",
                "category": "아파트",
                "address": "서울 마포구 연남동 123-45 빌라",
                "appraisal_price": 600000000,
                "min_bid_price": 360000000,
                "auction_date": "2025-03-15",
                "status": "진행",
                "url": f"{self.BASE_URL}/RetrieveRealEstDetailInq.laf?jiwonNm=서울중앙지방법원&saNo=2024타경12345"
            },
            {
                "court": "서울중앙지방법원",
                "case_no": "2024타경12346",
                "category": "아파트",
                "address": "서울 서대문구 북아현동 456-78 아파트",
                "appraisal_price": 450000000,
                "min_bid_price": 315000000,
                "auction_date": "2025-03-20",
                "status": "진행",
                "url": f"{self.BASE_URL}/RetrieveRealEstDetailInq.laf?jiwonNm=서울중앙지방법원&saNo=2024타경12346"
            },
            {
                "court": "서울중앙지방법원",
                "case_no": "2024타경12347",
                "category": "상업용",
                "address": "서울 마포구 서교동 789-12 상가",
                "appraisal_price": 800000000,
                "min_bid_price": 560000000,
                "auction_date": "2025-03-25",
                "status": "진행",
                "url": f"{self.BASE_URL}/RetrieveRealEstDetailInq.laf?jiwonNm=서울중앙지방법원&saNo=2024타경12347"
            }
        ]
        
        # TODO: 실제 HTML 파싱 로직 구현
        # 법원 사이트는 복잡한 JavaScript와 세션이 있어
        # selenium 또는 playwright 필요할 수 있음
        
        return sample_auctions
    
    def get_auction_detail(self, court, case_no):
        """
        특정 물건 상세 정보 조회
        
        Args:
            court: 법원명
            case_no: 사건번호
        
        Returns:
            dict: 상세 정보
        """
        detail_url = f"{self.BASE_URL}/RetrieveRealEstDetailInq.laf"
        
        post_data = {
            'jiwonNm': court,
            'saNo': case_no,
            'srnID': 'PNO102001'
        }
        
        encoded_data = urllib.parse.urlencode(post_data)
        html = self._make_request(detail_url, data=encoded_data)
        
        if html:
            return self._parse_detail_html(html, case_no)
        else:
            return None
    
    def _parse_detail_html(self, html, case_no):
        """
        상세 페이지 HTML 파싱
        """
        # TODO: 실제 파싱 구현
        return {
            "case_no": case_no,
            "status": "진행중",
            "detail_html_sample": html[:500] if html else "None"
        }


def test_scraper():
    """
    크롤러 테스트
    """
    print("="*60)
    print("법원 전자경매 크롤러 테스트")
    print("="*60)
    
    scraper = CourtAuctionScraper()
    
    # 테스트 1: 연결
    print("\n🧪 테스트 1: 사이트 연결")
    connected = scraper.get_initial_page()
    
    if not connected:
        print("⚠️ 법원 사이트 연결이 어렵습니다.")
        print("   (방화벽 또는 접속 제한 가능)")
        print("\n💡 샘플 데이터로 테스트 진행...")
    
    # 테스트 2: 검색
    print("\n🧪 테스트 2: 물건 검색")
    auctions = scraper.search_auctions(
        sido="서울",
        gungu="마포구",
        building_type="아파트",
        min_price=300000000,
        max_price=1000000000
    )
    
    print(f"\n📊 검색 결과: {len(auctions)}건")
    
    for i, auction in enumerate(auctions[:3], 1):
        print(f"\n   [{i}] 사건번호: {auction['case_no']}")
        print(f"       주소: {auction['address']}")
        print(f"       감정가: {auction['appraisal_price']:,}원")
        print(f"       최저입찰: {auction['min_bid_price']:,}원")
        print(f"       할인율: {(1 - auction['min_bid_price']/auction['appraisal_price'])*100:.1f}%")
        print(f"       입찰일: {auction['auction_date']}")
    
    # 테스트 3: 상세 조회
    if auctions:
        print("\n🧪 테스트 3: 상세 조회")
        detail = scraper.get_auction_detail(
            auctions[0]['court'],
            auctions[0]['case_no']
        )
        if detail:
            print(f"   사건번호: {detail['case_no']}")
            print(f"   상태: {detail['status']}")
    
    print("\n" + "="*60)
    print("✅ 테스트 완료!")
    print("="*60)
    
    return


if __name__ == "__main__":
    test_scraper()
