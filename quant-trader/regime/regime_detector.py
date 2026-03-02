"""
Phase 2: 시장 국면(Regime) 판단
상승장/하락장/횡보장 탐지

사용법:
    from regime.regime_detector import RegimeDetector
    
    detector = RegimeDetector()
    regime = detector.detect_regime(price_data)
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from data.data_pipeline import QuantDataPipeline
import math


class RegimeDetector:
    """
    시장 국면 탐지기
    
    국면 종류:
    - BULL: 상승장
    - BEAR: 하락장  
    - SIDEWAYS: 횡보장
    - HIGH_VOL: 고변동성
    """
    
    def __init__(self):
        print("🧠 Phase 2: 시장 국면 탐지기 준비!")
    
    def detect_regime(self, price_data):
        """
        시장 국면 탐지
        """
        if len(price_data) < 20:
            return {'regime': 'UNKNOWN', 'confidence': 0}
        
        closes = [d['close'] for d in price_data]
        returns_20d = (closes[-1] - closes[-20]) / closes[-20]
        
        # 변동성
        daily_returns = [(closes[i] - closes[i-1]) / closes[i-1] 
                        for i in range(1, len(closes))]
        volatility = (sum([r**2 for r in daily_returns]) / len(daily_returns)) ** 0.5
        volatility_annual = volatility * math.sqrt(252) * 100
        
        # 추세
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        ma_diff = (ma5 - ma20) / ma20
        
        # 판단
        if returns_20d > 0.02 and ma_diff > 0.02:
            return {
                'regime': 'BULL',
                'confidence': 85,
                'description': '📈 상승장',
                'strategy': '추세 추종 매수',
                'return_20d': round(returns_20d * 100, 2),
                'volatility': round(volatility_annual, 2)
            }
        elif returns_20d < -0.02 and ma_diff < -0.02:
            return {
                'regime': 'BEAR', 
                'confidence': 85,
                'description': '📉 하락장',
                'strategy': '관말 또는 공매도',
                'return_20d': round(returns_20d * 100, 2),
                'volatility': round(volatility_annual, 2)
            }
        elif volatility_annual > 50:
            return {
                'regime': 'HIGH_VOL',
                'confidence': 75,
                'description': '⚡ 고변동성',
                'strategy': '변동성 매도',
                'return_20d': round(returns_20d * 100, 2),
                'volatility': round(volatility_annual, 2)
            }
        else:
            return {
                'regime': 'SIDEWAYS',
                'confidence': 60,
                'description': '🔄 횡보장',
                'strategy': '평균 회귀',
                'return_20d': round(returns_20d * 100, 2),
                'volatility': round(volatility_annual, 2)
            }


def test():
    """테스트"""
    print("="*60)
    print("🧪 Phase 2 테스트")
    print("="*60)
    
    pipeline = QuantDataPipeline()
    detector = RegimeDetector()
    
    for symbol in ["AAPL", "TSLA"]:
        print(f"\n📊 {symbol} 분석")
        dataset = pipeline.prepare_dataset(symbol, days=30)
        regime = detector.detect_regime(dataset['prices'])
        
        print(f"   국면: {regime['description']}")
        print(f"   춤 ㄴ: {regime['strategy']}")
        print(f"   20일 수익률: {regime['return_20d']:+.2f}%")
    
    print("\n✅ 완료!")


if __name__ == "__main__":
    test()
