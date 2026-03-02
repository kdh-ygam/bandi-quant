#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║         반디 퀀트 - 표준 캔들차트 생성기 v3.0                      ║
║                                                                      ║
║  정책: 2026년 2월 28일부터 모든 브리핑 차트는 3개월 캔들차트로     ║
║                                                                      ║
║  기능:                                                               ║
║  • 6개월 OHLCV 캔들차트 (전체 120일 표시)                        ║
║  • 패턴 자동 감지 (망치형, 잉걸불, 모닝스타 등)                    ║
║  • RSI + 볼린저밴드 + 이동평균선                                    ║
║  • 거래량 차트                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

사용법:
    from chart_standard import create_stock_chart
    result = create_stock_chart("PLTR", "팔란티어", "/path/to/output.png")
"""

import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
from datetime import datetime
import os

# 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


def detect_patterns(df):
    """캔들 패턴 자동 감지 - 주요 패턴만, 연한 색상으로"""
    patterns = []
    
    for i in range(2, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        prev2 = df.iloc[i-2] if i >= 2 else None
        
        o, c, h, l = curr['Open'], curr['Close'], curr['High'], curr['Low']
        prev_o, prev_c = prev['Open'], prev['Close']
        
        body = abs(c - o)
        total_range = h - l
        upper_shadow = h - max(o, c)
        lower_shadow = min(o, c) - l
        
        # ========== 강력 패턴만 표시 (중요도 높음) ==========
        
        # 망치형 (Hammer) - 강한 반등 신호
        if lower_shadow > body * 1.8 and upper_shadow < body * 0.4 and c > o:
            patterns.append((i, 'Hammer', 'strong', '#A5D6A7'))  # 연초록
        
        # 잉걸불 (Bullish Engulfing) - 강한 매수 신호
        elif (prev_c < prev_o and c > o and 
              o < prev_c and c > prev_o):
            patterns.append((i, 'Engulfing', 'strong', '#81C784'))  # 연초록
        
        # 버피어 (Bearish Engulfing) - 매도 신호
        elif (prev_c > prev_o and c < o and 
              o > prev_c and c < prev_o):
            patterns.append((i, 'Bear.Engulf', 'strong', '#EF9A9A'))  # 연빨강
        
        # 모닝스타 (Morning Star) - 하락反轉
        if prev2 is not None:
            if (prev2['Close'] < prev2['Open'] and 
                abs(prev['Close'] - prev['Open']) < abs(prev2['Close'] - prev2['Open']) * 0.3 and
                c > o and c > (prev2['Open'] + prev2['Close']) / 2):
                patterns.append((i, 'M.Star', 'strong', '#66BB6A'))  # 중간초록
            
            # 이브닝스타 (Evening Star) - 상승反轉
            elif (prev2['Close'] > prev2['Open'] and 
                  abs(prev['Close'] - prev['Open']) < abs(prev2['Close'] - prev2['Open']) * 0.3 and
                  c < o and c < (prev2['Open'] + prev2['Close']) / 2):
                patterns.append((i, 'E.Star', 'strong', '#E57373'))  # 중간빨강
        
        # ========== 보통 패턴 (선택적 - 생략하거나 매우 연하게) ==========
        # 도지 (Doji) - 중립, 매우 연하게
        if total_range > 0 and body / total_range < 0.1:
            patterns.append((i, 'Doji', 'normal', '#E0E0E0'))  # 매우 연한 회색
    
    return patterns


def calculate_indicators(df):
    """기술적 지표 계산"""
    # RSI (14일)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 볼린저밴드 (20일)
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    # 이동평균선
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    
    # 볼린저밴드 위치 (0-1 사이)
    df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
    
    return df


def create_stock_chart(ticker, name, output_path, period="6mo", days_shown=120, 
                        signal_type=None, signal_strength=None, 
                        historical_signals=None):
    """
    표준 3개월 캔들차트 생성 + AI 신호 화살표 + 과거 신호 표시
    
    Args:
        ticker: 종목 티커
        name: 종목명
        output_path: 저장 경로
        period: Yahoo Finance 기간
        days_shown: 표시할 일수
        signal_type: 현재 신호 'buy'/'sell'/None
        signal_strength: 현재 신호 강도 'strong'/'normal'
        historical_signals: 과거 신호 리스트 [(date, signal_type, strength, price), ...]
    
    Returns:
        dict: 성공/실패 정보
    """
    try:
        # 데이터 다운로드
        print(f"📥 {ticker} 데이터 다운로드 중...")
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        
        if len(df) < 80:
            print(f"⚠️  데이터 부족: {len(df)}일")
            return {'success': False, 'error': 'Not enough data'}
        
        # 지표 계산
        df = calculate_indicators(df)
        patterns = detect_patterns(df)
        
        # 서브플롯 설정
        fig = plt.figure(figsize=(15, 12))
        gs = fig.add_gridspec(4, 1, height_ratios=[4, 1, 1, 1], hspace=0.08)
        
        ax1 = fig.add_subplot(gs[0])  # 캔들차트
        ax2 = fig.add_subplot(gs[1])  # RSI
        ax3 = fig.add_subplot(gs[2])  # 볼린저 위치
        ax4 = fig.add_subplot(gs[3])  # 거래량
        
        # 표시할 최근 데이터
        df_plot = df.tail(days_shown).copy().reset_index()
        
        # ===== 1. 캔들차트 =====
        for idx, row in df_plot.iterrows():
            o, c, h, l = row['Open'], row['Close'], row['High'], row['Low']
            
            # 한국식 색상: 양봉=빨강, 음봉=초록
            color = '#E74C3C' if c >= o else '#27AE60'
            
            # 몸통
            height = max(abs(c - o), 0.01)
            bottom = min(o, c)
            rect = Rectangle((idx - 0.35, bottom), 0.7, height,
                            facecolor=color, edgecolor=color, linewidth=0.8, alpha=0.9)
            ax1.add_patch(rect)
            
            # 꼬리
            ax1.plot([idx, idx], [l, h], color=color, linewidth=1.5)
            
            # 패턴 표시
            actual_idx = idx + len(df) - days_shown
            for p_idx, p_name, p_strength, p_color in patterns:
                if p_idx == actual_idx:
                    y_pos = h * 1.02 if c >= o else l * 0.98
                    bbox_props = dict(boxstyle='round,pad=0.3', facecolor=p_color, 
                                      alpha=0.9, edgecolor='white', linewidth=1.5)
                    ax1.annotate(p_name, xy=(idx, y_pos), fontsize=7, 
                                fontweight='bold', color='white', ha='center',
                                bbox=bbox_props)
                    if p_strength == 'strong':
                        ax1.scatter([idx], [y_pos * 1.03], s=50, color='gold', 
                                   marker='*', zorder=10)
        
        # 볼린저밴드
        ax1.plot(df_plot.index, df_plot['BB_Upper'], '--', color='#E74C3C', 
                alpha=0.5, linewidth=1, label='BB+2σ')
        ax1.plot(df_plot.index, df_plot['BB_Middle'], '-', color='#FF9800', 
                alpha=0.7, linewidth=1.2, label='BB Mid')
        ax1.plot(df_plot.index, df_plot['BB_Lower'], '--', color='#27AE60', 
                alpha=0.5, linewidth=1, label='BB-2σ')
        
        # ===== AI 신호 화살표 (NEW!) =====
        if signal_type and signal_strength:
            last_idx = len(df_plot) - 1
            last_row = df_plot.iloc[-1]
            last_high = last_row['High']
            last_low = last_row['Low']
            
            # 화살표 크기 및 스타일
            arrow_size = 20 if signal_strength == 'strong' else 15
            arrow_color = '#2196F3' if signal_strength == 'strong' else '#64B5F6'
            
            # Y축 범위 계산 (화살표/텍스트 위치용)
            y_min, y_max = ax1.get_ylim()
            y_range = y_max - y_min
            
            if signal_type == 'buy':
                # 매수 신호: 화살표는 캔들 바로 밑에
                # 마지막 캔들의 저점에서 조금만 아래로
                arrow_offset = y_range * 0.015  # Y축 범위의 1.5%
                arrow_y = last_low - arrow_offset
                # 큰 ^ 마커로 화살표 표시
                ax1.scatter([last_idx], [arrow_y], s=400, c=arrow_color,
                          marker='^', edgecolors='white', linewidths=2, zorder=10)
                # 텍스트: 화살표 아래 (Y축 기준 고정 간격)
                strength_text = 'STRONG BUY' if signal_strength == 'strong' else 'BUY'
                text_offset = y_range * 0.04  # Y축 범위의 4%
                text_y = arrow_y - text_offset
                ax1.text(last_idx, text_y, f'⬆ {strength_text}',
                        fontsize=8, fontweight='bold', color=arrow_color,
                        ha='center', va='top',
                        bbox=dict(boxstyle='round,pad=0.35', facecolor='white',
                                 edgecolor=arrow_color, linewidth=1.5, alpha=0.95))
            elif signal_type == 'sell':
                # 매도 신호: 화살표는 캔들 바로 위에
                arrow_offset = y_range * 0.015
                arrow_y = last_high + arrow_offset
                # 큰 v 마커로 화살표 표시
                ax1.scatter([last_idx], [arrow_y], s=400, c='#F44336',
                          marker='v', edgecolors='white', linewidths=2, zorder=10)
                # 텍스트: 화살표 위
                strength_text = 'STRONG SELL' if signal_strength == 'strong' else 'SELL'
                text_offset = y_range * 0.04
                text_y = arrow_y + text_offset
                ax1.text(last_idx, text_y, f'⬇ {strength_text}',
                        fontsize=8, fontweight='bold', color='#F44336',
                        ha='center', va='bottom',
                        bbox=dict(boxstyle='round,pad=0.35', facecolor='white',
                                 edgecolor='#F44336', linewidth=1.5, alpha=0.95))
            
            # 과거 신호도 표시 (NEW!)
            if historical_signals:
                print(f"   📍 과거 신호 {len(historical_signals)}개 표시")
                for i, (sig_date, sig_type, sig_strength, sig_price) in enumerate(historical_signals[:5]):
                    # 날짜를 인덱스로 변환
                    try:
                        from datetime import datetime
                        sig_dt = datetime.strptime(sig_date, '%Y-%m-%d')
                        # 차트에 있는 날짜 찾기
                        chart_dates = df_plot['Date'].dt.date if hasattr(df_plot['Date'], 'dt') else pd.to_datetime(df_plot['Date']).dt.date
                        date_list = list(chart_dates)
                        
                        if sig_dt.date() in date_list:
                            sig_idx = date_list.index(sig_dt.date())
                            sig_row = df_plot.iloc[sig_idx]
                            
                            # 과거 신호는 작은 아이콘으로 표시
                            if sig_type == 'buy':
                                marker_color = '#64B5F6'  # 연한 파랑
                                y_pos = sig_row['Low'] * 0.96
                                marker = '^'
                                label = 'B'
                            else:
                                marker_color = '#EF5350'  # 연한 빨강
                                y_pos = sig_row['High'] * 1.04
                                marker = 'v'
                                label = 'S'
                            
                            # 작은 마커 표시
                            ax1.scatter([sig_idx], [y_pos], s=80, c=marker_color, 
                                      marker=marker, edgecolors='white', linewidths=1.5,
                                      zorder=10, alpha=0.9)
                            # 날짜 라벨
                            ax1.annotate(f'{label}', xy=(sig_idx, y_pos),
                                        fontsize=7, fontweight='bold', color='white',
                                        ha='center', va='center')
                    except Exception as e:
                        continue  # 날짜 변환 실패하면 스킵
        
        # 이동평균선
        ax1.plot(df_plot.index, df_plot['MA5'], '-', color='#9C27B0', 
                alpha=0.8, linewidth=1.3, label='MA5')
        ax1.plot(df_plot.index, df_plot['MA20'], '-', color='#2196F3', 
                alpha=0.8, linewidth=1.3, label='MA20')
        
        ax1.set_ylabel('Price', fontsize=11, fontweight='bold')
        ax1.legend(loc='upper left', fontsize=8, ncol=2)
        ax1.grid(True, alpha=0.15, linestyle='--')
        ax1.set_xlim(-0.5, len(df_plot) - 0.5)
        
        # ===== 2. RSI 차트 =====
        ax2.fill_between(df_plot.index, 30, 70, alpha=0.1, color='gray')
        ax2.plot(df_plot.index, df_plot['RSI'], '-', color='#9C27B0', linewidth=2)
        ax2.axhline(y=70, color='#E74C3C', linestyle='--', alpha=0.5)
        ax2.axhline(y=30, color='#27AE60', linestyle='--', alpha=0.5)
        ax2.axhline(y=50, color='gray', linestyle='-', alpha=0.3)
        
        current_rsi = df_plot['RSI'].iloc[-1]
        ax2.text(len(df_plot)-1.5, current_rsi, f'{current_rsi:.1f}', 
                fontsize=10, fontweight='bold', color='#9C27B0',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
        ax2.set_ylabel('RSI(14)', fontsize=10, fontweight='bold')
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.15)
        
        # ===== 3. 볼린저 위치 =====
        bb_pos = df_plot['BB_Position']
        colors_bb = ['#E74C3C' if p > 0.8 else '#27AE60' if p < 0.2 else '#3498DB' 
                     for p in bb_pos]
        ax3.bar(df_plot.index, bb_pos, color=colors_bb, alpha=0.7)
        ax3.axhline(y=0.8, color='#E74C3C', linestyle='--', alpha=0.5)
        ax3.axhline(y=0.2, color='#27AE60', linestyle='--', alpha=0.5)
        ax3.axhline(y=0.5, color='gray', linestyle='-', alpha=0.3)
        ax3.set_ylabel('BB Pos', fontsize=10, fontweight='bold')
        ax3.set_ylim(0, 1)
        ax3.grid(True, alpha=0.15)
        
        # ===== 4. 거래량 =====
        colors_vol = ['#E74C3C' if df_plot['Close'].iloc[i] >= df_plot['Open'].iloc[i] 
                      else '#27AE60' for i in range(len(df_plot))]
        ax4.bar(df_plot.index, df_plot['Volume'], color=colors_vol, alpha=0.7)
        vol_ma20 = df_plot['Volume'].rolling(window=20).mean()
        ax4.plot(df_plot.index, vol_ma20, '-', color='orange', 
                alpha=0.8, linewidth=1.5, label='Vol MA20')
        ax4.set_ylabel('Volume', fontsize=10, fontweight='bold')
        ax4.set_xlabel('Date', fontsize=10, fontweight='bold')
        ax4.legend(loc='upper left', fontsize=8)
        ax4.grid(True, alpha=0.15)
        
        # x축 설정 (120일 기준)
        step = max(1, len(df_plot) // 10)
        dates = [d.strftime('%m/%d') for d in df_plot['Date']]
        for ax in [ax1, ax2, ax3, ax4]:
            ax.set_xticks(range(0, len(df_plot), step))
            ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)], 
                              rotation=45, fontsize=9)
            ax.set_xlim(-0.5, len(df_plot) - 0.5)
        
        # 제목
        current = df_plot['Close'].iloc[-1]
        prev = df_plot['Close'].iloc[-2]
        change_pct = ((current / prev) - 1) * 100
        
        recent_patterns = list(set([p[1] for p in patterns if p[0] >= len(df) - 60]))
        pattern_str = ', '.join(recent_patterns[-3:]) if recent_patterns else 'None'
        
        # AI 신호 추가
        ai_signal = ""
        if signal_type and signal_strength:
            sig_emoji = "🟢 BUY" if signal_type == 'buy' else "🔴 SELL"
            sig_str = "STRONG" if signal_strength == 'strong' else "WEAK"
            ai_signal = f" | AI: {sig_emoji} ({sig_str})"
        
        # 제목: 종목 이름만 표시 (분류코드 제외)
        title = f'{name} - 6M Candlestick Chart{ai_signal}'
        subtitle = f'Price: ${current:,.2f} ({change_pct:+.1f}%) | RSI: {current_rsi:.1f} | Patterns: {pattern_str}'
        fig.suptitle(title + '\n' + subtitle, fontsize=13, fontweight='bold', y=0.997)
        
        # 저장
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"✅ 차트 생성 완료: {output_path}")
        print(f"   현재가: ${current:.2f} ({change_pct:+.1f}%)")
        print(f"   RSI: {current_rsi:.1f}")
        print(f"   감지된 패턴: {pattern_str}")
        
        return {
            'success': True,
            'price': current,
            'change_pct': change_pct,
            'rsi': current_rsi,
            'patterns': recent_patterns,
            'path': output_path
        }
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        return {'success': False, 'error': str(e)}


# CLI 지원
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        ticker = sys.argv[1]
        name = sys.argv[2]
        output = sys.argv[3] if len(sys.argv) > 3 else f"chart_{ticker}.png"
    else:
        # 테스트용
        ticker = "PLTR"
        name = "Palantir"
        output = "/Users/mchom/.openclaw/workspace/charts/PLTR_standard_3m.png"
    
    create_stock_chart(ticker, name, output)
