#!/usr/bin/env python3
"""
반디 퀀트 - AI 신호 기록 관리
과거 신호를 저장하고 차트에 계속 표시
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

class SignalHistory:
    """AI 신호 기록 관리"""
    
    def __init__(self, history_file='data/signal_history.json'):
        self.history_file = history_file
        self.signals = defaultdict(list)  # ticker -> [(date, signal_type, strength, price), ...]
        self.load_history()
    
    def load_history(self):
        """저장된 신호 기록 불러오기"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for ticker, signal_list in data.items():
                        self.signals[ticker] = signal_list
                print(f"📚 신호 기록 로드: {len(self.signals)}개 종목")
            except Exception as e:
                print(f"⚠️  신호 기록 로드 실패: {e}")
    
    def save_history(self):
        """신호 기록 저장"""
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(dict(self.signals), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  신호 기록 저장 실패: {e}")
    
    def add_signal(self, ticker, signal_type, strength, price):
        """새 신호 추가"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 중복 체크 (같은 날짜, 같은 종목)
        existing = [s for s in self.signals[ticker] if s['date'] == today]
        if existing:
            # 업데이트
            existing[0].update({
                'signal_type': signal_type,
                'strength': strength,
                'price': price,
                'updated_at': datetime.now().isoformat()
            })
        else:
            # 새 추가
            self.signals[ticker].append({
                'date': today,
                'signal_type': signal_type,  # 'buy' 또는 'sell'
                'strength': strength,        # 'strong' 또는 'normal'
                'price': price,
                'created_at': datetime.now().isoformat()
            })
        
        self.save_history()
        print(f"✅ 신호 기록: {ticker} {signal_type} ({strength})")
    
    def get_active_signals(self, ticker, days=30):
        """특정 종목의 최근 활성 신호들 가져오기"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        if ticker not in self.signals:
            return []
        
        # 최근 N일 이내 신호만
        recent = [s for s in self.signals[ticker] if s['date'] >= cutoff_date]
        return sorted(recent, key=lambda x: x['date'], reverse=True)
    
    def get_all_active_signals(self, days=30):
        """모든 종목의 최근 활성 신호"""
        result = {}
        for ticker in self.signals:
            signals = self.get_active_signals(ticker, days)
            if signals:
                result[ticker] = signals
        return result
    
    def has_recent_signal(self, ticker, days=7):
        """최근 N일 내 신호가 있었는지 확인"""
        signals = self.get_active_signals(ticker, days)
        return len(signals) > 0
    
    def clear_old_signals(self, keep_days=90):
        """오래된 신호 정리"""
        cutoff_date = (datetime.now() - timedelta(days=keep_days)).strftime('%Y-%m-%d')
        
        for ticker in list(self.signals.keys()):
            self.signals[ticker] = [
                s for s in self.signals[ticker] 
                if s['date'] >= cutoff_date
            ]
            if not self.signals[ticker]:
                del self.signals[ticker]
        
        self.save_history()
        print(f"🧹 오래된 신호 정리 완료 (90일 이전)")

if __name__ == "__main__":
    # 테스트
    history = SignalHistory()
    
    # 테스트 신호 추가
    history.add_signal('005930.KS', 'buy', 'strong', 65000)
    history.add_signal('NVDA', 'sell', 'normal', 125.5)
    
    # 조회
    print("\n📊 삼성전자 최근 신호:")
    for s in history.get_active_signals('005930.KS'):
        print(f"  {s['date']}: {s['signal_type']} ({s['strength']}) @ ${s['price']}")
    
    print("\n📊 모든 활성 신호:")
    all_signals = history.get_all_active_signals()
    for ticker, signals in all_signals.items():
        print(f"  {ticker}: {len(signals)}개 신호")
