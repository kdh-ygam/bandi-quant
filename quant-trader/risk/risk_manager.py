"""
Phase 4: 리스크 관리
변동성 타게팅, 포지션 크기, 손절가 계산
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))


class RiskManager:
    """리스크 관리자"""
    
    def __init__(self, target_vol=0.15):
        print("💰 Phase 4: 리스크 관리자 준비!")
        self.target_vol = target_vol
    
    def calculate_position(self, capital, strength, volatility, regime):
        """포지션 크기 계산"""
        base = capital * 0.10
        vol_adj = self.target_vol / (volatility + 0.05)
        signal_adj = strength * base * vol_adj
        
        regime_mult = {'BULL': 1.2, 'BEAR': 0.5, 'SIDEWAYS': 0.8, 'HIGH_VOL': 0.4}
        final = signal_adj * regime_mult.get(regime, 1.0)
        final = min(max(final, capital * 0.01), capital * 0.30)
        
        return {'size': round(final, 0), 'pct': round(final / capital * 100, 2)}
    
    def calculate_stop(self, entry, atr, regime, signal_type):
        """손절가 계산"""
        mult = {'BULL': 2.5, 'BEAR': 1.5, 'SIDEWAYS': 2.0, 'HIGH_VOL': 3.0}
        distance = atr * mult.get(regime, 2.0)
        
        stop = entry - distance if signal_type == 'BUY' else entry + distance
        return {'stop_price': round(stop, 2), 'stop_pct': round(distance / entry * 100, 2)}


def test():
    print("="*60)
    print("🧪 Phase 4 테스트")
    print("="*60)
    
    rm = RiskManager()
    
    pos = rm.calculate_position(100_000_000, 0.8, 0.20, 'BULL')
    stop = rm.calculate_stop(100_000, 2_000, 'BULL', 'BUY')
    
    print(f"\n📊 투자금: {pos['size']:,}원 ({pos['pct']}%)")
    print(f"   손절가: {stop['stop_price']:,}원 ({stop['stop_pct']:.2f}%)")
    print("\n✅ 완료!")


if __name__ == "__main__":
    test()
