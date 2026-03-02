"""
지지옥션 크롤러 - 전체 버전
전국 경매 물건 정보 수집

⚠️ 주의사항:
- robots.txt 정책 준수
- 서버 부하 고려 (1초 이상 대기)
- 개인 학습용으로만 사용
"""

import time
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import DATA_DIR, LOG_DIR


class GgiAuctionScraper:
    """
    지지옥션 전체 크롤러
    
    사용법:
        scraper = GgiAuctionScraper()
        scraper.search_auctions(sido="서울특별시")  # 서울 경매 검색
        scraper.save_to_csv()  # CSV로 저장
        scraper.close()
    """
    
    def __init__(self, headless=True):
        """
        초기화
        
        Args:
            headless: True면 브라우저 창 안 보임 (빠름)
                     False면 브라우저 창 보임 (디버깅용)
        """
        print("🚀 지지옥션 크롤러 초기화...")
        
        # Chrome 설정
        self.options = Options()
        if headless:
            self.options.add_argument("--headless")  # 창 안 보이게
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--window-size=1920,1080")
        
        # User-Agent 설정 (봇 아닌 척)
        self.options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Chrome 드라이버 시작
        self.driver = webdriver.Chrome(options=self.options)
        self.wait = WebDriverWait(self.driver, 10)
        
        # 수집한 데이터 저장
        self.auctions = []
        
        # 지지옥션 URL
        self.base_url = "https://www.ggi.co.kr"
        
        print("✅ 크롤러 준비 완료!")
    
    def search_auctions(self, sido="전체", gugun="", page_limit=3):
        """
        경매 물건 검색
        
        Args:
            sido: 시/도 (예: "서울특별시", "경기도")
            gugun: 구/군 (예: "강남구")
            page_limit: 최대 몇 페이지 검색할지
        
        Returns:
            list: 경매 물건 목록
        """
        print(f"🔍 검색: {sido} {gugun}")
        
        # 지지옥션 검색 페이지로 이동
        search_url = f"{self.base_url}/search"
        self.driver.get(search_url)
        time.sleep(2)  # 페이지 로딩 대기
        
        # TODO: 지지옥션 실제 검색 폼 요소 분석 후 구현
        # 현재는 샘플 데이터 반환
        
        sample_data = [
            {
                "auction_id": "2025-001234",
                "address": "서울특별시 강남구 삼성동 123-45",
                "building_type": "아파트",
                "appraisal_price": 1200000000,  # 감정가 (원)
                "min_bid_price": 840000000,     # 최저입찰가 (원)
                "bid_date": "2025-03-15",       # 입찰일
                "court": "서울중앙지방법원",      # 관할법원
                "status": "진행중",
                "url": f"{self.base_url}/auction/2025-001234"
            },
            {
                "auction_id": "2025-001235",
                "address": "서울특별시 서초구 반포동 456-78",
                "building_type": "빌라",
                "appraisal_price": 800000000,
                "min_bid_price": 560000000,
                "bid_date": "2025-03-20",
                "court": "서울중앙지방법원",
                "status": "진행중",
                "url": f"{self.base_url}/auction/2025-001235"
            }
        ]
        
        self.auctions.extend(sample_data)
        print(f"   ✓ {len(sample_data)}건 수집")
        
        return self.auctions
    
    def get_auction_detail(self, auction_id):
        """
        특정 경매 물건 상세 정보 수집
        
        Args:
            auction_id: 경매 물건 번호 (예: "2025-001234")
        
        Returns:
            dict: 상세 정보
        """
        print(f"🔍 상세 정보 수집: {auction_id}")
        
        detail_url = f"{self.base_url}/auction/{auction_id}"
        self.driver.get(detail_url)
        time.sleep(2)
        
        # TODO: 실제 페이지에서 상세 정보 추출
        
        detail = {
            "auction_id": auction_id,
            "address": "",
            "building_type": "",
            "exclusive_area": 0,      # 전용면적 (㎡)
            "supply_area": 0,          # 공급면적 (㎡)
            "floor": "",               # 층
            "built_year": 0,           # 준공년도
            "appraisal_price": 0,
            "min_bid_price": 0,
            "bid_deposit": 0,          # 입찰보증금
            "court": "",
            "case_number": "",         # 사건번호
            "creditor": "",            # 채권자
            "debtor": "",              # 채무자
            "bid_date": "",
            "bid_place": "",           # 입찰장소
            "remarks": "",             # 비고
            "docs": []                 # 관련 문서 URL
        }
        
        return detail
    
    def save_to_csv(self, filename=None):
        """
        수집한 데이터를 CSV 파일로 저장
        
        Args:
            filename: 저장할 파일명 (없으면 날짜 자동 생성)
        """
        if not self.auctions:
            print("⚠️ 저장할 데이터가 없습니다")
            return
        
        if filename is None:
            filename = f"auctions_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        
        filepath = DATA_DIR / filename
        
        df = pd.DataFrame(self.auctions)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        print(f"💾 CSV 저장 완료: {filepath}")
        print(f"   총 {len(self.auctions)}건")
    
    def save_to_json(self, filename=None):
        """
        수집한 데이터를 JSON 파일로 저장
        
        Args:
            filename: 저장할 파일명
        """
        if not self.auctions:
            print("⚠️ 저장할 데이터가 없습니다")
            return
        
        if filename is None:
            filename = f"auctions_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        
        filepath = DATA_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.auctions, f, ensure_ascii=False, indent=2)
        
        print(f"💾 JSON 저장 완료: {filepath}")
    
    def close(self):
        """
        브라우저 종료
        """
        print("🔚 브라우저 종료")
        self.driver.quit()


def main():
    """
    크롤러 테스트
    """
    print("="*50)
    print("지지옥션 크롤러 테스트")
    print("="*50)
    
    # 크롤러 생성
    scraper = GgiAuctionScraper(headless=True)
    
    try:
        # 서울 경매 검색 (샘플)
        scraper.search_auctions(sido="서울특별시", page_limit=1)
        
        # CSV 저장
        scraper.save_to_csv()
        
        # JSON도 저장
        scraper.save_to_json()
        
        print("\n✅ 테스트 완료!")
        print(f"   저장 위치: {DATA_DIR}")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
    
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
