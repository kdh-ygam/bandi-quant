#!/usr/bin/env python3
"""
반디 퀀트 v2.4 - 캔들차트 + 기술적 지표 통합 분석
3개월 기준 + RSI/MACD/볼린저밴드 차트 포함
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

def calculate_indicators(data):
    """기술적 지표 계산 (RSI, MACD, 볼린저밴드)"""
    df = data.copy()
    
    # RSI 계산 (14일)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD 계산 (12, 26, 9)
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # 볼린저밴드 계산 (20일, 2표준편차)
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    # 이동평균선
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    
    return df

def analyze_candlestick_patterns(data):
    """캔들차트 패턴 분석 (3개월 기준)"""
    if len(data) < 10:
        return "데이터 부족"
    
    patterns = []
    recent_3m = data.tail(60)
    closes_3m = recent_3m['Close'].values
    
    # 장기 추세
    if len(closes_3m) >= 20:
        ma20 = np.mean(closes_3m[-20:])
        ma60 = np.mean(closes_3m) if len(closes_3m) >= 60 else np.mean(closes_3m)
        
        if closes_3m[-1] > ma20 > ma60:
            patterns.append("장기상승추세")
        elif closes_3m[-1] < ma20 < ma60:
            patterns.append("장기하락추세")
        else:
            patterns.append("추세전환구간")
    
    # 최근 1개월 상세 패턴
    last_month = data.tail(20)
    
    for i in range(len(last_month) - 1, max(len(last_month) - 5, 0), -1):
        if i < 1:
            continue
        
        curr = last_month.iloc[i]
        prev = last_month.iloc[i-1]
        
        body = abs(curr['Close'] - curr['Open'])
        range_total = curr['High'] - curr['Low']
        
        if range_total > 0 and body / range_total < 0.1:
            patterns.append("도지")
        
        lower_shadow = min(curr['Close'], curr['Open']) - curr['Low']
        upper_shadow = curr['High'] - max(curr['Close'], curr['Open'])
        if lower_shadow > body * 1.5 and upper_shadow < body * 0.5:
            patterns.append("망치형")
        if upper_shadow > body * 1.5 and lower_shadow < body * 0.5:
            patterns.append("슛팅스타")
    
    # 지지/저항선
    recent_low = last_month['Low'].min()
    recent_high = last_month['High'].max()
    current = last_month['Close'].iloc[-1]
    
    if abs(current - recent_low) / recent_low < 0.02:
        patterns.append("저점지지")
    elif abs(current - recent_high) / recent_high < 0.02:
        patterns.append("고점저항")
    
    return " | ".join(patterns[:3]) if patterns else "특이패턴없음"

def create_full_chart(ticker, name, data, output_path):
    """통합 차트 생성: 캔들 + 볼린저 + RSI + MACD"""
    
    # 지표 계산
    df = calculate_indicators(data)
    
    # 서브플롯 4개: 캔들+볼린저, RSI, MACD, 거래량
    fig = plt.figure(figsize=(14, 12))
    gs = fig.add_gridspec(4, 1, height_ratios=[4, 1.5, 1.5, 1.5], hspace=0.05)
    
    ax1 = fig.add_subplot(gs[0])  # 캔들 + 볼린저 + 이동평균
    ax2 = fig.add_subplot(gs[1])  # RSI
    ax3 = fig.add_subplot(gs[2])  # MACD
    ax4 = fig.add_subplot(gs[3])  # 거래량
    
    # 최근 40일 데이터
    df_plot = df.tail(40).copy().reset_index()
    
    # 1. 캔들차트 + 볼린저 + 이동평균
    for idx, row in df_plot.iterrows():
        color = '#E74C3C' if row['Close'] >= row['Open'] else '#27AE60'
        
        height = abs(row['Close'] - row['Open'])
        bottom = min(row['Open'], row['Close'])
        rect = Rectangle((idx - 0.4, bottom), 0.8, max(height, 0.01),
                        facecolor=color, edgecolor=color, linewidth=0.8)
        ax1.add_patch(rect)
        ax1.plot([idx, idx], [row['Low'], row['High']], color=color, linewidth=0.8)
    
    # 볼린저밴드
    ax1.plot(df_plot.index, df_plot['BB_Upper'], '--', color='red', alpha=0.5, label='BB 상단', linewidth=0.8)
    ax1.plot(df_plot.index, df_plot['BB_Middle'], '-', color='orange', alpha=0.7, label='BB 중간(20일)', linewidth=1)
    ax1.plot(df_plot.index, df_plot['BB_Lower'], '--', color='green', alpha=0.5, label='BB 하단', linewidth=0.8)
    
    # 이동평균선
    ax1.plot(df_plot.index, df_plot['MA5'], '-', color='purple', alpha=0.8, label='MA5', linewidth=1.2)
    ax1.plot(df_plot.index, df_plot['MA20'], '-', color='blue', alpha=0.8, label='MA20', linewidth=1.2)
    
    ax1.set_ylabel('가격', fontsize=10, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=8)
    ax1.grid(True, alpha=0.2)
    ax1.set_xlim(-0.5, len(df_plot) - 0.5)
    
    # 2. RSI 차트
    ax2.fill_between(df_plot.index, 30, 70, alpha=0.1, color='gray', label='정상범위')
    ax2.plot(df_plot.index, df_plot['RSI'], '-', color='purple', linewidth=1.5)
    ax2.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='과매수(70)')
    ax2.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='과매도(30)')
    ax2.axhline(y=50, color='gray', linestyle='-', alpha=0.3)
    
    # 현재 RSI 값 표시
    current_rsi = df_plot['RSI'].iloc[-1]
    ax2.scatter([len(df_plot)-1], [current_rsi], s=50, color='red', zorder=5)
    ax2.text(len(df_plot)-1.5, current_rsi+3, f'RSI: {current_rsi:.1f}', 
            fontsize=9, fontweight='bold', color='red')
    
    ax2.set_ylabel('RSI', fontsize=10, fontweight='bold')
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.2)
    
    # 3. MACD 차트
    colors_macd = ['#E74C3C' if h >= 0 else '#27AE60' for h in df_plot['MACD_Hist']]
    ax3.bar(df_plot.index, df_plot['MACD_Hist'], color=colors_macd, alpha=0.7, label='MACD 히스토그램')
    ax3.plot(df_plot.index, df_plot['MACD'], '-', color='blue', label='MACD', linewidth=1.2)
    ax3.plot(df_plot.index, df_plot['MACD_Signal'], '-', color='red', label='시그널', linewidth=1.2)
    ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # 골드/데드 크로스 표시
    for i in range(1, len(df_plot)):
        if df_plot['MACD'].iloc[i-1] < df_plot['MACD_Signal'].iloc[i-1] and \
           df_plot['MACD'].iloc[i] > df_plot['MACD_Signal'].iloc[i]:
            ax3.scatter([i], [df_plot['MACD'].iloc[i]], s=80, color='gold', marker='^', zorder=5)
        elif df_plot['MACD'].iloc[i-1] > df_plot['MACD_Signal'].iloc[i-1] and \
             df_plot['MACD'].iloc[i] < df_plot['MACD_Signal'].iloc[i]:
            ax3.scatter([i], [df_plot['MACD'].iloc[i]], s=80, color='black', marker='v', zorder=5)
    
    ax3.set_ylabel('MACD', fontsize=10, fontweight='bold')
    ax3.legend(loc='upper left', fontsize=8)
    ax3.grid(True, alpha=0.2)
    
    # 4. 거래량 차트
    colors_vol = ['#E74C3C' if df_plot['Close'].iloc[i] >= df_plot['Open'].iloc[i] else '#27AE60' 
                  for i in range(len(df_plot))]
    ax4.bar(df_plot.index, df_plot['Volume'], color=colors_vol, alpha=0.6)
    ax4.set_ylabel('거래량', fontsize=10, fontweight='bold')
    ax4.set_xlabel('날짜', fontsize=10, fontweight='bold')
    ax4.grid(True, alpha=0.2)
    
    # x축 설정
    step = max(1, len(df_plot) // 8)
    dates = [d.strftime('%m/%d') for d in df_plot['Date']]
    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_xticks(range(0, len(df_plot), step))
        ax.set_xticklabels(dates[::step], rotation=45, fontsize=8)
        ax.set_xlim(-0.5, len(df_plot) - 0.5)
    
    # 제목 및 현재가 정보
    current = df_plot['Close'].iloc[-1]
    prev = df_plot['Close'].iloc[-2] if len(df_plot) > 1 else current
    change = ((current / prev) - 1) * 100
    rsi_val = df_plot['RSI'].iloc[-1]
    
    title = f'{name} ({ticker}) - 통합 기술적 분석 차트'
    subtitle = f'현재가: {current:,.0f} ({change:+.1f}%) | RSI: {rsi_val:.1f} | 3개월 기준'
    fig.suptitle(title + '\n' + subtitle, fontsize=13, fontweight='bold', y=0.995)
    
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

def get_stock_data(ticker, period="3mo"):
    """주식 데이터 다운로드"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        return data
    except:
        return None

