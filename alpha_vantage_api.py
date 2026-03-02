#!/usr/bin/env python3
"""
Alpha Vantage API 연동 모듈
Yahoo Finance 실패 시 폴백용
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List


class AlphaVantageAPI:
    """Alpha Vantage API 클라이언트"""
    
    def __init__(self, api_key: str = None):
        if api_key is None:
            # 파일에서 로드
            key_path = '/Users/mchom/.openclaw/workspace/alpha_vantage_api_key.txt'
            if os.path.exists(key_path):
                with open(key_path, 'r') as f:
                    api_key = f.read().strip()
        
        self.api_key = api_key
        self.base_url = 'https://www.alphavantage.co/query'
        self.call_count = 0
        self.max_calls_per_day = 25  # 무료 계정 한도
    
    def get_daily_data(self, symbol: str) -> Optional[Dict]:
        """
        일별 주가 데이터 조회
        Yahoo Finance 티커 형식 유지 (.KS 등)
        """
        if not self.api_key:
            print("  ⚠️  Alpha Vantage API 키 없음")
            return None
        
        if self.call_count >= self.max_calls_per_day:
            print(f"  ⚠️  API 호출 한도 도달 ({self.max_calls_per_day}/일)")
            return None
        
        # 티커 변환 (KOSPI/KOSDAQ은 .KS 유지)
        av_symbol = symbol
        
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': av_symbol,
            'apikey': self.api_key,
            'outputsize': 'compact'  # 최근 100일
        }
        
        try:
            import time
            time.sleep(1.2)  # 1초 이상 대기 (Rate limit 준수)
            
            print(f"  🔄 Alpha Vantage 호출 중... ({self.call_count + 1}/{self.max_calls_per_day})")
            response = requests.get(self.base_url, params=params, timeout=30)
            data = response.json()
            
            if 'Time Series (Daily)' not in data:
                error_msg = data.get('Note', data.get('Information', 'Unknown error'))
                print(f"  ❌ API 오류: {error_msg}")
                return None
            
            self.call_count += 1
            
            # 데이터 파싱
            time_series = data['Time Series (Daily)']
            ohlcv_data = []
            
            for date_str, values in time_series.items():
                ohlcv_data.append({
                    'date': date_str,
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(values['5. volume'])
                })
            
            # 날짜순 정렬
            ohlcv_data.sort(key=lambda x: x['date'])
            
            return {
                'ticker': symbol,
                'ohlcv': ohlcv_data,
                'source': 'alphavantage',
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"  ❌ Alpha Vantage 오류: {e}")
            return None
    
    def get_global_quote(self, symbol: str) -> Optional[Dict]:
        """실시간 시세 (빠른 조회)"""
        if not self.api_key:
            return None
        
        if self.call_count >= self.max_calls_per_day:
            return None
        
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if 'Global Quote' in data and data['Global Quote']:
                quote = data['Global Quote']
                self.call_count += 1
                
                return {
                    'ticker': symbol,
                    'current_price': float(quote['05. price']),
                    'change_pct': float(quote['10. change percent'].replace('%', '')),
                    'volume': int(quote['06. volume']),
                    'timestamp': quote['07. latest trading day'],
                    'source': 'alphavantage'
                }
            
            return None
            
        except Exception as e:
            print(f"  ❌ Global Quote 오류: {e}")
            return None


def get_av_data_for_problem_tickers():
    """
    Yahoo Finance 안 되는 3개 종목용
    """
    problem_tickers = [
        ('196170.KS', '알테오젠'),
        ('136480.KS', '하나제약'),
        ('247540.KS', '에코프로비엠')
    ]
    
    av = AlphaVantageAPI()
    
    if not av.api_key:
        print("❌ API 키가 없습니다. alpha_vantage_api_key.txt 파일을 생성하세요.")
        return
    
    print("=" * 60)
    print("🔄 Alpha Vantage 데이터 수집")
    print("=" * 60)
    
    results = {}
    
    for ticker, name in problem_tickers:
        print(f"\n📊 {name} ({ticker})")
        print("-" * 40)
        
        data = av.get_daily_data(ticker)
        if data:
            print(f"   ✅ {len(data['ohlcv'])}일 데이터 수집")
            print(f"   최근: {data['ohlcv'][-1]['date']} 종가 ${data['ohlcv'][-1]['close']}")
            results[ticker] = data
        else:
            print("   ❌ 실패")
    
    print(f"\n✅ 완료! 오늘 남은 호출: {av.max_calls_per_day - av.call_count}/{av.max_calls_per_day}")
    
    return results


if __name__ == "__main__":
    # 테스트
    get_av_data_for_problem_tickers()
