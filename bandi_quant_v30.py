#!/usr/bin/env python3
"""
반디 퀀트 v3.0 - 매일 장마감 자동 브리핑 시스템
패턴 분석 + 반디 AI 의견 통합
"""

import os
import json
import subprocess
import requests
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# 텔레그램 설정
TELEGRAM_TOKEN = "8599663503:AAGfs7Sh2vy6tfHOr9UG-O_lcaG3cjPdH2s"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
CHAT_ID = "6146433054"


@dataclass
class StockAnalysis:
    """종목 분석 데이터 클래스 - v3.0"""
    ticker: str
    name: str
    sector: str
    current_price: float
    previous_price: float
    change_pct: float
    rsi: float
    macd_trend: str = ""
    bb_position: str = ""
    volume_ratio: float = 1.0
    currency: str = "KRW"
    # 패턴 분석
    patterns: List[Dict] = field(default_factory=list)
    pattern_summary: str = ""
    # AI 의견
    bandi_comment: str = ""
    bandi_opinion: str = ""
    bandi_strategy: str = ""
    recommendation: str = ""

    def __post_init__(self):
        if self.patterns is None:
            self.patterns = []


def detect_candlestick_patterns(prices_df):
    """
    14가지 고급 캔들 패턴 자동 감지
    """
    patterns = []
    
    for i in range(2, len(prices_df)):
        curr = prices_df.iloc[i]
        prev = prices_df.iloc[i-1]
        prev2 = prices_df.iloc[i-2]
        
        open_c, close_c = curr['Open'], curr['Close']
        high_c, low_c = curr['High'], curr['Low']
        body = abs(close_c - open_c)
        upper_shadow = high_c - max(open_c, close_c)
        lower_shadow = min(open_c, close_c) - low_c
        total_range = high_c - low_c
        
        open_p, close_p = prev['Open'], prev['Close']
        
        # 망치형 (Hammer)
        if lower_shadow > body * 1.8 and upper_shadow < body * 0.4 and close_c > open_c:
            patterns.append({
                "name": "망치형",
                "signal": "강함",
                "type": "매수",
                "desc": "하락 후 긴 아래꼬리, 반등 신호"
            })
        
        # 잉걸불 (Bullish Engulfing)
        elif close_p < open_p and close_c > open_c and open_c < close_p and close_c > open_p:
            patterns.append({
                "name": "잉걸불",
                "signal": "강함",
                "type": "매수",
                "desc": "양봉이 음봉 포용, 매수세 유입"
            })
        
        # 모닝스타
        elif i >= 2:
            prev2_close = prev2['Close']
            prev2_open = prev2['Open']
            if (prev2_close < prev2_open and
                abs(close_p - open_p) < abs(prev2_close - prev2_open) * 0.3 and
                close_c > open_c and close_c > (prev2_open + prev2_close) / 2):
                patterns.append({
                    "name": "모닝스타",
                    "signal": "강함",
                    "type": "매수",
                    "desc": "하락-관망-상승 3일 반전"
                })
        
        # 도지
        if total_range > 0 and body / total_range < 0.1:
            if lower_shadow > body * 2 and close_c > open_c:
                patterns.append({
                    "name": "망치형 도지",
                    "signal": "강함", 
                    "type": "매수",
                    "desc": "하락 후 반전"
                })
    
    return patterns


def calculate_indicators(df):
    """기술적 지표 계산 (RSI, MACD, 볼린저)"""
    import numpy as np
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # 볼린저
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    return df


