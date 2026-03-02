#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║           반디 퀀트 AI 종합 추천 시스템 v1.0                        ║
║                                                                      ║
║  기능:                                                               ║
║  - 기술적 지표 + 차트 패턴 종합 분석                                ║
║  - AI 가중치 기반 종합 점수 산정                                     ║
║  - 매수/매도 추천 종목 선정                                          ║
║  - 리스크 평가 및 포트폴리오 제안                                   ║
║                                                                      ║
║  Created by: 반디 🐾                                                ║
║  Date: 2026-02-26                                                    ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# chart_module 임포트
sys.path.insert(0, '/Users/mchom/.openclaw/workspace')
from chart_module import ChartGenerator, PatternRecognizer

import pandas as pd


@dataclass
class StockScore:
    """종목 평가 점수 데이터 클래스"""
    ticker: str
    name: str
    sector: str
    
    # 기술적 지표 점수 (0-100)
    rsi_score: float          # RSI 과매도/과매수 점수
    macd_score: float         # MACD 신호 점수
    bb_score: float           # 볼린저밴드 위치 점수
    volume_score: float       # 거래량 점수
    trend_score: float        # 추세 점수
    
    # 패턴 점수 (0-100)
    pattern_score: float      # 패턴 감지 점수
    pattern_bonus: float      # 패턴 보너스/페널티
    
    # 종합 점수
    total_score: float        # 총점
    signal: str               # 추천 신호
    confidence: str           # 신뢰도
    
    # 상세 정보
    current_price: float
    change_pct: float
    patterns_found: List[str]
    risk_level: str           # 리스크 등급
    position: str             # 투자 의견


