#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║           반디 듀얼 API 학습 스크립트 v3.1 🚀                        ║
║                                                                      ║
║  • 한투 API: 국내 주식 (Rate Limit 없음) - 내장모듈                 ║
║  • Yahoo Finance: 해외 주식 (Rate Limit 대비 지연)                   ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, timedelta
from typing import Optional, Dict, List

# ═══════════════════════════════════════════════════════════════════════
# 한투 API 모듈 (내장)
# ═══════════════════════════════════════════════════════════════════════
import requests
import pandas as pd

class KISAPI:
    """한국투자증권 API 클래스 (내장)"""
    
    BASE_URL = "https://openapi.koreainvestment.com:9443"
    BASE_URL_TEST = "https://openapivts.koreainvestment.com:29443"
    
    def __init__(self, app_key: str = None, app_secret: str = None, account_no: str = None, test_mode: bool = True):
        self.app_key = app_key or os.getenv('KIS_APP_KEY')
        self.app_secret = app_secret or os.getenv('KIS_APP_SECRET')
        self.account_no = account_no or os.getenv('KIS_ACCOUNT_NO')
        self.test_mode = test_mode
        self.base_url = self.BASE_URL_TEST if test_mode else self.BASE_URL
        self.access_token = None
        self.token_expired = None
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
            print(f"✅ KIS API 토큰 발급 완료")
            return True
        except Exception as e:
            print(f"❌ KIS API 토큰 발급 실패: {e}")
            return False
    
    def _ensure_token(self):
        if self.access_token is None or datetime.now() >= self.token_expired:
            self._get_access_token()
    
    def get_stock_data(self, ticker: str, period: str = "2y") -> Optional[pd.DataFrame]:
        """주식 일별 시세 조회"""
        self._ensure_token()
        ticker = ticker.replace('.KS', '').replace('.KQ', '')
        
        period_days = {'1d': 1, '1m': 30, '3m': 90, '6m': 180, '1y': 365, '2y': 730}.get(period, 730)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker,
            "FID_INPUT_DATE_1": start_date.strftime("%Y%m%d"),
            "FID_INPUT_DATE_2": end_date.strftime("%Y%m%d"),
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "0"
        }
        headers = {
            'content-type': 'application/json',
            'authorization': f'Bearer {self.access_token}',
            'appkey': self.app_key,
            'appsecret': self.app_secret,
            'tr_id': 'FHKST03010100'
        }
        
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get('rt_cd') != '0':
                print(f"⚠️ KIS API 오류: {data.get('msg1', 'Unknown')}")
                return None
            
            output = data.get('output2', [])
            if not output:
                return None
            
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
                except (KeyError, ValueError):
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

# 한투 API 사용 가능
KIS_AVAILABLE = True

# RL 트레이더 임포트
try:
    from bandi_rl_trader_v3 import BandiRLTraderV3
    RL_AVAILABLE = True
except ImportError:
    try:
        from bandi_rl_trader_v2 import BandiRLTrader, STOCKS
        RL_AVAILABLE = True
        print("⚠️ v2 트레이더 사용 중 (v3 없음)")
    except ImportError:
        RL_AVAILABLE = False
        print("❌ RL 트레이더 미설치")

# 설정
CONFIG = {
    'total_timesteps': 50000,
    'delay_between_stocks': 5.0,  # Yahoo용 기본 지연
    'rate_limit_delay': 3,        # Yahoo API 지연 (초)
    'retry_delay': 60,           # Rate Limit 재시도
    'max_retries': 3             # 재시도 횟수
}


class DualAPIDataLoader:
    """듀얼 API 데이터 로더"""
    
    def __init__(self, source: str = "AUTO"):
        self.source = source.upper()
        self.kis_api = None
        
        # 한투 API 초기화
        if self.source in ["KIS", "AUTO"]:
            self._init_kis()
    
    def _init_kis(self):
        """한투 API 초기화"""
        if not KIS_AVAILABLE:
            return
        
        try:
            app_key = os.getenv('KIS_APP_KEY')
            app_secret = os.getenv('KIS_APP_SECRET')
            account_no = os.getenv('KIS_ACCOUNT_NO')
            
            if app_key and app_secret:
                self.kis_api = KISAPI(app_key, app_secret, account_no)
                print("✅ 한투 API 연결됨")
        except Exception as e:
            print(f"⚠️ 한투 API 초기화 실패: {e}")
    
    def load_data(self, ticker: str, period: str = "2y"):
        """
        티커에 따라 자동으로 API 선택
        
        Returns:
            DataFrame or None
        """
        # 강제 소스 설정
        if self.source == "KIS":
            return self._load_kis(ticker, period)
        elif self.source == "YAHOO":
            return self._load_yahoo(ticker, period)
        
        # AUTO 모드: 티커 패턴으로 판단
        if ticker.endswith(('.KS', '.KQ')):
            return self._load_kis(ticker, period)
        else:
            return self._load_yahoo(ticker, period)
    
    def _load_kis(self, ticker: str, period: str) -> Optional[object]:
        """한투 API로 데이터 로드"""
        if self.kis_api is None:
            print(f"❌ 한투 API 미설치: {ticker}")
            return None
        
        try:
            # 한투 API 호출
            df = self.kis_api.get_stock_data(ticker, period=period)
            if df is not None and len(df) > 0:
                print(f"  ✅ 한투 API: {ticker} ({len(df)} rows)")
                return df
        except Exception as e:
            print(f"  ⚠️ 한투 실패 ({ticker}): {e}")
        
        return None
    
    def _load_yahoo(self, ticker: str, period: str) -> Optional[object]:
        """Yahoo Finance로 데이터 로드"""
        try:
            import yfinance as yf
            
            # Rate Limit 대비 지연
            delay = int(os.getenv('RATE_LIMIT_DELAY', CONFIG['rate_limit_delay']))
            if delay > 0:
                time.sleep(delay)
            
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(period=period)
            
            if len(df) > 0:
                print(f"  ✅ Yahoo: {ticker} ({len(df)} rows)")
                return df
            
        except Exception as e:
            error_msg = str(e)
            if "Rate limited" in error_msg or "429" in error_msg or "Too Many Requests" in error_msg:
                raise Exception(f"Rate limited: {ticker}")
            print(f"  ⚠️ Yahoo 실패 ({ticker}): {e}")
        
        return None


