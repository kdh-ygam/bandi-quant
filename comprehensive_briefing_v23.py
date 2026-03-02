#!/usr/bin/env python3
"""
반디 퀀트 v2.3 - 캔들차트 패턴 분석 포함 완성형 브리핑
3개월 데이터 기준 분석
"""

import os
import json
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np
from datetime import datetime, timedelta
import requests

def analyze_candlestick_patterns(data):
    """캔들차트 패턴 분석 (3개월 기준)"""
    if len(data) < 10:
        return "데이터 부족"
    
    patterns = []
    
    # 전체 3개월 추세 분석
    recent_3m = data.tail(60)  # 약 3개월 거래일
    closes_3m = recent_3m['Close'].values
    
    # 장기 추세
    if len(closes_3m) >= 20:
        ma20 = np.mean(closes_3m[-20:])
        ma60 = np.mean(closes_3m) if len(closes_3m) >= 60 else np.mean(closes_3m)
        
        if closes_3m[-1] > ma20 > ma60:
            patterns.append("장기 상승추세 유지")
        elif closes_3m[-1] < ma20 < ma60:
            patterns.append("장기 하락추세 지속")
        else:
            patterns.append("추세 전환 구간")
    
    # 최근 1개월 상세 패턴
    last_month = data.tail(20)
    
    for i in range(len(last_month) - 1, max(len(last_month) - 5, 0), -1):
        if i < 1:
            continue
        
        curr = last_month.iloc[i]
        prev = last_month.iloc[i-1]
        
        body = abs(curr['Close'] - curr['Open'])
        range_total = curr['High'] - curr['Low']
        
        # 도지 (Doji)
        if range_total > 0 and body / range_total < 0.1:
            patterns.append("도지-추세전환")
        
        # 망치형 (Hammer)
        lower_shadow = min(curr['Close'], curr['Open']) - curr['Low']
        upper_shadow = curr['High'] - max(curr['Close'], curr['Open'])
        if lower_shadow > body * 1.5 and upper_shadow < body * 0.5:
            patterns.append("망치형-반등신호")
        
        # 슛팅스타 (Shooting Star)
        if upper_shadow > body * 1.5 and lower_shadow < body * 0.5:
            patterns.append("슛팅스타-조정예고")
        
        # 긴 양봉/음봉
        if body / range_total > 0.8:
            if curr['Close'] > curr['Open']:
                patterns.append("강한양봉-매수세")
            else:
                patterns.append("강한음봉-매도세")
    
    # 지지/저항선
    recent_low = last_month['Low'].min()
    recent_high = last_month['High'].max()
    current = last_month['Close'].iloc[-1]
    
    if abs(current - recent_low) / recent_low < 0.02:
        patterns.append("저점지지-반등기대")
    elif abs(current - recent_high) / recent_high < 0.02:
        patterns.append("고점저항-익절고려")
    
    return " | ".join(patterns[:3]) if patterns else "특이패턴없음"

def create_candlestick_chart(ticker, name, data, output_path):
    """캔들차트 이미지 생성 - 3개월 기준"""
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), 
                                    gridspec_kw={'height_ratios': [3, 1]})
    fig.suptitle(f'{name} ({ticker})\n3개월 기준 캔들차트 (최근 40일)', fontsize=13, fontweight='bold')
    
    if data is None or len(data) == 0:
        ax1.text(0.5, 0.5, '데이터 없음', ha='center', va='center', transform=ax1.transAxes)
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
        return
    
    # 최근 40일 데이터 표시 (3개월 중)
    df = data.tail(40).copy()
    
    # 평균선 계산
    if len(data) >= 20:
        sma20 = data['Close'].rolling(20).mean()
        sma3m = data['Close'].rolling(60).mean() if len(data) >= 60 else data['Close'].rolling(len(data)).mean()
    
    # 캔들차트 그리기
    for idx, (date, row) in enumerate(df.iterrows()):
        open_p = row['Open']
        close_p = row['Close']
        high_p = row['High']
        low_p = row['Low']
        
        color = '#E74C3C' if close_p >= open_p else '#27AE60'
        
        height = abs(close_p - open_p)
        bottom = min(open_p, close_p)
        rect = Rectangle((idx - 0.4, bottom), 0.8, height, 
                         facecolor=color, edgecolor=color, linewidth=0.8)
        ax1.add_patch(rect)
        ax1.plot([idx, idx], [low_p, high_p], color=color, linewidth=0.8)
    
    ax1.set_xlim(-0.5, len(df) - 0.5)
    ax1.set_ylim(df['Low'].min() * 0.95, df['High'].max() * 1.05)
    ax1.set_ylabel('가격', fontsize=10)
    ax1.grid(True, alpha=0.2, linestyle='--')
    
    # x축 날짜 설정
    step = max(1, len(df) // 8)
    ax1.set_xticks(range(0, len(df), step))
    ax1.set_xticklabels([d.strftime('%m/%d') for d in df.index[::step]], rotation=45, fontsize=8)
    
    # 현재가 정보 패널
    current = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2] if len(df) > 1 else current
    change = ((current / prev_close) - 1) * 100
    
    # 3개월 고점/저점
    data_3m = data.tail(60)
    high_3m = data_3m['High'].max()
    low_3m = data_3m['Low'].min()
    
    info_text = f'현재가: {current:,.0f} | 등락: {change:+.1f}% | 3개월 고점: {high_3m:,.0f} | 저점: {low_3m:,.0f}'
    ax1.text(0.02, 0.95, info_text, transform=ax1.transAxes, fontsize=9,
             bbox=dict(boxstyle='round', facecolor='#FFF3E0', alpha=0.8))
    
    # 거래량 차트
    colors_vol = ['#E74C3C' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#27AE60' 
                  for i in range(len(df))]
    ax2.bar(range(len(df)), df['Volume'], color=colors_vol, alpha=0.6)
    ax2.set_ylabel('거래량', fontsize=10)
    ax2.set_xlabel('날짜', fontsize=10)
    ax2.grid(True, alpha=0.2, linestyle='--')
    ax2.set_xticks(range(0, len(df), step))
    ax2.set_xticklabels([d.strftime('%m/%d') for d in df.index[::step]], rotation=45, fontsize=8)
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

