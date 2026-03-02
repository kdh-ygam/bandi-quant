"""
경매 분석 툴 - 통합 시스템
Phase 1~5 완성본

사용법:
    python complete_system.py
"""

import json
from datetime import datetime
from pathlib import Path

# 각 모듈 임포트
from calculator.profit_calculator import AuctionProfitCalculator
from analyzer.rule_based_analyzer import RuleBasedAnalyzer
from notifier.telegram_notifier import ConsoleNotifier


class AuctionAnalyzerSystem:
    """
    통합 경매 분석 시스템
    """
    
    def __init__(self):
        print("🏠 파파의 경매 분석 시스템 v1.0")
        print("="*60)
        
        self.calculator = AuctionProfitCalculator()
        self.analyzer = RuleBasedAnalyzer()
        self.notifier = ConsoleNotifier()
    
    def analyze_auction(self, auction_data, document_text=None):
        """
        완전 분석 실행
        
        Args:
            auction_data: {
                'address': 주소,
                'appraisal_price': 감정가,
                'min_bid_price': 최저입찰가,
                'building_type': 건물유형,
                'area_pyeong': 면적,
                'strategy': 'flip' 또는 'rent'
            }
            document_text: 등기부등본 텍스트 (선택)
        
        Returns:
            dict: 통합 분석 결과
        """
        print(f"\n🔍 분석 시작: {auction_data.get('address', '미확인')}")
        
        # 1. 수익성 분석
        profit_result = self.calculator.calculate(
            winning_price=auction_data['min_bid_price'],
            appraisal_price=auction_data['appraisal_price'],
            building_type=auction_data.get('building_type', '아파트'),
            area_pyeong=auction_data.get('area_pyeong', 30),
            strategy=auction_data.get('strategy', 'flip'),
            accepted_rights_cost=auction_data.get('extra_cost', 0)
        )
        
        # 2. 권리 분석 (등기부 있는 경우)
        if document_text:
            analysis_result = self.analyzer.analyze_document(document_text)
        else:
            # 기본 분석
            analysis_result = {
                'risk_score': 50,
                'malso_date': '확인 필요',
                'accepted_rights': ['확인 필요'],
                'risks': ['등기부 분석 필요'],
                'estimated_cost': 0,
                'advice': '등기부등본 확인 권장',
                'recommend': profit_result['summary']['recommend']
            }
        
        # 3. 통합 결과
        final_result = {
            'timestamp': datetime.now().isoformat(),
            'auction': auction_data,
            'profit_analysis': profit_result,
            'rights_analysis': analysis_result,
            'final_score': self._calculate_final_score(profit_result, analysis_result),
            'recommendation': self._generate_recommendation(profit_result, analysis_result)
        }
        
        return final_result
    
    def _calculate_final_score(self, profit, analysis):
        """최종 점수 계산"""
        profit_score = min(profit['profit'].get('roi', 0) * 2, 50)  # ROI 기반 (최대 50점)
        risk_score = max(50 - analysis.get('risk_score', 50), 0)   # 위험도 (최대 50점)
        
        return profit_score + risk_score
    
    def _generate_recommendation(self, profit, analysis):
        """최종 추천"""
        roi = profit['profit'].get('roi', 0)
        risk = analysis.get('risk_score', 50)
        safe_margin = profit['summary'].get('safety_margin', 30)
        
        if roi > 20 and risk < 40 and safe_margin > 35:
            return "🎯 강력 추천"
        elif roi > 10 and risk < 60:
            return "⚡ 검토 추천"
        elif roi > 0:
            return "📋 보통"
        else:
            return "❌ 비추천"
    
    def print_report(self, result):
        """보고서 출력"""
        print("\n" + "="*60)
        print("📊 분석 결과 보고서")
        print("="*60)
        
        auction = result['auction']
        profit = result['profit_analysis']
        analysis = result['rights_analysis']
        
        # 물건 정보
        print(f"\n📍 {auction.get('address', '주소 미확인')}")
        print(f"   건물: {auction.get('building_type', '-')}, {auction.get('area_pyeong', '-')}평")
        
        # 가격 정보
        print(f"\n💰 가격 정보")
        print(f"   감정가: {profit['input']['appraisal_price']:,}원")
        print(f"   최저입찰가: {profit['input']['winning_price']:,}원")
        print(f"   할인율: {profit['summary']['safety_margin']:.1f}%")
        
        # 수익 정보
        print(f"\n📈 수익 분석 ({'단기매도' if auction.get('strategy') == 'flip' else '임대'})")
        print(f"   ROI: {profit['profit']['roi']:.1f}%")
        print(f"   순수익: {profit['profit']['net_profit']:,}원")
        print(f"   총투자금: {profit['costs']['total_investment']:,}원")
        
        # 권리 정보
        print(f"\n⚠️ 권리 분석")
        print(f"   위험점수: {analysis['risk_score']}/100")
        print(f"   인수비용: {analysis['estimated_cost']:,}원")
        print(f"   주요위험: {', '.join(analysis['risks'][:2])}")
        
        # 최종 평가
        print(f"\n🎯 최종 평가")
        print(f"   종합점수: {result['final_score']}/100")
        print(f"   추천: {result['recommendation']}")
        print(f"\n💡 {analysis['advice']}")
        
        print("\n" + "="*60)
    
    def save_report(self, result, filename=None):
        """보고서 저장"""
        if filename is None:
            addr = result['auction'].get('address', 'unknown').replace(' ', '_')[:20]
            filename = f"report_{addr}_{datetime.now().strftime('%Y%m%d')}.json"
        
        filepath = Path(__file__).parent / "data" / filename
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 보고서 저장: {filepath}")
        return filepath


