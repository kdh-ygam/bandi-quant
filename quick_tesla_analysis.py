#!/usr/bin/env python3
"""Tesla 단독 분석 - 반디 퀀트 (차트 포함)"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime
import os

# 차트 모듈 임포트
try:
    from chart_standard import create_stock_chart
    CHART_AVAILABLE = True
except ImportError:
    CHART_AVAILABLE = False
    print("⚠️ chart_standard 미설치 - 차트 생략")

# 차트 저장 경로
CHART_DIR = "/Users/mchom/.openclaw/workspace/charts"
os.makedirs(CHART_DIR, exist_ok=True)

print('=' * 60)
print('📊 반디 퀀트 - Tesla (TSLA) 단독 분석')
print('=' * 60)
print(f'⏰ {datetime.now().strftime("%Y-%m-%d %H:%M")} KST')
print()

# 데이터 수집
df = yf.download('TSLA', period='6mo', progress=False)

# 멀티인덱스 컬럼 처리
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

if len(df) < 30:
    print('데이터 부족')
    exit()

# 값 추출 함수
def to_float(val):
    if hasattr(val, 'item'):
        return float(val.item())
    return float(val)

# 현재가 계산
current = to_float(df['Close'].iloc[-1])
previous = to_float(df['Close'].iloc[-2])
change_pct = ((current - previous) / previous) * 100

print(f'💰 현재가: {current:,.0f}$ (전일대비 {change_pct:+.2f}%)')
print()

# RSI 계산
delta = df['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
rsi_vals = 100 - (100 / (1 + rs))
rsi = to_float(rsi_vals.iloc[-1])
rsi_status = '과매수 🔴' if rsi > 70 else '과매도 🟢' if rsi < 30 else '중립'
print(f'📈 RSI(14): {rsi:.1f} ({rsi_status})')

# MACD
ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
macd_line = ema_12 - ema_26
macd_signal = macd_line.ewm(span=9, adjust=False).mean()
macd_val = to_float(macd_line.iloc[-1])
macd_sig = to_float(macd_signal.iloc[-1])
macd_trend = '📈 상승세' if macd_val > macd_sig else '📉 하락세'
print(f'📊 MACD: {macd_trend}')

# 볼린저밴드
bb_mid = df['Close'].rolling(20).mean()
bb_std = df['Close'].rolling(20).std()
bb_up = bb_mid + (bb_std * 2)
bb_low = bb_mid - (bb_std * 2)
bb_pos_val = (current - to_float(bb_low.iloc[-1])) / (to_float(bb_up.iloc[-1]) - to_float(bb_low.iloc[-1]))

if bb_pos_val > 0.95:
    bb_status = '🚀 상단돌파'
elif bb_pos_val < 0.05:
    bb_status = '📉 하단이탈'
elif bb_pos_val > 0.7:
    bb_status = '🔼 상단접근'
elif bb_pos_val < 0.3:
    bb_status = '🔽 하단접근'
else:
    bb_status = '➖ 중간'
print(f'📐 볼린저밴드: {bb_status} ({bb_pos_val:.1%})')

# 거래량
vol = to_float(df['Volume'].iloc[-1])
vol_ma = to_float(df['Volume'].rolling(20).mean().iloc[-1])
vol_ratio = vol / vol_ma if vol_ma > 0 else 1.0
vol_status = '🔥 폭발' if vol_ratio > 2 else '📊 증가' if vol_ratio > 1 else '💤 보통'
print(f'📊 거래량: {vol_ratio:.1f}x 평균 ({vol_status})')

# 20일 고가/저가
high_20 = to_float(df['High'].tail(20).max())
low_20 = to_float(df['Low'].tail(20).min())
print(f'📈 20일 고가: {high_20:,.0f}$')
print(f'📉 20일 저가: {low_20:,.0f}$')
print()

# 간단한 ML 규칙 기반 예측
score = 0.5
if rsi < 35: 
    score += 0.3
elif rsi > 70: 
    score -= 0.3
if macd_val > 0: 
    score += 0.2
else: 
    score -= 0.2
if bb_pos_val > 0.8: 
    score -= 0.1
if vol_ratio > 1.5: 
    score += 0.1

direction = '📈 상승' if score > 0.5 else '📉 하락'
confidence = min(abs(score - 0.5) * 2, 1.0)

print('=' * 60)
print(f'🤖 반디 AI 예측: {direction} (신뢰도 {confidence:.0%})')
print('=' * 60)

# 패턴 감지
print()
print('🔍 최근 캔들 분석:')
for i in range(3, 0, -1):
    row = df.iloc[-i]
    o = to_float(row['Open'])
    c = to_float(row['Close'])
    h = to_float(row['High'])
    l = to_float(row['Low'])
    body = abs(c - o)
    total = h - l
    color = '🔴 양봉' if c >= o else '🟢 음봉'
    date = df.index[-i].strftime('%m/%d')
    print(f'   {date}: {color} | {o:,.0f}$ → {c:,.0f}$')
    
    patterns = []
    if total > 0 and body / total < 0.1:
        patterns.append('도지')
    lower = min(o, c) - l
    upper = h - max(o, c)
    if lower > body * 1.5 and c > o:
        patterns.append('망치형')
    if upper > body * 2 and c < o:
        patterns.append('슈팅스타')
    
    if patterns:
        print(f'         → 📍 {", ".join(patterns)} 패턴')

print()
print('💡 반디의 종합 의견:')
if rsi > 70 and macd_val < macd_sig:
    print('   🔴 조정 가능성 큼')
    print('   • RSI 과매수 + MACD 하락세')
    print('   • 단기 익절 및 관망 권장')
elif rsi < 40 and macd_val > macd_sig:
    print('   🟢 반등 기대')
    print('   • RSI 과매도 + MACD 상승세')
    print('   • 분할 매수 전략 고려')
elif bb_pos_val > 0.8:
    print('   🟡 상단 부근')
    print('   • 볼린저 상단 접근 - 추가상승 여력 제한')
    print('   • 익절 및 관망')
elif bb_pos_val < 0.2:
    print('   🟡 하단 부근')
    print('   • 볼린저 하단 접근 - 반등 기대')
    print('   • 매수 검토')
else:
    print(f'   ⚪ 중립')
    print(f'   • RSI {rsi:.1f}, MACD {macd_trend}')
    print(f'   • 현재 추세 유지 예상')

print()
print(f'🎯 현재 등급: ', end='')
if rsi > 70 or (macd_val < 0 and rsi > 60):
    print('🟠 매도권유')
elif rsi < 35 or (macd_val > 0 and rsi < 45):
    print('🟡 매수권유')
else:
    print('⚪ 보유')

print()
print('반디가 파파를 응$합니다 🐾')

# 📊 차트 생성
if CHART_AVAILABLE:
    print()
    print('=' * 60)
    print('📊 차트 생성 중...')
    print('=' * 60)
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # 신호 타입 결정
    if rsi < 35:
        signal_type = 'buy'
        signal_strength = 'strong'
    elif rsi > 70:
        signal_type = 'sell'  
        signal_strength = 'strong'
    elif score > 0.6:
        signal_type = 'buy'
        signal_strength = 'normal'
    elif score < 0.4:
        signal_type = 'sell'
        signal_strength = 'normal'
    else:
        signal_type = None
        signal_strength = None
    
    chart_path = f"{CHART_DIR}/Tesla_단독분석_{date_str}.png"
    
    result = create_stock_chart(
        ticker='TSLA',
        name='Tesla',
        output_path=chart_path,
        signal_type=signal_type,
        signal_strength=signal_strength
    )
    
    if result.get('success'):
        print(f'✅ 차트 생성 완료: {chart_path}')
        price_val = result['price']
        rsi_chart = result['rsi']
        patterns_chart = result['patterns']
        print(f'   가격: {price_val:,.0f}$')
        print(f'   RSI: {rsi_chart:.1f}')
        print(f'   패턴: {patterns_chart}')
    else:
        print(f'⚠️ 차트 생성 실패: {result.get("error")}')
else:
    print()
    print('⚠️ 차트 모듈 없음 - 텍스트 분석만 제공됨')
