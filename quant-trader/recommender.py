"""파파 AI 종목 추천기"""

import sys
sys.path.append('/Users/mchom/.openclaw/workspace/quant-trader')

from data.data_pipeline import QuantDataPipeline
from datetime import datetime
import random

class PapaRecommender:
    def __init__(self):
        self.pipeline = QuantDataPipeline()
        self.watchlist = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", 
            "AMD", "INTC", "PLTR", "COIN", "PYPL", "SQ", "CRWD", "NET",
            "005930.KS", "035420.KS", "000660.KS"
        ]
    
    def analyze_stock(self, symbol, days=30):
        """종목 분석"""
        data = self.pipeline.prepare_dataset(symbol, days)
        prices = data['prices']
        tech = data['technical']
        
        closes = [p['close'] for p in prices]
        rsi = tech['rsi']
        ma_diff = tech['ma_diff']
        volatility = tech['volatility']
        return_20d = (closes[-1] - closes[-20]) / closes[-20] * 100
        
        # 확률 계산
        score = 50
        signals = []
        
        if rsi < 35:
            score += 20
            signals.append('RSI 과매도')
        elif rsi < 40:
            score += 10
            signals.append('RSI 약과매도')
        
        if return_20d < -10:
            score += 10
            signals.append('과도한 하락')
        
        if ma_diff > 2:
            score += 5
            signals.append('상승추세')
        
        if volatility < 3:
            score += 5
            signals.append('안정적')
        
        score = max(10, min(95, score))
        
        return {
            'symbol': symbol,
            'prob': score,
            'price': closes[-1],
            'rsi': rsi,
            'return_20d': return_20d,
            'signals': signals,
            'recommend': 'STRONG_BUY' if score >= 70 else 'BUY' if score >= 60 else 'HOLD'
        }
    
    def scan_and_recommend(self):
        """70%+ 종목 찾기"""
        print("="*70)
        print("🎯 파파 AI 종목 추천기 (확률 70%+)")
        print("="*70)
        
        results = []
        for symbol in self.watchlist:
            try:
                result = self.analyze_stock(symbol)
                results.append(result)
            except:
                continue
        
        # 확률 높은 순 정렬
        results.sort(key=lambda x: x['prob'], reverse=True)
        
        # 70% 이상 필터
        top_picks = [r for r in results if r['prob'] >= 70]
        
        if top_picks:
            print(f"\n✅ 확률 70%+ 종목 {len(top_picks)}개 발견!\n")
            for i, pick in enumerate(top_picks, 1):
                print(f"{'='*70}")
                print(f"🥇 추천 {i}: {pick['symbol']}")
                print(f"   🎯 확률: {pick['prob']}%")
                print(f"   💰 현재가: ${pick['price']:.2f}")
                print(f"   📊 RSI: {pick['rsi']:.1f}")
                print(f"   📉 20일수익: {pick['return_20d']:+.1f}%")
                print(f"   ✅ 시그널: {', '.join(pick['signals'])}")
                print(f"   📋 등급: {pick['recommend']}")
        else:
            # 70% 없으면 60% 이상이라도 보여줌
            good_picks = [r for r in results if r['prob'] >= 60][:5]
            print(f"\n⚠️ 확률 70%+ 종목 없음")
            print(f"   대신 확률 60%+ 종목 {len(good_picks)}개:\n")
            for i, pick in enumerate(good_picks, 1):
                print(f"   {i}. {pick['symbol']}: {pick['prob']}%")
        
        print(f"\n{'='*70}")
        return top_picks

if __name__ == "__main__":
    rec = PapaRecommender()
    rec.scan_and_recommend()
