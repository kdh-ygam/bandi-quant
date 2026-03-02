#!/usr/bin/env python3
"""
반디 퀀트 v2.2 - 완성형 브리핑 생성기
차트 이미지 + 분석 요약 + 의견 + 종합 평가
"""

import os
import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from datetime import datetime
import requests

# 텔레그램 설정
TELEGRAM_TOKEN = "8599663503:AAGfs7Sh2vy6tfHOr9UG-O_lcaG3cjPdH2s"
CHAT_ID = "6146433054"

def create_chart_image(stocks_data, output_path):
    """추천 종목 차트 이미지 생성"""
    
    # 한글 폰트 설정
    plt.rcParams['font.family'] = ['AppleGothic', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 매수 추천 종목만 필터링
    buy_stocks = [s for s in stocks_data if '매수' in s.get('recommendation', '')]
    buy_stocks = sorted(buy_stocks, key=lambda x: x.get('rsi', 50))[:5]
    
    if not buy_stocks:
        return None
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('반디 퀀트 - 매수 추천 종목 분석', fontsize=16, fontweight='bold', y=0.98)
    
    colors = {'강력매수': '#4CAF50', '매수권유': '#FFC107', '매수대비': '#FF9800'}
    
    for idx, stock in enumerate(buy_stocks):
        row = idx // 3
        col = idx % 3
        ax = axes[row, col]
        
        # RSI 게이지 차트
        rsi = stock.get('rsi', 50)
        rec = stock.get('recommendation', '보유')
        color = '#4CAF50' if '강력' in rec else '#FFC107' if '권유' in rec else '#FF9800'
        
        # 반원차트
        theta = np.linspace(0, np.pi, 100)
        
        # 배경
        ax.fill_between(np.cos(theta) * 100, np.sin(theta) * 100, 
                        alpha=0.1, color='gray')
        
        # RSI 값
        rsi_theta = (rsi / 100) * np.pi
        ax.fill_between([0, np.cos(rsi_theta) * 100], 
                        [0, np.sin(rsi_theta) * 100], 
                        alpha=0.7, color=color)
        
        ax.plot([0, np.cos(rsi_theta) * 100], 
                [0, np.sin(rsi_theta) * 100], 
                color=color, linewidth=3)
        
        ax.scatter([np.cos(rsi_theta) * 100], [np.sin(rsi_theta) * 100], 
                   s=100, color=color, zorder=5)
        
        ax.set_xlim(-110, 110)
        ax.set_ylim(-10, 110)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # 제목 및 정보
        name = stock.get('name', '')
        ticker = stock.get('ticker', '')
        price = stock.get('current_price', 0)
        change = stock.get('change_pct', 0)
        
        ax.set_title(f"{name}\n({ticker})", fontsize=11, fontweight='bold', pad=10)
        
        # RSI 값
        ax.text(0, -25, f"RSI: {rsi:.1f}", ha='center', fontsize=12, fontweight='bold', color=color)
        ax.text(0, -40, f"{change:+.1f}%", ha='center', fontsize=10)
        
        # 추천 등급
        ax.text(0, -55, rec, ha='center', fontsize=9, 
                bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.3))
    
    # 빈 칸 숨기기
    if len(buy_stocks) < 6:
        for idx in range(len(buy_stocks), 6):
            row = idx // 3
            col = idx % 3
            axes[row, col].axis('off')
    
    # 한줄평
    ax_summary = fig.add_axes([0.15, 0.02, 0.7, 0.08])
    ax_summary.axis('off')
    
    if buy_stocks:
        best = buy_stocks[0]
        summary_text = f"반디의 한줄평: {best['name']} RSI {best['rsi']:.1f}로 과매도에 가까움. 분할 매수 기회!"
        ax_summary.text(0.5, 0.5, summary_text, ha='center', va='center', 
                        fontsize=11, style='italic',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='#E3F2FD', alpha=0.8))
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return output_path

def send_comprehensive_briefing():
    """완성형 브리핑 전송"""
    
    date_str = "2026-02-27"
    
    # JSON 데이터 로드
    json_path = f"/Users/mchom/.openclaw/workspace/analysis/daily_briefing_{date_str}.json"
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stocks = data.get('stocks', [])
    
    # 차트 이미지 생성
    chart_path = f"/Users/mchom/.openclaw/workspace/chart_{date_str}.png"
    create_chart_image(stocks, chart_path)
    
    # 매수 추천 종목 필터링
    buy_stocks = [s for s in stocks if '매수' in s.get('recommendation', '')]
    buy_stocks = sorted(buy_stocks, key=lambda x: x.get('rsi', 50))[:5]
    
    # 메시지 구성
    message = f"""반디 퀀트 완성형 브리핑 | {date_str}

========================================
세부 분석 및 반디 의견
========================================
"""
    
    for idx, s in enumerate(buy_stocks, 1):
        rec = s.get('recommendation', '')
        
        # 기술적 지표 요약
        macd_str = s.get('macd_trend', '분석중')
        bb_str = s.get('bb_position', '분석중')
        
        message += f"""
{idx}. {s['name']} ({s['ticker']}) - {rec}

가격: {s['current_price']:,.0f}원 | {s['change_pct']:+.1f}%
RSI: {s['rsi']:.1f} (과매도->중립)
MACD: {macd_str}
볼린저밴드: {bb_str}
거래량: {s['volume_ratio']:.1f}x

[반디 분석]
{s.get('comment', '분석 준비중')}

[반디 의견] """
        
        # 종목별 맞춤 의견
        if s['rsi'] < 35:
            message += "과매도 구간! 분할 매수 적기입니다."
        elif s['rsi'] < 45:
            message += "RSI 저점 확인 중. 소량 매수 후 추가 하락 시 분할."
        else:
            message += "관망 후 진입 권고. 추세 확인 필요."
        
        message += "\n\n"
    
    # 종합 평가
    avg_rsi = sum(s['rsi'] for s in buy_stocks) / len(buy_stocks) if buy_stocks else 50
    message += f"""========================================
종합 평가 및 전략
========================================

[시장 상황]
총 분석 종목: {len(stocks)}개
매수 추천: {len(buy_stocks)}개
매수추천 평균 RSI: {avg_rsi:.1f}
전체 시장 흐름: 조정 중 (상승 14 / 하락 16)

[반디의 실행 전략]

즉시 실행:
-> QuantumScape (RSI 32.6): 과매도, 분할 매수 시작

대기 관망:
-> GM / 하나제약: 추가 하락 시 진입
-> Tesla / NVIDIA: RSI 45 근접 대기

리스크 관리:
전체 포지션 30% 이내로 시작
QS는 소액 분할 매수 (3회 분할 권고)

========================================
반디가 파파를 응원합니다
"""
    
    # 텔레그램 전송 (이미지 + 텍스트)
    if os.path.exists(chart_path):
        with open(chart_path, 'rb') as photo:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            files = {'photo': photo}
            data = {'chat_id': CHAT_ID, 'caption': message}
            response = requests.post(url, files=files, data=data)
            return response.status_code == 200
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {'chat_id': CHAT_ID, 'text': message}
        response = requests.post(url, json=data)
        return response.status_code == 200

if __name__ == "__main__":
    success = send_comprehensive_briefing()
    print(f"브리핑 전송 {'성공' if success else '실패'}")