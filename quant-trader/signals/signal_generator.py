"""
Phase 3: 신호 생성 (Signal Generation)
여러 AI 에이전트가 투표하는 앙상블 시스템

에이전트:
- Agent A: 모멘텀 (추세 따라가기)
- Agent B: 평균 회귀 (과매수/과매도 되돌림)
- Agent C: 이벤트 (뉴스/실적 기반)
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from data.data_pipeline import QuantDataPipeline
from regime.regime_detector import RegimeDetector


class SignalAgent:
    """
    개별 신호 에이전트
    """
    
    def __init__(self, name, strategy):
        self.name = name
        self.strategy = strategy
    
    def analyze(self, dataset, regime):
        """
        분석 실행
        
        Returns:
            dict: {'signal': 'BUY'/'SELL'/'HOLD', 'strength': 0-1, 'reason': '설명'}
        """
        raise NotImplementedError


class MomentumAgent(SignalAgent):
    """
    에이전트 A: 모멘텀 전략
    상승 추세를 따라감
    """
    
    def __init__(self):
        super().__init__("Agent A (모멘텀)", "추세 추종")
    
    def analyze(self, dataset, regime):
        prices = dataset['prices']
        closes = [p['close'] for p in prices]
        
        # MA 차이
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        ma_diff = (ma5 - ma20) / ma20
        
        # RSI
        tech = dataset.get('technical', {})
        rsi = tech.get('rsi', 50)
        
        # 국면 고려
        if regime['regime'] == 'BULL':
            if ma_diff > 0.02 and rsi < 70:
                return {
                    'agent': self.name,
                    'signal': 'BUY',
                    'strength': 0.8,
                    'reason': f"MA 상승(+{ma_diff*100:.1f}%), RSI 양호({rsi})"
                }
        
        elif regime['regime'] == 'BEAR':
            if ma_diff < -0.02:
                return {
                    'agent': self.name,
                    'signal': 'SELL',
                    'strength': 0.7,
                    'reason': f"하락 추세({ma_diff*100:.1f}%)"
                }
        
        return {
            'agent': self.name,
            'signal': 'HOLD',
            'strength': 0.3,
            'reason': "추세 불명확"
        }


class MeanReversionAgent(SignalAgent):
    """
    에이전트 B: 평균 회귀
    과매수/과매도 반전
    """
    
    def __init__(self):
        super().__init__("Agent B (평균회귀)", "역추세")
    
    def analyze(self, dataset, regime):
        tech = dataset.get('technical', {})
        rsi = tech.get('rsi', 50)
        
        if rsi > 70:
            return {
                'agent': self.name,
                'signal': 'SELL',
                'strength': 0.7,
                'reason': f"RSI 과매수({rsi})"
            }
        elif rsi < 30:
            return {
                'agent': self.name,
                'signal': 'BUY',
                'strength': 0.7,
                'reason': f"RSI 과매도({rsi})"
            }
        
        return {
            'agent': self.name,
            'signal': 'HOLD',
            'strength': 0.2,
            'reason': f"RSI 중립({rsi})"
        }


class EventAgent(SignalAgent):
    """
    에이전트 C: 이벤트 기반
    뉴스/감성 분석
    """
    
    def __init__(self):
        super().__init__("Agent C (이벤트)", "감성 분석")
    
    def analyze(self, dataset, regime):
        alt = dataset.get('alternative', {})
        sentiment = alt.get('news_sentiment', 0)
        
        if sentiment > 0.3:
            return {
                'agent': self.name,
                'signal': 'BUY',
                'strength': min(sentiment + 0.4, 0.9),
                'reason': f"뉴스 긍정({sentiment:+.2f})"
            }
        elif sentiment < -0.3:
            return {
                'agent': self.name,
                'signal': 'SELL',
                'strength': min(abs(sentiment) + 0.4, 0.9),
                'reason': f"뉴스 부정({sentiment:+.2f})"
            }
        
        return {
            'agent': self.name,
            'signal': 'HOLD',
            'strength': 0.3,
            'reason': f"뉴스 중립({sentiment:+.2f})"
        }


class EnsembleSignalGenerator:
    """
    앙상블 신호 생성기
    3개 에이전트의 의겳을 결합
    """
    
    def __init__(self):
        print("🤖 Phase 3: 신호 생성기 준비!")
        self.agents = [
            MomentumAgent(),
            MeanReversionAgent(),
            EventAgent()
        ]
    
    def generate_signal(self, dataset, regime):
        """
        최종 신호 생성
        
        Returns:
            dict: {
                'final_signal': 'BUY'/'SELL'/'HOLD',
                'signal_strength': 0-1,
                'agent_votes': [각 에이전트 결과],
                'explanation': '설명'
            }
        """
        print(f"\n   🎯 {dataset.get('symbol', '종목')} 신호 생성")
        
        # 각 에이전트 실행
        votes = []
        buy_count = 0
        sell_count = 0
        total_strength = 0
        
        for agent in self.agents:
            vote = agent.analyze(dataset, regime)
            votes.append(vote)
            
            if vote['signal'] == 'BUY':
                buy_count += 1
            elif vote['signal'] == 'SELL':
                sell_count += 1
            
            total_strength += vote['strength']
            
            print(f"      {vote['agent']}: {vote['signal']} (강도: {vote['strength']:.1f}) - {vote['reason']}")
        
        # 앙상블 결정
        avg_strength = total_strength / len(votes)
        
        if buy_count >= 2:
            final_signal = 'BUY'
            confidence = min(avg_strength + 0.2, 0.95)
        elif sell_count >= 2:
            final_signal = 'SELL'
            confidence = min(avg_strength + 0.2, 0.95)
        else:
            final_signal = 'HOLD'
            confidence = 0.5
        
        return {
            'symbol': dataset.get('symbol', 'UNKNOWN'),
            'final_signal': final_signal,
            'signal_strength': round(confidence, 2),
            'agent_votes': votes,
            'vote_summary': f"매수: {buy_count}, 매도: {sell_count}, 관말: {3-buy_count-sell_count}",
            'explanation': f"3개 에이전트 중 {buy_count if final_signal == 'BUY' else sell_count}개가 {final_signal} 추천"
        }


def test():
    """테스트"""
    print("="*60)
    print("🧪 Phase 3 테스트: 신호 생성")
    print("="*60)
    
    pipeline = QuantDataPipeline()
    regime_detector = RegimeDetector()
    signal_generator = EnsembleSignalGenerator()
    
    for symbol in ["AAPL", "005930.KS"]:
        print(f"\n{'='*60}")
        print(f"📊 {symbol} 신호 생성 테스트")
        print(f"{'='*60}")
        
        # 데이터 준비
        dataset = pipeline.prepare_dataset(symbol, days=30)
        
        # 국면 판단
        regime = regime_detector.detect_regime(dataset['prices'])
        print(f"\n   📈 현재 국면: {regime['description']}")
        
        # 신호 생성
        result = signal_generator.generate_signal(dataset, regime)
        
        print(f"\n   🎯 최종 신호: {result['final_signal']}")
        print(f"      신호 강도: {result['signal_strength']*100:.0f}%")
        print(f"      투표 결과: {result['vote_summary']}")
        print(f"      설명: {result['explanation']}")
    
    print(f"\n{'='*60}")
    print("✅ Phase 3 테스트 완료!")
    print("="*60)


if __name__ == "__main__":
    test()
