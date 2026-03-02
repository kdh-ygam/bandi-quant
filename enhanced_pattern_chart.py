#!/usr/bin/env python3
"""
반디 퀀트 v2.5 - 고급 캔들 패턴 자동 감지 + 통합 차트
도지, 망치형, 십자가, 잉걸/버피, 모닝스타, 슛팅스타 등 자동 감지
"""

import os
import json
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D
import numpy as np
from datetime import datetime
import requests


def detect_candlestick_patterns(df):
    """
    고급 캔들 패턴 자동 감지
    반환: [(날짜인덱스, 패턴이름, 신호강도, 색상), ...]
    """
    patterns = []
    
    for i in range(2, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        prev2 = df.iloc[i-2]
        
        # 현재 캔들 속성
        open_c = curr['Open']
        close_c = curr['Close']
        high_c = curr['High']
        low_c = curr['Low']
        
        body = abs(close_c - open_c)
        upper_shadow = high_c - max(open_c, close_c)
        lower_shadow = min(open_c, close_c) - low_c
        total_range = high_c - low_c
        
        # 전일 캔들 속성
        open_p = prev['Open']
        close_p = prev['Close']
        body_p = abs(close_p - open_p)
        
        # ===== 단일 캔들 패턴 =====
        
        # 1. 도지 (Doji) - 몸통이 매우 작거나 없음
        if total_range > 0 and body / total_range < 0.1:
            if lower_shadow > body * 2 or upper_shadow > body * 2:
                if lower_shadow > upper_shadow:
                    patterns.append((i, '망치형 도지', '강함', '#4CAF50'))  # 매수 신호
                else:
                    patterns.append((i, '슛팅스타 도지', '강함', '#F44336'))  # 매도 신호
            else:
                patterns.append((i, '도지', '보통', '#FF9800'))
        
        # 2. 망치형 (Hammer) - 긴 아래꼬리 + 작은 윗꼬리
        elif lower_shadow > body * 1.8 and upper_shadow < body * 0.4 and close_c > open_c:
            patterns.append((i, '망치형', '강함', '#4CAF50'))  # 하락 후 반등
        
        # 3. 역망치형 (Inverted Hammer)
        elif upper_shadow > body * 1.8 and lower_shadow < body * 0.4:
            patterns.append((i, '역망치형', '보통', '#2196F3'))
        
        # 4. 십자가 (Spinning Top) - 몸통 작음 + 위아래 꼬리 길음
        elif body / total_range < 0.3 and upper_shadow > body and lower_shadow > body:
            patterns.append((i, '십자가', '보통', '#FF9800'))
        
        # 5. 긴 양봉 (Long Bullish) - 강한 매수세
        elif body / total_range > 0.7 and close_c > open_c and body > body_p * 1.5:
            patterns.append((i, '강한양봉', '강함', '#4CAF50'))
        
        # 6. 긴 음봉 (Long Bearish) - 강한 매도세
        elif body / total_range > 0.7 and close_c < open_c and body > body_p * 1.5:
            patterns.append((i, '강한음봉', '강함', '#F44336'))
        
        # 7. 도깨비형 (Gravestone Doji) - 상단 꼬리만 길음
        elif upper_shadow > body * 2 and lower_shadow < body * 0.3:
            patterns.append((i, '도깨비형', '보통', '#FF5722'))
        
        # 8. 잠자리형 (Dragonfly Doji) - 하단 꼬리만 길음
        elif lower_shadow > body * 2 and upper_shadow < body * 0.3:
            patterns.append((i, '잠자리형', '강함', '#4CAF50'))  # 강력 반등 신호
        
        # ===== 2캔들 패턴 =====
        
        # 9. 잉걸불 (Bullish Engulfing)
        elif (close_p < open_p and  # 전일 음봉
              close_c > open_c and  # 현재 양봉
              open_c < close_p and  # 현재 시가 < 전일 종가
              close_c > open_p):    # 현재 종가 > 전일 시가
            patterns.append((i, '잉걸불', '강함', '#4CAF50'))
        
        # 10. 버피어 (Bearish Engulfing)
        elif (close_p > open_p and  # 전일 양봉
              close_c < open_c and  # 현재 음봉
              open_c > close_p and  # 현재 시가 > 전일 종가
              close_c < open_p):    # 현재 종가 < 전일 시가
            patterns.append((i, '버피어', '강함', '#F44336'))
        
        # 11. 커버드 (Piercing Line)
        elif (close_p < open_p and  # 전일 음봉
              close_c > open_c and  # 현재 양봉
              open_c < prev['Low'] and    # 갭 하락
              close_c > (open_p + close_p) / 2):  # 전일 중간 돌파
            patterns.append((i, '커버드', '보통', '#2196F3'))
        
        # 12. 다크커버 (Dark Cloud Cover)
        elif (close_p > open_p and  # 전일 양봉
              close_c < open_c and  # 현재 음봉
              open_c > prev['High'] and   # 갭 상승
              close_c < (open_p + close_p) / 2):
            patterns.append((i, '다크커버', '보통', '#FF5722'))
        
        # ===== 3캔들 패턴 =====
        
        if i >= 2:
            prev2_open = prev2['Open']
            prev2_close = prev2['Close']
            
            # 13. 모닝스타 (Morning Star) - 하락反轉
            if (prev2_close < prev2_open and  # 첫날 음봉
                abs(prev['Close'] - prev['Open']) < abs(prev2_close - prev2_open) * 0.3 and  # 둘째날 작은 몸통
                close_c > open_c and  # 셋째날 양봉
                close_c > (prev2_open + prev2_close) / 2):  # 첫날 중간 위로
                patterns.append((i, '모닝스타', '강함', '#4CAF50'))
            
            # 14. 이브닝스타 (Evening Star) - 상승反轉
            elif (prev2_close > prev2_open and  # 첫날 양봉
                  abs(prev['Close'] - prev['Open']) < abs(prev2_close - prev2_open) * 0.3 and
                  close_c < open_c and  # 셋째날 음봉
                  close_c < (prev2_open + prev2_close) / 2):
                patterns.append((i, '이브닝스타', '강함', '#F44336'))
    
    return patterns


def calculate_indicators(data):
    """기술적 지표 계산"""
    df = data.copy()
    
    # RSI (14일)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # 볼린저밴드
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    # 이동평균선
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    
    return df


def create_pattern_chart(ticker, name, data, output_path):
    """패턴 감지 통합 차트 생성"""
    
    # 지표 계산
    df = calculate_indicators(data)
    
    # 패턴 감지
    patterns = detect_candlestick_patterns(df)
    
    # 서브플롯 4개
    fig = plt.figure(figsize=(15, 14))
    gs = fig.add_gridspec(4, 1, height_ratios=[4.5, 1.5, 1.5, 1.5], hspace=0.08)
    
    ax1 = fig.add_subplot(gs[0])  # 캔들 + 패턴 + 볼린저
    ax2 = fig.add_subplot(gs[1])  # RSI
    ax3 = fig.add_subplot(gs[2])  # MACD
    ax4 = fig.add_subplot(gs[3])  # 거래량
    
    # 최근 40일 데이터
    df_plot = df.tail(40).copy().reset_index()
    
    # ===== 캔들차트 + 패턴 표시 =====
    pattern_annotations = []
    
    for idx, row in df_plot.iterrows():
        open_p = row['Open']
        close_p = row['Close']
        high_p = row['High']
        low_p = row['Low']
        
        # 캔들 색상
        color = '#E74C3C' if close_p >= open_p else '#27AE60'
        
        # 몸통
        height = abs(close_p - open_p)
        bottom = min(open_p, close_p)
        rect = Rectangle((idx - 0.35, bottom), 0.7, max(height, 0.01),
                        facecolor=color, edgecolor=color, linewidth=0.8, alpha=0.9)
        ax1.add_patch(rect)
        
        # 꼬리
        ax1.plot([idx, idx], [low_p, high_p], color=color, linewidth=1.5, alpha=0.8)
        
        # 해당 인덱스의 패턴 찾기
        for pattern_idx, pattern_name, strength, pcolor in patterns:
            if pattern_idx == idx + len(df) - 40:  # 전체 데이터에서의 인덱스 변환
                # 패턴 표시
                y_pos = high_p * 1.02 if color == '#E74C3C' else low_p * 0.98
                
                # 패턴 이름 배경 박스
                bbox_props = dict(boxstyle='round,pad=0.3', facecolor=pcolor, 
                                  alpha=0.85, edgecolor='white', linewidth=1.5)
                
                # 화살표 + 텍스트
                ax1.annotate(pattern_name, xy=(idx, y_pos), 
                            xytext=(idx, y_pos * (1.05 if color == '#E74C3C' else 0.95)),
                            fontsize=7, fontweight='bold', color='white',
                            bbox=bbox_props, ha='center', va='center',
                            arrowprops=dict(arrowstyle='->', color=pcolor, lw=1.5))
                
                # 패턴 강도 표시
                if strength == '강함':
                    ax1.scatter([idx], [y_pos], s=100, color=pcolor, 
                               marker='*', zorder=10, edgecolors='white', linewidths=1)
    
    # 볼린저밴드
    ax1.plot(df_plot.index, df_plot['BB_Upper'], '--', color='#E74C3C', 
            alpha=0.6, label='BB Upper', linewidth=1)
    ax1.plot(df_plot.index, df_plot['BB_Middle'], '-', color='#FF9800', 
            alpha=0.8, label='BB Middle', linewidth=1.2)
    ax1.plot(df_plot.index, df_plot['BB_Lower'], '--', color='#27AE60', 
            alpha=0.6, label='BB Lower', linewidth=1)
    
    # 이동평균선
    ax1.plot(df_plot.index, df_plot['MA5'], '-', color='#9C27B0', 
            alpha=0.8, label='MA5', linewidth=1.3)
    ax1.plot(df_plot.index, df_plot['MA20'], '-', color='#2196F3', 
            alpha=0.8, label='MA20', linewidth=1.3)
    
    # 추세선 (최근 10일 선형회귀)
    if len(df_plot) >= 10:
        x = np.arange(10)
        y = df_plot['Close'].values[-10:]
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        trend_x = np.arange(len(df_plot) - 10, len(df_plot))
        ax1.plot(trend_x, p(np.arange(10)), '--', color='gray', 
                alpha=0.5, linewidth=1.5, label='Trend')
    
    ax1.set_ylabel('Price', fontsize=10, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=8, ncol=2)
    ax1.grid(True, alpha=0.15, linestyle='--')
    ax1.set_xlim(-0.5, len(df_plot) - 0.5)
    
    # ===== RSI 차트 =====
    ax2.fill_between(df_plot.index, 30, 70, alpha=0.08, color='gray')
    ax2.plot(df_plot.index, df_plot['RSI'], '-', color='#9C27B0', linewidth=1.5)
    ax2.axhline(y=70, color='#E74C3C', linestyle='--', alpha=0.5, linewidth=1)
    ax2.axhline(y=30, color='#27AE60', linestyle='--', alpha=0.5, linewidth=1)
    ax2.axhline(y=50, color='gray', linestyle='-', alpha=0.3, linewidth=0.8)
    
    # RSI 영역 색상
    ax2.fill_between(df_plot.index, df_plot['RSI'], 30, 
                    where=(df_plot['RSI'] < 35), alpha=0.3, color='#27AE60', label='Oversold')
    ax2.fill_between(df_plot.index, df_plot['RSI'], 70, 
                    where=(df_plot['RSI'] > 65), alpha=0.3, color='#E74C3C', label='Overbought')
    
    current_rsi = df_plot['RSI'].iloc[-1]
    ax2.scatter([len(df_plot)-1], [current_rsi], s=80, color='#9C27B0', zorder=5)
    ax2.text(len(df_plot)-1.8, current_rsi + 5, f'RSI: {current_rsi:.1f}', 
            fontsize=9, fontweight='bold', color='#9C27B0',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax2.set_ylabel('RSI', fontsize=10, fontweight='bold')
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.15)
    
    # ===== MACD 차트 =====
    colors_macd = ['#E74C3C' if h >= 0 else '#27AE60' for h in df_plot['MACD_Hist']]
    ax3.bar(df_plot.index, df_plot['MACD_Hist'], color=colors_macd, alpha=0.7)
    ax3.plot(df_plot.index, df_plot['MACD'], '-', color='#2196F3', label='MACD', linewidth=1.2)
    ax3.plot(df_plot.index, df_plot['MACD_Signal'], '-', color='#FF9800', 
            label='Signal', linewidth=1.2)
    ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=0.8)
    
    # 골드/데드 크로스 표시
    for i in range(1, len(df_plot)):
        if df_plot['MACD'].iloc[i-1] < df_plot['MACD_Signal'].iloc[i-1] and \
           df_plot['MACD'].iloc[i] > df_plot['MACD_Signal'].iloc[i]:
            ax3.scatter([i], [df_plot['MACD'].iloc[i]], s=120, color='#FFD700', 
                       marker='^', zorder=5, edgecolors='black', linewidths=1)
            ax3.annotate('Golden', xy=(i, df_plot['MACD'].iloc[i]), 
                        xytext=(i, df_plot['MACD'].iloc[i] + 0.5),
                        fontsize=7, color='#FFD700', fontweight='bold')
        elif df_plot['MACD'].iloc[i-1] > df_plot['MACD_Signal'].iloc[i-1] and \
             df_plot['MACD'].iloc[i] < df_plot['MACD_Signal'].iloc[i]:
            ax3.scatter([i], [df_plot['MACD'].iloc[i]], s=120, color='black', 
                       marker='v', zorder=5, edgecolors='white', linewidths=1)
            ax3.annotate('Dead', xy=(i, df_plot['MACD'].iloc[i]), 
                        xytext=(i, df_plot['MACD'].iloc[i] - 0.5),
                        fontsize=7, color='black', fontweight='bold')
    
    ax3.set_ylabel('MACD', fontsize=10, fontweight='bold')
    ax3.legend(loc='upper left', fontsize=8)
    ax3.grid(True, alpha=0.15)
    
    # ===== 거래량 차트 =====
    colors_vol = ['#E74C3C' if df_plot['Close'].iloc[i] >= df_plot['Open'].iloc[i] 
                  else '#27AE60' for i in range(len(df_plot))]
    bars = ax4.bar(df_plot.index, df_plot['Volume'], color=colors_vol, alpha=0.7)
    
    # 거래량 평균선
    vol_ma20 = df_plot['Volume'].rolling(window=20).mean()
    ax4.plot(df_plot.index, vol_ma20, '-', color='orange', 
            alpha=0.8, label='Vol MA20', linewidth=1.5)
    
    ax4.set_ylabel('Volume', fontsize=10, fontweight='bold')
    ax4.set_xlabel('Date', fontsize=10, fontweight='bold')
    ax4.legend(loc='upper left', fontsize=8)
    ax4.grid(True, alpha=0.15)
    
    # x축 설정
    step = max(1, len(df_plot) // 8)
    dates = [d.strftime('%m/%d') for d in df_plot['Date']]
    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_xticks(range(0, len(df_plot), step))
        ax.set_xticklabels(dates[::step], rotation=45, fontsize=8)
        ax.set_xlim(-0.5, len(df_plot) - 0.5)
    
    # 제목
    current = df_plot['Close'].iloc[-1]
    prev = df_plot['Close'].iloc[-2] if len(df_plot) > 1 else current
    change = ((current / prev) - 1) * 100
    rsi_val = df_plot['RSI'].iloc[-1] if not np.isnan(df_plot['RSI'].iloc[-1]) else 50
    
    # 패턴 요약
    recent_patterns = [p[1] for p in patterns if p[0] >= len(df) - 42]
    pattern_summary = ', '.join(recent_patterns[-3:]) if recent_patterns else 'No Pattern'
    
    title = f'{name} ({ticker}) - Pattern Detection Chart (40 Days)'
    subtitle = f'Price: {current:,.0f} ({change:+.1f}%) | RSI: {rsi_val:.1f} | Recent: {pattern_summary}'
    fig.suptitle(title + '\n' + subtitle, fontsize=12, fontweight='bold', y=0.997)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return patterns


def get_stock_data(ticker, period="3mo"):
    """주식 데이터 다운로드"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        return data
    except:
        return None


def send_pattern_briefing():
    """패턴 감지 브리핑 전송"""
    
    date_str = "2026-02-27"
    
    # JSON 데이터 로드
    json_path = f"/Users/mchom/.openclaw/workspace/analysis/daily_briefing_{date_str}.json"
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stocks = data.get('stocks', [])
    buy_stocks = [s for s in stocks if '매수' in s.get('recommendation', '')]
    buy_stocks = sorted(buy_stocks, key=lambda x: x.get('rsi', 50))[:5]
    
    TOKEN = "8599663503:AAGfs7Sh2vy6tfHOr9UG-O_lcaG3cjPdH2s"
    CHAT_ID = "6146433054"
    
    # 먼저 텍스트 메시지 전송
    message = """📊 반디 퀀트 v2.5 - 고급 패턴 감지 브리핑
2026년 2월 27일

========================================
🔍 자동 감지된 캔들 패턴:
========================================

✨ 새로운 기능:
• 도지 (Doji) - 추세 전환
• 망치형 (Hammer) - 반등 신호
• 잉걸불/버피어 (Engulfing) - 방향 전환
• 모닝/이브닝 스타 - 3일 반전 패턴
• 십자가 (Spinning Top) - 관망
• 잠자리형 (Dragonfly) - 강한 반등

========================================
"""
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHAT_ID, 'text': message})
    
    # 각 종목 차트 생성 및 전송
    for stock in buy_stocks[:3]:
        ticker = stock['ticker']
        name = stock['name']
        
        stock_data = get_stock_data(ticker, period="3mo")
        if stock_data is not None and len(stock_data) >= 40:
            chart_path = f"/Users/mchom/.openclaw/workspace/pattern_chart_{ticker.replace('.', '_')}.png"
            patterns = create_pattern_chart(ticker, name, stock_data, chart_path)
            
            # 패턴 요약
            recent_patterns = [p[1] for p in patterns if p[0] >= len(stock_data) - 42]
            pattern_text = ', '.join(recent_patterns[-3:]) if recent_patterns else 'No Pattern'
            
            # 매수 신호 패턴 카운트
            buy_signals = [p for p in patterns if p[3] in ['#4CAF50', '#2196F3'] and p[0] >= len(stock_data) - 42]
            sell_signals = [p for p in patterns if p[3] in ['#F44336', '#FF5722'] and p[0] >= len(stock_data) - 42]
            
            caption = f"📊 {name} ({ticker})\n"
            caption += f"RSI: {stock['rsi']:.1f} | {stock['recommendation']}\n"
            caption += f"\n🔍 최근 감지된 패턴: {pattern_text}\n"
            caption += f"📈 매수 신호: {len(buy_signals)}개 | 매도 신호: {len(sell_signals)}개\n\n"
            
            # 패턴 기반 분석
            if '모닝스타' in pattern_text or '망치형' in pattern_text:
                caption += "💡 반디 분석: 반등 패턴 감지! 매수 적기"
            elif '잉걸불' in pattern_text:
                caption += "💡 반디 분석: 매수세 유입 확인! 상승 기대"
            elif '도지' in pattern_text:
                caption += "💡 반디 분석: 추세 전환 예고, 관망 후 진입"
            else:
                caption += "💡 반디 분석: 명확한 패턴 없음, 지표 중심 분석 필요"
            
            if os.path.exists(chart_path):
                with open(chart_path, 'rb') as photo:
                    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
                    files = {'photo': photo}
                    data = {'chat_id': CHAT_ID, 'caption': caption}
                    requests.post(url, files=files, data=data)
    
    return True


if __name__ == "__main__":
    send_pattern_briefing()
    print("패턴 감지 차트 브리핑 완료")
