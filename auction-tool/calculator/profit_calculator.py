"""
수익성 계산기
경매 물건의 모든 비용과 수익을 계산

파파가 이해하기 쉽게!
"""

from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config import TAX_RATES, PROFITABILITY


class AuctionProfitCalculator:
    """
    경매 수익성 계산기
    
    사용법:
        calc = AuctionProfitCalculator()
        result = calc.calculate(
            winning_price=500000000,  # 낙찰가 5억
            appraisal_price=700000000,  # 감정가 7억
            strategy="flip"  # "flip"(단기) 또는 "rent"(임대)
        )
    """
    
    def __init__(self):
        print("🧮 수익성 계산기 준비!")
        
        # 세금 설정 로드
        self.tax_rates = TAX_RATES
        self.profit_config = PROFITABILITY
    
    def calculate(self, winning_price, appraisal_price, 
                  building_type="주택", area_pyeong=30, 
                  strategy="flip", holding_months=6,
                  accepted_rights_cost=0,
                  repair_needed=True):
        """
        수익성 계산
        
        Args:
            winning_price: 낙찰가 (원)
            appraisal_price: 감정가 (원)
            building_type: 주택/상가/토지
            area_pyeong: 면적 (평)
            strategy: "flip"(단기매도) 또는 "rent"(임대)
            holding_months: 보유 기간 (월)
            accepted_rights_cost: 인수 권리 비용 (원)
            repair_needed: 수리 필요 여부
        
        Returns:
            dict: 모든 계산 결과
        """
        print(f"🔍 분석 중: {winning_price:,}원 ({building_type}, {area_pyeong}평)")
        
        # === 1. 취득 비용 계산 ===
        acquisition_costs = self._calc_acquisition_costs(
            winning_price, building_type
        )
        
        # === 2. 명도/인도 비용 ===
        eviction_cost = self._calc_eviction_cost(area_pyeong)
        
        # 총 취득 비용
        total_acquisition = (winning_price + 
                            acquisition_costs['total'] + 
                            eviction_cost + 
                            accepted_rights_cost)
        
        # === 3. 수리 비용 ===
        repair_cost = self._calc_repair_cost(area_pyeong) if repair_needed else 0
        
        # === 4. 보유 비용 (대출 이자) ===
        loan_amount = winning_price * 0.7  # 70% 대출 가정
        holding_cost = self._calc_holding_cost(loan_amount, holding_months)
        
        # 총 투자 비용
        total_investment = total_acquisition + repair_cost + holding_cost
        
        # === 5. 매도/수익 계산 ===
        if strategy == "flip":
            profit_result = self._calc_flip_profit(
                appraisal_price, total_investment, 
                holding_months, winning_price
            )
        else:  # rent
            profit_result = self._calc_rent_yield(
                appraisal_price, total_investment, area_pyeong
            )
        
        return {
            "input": {
                "winning_price": winning_price,
                "appraisal_price": appraisal_price,
                "building_type": building_type,
                "area_pyeong": area_pyeong,
                "strategy": strategy,
                "holding_months": holding_months
            },
            "costs": {
                "acquisition": {
                    "winning_price": winning_price,
                    "taxes": acquisition_costs,
                    "eviction": eviction_cost,
                    "accepted_rights": accepted_rights_cost,
                    "total": total_acquisition
                },
                "repair": repair_cost,
                "holding": holding_cost,
                "total_investment": total_investment
            },
            "profit": profit_result,
            "summary": {
                "safety_margin": (appraisal_price - winning_price) / appraisal_price * 100,
                "profit_margin": profit_result.get("profit_margin", 0),
                "roi": profit_result.get("roi", 0),
                "recommend": profit_result.get("roi", 0) > 15  # 15% 이상이면 추천
            }
        }
    
    def _calc_acquisition_costs(self, winning_price, building_type):
        """취득 세금 계산"""
        
        # 취득세 (고가주택 여부)
        is_high_value = winning_price >= 900000000  # 9억 이상
        
        if is_high_value:
            acq_tax = winning_price * self.tax_rates['acquisition_high']
        else:
            acq_tax = winning_price * self.tax_rates['acquisition_normal']
        
        # 지방교육세 + 농특세
        edu_tax = winning_price * self.tax_rates['education_tax']
        agri_tax = winning_price * self.tax_rates['agriculture_tax']
        
        # 중개보수 (경매는 없음, 매매시만)
        
        total_tax = acq_tax + edu_tax + agri_tax
        
        return {
            "acquisition_tax": int(acq_tax),
            "education_tax": int(edu_tax),
            "agriculture_tax": int(agri_tax),
            "total": int(total_tax),
            "rate": f"{total_tax/winning_price*100:.2f}%"
        }
    
    def _calc_eviction_cost(self, area_pyeong):
        """명도 비용 계산"""
        cost_per_pyeong = self.profit_config['eviction_cost_per_pyeong']
        return int(area_pyeong * cost_per_pyeong)
    
    def _calc_repair_cost(self, area_pyeong):
        """수리 비용 계산"""
        cost_per_pyeong = self.profit_config['repair_cost_per_pyeong']
        return int(area_pyeong * cost_per_pyeong)
    
    def _calc_holding_cost(self, loan_amount, months):
        """보유 비용 (대출 이자)"""
        annual_rate = self.profit_config['loan_interest_rate']
        monthly_rate = annual_rate / 12
        return int(loan_amount * monthly_rate * months)
    
    def _calc_flip_profit(self, appraisal_price, total_cost, months, winning_price):
        """단기 매도 수익 계산"""
        
        # 예상 매도가 (시세의 95% - 급매 가정)
        expected_sale = int(appraisal_price * 0.95)
        
        # 양도 소득세
        profit = expected_sale - winning_price
        if months < 12:
            # 단기 (1년 미만)
            capital_gains = profit * self.tax_rates['capital_gains_short']
        else:
            # 장기
            capital_gains = profit * self.tax_rates['capital_gains_long']
        
        # 중개수수료
        brokerage = expected_sale * self.profit_config['brokerage_fee_rate']
        
        # 총 매도 비용
        sale_costs = int(capital_gains + brokerage)
        
        # 최종 수익
        net_profit = expected_sale - total_cost - sale_costs
        roi = net_profit / total_cost * 100
        
        # 월 수익률 (연환산)
        monthly_roi = roi / months
        
        return {
            "strategy": "flip",
            "expected_sale_price": expected_sale,
            "sale_costs": {
                "capital_gains_tax": int(capital_gains),
                "brokerage_fee": int(brokerage),
                "total": sale_costs
            },
            "net_profit": net_profit,
            "roi": round(roi, 2),
            "roi_annualized": round(monthly_roi * 12, 2),
            "profit_margin": round(net_profit / expected_sale * 100, 2)
        }
    
    def _calc_rent_yield(self, appraisal_price, total_cost, area_pyeong):
        """임대 수익률 계산"""
        
        # 평당 월세 추정 (서울 기준)
        monthly_rent_per_pyeong = 50000  # 평당 5만원
        monthly_rent = area_pyeong * monthly_rent_per_pyeong
        
        # 연간 임대 수익
        annual_rent = monthly_rent * 12
        
        # 공실, 관리비 등 제외 (80% 실수익)
        net_annual_rent = annual_rent * 0.8
        
        # 자기자본 수익률
        own_capital = total_cost * 0.3  # 30% 자기자본
        loan_amount = total_cost * 0.7
        
        # 대출 이자 연간
        annual_interest = loan_amount * self.profit_config['loan_interest_rate']
        
        # 순수익
        net_income = net_annual_rent - annual_interest
        
        # ROE (자기자본 수익률)
        roe = net_income / own_capital * 100
        
        return {
            "strategy": "rent",
            "monthly_rent": monthly_rent,
            "annual_rent": annual_rent,
            "net_annual_income": int(net_income),
            "own_capital": int(own_capital),
            "loan_amount": int(loan_amount),
            "annual_interest": int(annual_interest),
            "gross_yield": round(annual_rent / total_cost * 100, 2),
            "net_yield": round(net_income / total_cost * 100, 2),
            "roe": round(roe, 2)
        }


