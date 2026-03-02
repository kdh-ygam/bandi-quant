#!/usr/bin/env python3
"""
반디 퀀트 - 종목명 매핑
티커 코드 → 한국어/영어 종목명 변환
"""

# 종목명 매핑 (한국 종목은 한글 이름으로!)
STOCK_NAMES = {
    # 반도체
    '000660.KS': 'SK하이닉스',
    '005930.KS': '삼성전자',
    '042700.KS': '한미반도체',
    '001740.KS': 'SK스퀘어',
    'NVDA': 'NVIDIA',
    # 바이오
    '068270.KS': '셀트리온',
    '207940.KS': '삼성바이오',
    '196170.KS': '알테오젠',
    '136480.KS': '하나제약',
    'JNJ': '존슨앤존슨',
    # 전력/인프라
    '010120.KS': 'LS일렉',
    '267260.KS': '현대일렉',
    '051600.KS': '한전KPS',
    '052690.KS': '한전기술',
    '003670.KS': '포스코DX',
    # 신재생에너지
    'NEE': 'NextEra',
    'TE': 'T1에너지',
    'ENPH': 'Enphase',
    'SEDG': 'SolarEdge',
    'FSLR': 'FirstSolar',
    'RUN': 'Sunrun',
    'BE': 'BloomE',
    # AI/소프트웨어
    'PLTR': 'Palantir',
    'AMD': 'AMD',
    'AI': 'C3.ai',
    'SNOW': 'Snowflake',
    'CRWD': 'CrowdStrike',
    'ARM': 'ARM',
    # 자동차
    '005380.KS': '현대차',
    '000270.KS': '기아',
    '012330.KS': '현대모비스',
    '003620.KS': 'KG모빌리티',
    'TSLA': 'Tesla',
    'F': 'Ford',
    'GM': 'GM',
    'RIVN': 'Rivian',
    # 2차 전지
    '373220.KS': 'LG에솔',
    '006400.KS': '삼성SDI',
    '005490.KS': 'POSCO홀딩스',
    '247540.KS': '에코프로',
    'ALB': 'Albemarle',
    'QS': 'QuantumScape',
    # 기타
    'ONON': 'OnRunning'
}

def get_stock_name(ticker):
    """티커 코드를 종목명으로 변환"""
    return STOCK_NAMES.get(ticker, ticker)

if __name__ == "__main__":
    # 테스트
    samples = ['005930.KS', 'NVDA', 'PLTR', '373220.KS']
    for t in samples:
        print(f"{t} → {get_stock_name(t)}")
