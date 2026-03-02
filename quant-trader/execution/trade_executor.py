"""Phase 5: 실행 및 백테스팅"""

import sys
sys.path.append('/Users/mchom/.openclaw/workspace/quant-trader')

from data.data_pipeline import QuantDataPipeline
from regime.regime_detector import RegimeDetector  
from signals.signal_generator import EnsembleSignalGenerator
from risk.risk_manager import RiskManager

class QuantSystem:
    def __init__(self, capital=100_000_000):
        print("🚀 Phase 5: 퀀트 시스템!")
        self.capital = capital
        self.pipeline = QuantDataPipeline()
        self.regime = RegimeDetector()
        self.signal = EnsembleSignalGenerator()
        self.risk = RiskManager()
    
    def analyze(self, symbol, days=30):
        print(f"\n🎯 {symbol}")
        data = self.pipeline.prepare_dataset(symbol, days)
        reg = self.regime.detect_regime(data['prices'])
        sig = self.signal.generate_signal(data, reg)
        
        vol = data['technical'].get('volatility', 2.0) / 100
        atr = data['prices'][-1]['close'] * vol * 0.1
        
        pos = self.risk.calculate_position(self.capital, sig['signal_strength'], vol, reg['regime'])
        stop = self.risk.calculate_stop(data['prices'][-1]['close'], atr, reg['regime'], sig['final_signal'])
        
        print(f"   {sig['final_signal']}: {pos['size']:,}원 (손절 {stop['stop_pct']:.1f}%)")
        return sig['final_signal']

def main():
    print("="*60)
    print("🚀 파파AI 퀀트 트레이더")
    print("="*60)
    system = QuantSystem()
    
    for symbol in ["AAPL", "TSLA"]:
        system.analyze(symbol)
    
    print("\n✅ 완료!")

if __name__ == "__main__":
    main()