class BandiQuantAI:
    """반디 퀀트 AI 추천 엔진"""
    
    def __init__(self, analysis_date: str = None):
        self.analysis_date = analysis_date or datetime.now().strftime('%Y-%m-%d')
        self.chart_gen = ChartGenerator()
        self.scores = []
        
        # 가중치 설정 (합계 100)
        self.weights = {
            'rsi': 20,            # RSI 과매도/과매수 (20%)
            'macd': 15,           # MACD 신호 (15%)
            'bb': 15,             # 볼린저밴드 (15%)
            'volume': 10,         # 거래량 (10%)
            'trend': 15,          # 추세 (15%)
            'pattern': 25         # 패턴 (25%) - 가장 중요
        }
    
    def calculate_rsi_score(self, rsi: float) -> float:
        """RSI 점수 계산 (과매도=높은점수, 과매수=낮은점수)"""
        # RSI 30 이하: 매수 적기 (100점)
        # RSI 70 이상: 매도 적기 (0점)
        # 중간: 선형 보간
        if rsi <= 30:
            return 100 - (rsi / 30) * 20  # 30→80점, 0→100점
        elif rsi >= 70:
            return max(0, 50 - ((rsi - 70) / 30) * 50)  # 70→50점, 100→0점
        else:
            # 30-70 사이: 중립대에서 점수 하�
            return 80 - abs(rsi - 50) * 1.5
    
    def calculate_macd_score(self, macd_trend: str, macd_hist: float = 0) -> float:
        """MACD 점수 계산"""
        trend_scores = {
            '🟢 골든크로스': 100,
            '📈 상승세': 70,
            '중립': 50,
            '📉 하락세': 30,
            '🔴 데드크로스': 0
        }
        
        base_score = trend_scores.get(macd_trend, 50)
        
        # 히스토그램 강도 반영
        if macd_hist > 0:
            base_score += min(10, macd_hist / 1000)  # 양수 보너스
        else:
            base_score -= min(10, abs(macd_hist) / 1000)  # 음수 페널티
        
        return max(0, min(100, base_score))
    
    def calculate_bb_score(self, bb_position: str, bb_width: float = 0) -> float:
        """볼린저밴드 점수 계산"""
        # 하단 근처 = 매수 기회 (높은 점수)
        # 상단 근처 = 매도 기회 (낮은 점수)
        position_scores = {
            '📉 하단이탈': 100,      # 과매도 - 강한 매수
            '🔽 하단접근': 80,       # 하단 근처 - 매수 관망
            '중간': 50,              # 중립
            '🔼 상단접근': 20,       # 상단 근처 - 매도 관망
            '🚀 상단돌파': 0         # 과매수 - 매도
        }
        
        base_score = position_scores.get(bb_position, 50)
        
        # 밴드폭 반영 (좁으면 변동성 확대 예고 - 중립 유지)
        if bb_width < 10:  # 스퀴즈 상태
            base_score = 50  # 중립으로 조정
        
        return base_score
    
    def calculate_volume_score(self, volume_ratio: float) -> float:
        """거래량 점수 계산"""
        # 1.0-1.5x: 정상 (50점)
        # 1.5-2.5x: 활발 (60-80점)
        # 2.5x+: 거래폭발 (80-100점) - 돌파 확인
        # <0.5x: 소진 (30점) - 주의
        
        if volume_ratio >= 2.5:
            return min(100, 80 + (volume_ratio - 2.5) * 10)
        elif volume_ratio >= 1.5:
            return 60 + (volume_ratio - 1.5) * 20
        elif volume_ratio >= 0.8:
            return 40 + (volume_ratio - 0.8) * 25
        else:
            return max(20, volume_ratio * 50)
    
    def calculate_trend_score(self, trend_emoji: str) -> float:
        """추세 점수 계산"""
        trend_map = {
            '📈': 80,    # 상승추세
            '📉': 20,    # 하락추세
            '➡️': 50     # 횡보
        }
        return trend_map.get(trend_emoji, 50)
    
    def calculate_pattern_score(self, patterns: List[Dict]) -> Tuple[float, float]:
        """
        패턴 점수 계산
        Returns: (패턴점수, 보너스)
        """
        if not patterns:
            return 50, 0  # 패턴 없음 = 중립
        
        # 패턴 유형별 점수
        pattern_scores = {
            '쌍바닥': 95,
            'Double Bottom': 95,
            '역헤드앤숄더': 95,
            'Inverse Head and Shoulders': 95,
            '컵앤핸들': 90,
            '하락쐐기': 85,
            '모닝스타': 85,
            '상승잉걸핑': 80,
            '망치형': 75,
            '상승삼각형': 70,
            '불페넌트': 70,
            '볼린저 스퀴즈': 60,
            '대칭삼각형': 50,
            '베어페넌트': 25,
            '하락잉걸핑': 20,
            '역망치형': 20,
            '이브닝스타': 15,
            '헤드앤숄더': 10,
            '쌍천장': 10,
            '상승쐐기': 5,
            '하락삼각형': 0
        }
        
        scores = []
        bonuses = []
        
        for pattern in patterns:
            pattern_name = pattern.get('pattern', '')
            signal = pattern.get('signal', '')
            
            # 패턴 이름 매칭
            base_score = 50
            for key, score in pattern_scores.items():
                if key in pattern_name:
                    base_score = score
                    break
            
            scores.append(base_score)
            
            # 신호 강도 보너스
            if '강력' in signal or '강한' in signal:
                bonuses.append(10)
            elif '반전' in signal:
                bonuses.append(5)
        
        avg_score = sum(scores) / len(scores) if scores else 50
        total_bonus = sum(bonuses)
        
        return avg_score, total_bonus
    
    def analyze_stock(self, stock_data: Dict) -> Optional[StockScore]:
        """개별 종목 종합 분석"""
        ticker = stock_data['ticker']
        name = stock_data['name']
        
        print(f"🔄 {name} ({ticker}) 분석 중...")
        
        # 1. 기술적 지표 점수
        rsi_score = self.calculate_rsi_score(stock_data.get('rsi', 50))
        macd_score = self.calculate_macd_score(
            stock_data.get('macd_trend', '중립'),
            stock_data.get('macd_histogram', 0)
        )
        bb_score = self.calculate_bb_score(
            stock_data.get('bb_position', '중간'),
            stock_data.get('bb_width', 0)
        )
        volume_score = self.calculate_volume_score(stock_data.get('volume_ratio', 1.0))
        
        # 2. 차트 패턴 분석
        try:
            ohlcv_data = self.chart_gen.fetch_ohlcv_data(ticker, days=60)
            if ohlcv_data and len(ohlcv_data['ohlcv']) >= 30:
                df = pd.DataFrame(ohlcv_data['ohlcv'])
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df.rename(columns={'open':'Open','high':'High','low':'Low',
                                  'close':'Close','volume':'Volume'}, inplace=True)
                df = df.dropna()
                
                recognizer = PatternRecognizer(df)
                pattern_results = recognizer.analyze_all_patterns()
                
                trend_emoji = pattern_results['trend']['emoji']
                trend_score = self.calculate_trend_score(trend_emoji)
                
                pattern_score, pattern_bonus = self.calculate_pattern_score(
                    pattern_results['patterns']
                )
                
                patterns_found = [p['pattern'] for p in pattern_results['patterns']]
            else:
                trend_score = 50
                pattern_score = 50
                pattern_bonus = 0
                patterns_found = []
        except Exception as e:
            print(f"   ⚠️  패턴 분석 실패: {e}")
            trend_score = 50
            pattern_score = 50
            pattern_bonus = 0
            patterns_found = []
        
        # 3. 종합 점수 계산 (가중치 적용)
        total_score = (
            rsi_score * self.weights['rsi'] / 100 +
            macd_score * self.weights['macd'] / 100 +
            bb_score * self.weights['bb'] / 100 +
            volume_score * self.weights['volume'] / 100 +
            trend_score * self.weights['trend'] / 100 +
            (pattern_score + pattern_bonus) * self.weights['pattern'] / 100
        )
        
        total_score = max(0, min(100, total_score))
        
        # 4. 신호 및 의견 도출
        if total_score >= 80:
            signal = '🟢 강력매수'
            confidence = '높음'
            position = '적극 매수 권장'
        elif total_score >= 65:
            signal = '🟡 매수'
            confidence = '중간'
            position = '분할 매수 고려'
        elif total_score >= 45:
            signal = '⚪ 관망'
            confidence = '낮음'
            position = '현상태 유지'
        elif total_score >= 30:
            signal = '🟠 매도대비'
            confidence = '중간'
            position = '매도 준비'
        else:
            signal = '🔴 강력매도'
            confidence = '높음'
            position = '즉시 매도 권장'
        
        # 5. 리스크 평가
        volatility = stock_data.get('bb_width', 20)
        if volatility > 30:
            risk_level = '높음'
        elif volatility > 15:
            risk_level = '중간'
        else:
            risk_level = '낮음'
        
        score = StockScore(
            ticker=ticker,
            name=name,
            sector=stock_data.get('sector', '기타'),
            rsi_score=round(rsi_score, 1),
            macd_score=round(macd_score, 1),
            bb_score=round(bb_score, 1),
            volume_score=round(volume_score, 1),
            trend_score=round(trend_score, 1),
            pattern_score=round(pattern_score, 1),
            pattern_bonus=pattern_bonus,
            total_score=round(total_score, 1),
            signal=signal,
            confidence=confidence,
            current_price=stock_data.get('current_price', 0),
            change_pct=stock_data.get('change_pct', 0),
            patterns_found=patterns_found,
            risk_level=risk_level,
            position=position
        )
        
        print(f"   ✅ 종합점수: {total_score:.1f} | 신호: {signal}")
        return score
    
    def generate_recommendations(self, json_path: str = None):
        """전체 종목 분석 및 추천 생성"""
        if json_path is None:
            json_path = f"/Users/mchom/.openclaw/workspace/analysis/daily_briefing_{self.analysis_date}.json"
        
        if not os.path.exists(json_path):
            print(f"❌ 분석 파일 없음: {json_path}")
            return None
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        stocks = data.get('stocks', [])
        
        print("=" * 70)
        print("🤖 반디 퀀트 AI 종합 추천 시스템")
        print("=" * 70)
        print(f"분석 대상: {len(stocks)}개 종목")
        print(f"분석 날짜: {self.analysis_date}")
        print("=" * 70)
        
        # 모든 종목 분석
        for stock in stocks:
            score = self.analyze_stock(stock)
            if score:
                self.scores.append(score)
            print()
        
        # 점수순 정렬
        self.scores.sort(key=lambda x: x.total_score, reverse=True)
        
        return self.generate_report()
    
    def generate_report(self) -> str:
        """최종 추천 리포트 생성"""
        report = []
        
        report.append("=" * 70)
        report.append("📊 반디 퀀트 AI 종합 추천 리포트")
        report.append(f"생성시간: {datetime.now().strftime('%Y-%m-%d %H:%M')} KST")
        report.append("=" * 70)
        report.append("")
        
        # TOP 5 매수 추천
        buy_candidates = [s for s in self.scores if s.total_score >= 65]
        buy_candidates.sort(key=lambda x: x.total_score, reverse=True)
        
        report.append("🏆 TOP 5 매수 추천 종목")
        report.append("-" * 70)
        for i, score in enumerate(buy_candidates[:5], 1):
            report.append(f"\n{i}. {score.signal} {score.name} ({score.ticker})")
            report.append(f"   종합점수: {score.total_score} | 신뢰도: {score.confidence}")
            report.append(f"   현재가: ${score.current_price:,.2f} ({score.change_pct:+.2f}%)")
            report.append(f"   투자의견: {score.position}")
            report.append(f"   상세점수: RSI({score.rsi_score}) MACD({score.macd_score}) BB({score.bb_score})")
            report.append(f"            추세({score.trend_score}) 패턴({score.pattern_score}+{score.pattern_bonus})")
            if score.patterns_found:
                report.append(f"   🎯 감지패턴: {', '.join(score.patterns_found[:2])}")
            report.append(f"   ⚠️  리스크: {score.risk_level}")
        
        # 매도 주의 종목
        sell_candidates = [s for s in self.scores if s.total_score <= 35]
        if sell_candidates:
            report.append("\n")
            report.append("🔴 매도 주의 종목 (상위 5개)")
            report.append("-" * 70)
            for i, score in enumerate(sorted(sell_candidates, key=lambda x: x.total_score)[:5], 1):
                report.append(f"{i}. {score.signal} {score.name} - 점수: {score.total_score}")
        
        # 포트폴리오 제안
        report.append("\n")
        report.append("💼 포트폴리오 제안")
        report.append("-" * 70)
        report.append("안전형: 상위 3개 종목 각 5%씩 분할 매수")
        report.append("공격형: 상위 1-2개 종목 집중 매수 (리스크 감수)")
        report.append("위험관리: RSI 70+ 종목은 50% 익절 고려")
        
        report.append("\n" + "=" * 70)
        report.append("_반디가 파파의 수익을 응원합니다 🐾_")
        
        return "\n".join(report)


def main():
    """메인 실행"""
    ai = BandiQuantAI()
    report = ai.generate_recommendations()
    
    if report:
        print(report)
        
        # 파일 저장
        output_path = f"/Users/mchom/.openclaw/workspace/analysis/ai_recommendation_{ai.analysis_date}.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n💾 리포트 저장 완료: {output_path}")


if __name__ == "__main__":
    main()
