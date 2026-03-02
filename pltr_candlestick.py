#!/usr/bin/env python3
"""
반디 퀀트 - PLTR 캔들차트 생성 (최신 버전 v2.5)
패턴 자동 감지 + 기술적 지표 통합
"""
import os
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import numpy as np
from datetime import datetime

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'

def detect_candlestick_patterns(df):
    """캔들 패턴 자동 감지"""
    patterns = []
    
    for i in range(2, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        prev2 = df.iloc[i-2]
        
        open_c = curr['Open']
        close_c = curr['Close']
        high_c = curr['High']
        low_c = curr['Low']
        
        body = abs(close_c - open_c)
        upper_shadow = high_c - max(open_c, close_c)
        lower_shadow = min(open_c, close_c) - low_c
        total_range = high_c - low_c
        
        open_p = prev['Open']
        close_p = prev['Close']
        
        # 도지
        if total_range > 0 and body / total_range < 0.1:
            patterns.append((i, 'Doji', 'normal', '#FF9800'))
        
        # 망치형 (Hammer)
        elif lower_shadow > body * 1.8 and upper_shadow < body * 0.4 and close_c > open_c:
            patterns.append((i, 'Hammer', 'strong', '#4CAF50'))
        
        # 잉걸불 (Bullish Engulfing)
        elif (close_p < open_p and close_c > open_c and 
              open_c < close_p and close_c > open_p):
            patterns.append((i, 'Engulfing', 'strong', '#4CAF50'))
        
        # 버피어 (Bearish Engulfing)
        elif (close_p > open_p and close_c < open_c and 
              open_c > close_p and close_c < open_p):
            patterns.append((i, 'Bear Engulf', 'strong', '#F44336'))
        
        # 모닝스타 (Morning Star)
        elif (prev2['Close'] < prev2['Open'] and 
              abs(prev['Close'] - prev['Open']) < abs(prev2['Close'] - prev2['Open']) * 0.3 and
              close_c > open_c and 
              close_c > (prev2['Open'] + prev2['Close']) / 2):
            patterns.append((i, 'MorningStar', 'strong', '#4CAF50'))
        
        # 긴 양봉
        elif body / total_range > 0.7 and close_c > open_c:
            patterns.append((i, 'Strong Bull', 'normal', '#4CAF50'))
        
        # 긴 음봉
        elif body / total_range > 0.7 and close_c < open_c:
            patterns.append((i, 'Strong Bear', 'normal', '#F44336'))
    
    return patterns


def calculate_indicators(df):
    """기술적 지표 계산"""
    # RSI (14일)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 볼린저밴드
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    # 이동평균선
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    
    return df


def create_candlestick_chart(ticker, output_path):
    """캔들차트 생성"""
    
    # 데이터 다운로드
    print(f"Downloading {ticker} data...")
    stock = yf.Ticker(ticker)
    df = stock.history(period="3mo")
    
    if len(df) < 40:
        print("Error: Not enough data")
        return None
    
    # 지표 계산
    df = calculate_indicators(df)
    patterns = detect_candlestick_patterns(df)
    
    # 서브플롯 설정
    fig = plt.figure(figsize=(15, 12))
    gs = fig.add_gridspec(4, 1, height_ratios=[4, 1, 1, 1], hspace=0.08)
    
    ax1 = fig.add_subplot(gs[0])  # 캔들 + 패턴
    ax2 = fig.add_subplot(gs[1])  # RSI
    ax3 = fig.add_subplot(gs[2])  # 볼린저밴드 위치
    ax4 = fig.add_subplot(gs[3])  # 거래량
    
    # 최근 40일 데이터
    df_plot = df.tail(40).copy().reset_index()
    
    # ===== 캔들차트 =====
    pattern_annotations = []
    
    for idx, row in df_plot.iterrows():
        open_p = row['Open']
        close_p = row['Close']
        high_p = row['High']
        low_p = row['Low']
        
        # 캔들 색상 (한국식: 양봉=빨강, 음봉=초록)
        color = '#E74C3C' if close_p >= open_p else '#27AE60'
        
        # 몸통
        height = abs(close_p - open_p)
        bottom = min(open_p, close_p)
        rect = Rectangle((idx - 0.35, bottom), 0.7, max(height, 0.01),
                        facecolor=color, edgecolor=color, linewidth=0.8, alpha=0.9)
        ax1.add_patch(rect)
        
        # 꼬리 (위아래)
        ax1.plot([idx, idx], [low_p, high_p], color=color, linewidth=1.5)
        
        # 패턴 표시
        actual_idx = idx + len(df) - 40
        for pattern_idx, pattern_name, strength, pcolor in patterns:
            if pattern_idx == actual_idx:
                y_pos = high_p * 1.015 if close_p >= open_p else low_p * 0.985
                bbox_props = dict(boxstyle='round,pad=0.3', facecolor=pcolor, 
                                  alpha=0.85, edgecolor='white', linewidth=1)
                ax1.annotate(pattern_name, xy=(idx, y_pos), 
                            fontsize=7, fontweight='bold', color='white',
                            bbox=bbox_props, ha='center', va='center',
                            rotation=0)
                if strength == 'strong':
                    ax1.scatter([idx], [y_pos], s=60, color=pcolor, 
                               marker='*', zorder=10, edgecolors='white')
    
    # 볼린저밴드
    ax1.plot(df_plot.index, df_plot['BB_Upper'], '--', color='#E74C3C', 
            alpha=0.5, label='BB Upper', linewidth=1)
    ax1.plot(df_plot.index, df_plot['BB_Middle'], '-', color='#FF9800', 
            alpha=0.7, label='BB Middle', linewidth=1.2)
    ax1.plot(df_plot.index, df_plot['BB_Lower'], '--', color='#27AE60', 
            alpha=0.5, label='BB Lower', linewidth=1)
    
    # 이동평균선
    ax1.plot(df_plot.index, df_plot['MA5'], '-', color='#9C27B0', 
            alpha=0.8, label='MA5', linewidth=1.3)
    ax1.plot(df_plot.index, df_plot['MA20'], '-', color='#2196F3', 
            alpha=0.8, label='MA20', linewidth=1.3)
    
    ax1.set_ylabel('Price ($)', fontsize=11, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=8, ncol=2)
    ax1.grid(True, alpha=0.2, linestyle='--')
    ax1.set_xlim(-0.5, len(df_plot) - 0.5)
    
    # ===== RSI 차트 =====
    ax2.fill_between(df_plot.index, 30, 70, alpha=0.08, color='gray')
    ax2.plot(df_plot.index, df_plot['RSI'], '-', color='#9C27B0', linewidth=2)
    ax2.axhline(y=70, color='#E74C3C', linestyle='--', alpha=0.6, linewidth=1)
    ax2.axhline(y=30, color='#27AE60', linestyle='--', alpha=0.6, linewidth=1)
    ax2.axhline(y=50, color='gray', linestyle='-', alpha=0.3)
    
    current_rsi = df_plot['RSI'].iloc[-1]
    ax2.text(len(df_plot)-1.5, current_rsi + 4, f'{current_rsi:.1f}', 
            fontsize=10, fontweight='bold', color='#9C27B0',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    ax2.set_ylabel('RSI(14)', fontsize=10, fontweight='bold')
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.2)
    
    # ===== 볼린저밴드 위치 차트 =====
    bb_position = (df_plot['Close'] - df_plot['BB_Lower']) / (df_plot['BB_Upper'] - df_plot['BB_Lower'])
    colors_bb = ['#E74C3C' if p > 0.8 else '#27AE60' if p < 0.2 else '#3498DB' for p in bb_position]
    ax3.bar(df_plot.index, bb_position, color=colors_bb, alpha=0.7)
    ax3.axhline(y=0.8, color='#E74C3C', linestyle='--', alpha=0.5, label='Overbought (0.8)')
    ax3.axhline(y=0.2, color='#27AE60', linestyle='--', alpha=0.5, label='Oversold (0.2)')
    ax3.axhline(y=0.5, color='gray', linestyle='-', alpha=0.3)
    ax3.set_ylabel('BB Position', fontsize=10, fontweight='bold')
    ax3.set_ylim(0, 1)
    ax3.legend(loc='upper left', fontsize=8)
    ax3.grid(True, alpha=0.2)
    
    # ===== 거래량 차트 =====
    colors_vol = ['#E74C3C' if df_plot['Close'].iloc[i] >= df_plot['Open'].iloc[i] 
                  else '#27AE60' for i in range(len(df_plot))]
    ax4.bar(df_plot.index, df_plot['Volume'], color=colors_vol, alpha=0.7)
    
    # 거래량 평균선
    vol_ma20 = df_plot['Volume'].rolling(window=20).mean()
    ax4.plot(df_plot.index, vol_ma20, '-', color='orange', 
            alpha=0.8, label='Vol MA20', linewidth=1.5)
    
    ax4.set_ylabel('Volume', fontsize=10, fontweight='bold')
    ax4.set_xlabel('Date', fontsize=10, fontweight='bold')
    ax4.legend(loc='upper left', fontsize=8)
    ax4.grid(True, alpha=0.2)
    
    # x축 설정
    step = max(1, len(df_plot) // 8)
    dates = [d.strftime('%m/%d') for d in df_plot['Date']]
    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_xticks(range(0, len(df_plot), step))
        ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)], 
                          rotation=45, fontsize=9)
        ax.set_xlim(-0.5, len(df_plot) - 0.5)
    
    # 제목 및 정보
    current = df_plot['Close'].iloc[-1]
    prev = df_plot['Close'].iloc[-2]
    change = ((current / prev) - 1) * 100
    rsi_val = df_plot['RSI'].iloc[-1]
    
    # 패턴 요약
    recent_patterns = [p[1] for p in patterns if p[0] >= len(df) - 42]
    pattern_text = ', '.join(list(set(recent_patterns))[-3:]) if recent_patterns else 'None'
    
    title = f'Palantir (PLTR) - Candlestick Pattern Chart (40 Days)'
    subtitle = f'Price: ${current:.2f} ({change:+.1f}%) | RSI: {rsi_val:.1f} | Patterns: {pattern_text}'
    fig.suptitle(title + '\n' + subtitle, fontsize=13, fontweight='bold', y=0.997)
    
    # 저장
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Chart saved: {output_path}")
    print(f"Latest: ${current:.2f} ({change:+.1f}%)")
    print(f"RSI: {rsi_val:.1f}")
    print(f"Patterns detected: {pattern_text}")
    
    return {
        'price': current,
        'change': change,
        'rsi': rsi_val,
        'patterns': recent_patterns
    }


if __name__ == "__main__":
    output = "/Users/mchom/.openclaw/workspace/charts/PLTR_candlestick_20260228.png"
    result = create_candlestick_chart("PLTR", output)
    print("\nDone!")