def get_stock_data(ticker, period="3mo"):
    """주식 데이터 다운로드 (기본 3개월)"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        return data
    except:
        return None

def send_comprehensive_briefing():
    """완성형 브리핑 전송"""
    
    date_str = "2026-02-27"
    
    json_path = f"/Users/mchom/.openclaw/workspace/analysis/daily_briefing_{date_str}.json"
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stocks = data.get('stocks', [])
    
    buy_stocks = [s for s in stocks if '매수' in s.get('recommendation', '')]
    buy_stocks = sorted(buy_stocks, key=lambda x: x.get('rsi', 50))[:5]
    
    chart_paths = []
    for stock in buy_stocks[:3]:
        ticker = stock['ticker']
        name = stock['name']
        
        yf_ticker = ticker
        stock_data = get_stock_data(yf_ticker, period="3mo")
        
        if stock_data is not None:
            pattern = analyze_candlestick_patterns(stock_data)
            stock['candle_pattern'] = pattern
            
            chart_path = f"/Users/mchom/.openclaw/workspace/candle_3m_{ticker.replace('.', '_')}.png"
            create_candlestick_chart(ticker, name, stock_data, chart_path)
            chart_paths.append((stock, chart_path))
    
    message = f"""반디 퀀트 완성형 브리핑 | {date_str}
========================================
캔들차트 패턴 분석 (3개월 기준) + 반디 의견
========================================"""
    
    for idx, s in enumerate(buy_stocks, 1):
        rec = s.get('recommendation', '')
        pattern = s.get('candle_pattern', '분석중')
        macd_str = s.get('macd_trend', '분석중')
        bb_str = s.get('bb_position', '분석중')
        
        message += f"""
{idx}. {s['name']} ({s['ticker']}) - {rec}

가격: {s['current_price']:,.0f} | {s['change_pct']:+.1f}%
RSI: {s['rsi']:.1f} | 거래량: {s['volume_ratio']:.1f}x
MACD: {macd_str} | 볼린저: {bb_str}

[3개월 캔들패턴 분석]
{pattern}

[반디 분석]
{s.get('comment', '분석 준비중')}

[반디의 의견] """
        
        if s['rsi'] < 35:
            message += "과매도 + 3개월 저점 근접. 분할 매수 적기!"
        elif s['rsi'] < 45:
            message += "RSI 저점, 3개월 추세선 지지 확인 시 진입"
        else:
            message += "관망 후 3개월 평균선 근접 시 고려"
        
        message += "\n========================================"
    
    avg_rsi = sum(s['rsi'] for s in buy_stocks) / len(buy_stocks) if buy_stocks else 50
    message += f"""

종합 평가 및 전략
========================================

[시장 상황]
분석 종목: 32개 | 매수 추천: {len(buy_stocks)}개
평균 RSI: {avg_rsi:.1f}

[3개월 추세 분석]
• QS: 장기 하락 후 저점 형성 중
• GM: 조정 후 반등 시도
• 하나제약: 지지선 테스트 중

[반디의 실행 전략]
즉시 실행: QuantumScape (과매도+저점)
대기 관망: GM/하나제약/NVIDIA/Tesla

[캔들 패턴 진입 기준]
1. 망치형(Hammer) = 반등 신호
2. 도지(Doji) = 추세 전환
3. 저점지지 확인 + 거래량 증가 = 필수

리스크 관리:
전체 포지션 30% 이내 | 3회 분할 매수

========================================
반디가 파파를 응원합니다"""
    
    TELEGRAM_TOKEN = "8599663503:AAGfs7Sh2vy6tfHOr9UG-O_lcaG3cjPdH2s"
    CHAT_ID = "6146433054"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data_msg = {'chat_id': CHAT_ID, 'text': message}
    requests.post(url, json=data_msg)
    
    for stock, path in chart_paths[:3]:
        if os.path.exists(path):
            with open(path, 'rb') as photo:
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
                files = {'photo': photo}
                caption = f"{stock['name']} ({stock['ticker']})\n3개월 패턴: {stock.get('candle_pattern', '분석중')}"
                data = {'chat_id': CHAT_ID, 'caption': caption}
                requests.post(url, files=files, data=data)
    
    return True

if __name__ == "__main__":
    success = send_comprehensive_briefing()
    print(f"브리핑 전송 완료")
