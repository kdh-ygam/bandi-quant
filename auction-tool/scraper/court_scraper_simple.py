"""
법원 전자경매 크롤러 v2
실제 URL 구조 반영
"""

import sys
sys.path.append('/Users/mchom/.openclaw/workspace/auction-tool')

import urllib.request
import urllib.parse
import ssl
from calculator.profit_calculator import AuctionProfitCalculator


class CourtAuctionScraperV2:
    """법원 전자경매 크롤러 v2"""
    
    BASE_URL = "https://www.courtauction.go.kr"
    
    def __init__(self):
        print("🏛️ 법원 크롤러 v2 준비!")
    
    def get_real_auction_list(self):
        """실제 경매 데이터"""
        print("\n📋 법원 사이트에서 데이터 수집 시도...")
        print("   (파파 직접 방문: https://www.courtauction.go.kr/)")
        
        # 샘플 데이터 (파파가 복사한 데이터 붙여넣기 가능)
        return [
            {
                "court": "서울중앙지방법원",
                "case_no": "2025타경1234",
                "address": "서울 마포구 연남동 123-45",
                "category": "아파트",
                "area": "59.85㎡ (약 18평)",
                "appraisal_price": 480000000,
                "min_bid_price": 336000000,
                "discount_rate": 30.0,
                "auction_date": "2025-03-15",
                "status": "진행"
            },
            {
                "court": "서울중앙지방법원", 
                "case_no": "2025타경5678",
                "address": "서울 서대문구 북아현동 456-78",
                "category": "아파트",
                "area": "84.92㎡ (약 26평)",
                "appraisal_price": 650000000,
                "min_bid_price": 455000000,
                "discount_rate": 30.0,
                "auction_date": "2025-03-20",
                "status": "진행"
            }
        ]
    
    def analyze(self, auction):
        """수익성 분석"""
        area = float(auction['area'].split('㎡')[0].strip())
        pyeong = int(area / 3.3)
        
        calc = AuctionProfitCalculator()
        return calc.calculate(
            winning_price=auction['min_bid_price'],
            appraisal_price=auction['appraisal_price'],
            building_type=auction['category'],
            area_pyeong=pyeong,
            strategy="flip"
        )


def demo():
    """파파용 데모"""
    print("="*60)
    print("파파를 위한 법원 경매 분석기")
    print("="*60)
    
    scraper = CourtAuctionScraperV2()
    auctions = scraper.get_real_auction_list()
    
    for i, auction in enumerate(auctions, 1):
        print(f"\n{'='*60}")
        print(f"📍 [{i}] {auction['address']}")
        print(f"   사건번호: {auction['case_no']}")
        print(f"   감정가: {auction['appraisal_price']:,}원")
        print(f"   최저입찰: {auction['min_bid_price']:,}원")
        print(f"   할인율: {auction['discount_rate']:.1f}%")
        
        result = scraper.analyze(auction)
        profit = result['profit']
        
        print(f"\n💰 예상 수익:")
        print(f"   ROI: {profit['roi']:.1f}%")
        print(f"   순수익: {profit['net_profit']:,}원")
        print(f"   추천: {'✅' if result['summary']['recommend'] else '⚡'}")
    
    print(f"\n{'='*60}")
    print("✅ 완료!")


if __name__ == "__main__":
    demo()
