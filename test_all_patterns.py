#!/usr/bin/env python3
"""전체 패턴 테스트"""

from chart_module import ChartGenerator, PatternRecognizer
import pandas as pd
import json

gen = ChartGenerator()

# 오늘 분석 결과 불러오기
with open('analysis/daily_briefing_2026-02-26.json', 'r') as f:
    data = json.load(f)

# 테스트 종목 선택
test_tickers = [
    ('QS', 'QuantumScape'),
    ('TSLA', 'Tesla'),
    ('NVDA', 'NVIDIA'),
    ('000660.KS', 'SK하이닉스'),
    ('AAPL', 'Apple'),
]

print("=" * 70)
print("🔍 반디 퀀트 패턴 인식 v1.0 - 전체 테스트")
print("=" * 70)

for ticker, name in test_tickers:
    print(f"\n📊 {name} ({ticker})")
    print("-" * 50)
    
    data = gen.fetch_ohlcv_data(ticker, days=60)
    if not data or len(data['ohlcv']) < 30:
        print("   ❌ 데이터 부족")
        continue
    
    df = pd.DataFrame(data['ohlcv'])
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}, inplace=True)
    df = df.dropna()
    
    recognizer = PatternRecognizer(df)
    results = recognizer.analyze_all_patterns()
    
    # 추세
    print(f"   📈 추세: {results['trend']['emoji']} {results['trend']['trend']}")
    
    # 지지/저항
    sr = results['support_resistance']
    if sr.get('support_desc'):
        print(f"   💰 지지선: {', '.join(sr['support_desc'][:2])}")
    if sr.get('resistance_desc'):
        print(f"   📊 저항선: {', '.join(sr['resistance_desc'][:2])}")
    
    # 패턴들
    if results['patterns']:
        print(f"   🎯 감지된 패턴 ({len(results['patterns'])}개):")
        for p in results['patterns']:
            print(f"      {p['signal']} {p['pattern']}")
    else:
        print("   ➖ 뚜렷한 패턴 미감지")

print("\n" + "=" * 70)
print("✅ 테스트 완료!")
print("=" * 70)