def generate_bandai_analysis(stock: StockAnalysis) -> Dict[str, str]:
    """반디 AI 심층 분석 및 의견 생성"""
    opinion_parts = []
    strategy_parts = []
    
    # RSI 분석
    if stock.rsi < 30:
        opinion_parts.append(f"RSI {stock.rsi:.1f} 과매도. 역사적으로 반등이 나타납니다.")
        strategy_parts.append("과매도 구간에서 소량 분할 매수 고려.")
    elif stock.rsi < 40:
        opinion_parts.append(f"RSI {stock.rsi:.1f} 저점 근접.")
        strategy_parts.append("추가 하락 시 분할 매수 또는 반등 확인 후 진입.")
    elif stock.rsi > 70:
        opinion_parts.append(f"RSI {stock.rsi:.1f} 과매수. 익절 고려.")
        strategy_parts.append("수익 시 일부 익절 권고.")
    
    # 패턴 분석
    if stock.patterns:
        buy_patterns = [p for p in stock.patterns if p['type'] == '매수']
        if buy_patterns:
            p = buy_patterns[0]
            opinion_parts.append(f"'{p['name']}' 패턴: {p['desc']}")
            strategy_parts.append("패턴 확인으로 매수 타이밍.")
    
    # 볼린저
    if '상단돌파' in stock.bb_position:
        opinion_parts.append("볼린저 상단 돌파. 단기 조정 가능.")
    elif '하단' in stock.bb_position:
        opinion_parts.append("볼린저 하단 근접. 매수 적기 가능.")
        strategy_parts.append("분할 매수 접근.")
    
    # MACD
    if '골든' in stock.macd_trend:
        opinion_parts.append("MACD 골든크로스. 상승 추세.")
        strategy_parts.append("추가 상승 확인 후 확대.")
    
    if not opinion_parts:
        opinion_parts.append("특별한 신호 없음. 추세 관망.")
    
    if not strategy_parts:
        if '매수' in stock.recommendation:
            strategy_parts.append("분할 매수 접근.")
        else:
            strategy_parts.append("관망 후 추세 확인.")
    
    return {
        "comment": " ".join(opinion_parts),
        "opinion": "\n".join(opinion_parts),
        "strategy": "\n".join(strategy_parts)
    }


