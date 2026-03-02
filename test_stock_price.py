#!/usr/bin/env python3
"""주가 API 테스트"""

import requests
import json

def test_yahoo(symbol):
    """Yahoo Finance 테스트"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    print(f"\n🔍 테스트: {symbol}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 결과 확인
            result = data.get('chart', {}).get('result', [])
            if result:
                meta = result[0].get('meta', {})
                current = meta.get('regularMarketPrice')
                previous = meta.get('previousClose')
                currency = meta.get('currency', 'USD')
                
                print(f"✅ 성공!")
                print(f"   현재가: {current} {currency}")
                print(f"   전일가: {previous} {currency}")
                return True
            else:
                print(f"❌ 결과 없음: {data.get('chart', {}).get('error', 'Unknown')}")
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            print(f"   내용: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
    
    return False

# 테스트
print("="*50)
print("Yahoo Finance API 테스트")
print("="*50)

symbols = ["NVDA", "TSLA", "005380.KS"]

for symbol in symbols:
    test_yahoo(symbol)

print("\n" + "="*50)