class DualAPITrainer:
    """듀얼 API RL 트레이너"""
    
    def __init__(self, source: str):
        self.source = source.upper()
        self.data_loader = DualAPIDataLoader(source)
        
        # Yahoo용 지연 설정
        if self.source == "YAHOO":
            os.environ['YF_DOWNLOAD_DELAY'] = str(CONFIG['rate_limit_delay'])
        
        print(f"\n{'='*60}")
        print(f"🚀 듀얼 API 트레이너 초기화")
        print(f"소스: {self.source}")
        print(f"{'='*60}")
    
    def train_stocks(self, tickers: list) -> dict:
        """종목 리스트 학습"""
        results = []
        
        print(f"\n대상 종목: {len(tickers)}개")
        print(f"설정: {CONFIG}")
        print(f"{'='*60}\n")
        
        for i, ticker in enumerate(tickers):
            print(f"\n📊 [{i+1}/{len(tickers)}] {ticker}")
            
            # 종목 간 지연 (Yahoo용)
            if i > 0 and self.source == "YAHOO":
                delay = float(os.getenv('DELAY_BETWEEN_STOCKS', CONFIG['delay_between_stocks']))
                print(f"    ⏳ {delay}초 지연...")
                time.sleep(delay)
            
            # 학습 시도
            result = self._train_single(ticker)
            results.append(result)
        
        return {
            'source': self.source,
            'timestamp': datetime.now().isoformat(),
            'config': CONFIG,
            'results': results
        }
    
    def _train_single(self, ticker: str, max_retries: int = 3) -> dict:
        """단일 종목 학습"""
        
        for attempt in range(max_retries):
            try:
                # 데이터 로드
                df = self.data_loader.load_data(ticker)
                
                if df is None or len(df) < 100:
                    raise ValueError(f"데이터 부족: {ticker}")
                
                # RL 학습
                print(f"    🎯 RL 학습 시작...")
                
                # v3 또는 v2 트레이더 사용
                try:
                    from bandi_rl_trader_v3 import BandiRLTraderV3
                    trader = BandiRLTraderV3()
                except:
                    from bandi_rl_trader_v2 import BandiRLTrader
                    trader = BandiRLTrader()
                
                model = trader.train(
                    ticker=ticker,
                    total_timesteps=CONFIG['total_timesteps']
                )
                
                # 모델 저장
                os.makedirs('rl_models_v3', exist_ok=True)
                model_path = f"rl_models_v3/bandi_rl_{self.source}_{ticker.replace('.', '_')}.zip"
                model.save(model_path)
                
                print(f"    ✅ 성공! → {model_path}")
                
                return {
                    'ticker': ticker,
                    'success': True,
                    'attempt': attempt + 1
                }
                
            except Exception as e:
                error_msg = str(e)
                print(f"    ⚠️ 시도 {attempt+1}/{max_retries}: {error_msg[:80]}")
                
                # Rate Limit이면 재시도
                if "Rate limited" in error_msg or "429" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = CONFIG['retry_delay'] * (attempt + 1)
                        print(f"    ⏳ {wait_time}초 대기 후 재시도...")
                        time.sleep(wait_time)
                    else:
                        print(f"    ❌ 최종 실패 (Rate Limit)")
                else:
                    print(f"    ❌ 최종 실패: {error_msg[:80]}")
                    break
        
        return {
            'ticker': ticker,
            'success': False,
            'error': error_msg
        }


def main():
    parser = argparse.ArgumentParser(
        description='반디 듀얼 API RL 학습'
    )
    parser.add_argument(
        '--source', 
        required=True, 
        choices=['KIS', 'YAHOO'],
        help='데이터 소스: KIS (한투) 또는 YAHOO'
    )
    parser.add_argument(
        '--stocks', 
        required=True,
        help='학습 종목 (콤마 구분)'
    )
    parser.add_argument(
        '--output', 
        default='training_results_{source}.json',
        help='결과 파일명'
    )
    
    args = parser.parse_args()
    
    # 종목 리스트 파싱
    tickers = [s.strip() for s in args.stocks.split(',')]
    
    # 트레이너 실행
    trainer = DualAPITrainer(args.source)
    results = trainer.train_stocks(tickers)
    
    # 결과 저장
    output_file = args.output.format(source=args.source)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # 요약 출력
    success_count = sum(1 for r in results['results'] if r['success'])
    total = len(results['results'])
    
    print(f"\n{'='*60}")
    print(f"✅ 학습 완료!")
    print(f"성공: {success_count}/{total} ({success_count/total*100:.1f}%)")
    print(f"결과: {output_file}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