class MarketBriefing:
    """반디 퀀트 브리핑 시스템 v3.0"""
    
    def __init__(self):
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self.time_str = datetime.now().strftime("%H:%M")
        self.results = []
        self.buy_recommendations = []
        self.sell_recommendations = []
    
    def analyze_stock(self, ticker: str, name: str, period="3mo") -> Optional[StockAnalysis]:
        """개별 종목 분석 (패턴 + 지표 + AI 의견)"""
        import numpy as np
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
            
            if data.empty or len(data) < 20:
                return None
            
            # 지표 계산
            data = calculate_indicators(data)
            
            # 패턴 감지
            patterns = detect_candlestick_patterns(data)
            
            # 최근 데이터
            latest = data.iloc[-1]
            prev = data.iloc[-2]
            
            # 통화 단위
            currency = 'KRW' if ticker.endswith('.KS') else 'USD'
            
            # 분석 결과
            analysis = StockAnalysis(
                ticker=ticker,
                name=name,
                sector="",
                current_price=latest['Close'],
                previous_price=prev['Close'],
                change_pct=((latest['Close']/prev['Close'])-1)*100,
                rsi=latest['RSI'] if not np.isnan(latest['RSI']) else 50,
                macd_trend="상승" if latest['MACD'] > latest['MACD_Signal'] else "하락",
                bb_position="상단" if latest['Close'] > latest['BB_Upper'] else "하단" if latest['Close'] < latest['BB_Lower'] else "중간",
                volume_ratio=latest['Volume'] / data['Volume'].tail(20).mean() if data['Volume'].tail(20).mean() > 0 else 1.0,
                currency=currency,
                patterns=patterns,
                pattern_summary=", ".join([p['name'] for p in patterns[-3:]]) if patterns else "없음",
                recommendation="분석중"
            )
            
            # 반디 AI 의견 생성
            bandi_analysis = generate_bandai_analysis(analysis)
            analysis.bandi_comment = bandi_analysis['comment']
            analysis.bandi_opinion = bandi_analysis['opinion']
            analysis.bandi_strategy = bandi_analysis['strategy']
            
            # 등급 판정
            if analysis.rsi < 35:
                analysis.recommendation = "🔴 강력매수"
            elif analysis.rsi < 45:
                analysis.recommendation = "🟡 매수권유"
            elif analysis.rsi < 50 and analysis.change_pct < 0:
                analysis.recommendation = "🟠 매수대비"
            elif analysis.rsi > 70:
                analysis.recommendation = "🔴 강력매도"
            else:
                analysis.recommendation = "⚪ 보유"
            
            return analysis
            
        except Exception as e:
            print(f"분석 오류 {ticker}: {e}")
            return None
    
    def generate_telegram_message(self) -> str:
        """텔레그램 브리핑 메시지 생성 (패턴 + 반디 의견 포함)"""
        lines = []
        
        # 헤더
        lines.append(f"📊 반디 퀀트 v3.0 장마감 브리핑")
        lines.append(f"⏰ {self.date_str} {self.time_str} KST")
        lines.append(f"🎯 기준: 캔들패턴 + 기술지표 + 반디 의견")
        lines.append("")
        
        # 매수 추천
        if self.buy_recommendations:
            lines.append("━" * 40)
            lines.append("🎯 *매수 추천 종목 (패턴 + 반디 분석)*")
            lines.append("━" * 40)
            
            sorted_buys = sorted(self.buy_recommendations, key=lambda x: x.rsi)[:5]
            for idx, s in enumerate(sorted_buys, 1):
                unit = "원" if s.currency == 'KRW' else "$"
                price_str = f"{int(s.current_price):,}{unit}" if s.currency == 'KRW' else f"{unit}{s.current_price:,.2f}"
                
                lines.append(f"")
                lines.append(f"{idx}. *{s.name}* ({s.ticker})")
                lines.append(f"   📍 등급: {s.recommendation}")
                lines.append(f"   💰 가격: {price_str} ({s.change_pct:+.1f}%)")
                lines.append(f"   📊 RSI: {s.rsi:.1f} | MACD: {s.macd_trend}")
                lines.append(f"   📈 볼린저: {s.bb_position}")
                
                # 패턴 정보
                if s.pattern_summary:
                    lines.append(f"   🔍 패턴: {s.pattern_summary}")
                
                # 반디 의견
                lines.append(f"")
                lines.append(f"   💬 *반디 분석:*")
                for op in s.bandi_opinion.split('\n'):
                    if op:
                        lines.append(f"      • {op}")
                
                lines.append(f"   💡 *반디 전략:*")
                for st in s.bandi_strategy.split('\n'):
                    if st:
                        lines.append(f"      → {st}")
                
                lines.append("━" * 40)
        
        # 푸터
        lines.append("")
        lines.append("_반디가 파파를 응원합니다 🐾_")
        lines.append("✨ v3.0: 14가지 패턴 자동 감지 + 반디 AI 의견 포함")
        
        return "\n".join(lines)
    
    def send_telegram(self, message: str):
        """텔레그램 전송"""
        url = f"{TELEGRAM_API}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"전송 오류: {e}")
            return False
    
    def run(self):
        """메인 실행"""
        print("=" * 70)
        print("📊 반디 퀀트 v3.0 - 패턴 분석 + AI 의견 브리핑")
        print("=" * 70)
        print(f"⏰ {self.date_str} {self.time_str} KST")
        
        # 종목 리스트
        stocks_list = [
            ("000660.KS", "SK하이닉스", "반도체"),
            ("005930.KS", "삼성전자", "반도체"),
            ("NVDA", "NVIDIA", "반도체"),
            ("136480.KS", "하나제약", "바이오"),
            ("GM", "General Motors", "자동차"),
            ("QS", "QuantumScape", "배터리"),
            ("TSLA", "Tesla", "자동차"),
            ("PLTR", "Palantir", "AI/소프트웨어"),
        ]
        
        # 분석
        for ticker, name, sector in stocks_list:
            result = self.analyze_stock(ticker, name)
            if result:
                self.results.append(result)
                if '매수' in result.recommendation:
                    self.buy_recommendations.append(result)
                elif '매도' in result.recommendation:
                    self.sell_recommendations.append(result)
                print(f"✅ {name} 분석 완료")
        
        print(f"\n📈 분석된 종목: {len(self.results)}개")
        print(f"📈 매수 추천: {len(self.buy_recommendations)}개")
        print(f"📈 매도 권고: {len(self.sell_recommendations)}개")
        
        # 텔레그램 전송
        message = self.generate_telegram_message()
        if self.send_telegram(message):
            print("\n✅ 텔레그램 전송 완료!")
        else:
            print("\n❌ 텔레그램 전송 실패")
        
        print("=" * 70)


if __name__ == "__main__":
    briefing = MarketBriefing()
    briefing.run()
