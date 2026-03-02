"""
경매 분석 웹 대시보드
Streamlit 기반 GUI

실행: streamlit run dashboard/app.py
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from calculator.profit_calculator import AuctionProfitCalculator, format_money
from analyzer.rule_based_analyzer import RuleBasedAnalyzer
import json


def main():
    """
    Streamlit 대시보드
    """
    try:
        import streamlit as st
    except ImportError:
        print("⚠️ Streamlit 설치 필요: pip install streamlit")
        print("대신 CLI 버전 실행...")
        run_cli_version()
        return
    
    st.set_page_config(
        page_title="파파의 경매 투자 도우미",
        page_icon="🏠",
        layout="wide"
    )
    
    # 헤더
    st.title("🏠 파파의 경매 투자 분석 도우미")
    st.markdown("---")
    
    # 사이드바 - 입력
    st.sidebar.header("📋 물건 정보 입력")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        winning_price = st.number_input(
            "낙찰가 (만원)", 
            min_value=1000, 
            value=30000,
            step=1000
        ) * 10000
    with col2:
        appraisal_price = st.number_input(
            "감정가 (만원)",
            min_value=1000,
            value=50000,
            step=1000
        ) * 10000
    
    building_type = st.sidebar.selectbox(
        "건물 유형",
        ["아파트", "빌라", "상가", "토지", "기타"]
    )
    
    area_pyeong = st.sidebar.slider("면적 (평)", 5, 100, 30)
    
    strategy = st.sidebar.radio(
        "투자 전략",
        ["flip", "rent"],
        format_func=lambda x: "단기 매도 💰" if x == "flip" else "임대 수익 🏢"
    )
    
    extra_cost = st.sidebar.number_input(
        "인수 비용 (만원)",
        min_value=0,
        value=3000,
        step=500
    ) * 10000
    
    # 분석 버튼
    st.sidebar.markdown("---")
    analyze_button = st.sidebar.button("🚀 분석 시작!", type="primary")
    
    # 메인 컨텐츠
    if analyze_button:
        with st.spinner("분석 중... 잠시만 기다려 주세요!"):
            # 수익성 계산
            calc = AuctionProfitCalculator()
            result = calc.calculate(
                winning_price=winning_price,
                appraisal_price=appraisal_price,
                building_type=building_type,
                area_pyeong=area_pyeong,
                strategy=strategy,
                accepted_rights_cost=extra_cost,
                repair_needed=True
            )
        
        # 결과 표시
        st.markdown("---")
        st.header("📊 분석 결과")
        
        # KPI 카드
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            roi = result['profit'].get('roi', 0)
            st.metric(
                "수익률 (ROI)",
                f"{roi:.1f}%",
                delta="좋음" if roi > 15 else "보통" if roi > 0 else "위험"
            )
        
        with col2:
            net_profit = result['profit'].get('net_profit', 0)
            st.metric(
                "순수익",
                format_money(net_profit)
            )
        
        with col3:
            safety = result['summary']['safety_margin']
            st.metric(
                "안전마진",
                f"{safety:.1f}%"
            )
        
        with col4:
            recommend = "✅ 추천" if result['summary']['recommend'] else "⚡ 보통"
            st.metric(
                "추천 여부",
                recommend
            )
        
        st.markdown("---")
        
        # 상세 정보
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("💸 비용明细")
            
            costs = result['costs']
            st.write(f"**취득 비용:**")
            st.write(f"- 낙찰가: {format_money(costs['acquisition']['winning_price'])}")
            st.write(f"- 취득세: {format_money(costs['acquisition']['taxes']['total'])}")
            st.write(f"- 명도비: {format_money(costs['acquisition']['eviction'])}")
            st.write(f"- 인수비용: {format_money(costs['acquisition']['accepted_rights'])}")
            st.write(f"- 수리비: {format_money(costs['repair'])}")
            st.write(f"**총 투자금:** {format_money(costs['total_investment'])}")
        
        with col_right:
            st.subheader("💵 예상 수익")
            
            profit = result['profit']
            if strategy == "flip":
                st.write(f"**매도 전략:**")
                st.write(f"- 예상매도가: {format_money(profit['expected_sale_price'])}")
                st.write(f"- 양도세: {format_money(profit['sale_costs']['capital_gains_tax'])}")
                st.write(f"- 중개수수료: {format_money(profit['sale_costs']['brokerage_fee'])}")
                st.write(f"**순수익:** {format_money(profit['net_profit'])}")
            else:
                st.write(f"**임대 전략:**")
                st.write(f"- 월세: {format_money(profit['monthly_rent'])}/월")
                st.write(f"- 연임대수익: {format_money(profit['annual_rent'])}")
                st.write(f"- 순수익(연): {format_money(profit['net_annual_income'])}")
                st.write(f"**ROE:** {profit['roe']:.1f}%")
        
        st.markdown("---")
        
        # JSON 다운로드
        st.subheader("📥 데이터 내보내기")
        result_json = json.dumps(result, ensure_ascii=False, indent=2)
        st.download_button(
            label="JSON 다운로드",
            data=result_json,
            file_name=f"auction_analysis_{result['input']['winning_price']}.json",
            mime="application/json"
        )
    
    else:
        # 초기 화면
        st.info("👈 왼쪽 사이드바에서 물건 정보를 입력하고 '분석 시작!' 버튼을 눌러주세요!")
        
        st.markdown("""
        ### 🎯 사용법
        1. **낙찰가**와 **감정가**를 입력하세요
        2. **건물 유형**과 **면적**을 선택하세요
        3. **투자 전략**을 골라주세요
        4. **분석 시작!** 버튼을 누르면 결과가 나와요
        
        ### 💡 팁
        - 할인율이 30% 이상이면 좋은 물건!
        - 수익률(ROI)이 15% 이상이면 추천
        - 위험 점수가 60 이상이면 주의 필요
        """)


def run_cli_version():
    """Streamlit 없을 때 CLI 버전"""
    print("="*60)
    print(" 경매 분석 도우미 - CLI 버전")
    print("="*60)
    print()
    print("Streamlit 설치 후 웹 버전을 사용하세요:")
    print("  pip install streamlit")
    print("  streamlit run dashboard/app.py")
    print()
    print("현재는 수익성 계산기만 CLI로 사용 가능:")
    print("  python -m calculator.profit_calculator")


if __name__ == "__main__":
    main()
