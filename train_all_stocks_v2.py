#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║     반디 RL 트레이더 - 43종목 전체 학습 파이프라인 v2.0 🔥         ║
║                                                                      ║
║  • Rate limit 방지 (지연 시간 추가)                                   ║
║  • 공격적 Reward (거래 장려)                                         ║
║  • 보수적 보상 페널티 제거                                           ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List

# RL 트레이더 임포트
from bandi_rl_trader_v2 import BandiRLTrader, STOCKS

# ============================================
# 📊 학습 설정 (공격적 버전)
# ============================================
TRAINING_CONFIG = {
    "total_timesteps": 50000,
    "results_file": "training_results_v2.json",
    "progress_file": "training_progress_v2.json",
    "model_dir": "rl_models_v2",
    "delay_between_stocks": 3.0,  # ⭐ YF Rate Limit 방지
    "retry_delay": 60,            # 재시도 지연 (초)
    "max_retries": 3              # 최대 재시도 횟수
}

class TrainingPipeline:
    """학습 파이프라인 v2.0"""
    
    def __init__(self):
        self.progress = self.load_progress()
        self.results = {}
        self.trader = BandiRLTrader(model_dir=TRAINING_CONFIG["model_dir"])
    
    def load_progress(self):
        if os.path.exists(TRAINING_CONFIG["progress_file"]):
            with open(TRAINING_CONFIG["progress_file"], 'r') as f:
                return json.load(f)
        return {
            "completed": [],
            "failed": [],
            "in_progress": None,
            "total_start": datetime.now().isoformat()
        }
    
    def save_progress(self):
        with open(TRAINING_CONFIG["progress_file"], 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, indent=2, ensure_ascii=False)
    
    def save_results(self):
        with open(TRAINING_CONFIG["results_file"], 'w', encoding='utf-8') as f:
            json.dump({
                "progress": self.progress,
                "results": self.results,
                "updated_at": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
    
    def train_stock_with_retry(self, ticker: str, name: str) -> Dict:
        """재시도 로직 포함 학습"""
        for attempt in range(TRAINING_CONFIG["max_retries"]):
            try:
                result = self.train_stock(ticker, name)
                if result and result.get('success'):
                    return result
            except Exception as e:
                error_msg = str(e)
                if "Rate limited" in error_msg or "429" in error_msg:
                    wait_time = TRAINING_CONFIG["retry_delay"] * (attempt + 1)
                    print(f"    ⏳ Rate limited. Waiting {wait_time}s... (attempt {attempt+1}/{TRAINING_CONFIG['max_retries']})")
                    time.sleep(wait_time)
                else:
                    raise
        
        return {
            'ticker': ticker,
            'success': False,
            'error': 'Max retries exceeded'
        }
    
    def train_stock(self, ticker: str, name: str) -> Dict:
        """단일 종목 학습"""
        print(f"\n{'='*60}")
        print(f"🚀 [{ticker}] {name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # ⭐ 지연 시간 추가 (Rate Limit 방지)
            time.sleep(TRAINING_CONFIG["delay_between_stocks"])
            
            model = self.trader.train(
                ticker, 
                total_timesteps=TRAINING_CONFIG["total_timesteps"],
                save=True
            )
            
            elapsed = time.time() - start_time
            
            result = {
                'ticker': ticker,
                'name': name,
                'success': True,
                'elapsed_seconds': elapsed,
                'model_path': f"{TRAINING_CONFIG['model_dir']}/bandi_rl_{ticker}.zip"
            }
            
            print(f"  ✅ 완료 ({elapsed:.1f}s)")
            
            return result
            
        except Exception as e:
            print(f"  ❌ 실패: {e}")
            return {
                'ticker': ticker,
                'name': name,
                'success': False,
                'error': str(e)
            }
    
    def run(self):
        """전체 학습 실행"""
        print("="*60)
        print("🚀 반디 RL 트레이더 학습 파이프라인 v2.0")
        print("="*60)
        print(f"설정: {TRAINING_CONFIG}")
        print(f"완료: {len(self.progress['completed'])}개")
        print(f"실패: {len(self.progress['failed'])}개")
        print("="*60)
        
        # 그룹별 학습
        groups = {
            'semiconductor': ['NVDA', 'AMD', 'ARM', '000660.KS', '005930.KS', '042700.KS', '001740.KS'],
            'bio': ['068270.KS', '207940.KS', '196170.KS', '136480.KS', 'JNJ'],
            'auto': ['TSLA', '005380.KS', '000270.KS', '012330.KS', '003620.KS', 'F', 'GM', 'RIVN'],
            'battery': ['373220.KS', '006400.KS', '005490.KS', '247540.KS', 'ALB', 'QS'],
            'energy': ['NEE', 'ENPH', 'SEDG', 'FSLR', 'RUN', 'BE'],
            'ai': ['PLTR', 'AI', 'SNOW', 'CRWD', 'ONON']
        }
        
        all_tickers = []
        for group_name, tickers in groups.items():
            for ticker in tickers:
                if ticker not in self.progress['completed'] and ticker not in self.progress['failed']:
                    all_tickers.append((group_name, ticker))
        
        print(f"\n📊 총 {len(all_tickers)}개 종목 학습 예정")
        
        for group_name, ticker in all_tickers:
            if ticker in STOCKS:
                name = STOCKS[ticker]['name']
            else:
                name = ticker
            
            self.progress['in_progress'] = ticker
            self.save_progress()
            
            # 재시도 로직 포함 학습
            result = self.train_stock_with_retry(ticker, name)
            
            if result['success']:
                self.progress['completed'].append(ticker)
                self.results[ticker] = result
            else:
                self.progress['failed'].append(ticker)
            
            self.progress['in_progress'] = None
            self.save_progress()
            self.save_results()
        
        print("\n" + "="*60)
        print("✅ 전체 학습 완료!")
        print(f"성공: {len(self.progress['completed'])}개")
        print(f"실패: {len(self.progress['failed'])}개")
        print("="*60)
        
        if self.progress['failed']:
            print("\n⚠️ 실패한 종목:")
            for ticker in self.progress['failed']:
                print(f"  - {ticker}")


if __name__ == '__main__':
    pipeline = TrainingPipeline()
    pipeline.run()
