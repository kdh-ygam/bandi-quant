#!/usr/bin/env python3
"""
그룹별 RL 학습 스크립트 v2.0 (Rate Limit 방지 + 공격적 보상)
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime

from bandi_rl_trader_v2 import BandiRLTrader, STOCKS

# 그룹별 종목 정의
GROUPS = {
    'ai': ['PLTR', 'AI', 'SNOW', 'CRWD', 'ONON'],
    'auto': ['TSLA', '005380.KS', '000270.KS', '012330.KS', '003620.KS', 'F', 'GM', 'RIVN'],
    'battery': ['373220.KS', '006400.KS', '005490.KS', '247540.KS', 'ALB', 'QS'],
    'bio': ['068270.KS', '207940.KS', '196170.KS', '136480.KS', 'JNJ'],
    'energy': ['NEE', 'ENPH', 'SEDG', 'FSLR', 'RUN', 'BE'],
    'semiconductor': ['NVDA', 'AMD', 'ARM', '000660.KS', '005930.KS', '042700.KS', '001740.KS'],
}

CONFIG = {
    'total_timesteps': 50000,
    'delay_between_stocks': 5.0,  # 종목 간 지연 (초)
    'retry_delay': 60,           # 재시도 지연
    'max_retries': 3             # 재시도 횟수
}

def train_group(group_name):
    """그룹별 학습"""
    tickers = GROUPS.get(group_name, [])
    
    if not tickers:
        print(f"❌ Unknown group: {group_name}")
        return
    
    print(f"\n{'='*60}")
    print(f"🚀 그룹 [{group_name}] 학습 시작")
    print(f"대상 종목: {len(tickers)}개")
    print(f"설정: {CONFIG}")
    print(f"{'='*60}")
    
    trader = BandiRLTrader()
    results = []
    
    for i, ticker in enumerate(tickers):
        print(f"\n📊 [{i+1}/{len(tickers)}] {ticker}")
        
        # Rate Limit 방지 지연
        if i > 0:
            print(f"    ⏳ Rate Limit 방지: {CONFIG['delay_between_stocks']}초 대기...")
            time.sleep(CONFIG['delay_between_stocks'])
        
        success = False
        for attempt in range(CONFIG['max_retries']):
            try:
                model = trader.train(ticker, total_timesteps=CONFIG['total_timesteps'])
                results.append({
                    'ticker': ticker,
                    'success': True,
                    'attempt': attempt + 1
                })
                success = True
                print(f"  ✅ 성공!")
                break
            except Exception as e:
                error_msg = str(e)
                print(f"  ⚠️ 시도 {attempt+1}/{CONFIG['max_retries']}: {error_msg[:100]}")
                
                if "Rate limited" in error_msg or "429" in error_msg or "Too Many Requests" in error_msg:
                    wait_time = CONFIG['retry_delay'] * (attempt + 1)
                    print(f"    ⏳ {wait_time}초 대기 후 재시도...")
                    time.sleep(wait_time)
                else:
                    break
        
        if not success:
            print(f"  ❌ 최종 실패")
            results.append({
                'ticker': ticker,
                'success': False
            })
    
    # 결과 저장
    result_file = f"training_results_{group_name}_v2.json"
    with open(result_file, 'w') as f:
        json.dump({
            'group': group_name,
            'timestamp': datetime.now().isoformat(),
            'config': CONFIG,
            'results': results
        }, f, indent=2)
    
    success_count = sum(1 for r in results if r['success'])
    print(f"\n{'='*60}")
    print(f"✅ 그룹 [{group_name}] 완료!")
    print(f"성공: {success_count}/{len(tickers)}")
    print(f"{'='*60}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--group', required=True, help='Training group name')
    args = parser.parse_args()
    
    train_group(args.group)