def send_enhanced_briefing():
    """향상된 브리핑 전송"""
    
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
        
        stock_data = get_stock_data(ticker, period="3mo")
        if stock_data is not None and len(stock_data) >= 40:
            pattern = analyze_candlestick_patterns(stock_data)
            stock['candle_pattern'] = pattern
            
            chart_path = f"/Users/mchom/.openclaw/workspace/full_chart_{ticker.replace('.', '_')}.png"
            create_full_chart(ticker, name, stock_data, chart_path)
            chart_paths.append((stock, chart_path))
    
    # 텔레그램 전송
    TOKEN = "8599663503:AAGfs7Sh2vy6tfHOr9UG-O_lcaG3cjPdH2s"
    CHAT_ID = "6146433054"
    
    for stock, path in chart_paths:
        if os.path.exists(path):
            with open(path, 'rb') as photo:
                url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
                files = {'photo': photo}
                caption = f"📊 {stock['name']} ({stock['ticker']})\n\n🔥 패턴: {stock.get('candle_pattern', '분석중')}\nRSI: {stock['rsi']:.1f} | {stock['recommendation']}\n\n차트 구성: 캔들+볼린저+MA / RSI / MACD / 거래량"
                data = {'chat_id': CHAT_ID, 'caption': caption}
                requests.post(url, files=files, data=data)
    
    return True

if __name__ == "__main__":
    send_enhanced_briefing()
    print("통합 차트 브리핑 완료")
