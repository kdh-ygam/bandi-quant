#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║           한국투자증권(KIS) API 모듈 v1.0                             ║
║                                                                      ║
║  • 국내 주식 실시간/시세 데이터                                      ║
║  • 해외 주식 데이터 지원                                            ║
║  • WebSocket 지원                                                   ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import time


class KISAPI:
    """한국투자증권 API 클래스"""
    
    # API 엔드포인트
    BASE_URL = "https://openapi.koreainvestment.com:9443"  # 실전
    BASE_URL_TEST = "https://openapivts.koreainvestment.com:29443"  # 모의
    
    def __init__(self, app_key: str = None, app_secret: str = None, account_no: str = None, test_mode: bool = True):
        """
        KIS API 초기화
        
        Args:
            app_key: 한투 앱키
            app_secret: 한투 시크릿
            account_no: 계좌번호
            test_mode: 모의투자 모드
        """
        self.app_key = app_key or os.getenv('KIS_APP_KEY')
        self.app_secret = app_secret or os.getenv('KIS_APP_SECRET')
        self.account_no = account_no or os.getenv('KIS_ACCOUNT_NO')
        self.test_mode = test_mode
        
        self.base_url = self.BASE_URL_TEST if test_mode else self.BASE_URL
        self.access_token = None
        self.token_expired = None
        
        # 토큰 발급
        self._get_access_token()
    
    def _get_access_token(self) -> bool:
        """접근 토큰 발급"""
        url = f"{self.base_url}/oauth2/tokenP"
        
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            self.access_token = data.get('access_token')
            expires_in = data.get('expires_in', 86400)
            self.token_expired = datetime.now() + timedelta(seconds=int(expires_in) - 60)
            
            print(f"✅ KIS API 토큰 발급 완료 (만료: {self.token_expired})")
            return True
            
        except Exception as e:
            print(f"❌ KIS API 토큰 발급 실패: {e}")
            return False
    
    def _ensure_token(self):
        """토큰 유효성 확인 및 갱신"""
        if self.access_token is None or datetime.now() >= self.token_expired:
            self._get_access_token()
    
    def _get_headers(self, tr_id: str = None) -> Dict:
        """API 요청 헤더 생성"""
        self._ensure_token()
        
        headers = {
            'content-type': 'application/json',
            'authorization': f'Bearer {self.access_token}',
            'appkey': self.app_key,
            'appsecret': self.app_secret,
        }
        
        if tr_id:
            headers['tr_id'] = tr_id
            
        return headers
    
    def get_stock_data(self, ticker: str, period: str = "2y") -> Optional[pd.DataFrame]:
        """
        주식 일별 시세 조회
        
        Args:
            ticker: 종목코드 (예: "000660", "005930")
            period: 조회 기간 (1d, 1m, 3m, 6m, 1y, 2y)
        
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
        """
        # .KS, .KQ 제거
        ticker = ticker.replace('.KS', '').replace('.KQ', '')
        
        # 조회 기간 설정
        period_days = {
            '1d': 1, '1m': 30, '3m': 90, 
            '6m': 180, '1y': 365, '2y': 730
        }.get(period, 730)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # API 호출
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 주식
            "FID_INPUT_ISCD": ticker,
            "FID_INPUT_DATE_1": start_date.strftime("%Y%m%d"),
            "FID_INPUT_DATE_2": end_date.strftime("%Y%m%d"),
            "FID_PERIOD_DIV_CODE": "D",  # 일봉
            "FID_ORG_ADJ_PRC": "0"  # 수정주가
        }
        
        headers = self._get_headers(tr_id="FHKST03010100")
        
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get('rt_cd') != '0':
                print(f"⚠️ KIS API 오류: {data.get('msg1', 'Unknown error')}")
                return None
            
            output = data.get('output2', [])
            if not output:
                return None
            
            # DataFrame 변환
            df_data = []
            for item in output:
                try:
                    df_data.append({
                        'Date': pd.to_datetime(item['stck_bsop_date']),
                        'Open': float(item['stck_oprc']),
                        'High': float(item['stck_hgpr']),
                        'Low': float(item['stck_lwpr']),
                        'Close': float(item['stck_clpr']),
                        'Volume': int(item['acml_vol'])
                    })
                except (KeyError, ValueError) as e:
                    continue
            
            if not df_data:
                return None
                
            df = pd.DataFrame(df_data)
            df = df.sort_values('Date').set_index('Date')
            
            print(f"  ✅ KIS: {ticker} ({len(df)} rows)")
            return df
            
        except Exception as e:
            print(f"  ❌ KIS API 오류 ({ticker}): {e}")
            return None
    
    def get_overseas_stock_data(self, ticker: str, market: str = "NAS", period: str = "2y") -> Optional[pd.DataFrame]:
        """
        해외주식 조회 (한투 해외주식 API)
        
        Args:
            ticker: 종목코드
            market: 거래소 (NAS:나스닥, NYS:뉴욕, ...)
            period: 조회 기간
        """
        period_days = {
            '1d': 1, '1m': 30, '3m': 90, 
            '6m': 180, '1y': 365, '2y': 730
        }.get(period, 730)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        url = f"{self.base_url}/uapi/overseas-price/v1/quotations/dailyprice"
        
        params = {
            "AUTH": "",
            "EXCD": market,
            "SYMB": ticker,
            "GUBN": "0",  # 일간
            "BYMD": start_date.strftime("%Y%m%d"),
            "EYMD": end_date.strftime("%Y%m%d"),
            "KEYB": ""
        }
        
        headers = self._get_headers(tr_id="HHDFS76240000")
        
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get('rt_cd') != '0':
                return None
            
            output = data.get('output2', [])
            if not output:
                return None
            
            df_data = []
            for item in output:
                try:
                    df_data.append({
                        'Date': pd.to_datetime(item['xymd']),
                        'Open': float(item['open']),
                        'High': float(item['high']),
                        'Low': float(item['low']),
                        'Close': float(item['clos']),
                        'Volume': int(item['tvol'])
                    })
                except (KeyError, ValueError):
                    continue
            
            if not df_data:
                return None
                
            df = pd.DataFrame(df_data)
            df = df.sort_values('Date').set_index('Date')
            
            print(f"  ✅ KIS Overseas: {ticker} ({len(df)} rows)")
            return df
            
        except Exception as e:
            print(f"  ❌ KIS Overseas 오류 ({ticker}): {e}")
            return None


# 테스트용
if __name__ == '__main__':
    # 환경변수에서 키 로드
    api = KISAPI(test_mode=True)
    
    # 테스트: SK하이닉스
    df = api.get_stock_data("000660")
    if df is not None:
        print(f"\n📊 샘플 데이터:\n{df.tail(3)}")
