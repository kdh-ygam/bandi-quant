#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║           네이버 금융 크롤러 - 국내 주식 데이터 수집               ║
║                                                                      ║
║  기능:                                                               ║
║  - 네이버 금융에서 실시간 주가 조회                                 ║
║  - OHLCV 데이터 수집                                                ║
║  - Yahoo Finance 실패 시 폴백                                       ║
║                                                                      ║
║  Created by: 반디 🐾                                                ║
║  Date: 2026-02-26                                                    ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import requests
import re
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import pandas as pd


class NaverFinanceCrawler:
    """네이버 금융 크롤러"""
    
    def __init__(self):
        self.base_url = "https://finance.naver.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        }
    
    def get_current_price(self, ticker: str) -> Optional[Dict]:
        """
        현재가 정보 조회
        ticker: 6자리 숫자 코드 (예: '000660')
        """
        # .KS 제거
        code = ticker.replace('.KS', '')
        url = f"{self.base_url}/item/main.naver?code={code}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            html = response.text
            
            # 현재가 추출
            price_match = re.search(r'<em class="no_up">([\d,]+)</em>', html)
            if not price_match:
                price_match = re.search(r'<em class="no_down">([\d,]+)</em>', html)
            if not price_match:
                price_match = re.search(r'<em class="no0">([\d,]+)</em>', html)
            
            if price_match:
                current_price = int(price_match.group(1).replace(',', ''))
            else:
                print(f"  ⚠️  현재가 추출 실패: {ticker}")
                return None
            
            # 등락률 추출
            change_match = re.search(r'<em class="[^"]*">([\d\.]+)</em>\s*<span class="blind">([%상하])</span>', html)
            change_pct = 0
            if change_match:
                change_value = float(change_match.group(1))
                direction = change_match.group(2)
                change_pct = change_value if direction == '상' else -change_value
            
            # 거래량 추출
            volume_match = re.search(r'거래대금</th>\s*<td><em>([\d,]+)</em>', html)
            volume = 0
            if volume_match:
                volume_str = volume_match.group(1).replace(',', '')
                volume = int(volume_str) * 1000  # 천원 단위 -> 원
            
            # 전일 종가 계산
            prev_price = current_price / (1 + change_pct/100) if change_pct != 0 else current_price
            
            return {
                'ticker': ticker,
                'current_price': current_price,
                'previous_price': prev_price,
                'change_pct': change_pct,
                'volume': volume,
                'currency': 'KRW',
                'source': 'naver',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"  ❌ 네이버 크롤링 실패 {ticker}: {e}")
            return None
    
    def get_historical_data(self, ticker: str, days: int = 60) -> Optional[List[Dict]]:
        """
        과거 데이터 조회 (일별)
        """
        code = ticker.replace('.KS', '')
        
        # 네이버 일별 시세 페이지
        url = f"{self.base_url}/item/sise_day.naver?code={code}"
        
        try:
            all_data = []
            page = 1
            
            while len(all_data) < days and page <= 20:  # 최대 20페이지
                page_url = f"{url}&page={page}"
                response = requests.get(page_url, headers=self.headers, timeout=10)
                
                # 테이블 파싱
                import re
                rows = re.findall(r'<tr>\s*<td align="center"><span class="tah p10 gray03">(\d{4}\.\d{2}\.\d{2})</span></td>\s*<td class="num"><span class="tah p11 ([^"]*)">([\d,]+)</span></td>\s*<td class="num"><span class="tah p11 ([^"]*)">([\d,]+)</span></td>\s*<td class="num"><span class="tah p11 ([^"]*)">([\d,]+)</span></td>\s*<td class="num"><span class="tah p11 ([^"]*)">([\d,]+)</span></td>\s*<td class="num"><span class="tah p11">([\d,]+)</span></td>', response.text)
                
                for row in rows:
                    date_str, close_class, close, open_class, open_, high_class, high, low_class, low, volume = row
                    
                    data = {
                        'date': datetime.strptime(date_str, '%Y.%m.%d').strftime('%Y-%m-%d'),
                        'open': int(open_.replace(',', '')),
                        'high': int(high.replace(',', '')),
                        'low': int(low.replace(',', '')),
                        'close': int(close.replace(',', '')),
                        'volume': int(volume.replace(',', ''))
                    }
                    all_data.append(data)
                
                if not rows:
                    break
                
                page += 1
            
            return all_data[:days]
            
        except Exception as e:
            print(f"  ❌ 과거 데이터 조회 실패 {ticker}: {e}")
            return None
    
    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        """종목 기본 정보 조회"""
        code = ticker.replace('.KS', '')
        url = f"{self.base_url}/item/main.naver?code={code}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            html = response.text
            
            # 종목명 추출
            name_match = re.search(r'<div class="wrap_company">\s*<h2>\s*<a[^>]*>([^<]+)</a>', html)
            name = name_match.group(1).strip() if name_match else ticker
            
            # 업종 추출
            sector_match = re.search(r'<th scope="row">업종</th>\s*<td><a[^>]*>([^<]+)</a>', html)
            sector = sector_match.group(1) if sector_match else '기타'
            
            return {
                'name': name,
                'sector': sector,
                'ticker': ticker
            }
            
        except Exception as e:
            return None


def test_crawler():
    """크롤러 테스트"""
    crawler = NaverFinanceCrawler()
    
    # 문제 종목 테스트
    test_tickers = [
        ('196170.KS', '알테오젠'),
        ('136480.KS', '하나제약'),
        ('247540.KS', '에코프로비엠'),
        ('000660.KS', 'SK하이닉스'),
    ]
    
    print("=" * 60)
    print("🧪 네이버 금융 크롤러 테스트")
    print("=" * 60)
    
    for ticker, name in test_tickers:
        print(f"\n📊 {name} ({ticker})")
        print("-" * 40)
        
        # 현재가
        current = crawler.get_current_price(ticker)
        if current:
            print(f"   현재가: {current['current_price']:,}원")
            print(f"   등락률: {current['change_pct']:+.2f}%")
            print(f"   거래량: {current['volume']:,}")
            print("   ✅ 성공")
        else:
            print("   ❌ 실패")
        
        # 과거 데이터 샘플
        hist = crawler.get_historical_data(ticker, days=5)
        if hist:
            print(f"   과거 데이터: {len(hist)}일 조회")
            print(f"   최근: {hist[0]['date']} 종가 {hist[0]['close']:,}원")
        else:
            print("   ⚠️  과거 데이터 없음")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_crawler()