def demo():
    """
    데모 실행
    """
    print("="*60)
    print("파파의 경매 분석 시스템 - 데모")
    print("="*60)
    
    system = AuctionAnalyzerSystem()
    
    # 테스트 케이스 1: 좋은 물건
    print("\n🎯 테스트 1: 좋은 물건")
    auction1 = {
        "address": "서울 마포구 연남동 123-45",
        "appraisal_price": 600_000_000,
        "min_bid_price": 360_000_000,  # 40% 할인!
        "building_type": "빌라",
        "area_pyeong": 25,
        "strategy": "flip",
        "extra_cost": 20_000_000
    }
    
    document1 = """
    [등기부등본]
    [저당권] OO은행, 2억원, 2023년 5월 15일
    [가압류] 없음
    임차인 없음
    """
    
    result1 = system.analyze_auction(auction1, document1)
    system.print_report(result1)
    
    # 테스트 케이스 2: 위험한 물건
    print("\n🎯 테스트 2: 위험한 물건")
    auction2 = {
        "address": "서울 강남구 청담동 567-89",
        "appraisal_price": 2_000_000_000,
        "min_bid_price": 1_400_000_000,  # 30% 할인
        "building_type": "아파트",
        "area_pyeong": 40,
        "strategy": "flip",
        "extra_cost": 150_000_000
    }
    
    document2 = """
    [등기부등본]
    [저당권] OO은행, 8억원, 2022년 8월 10일
    [임차권] 대항력 있는 임차인, 보증금 1억원
    [유치권] 공사업자, 2천만원
    [가압류] 2건
    """
    
    result2 = system.analyze_auction(auction2, document2)
    system.print_report(result2)
    
    # 결과 저장
    system.save_report(result1, "demo_good_auction.json")
    system.save_report(result2, "demo_risky_auction.json")
    
    print("\n" + "="*60)
    print("✅ 데모 완료!")
    print("="*60)
    print("\n💡 실제 사용:")
    print("   system = AuctionAnalyzerSystem()")
    print("   result = system.analyze_auction(물건정보, 등기부텍스트)")
    print("   system.print_report(result)")


if __name__ == "__main__":
    demo()
