#!/usr/bin/env python3
"""
파파 텔레그램 주식 봇
실시간 주가 알림 및 음성 브리핑
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import Optional, Dict, List

# 설정
TELEGRAM_TOKEN = "8599663503:AAGfs7Sh2vy6tfHOr9UG-O_lcaG3cjPdH2s"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# TOP 12 종목
TOP_STOCKS = {
    # 국내 종목
    "005380.KS": {"name": "현대차", "sector": "자동차", "recommend": "🟠 매수권유"},
    "373220.KS": {"name": "LG에너지솔루션", "sector": "배터리", "recommend": "🟠 매수권유"},
    "006400.KS": {"name": "삼성SDI", "sector": "배터리", "recommend": "🟠 매수권유"},
    "005490.KS": {"name": "POSCO홀딩스", "sector": "배터리", "recommend": "🟠 매수권유"},
    "068270.KS": {"name": "셀트리온", "sector": "바이오", "recommend": "🟠 매수권유"},
    "207940.KS": {"name": "삼성바이오로직스", "sector": "바이오", "recommend": "🟠 매수권유"},
    "000270.KS": {"name": "기아", "sector": "자동차", "recommend": "🟠 매수권유"},
    "012330.KS": {"name": "현대모비스", "sector": "자동차", "recommend": "🟠 매수권유"},
    # 미국 종목
    "NVDA": {"name": "NVIDIA", "sector": "반도체", "recommend": "🟠 매수권유"},
    "TSLA": {"name": "Tesla", "sector": "자동차", "recommend": "🟡 매수대비"},
    "F": {"name": "Ford", "sector": "자동차", "recommend": "🟠 매수권유"},
    "GM": {"name": "GM", "sector": "자동차", "recommend": "🟠 매수권유"},
    "NEE": {"name": "NextEra", "sector": "전력", "recommend": "🟠 매수권유"},
}

def get_stock_price_yahoo(symbol: str) -> Optional[Dict]:
    """Yahoo Finance에서 주가 가져오기 (전일 종가 포함)"""
    try:
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('chart', {}).get('result', [])
            
            if result and len(result) > 0:
                result_data = result[0]
                meta = result_data.get('meta', {})
                
                # 현재가
                current = meta.get('regularMarketPrice', 0)
                
                # 전일 종가 (우선순위: chartPreviousClose > previousClose)
                previous = meta.get('chartPreviousClose', 0)
                if not previous:
                    previous = meta.get('previousClose', 0)
                
                # 만약 meta에 없으면 timestamp 데이터에서 추출
                if not previous and 'timestamp' in result_data:
                    timestamps = result_data.get('timestamp', [])
                    closes = result_data.get('indicators', {}).get('quote', [{}])[0].get('close', [])
                    if len(closes) >= 2:
                        previous = closes[-2]  # 마지막에서 두 번째 (전일)
                
                if current:
                    change = current - previous if previous else 0
                    change_pct = (change / previous * 100) if previous else 0
                    
                    currency = 'KRW' if '.KS' in symbol else 'USD'
                    
                    return {
                        'symbol': symbol,
                        'current': current,
                        'previous': previous,
                        'change': change,
                        'change_pct': change_pct,
                        'currency': currency,
                    }
            
        return None
    except Exception as e:
        print(f"      ❌ 예외: {e}")
        return None

def format_price_message(stock_data: Dict, stock_info: Dict) -> str:
    """주가 메시지 포맷팅 (전일 종가 포함)"""
    symbol = stock_data['symbol']
    current = stock_data['current']
    previous = stock_data['previous']
    change_pct = stock_data['change_pct']
    currency = stock_data['currency']
    
    # 화폐 단위
    unit = "원" if ".KS" in symbol else "$"
    
    # 등락 이모지
    if change_pct > 0:
        trend = "📈"
    elif change_pct < 0:
        trend = "📉"
    else:
        trend = "➖"
    
    # 소수점 처리 (미국은 2자리, 한국은 0자리)
    if ".KS" in symbol:
        current_str = f"{int(current):,}{unit}"
        previous_str = f"{int(previous):,}{unit}" if previous else "-"
        change_str = f"{change_pct:+.2f}%"
    else:
        current_str = f"{unit}{current:,.2f}"
        previous_str = f"{unit}{previous:,.2f}" if previous else "-"
        change_str = f"{change_pct:+.2f}%"
    
    return (
        f"{trend} <b>{stock_info['name']}</b> ({symbol.replace('.KS', '')})\n"
        f"💰 현재가: {current_str}\n"
        f"📉 전일: {previous_str}\n"
        f"📊 등락: {change_str}\n"
        f"🏷️ 섹터: {stock_info['sector']}\n"
        f"🎯 추천: {stock_info['recommend']}\n"
        f"{'─' * 25}"
    )

def get_updates():
    """텔레그램 업데이트 받기 (chat_id 확인용)"""
    url = f"{TELEGRAM_API}/getUpdates"
    try:
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error getting updates: {e}")
        return None

def send_message(chat_id: str, message: str, parse_mode: str = "HTML"):
    """텔레그램 메시지 전송"""
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def send_market_summary(chat_id: str):
    """TOP 12 종목 시세 요약 전송"""
    header = f"📊 <b>파파 주식 브리핑</b>\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n{'='*30}\n\n"
    
    messages = []
    failed_stocks = []
    
    print(f"🔍 총 {len(TOP_STOCKS)}개 종목 조회 중...")
    
    for i, (symbol, info) in enumerate(TOP_STOCKS.items()):
        print(f"  [{i+1}/{len(TOP_STOCKS)}] {info['name']} ({symbol}) 조회 중...")
        data = get_stock_price_yahoo(symbol)
        if data:
            print(f"      ✅ 성공: {data['current']} {data['currency']}")
            msg = format_price_message(data, info)
            messages.append(msg)
        else:
            print(f"      ❌ 실패")
            failed_stocks.append(info['name'])
        time.sleep(0.5)  # API 과부하 방지
    
    # 메시지 조합
    if messages:
        full_message = header + "\n".join(messages)
    else:
        full_message = header + "❌ 시세 정보를 가져올 수 없습니다. 잠시 후 다시 시도해주세요."
    
    print(f"\n📤 메시지 전송 중... (길이: {len(full_message)}자)")
    
    # 메시지가 너무 길면 분할
    if len(full_message) > 4000:
        print("  메시지가 길어서 분할 전송합니다...")
        parts = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
        for i, part in enumerate(parts, 1):
            print(f"    부분 {i}/{len(parts)} 전송...")
            send_message(chat_id, part)
    else:
        send_message(chat_id, full_message)
    
    if failed_stocks:
        print(f"\n⚠️ 조회 실패 종목: {', '.join(failed_stocks)}")
    
    print("✅ 전송 완료!")

def get_chat_id():
    """텔레그램 chat_id 자동 감지"""
    updates = get_updates()
    if updates and updates.get('ok'):
        results = updates.get('result', [])
        if results:
            # 마지막 메시지의 chat_id 반환
            last_msg = results[-1]
            chat_id = last_msg.get('message', {}).get('chat', {}).get('id')
            if chat_id:
                return chat_id
    return None

def main():
    """메인 함수"""
    print("🤖 파파 텔레그램 주식 봇 시작!")
    print("")
    print("📱 봇에게 메시지를 보내셨나요?")
    print("   봇에게 '/start'를 보내주세요!")
    print("")
    
    # chat_id 확인
    chat_id = get_chat_id()
    
    if chat_id:
        print(f"✅ chat_id 발견: {chat_id}")
        print("📊 시세 정보 전송 중...")
        send_market_summary(chat_id)
        print("✅ 전송 완료!")
    else:
        print("❌ chat_id를 찾을 수 없습니다.")
        print("   봇에게 메시지를 보낸 후 다시 실행해주세요.")
        print("")
        print("   방법:")
        print("   1. 텔레그램에서 @papa_stock_bot 검색")
        print("   2. '/start' 입력")
        print("   3. 이 스크립트 다시 실행")

if __name__ == "__main__":
    main()