def format_money(amount):
    """금액 포맷팅"""
    if amount >= 100_000_000:
        return f"{amount/100_000_000:.1f}억원"
    elif amount >= 10_000:
        return f"{amount/10_000:,.0f}만원"
    else:
        return f"{amount:,}원"


def main():
    """테스트"""
    print("="*60)
    print("경매 수익성 계산기 테스트")
    print("="*60)
    
    calculator = AuctionProfitCalculator()
    
    # 테스트 케이스 1: 단기 매도
    print("\n📊 케이스 1: 단기 매도 (Flipping)")
    print("-"*60)
    
    result = calculator.calculate(
        winning_price=490_000_000,      # 낙찰가 4.9억
        appraisal_price=700_000_000,     # 감정가 7억
        building_type="아파트",
        area_pyeong=30,
        strategy="flip",
        holding_months=6,
        accepted_rights_cost=50_000_000,  # 임차인 보증금
        repair_needed=True
    )
    
    print(f"📍 물건: {result['input']['building_type']}, {result['input']['area_pyeong']}평")
    print(f"💰 낙찰가: {format_money(result['input']['winning_price'])}")
    print(f"📈 감정가: {format_money(result['input']['appraisal_price'])}")
    
    print(f"\n💸 취득 비용:")
    print(f"  • 취득세: {format_money(result['costs']['acquisition']['taxes']['acquisition_tax'])}")
    print(f"  • 교육세+농특세: {format_money(result['costs']['acquisition']['taxes']['education_tax'] + result['costs']['acquisition']['taxes']['agriculture_tax'])}")
    print(f"  • 명도비: {format_money(result['costs']['acquisition']['eviction'])}")
    print(f"  • 인수권리: {format_money(result['costs']['acquisition']['accepted_rights'])}")
    print(f"  • 수리비: {format_money(result['costs']['repair'])}")
    
    print(f"\n💵 매도 계산:")
    p = result['profit']
    print(f"  • 예상매도가: {format_money(p['expected_sale_price'])}")
    print(f"  • 양도세: {format_money(p['sale_costs']['capital_gains_tax'])}")
    print(f"  • 중개수수료: {format_money(p['sale_costs']['brokerage_fee'])}")
    
    print(f"\n🎯 결과:")
    print(f"  • 총투자금: {format_money(result['costs']['total_investment'])}")
    print(f"  • 순수익: {format_money(p['net_profit'])} 💰")
    print(f"  • 수익률(ROI): {p['roi']}%")
    print(f"  • 연환산: {p['roi_annualized']}%")
    print(f"  • 안전마진: {result['summary']['safety_margin']:.1f}%")
    print(f"  • 추천: {'✅ 좋음!' if result['summary']['recommend'] else '⚡ 보통'}")
    
    # 테스트 케이스 2: 임대
    print("\n" + "="*60)
    print("📊 케이스 2: 임대 수익 (Yield)")
    print("-"*60)
    
    result2 = calculator.calculate(
        winning_price=300_000_000,
        appraisal_price=450_000_000,
        building_type="빌라",
        area_pyeong=20,
        strategy="rent",
        accepted_rights_cost=0
    )
    
    p2 = result2['profit']
    print(f"월세: {format_money(p2['monthly_rent'])}/월")
    print(f"연임대수익: {format_money(p2['annual_rent'])}")
    print(f"자기자본: {format_money(p2['own_capital'])}")
    print(f"순수익(연): {format_money(p2['net_annual_income'])}")
    print(f"임대수익률: {p2['net_yield']}%")
    print(f"ROE: {p2['roe']}%")
    
    print("\n" + "="*60)
    print("✅ 테스트 완료!")


if __name__ == "__main__":
    main()
