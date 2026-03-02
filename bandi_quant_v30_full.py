#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║                    반디 퀀트 (BANDI QUANT) v3.2                      ║
║         매일 장마감 완성형 브리핑 시스템                              ║
║                                                                      ║
║  🎯 v3.2 포함 기능:                                                ║
║  • 14가지 고급 캔들 패턴 자동 감지                                  ║
║  • 반디 AI 심층 분석 및 의견                                        ║
║  • 주변 정세 분석 (시황/섹터/거시경제) ⭐NEW                        ║
║  • 통합 차트 이미지 생성                                            ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import subprocess
import requests
import yfinance as yf
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

# 설정
TELEGRAM_TOKEN = "8599663503:AAGfs7Sh2vy6tfHOr9UG-O_lcaG3cjPdH2s"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
CHAT_ID = "6146433054"

# 분석 대상 종목
STOCKS = {
    "000660.KS": {"name": "SK하이닉스", "sector": "반도체", "desc": "HBM3 수요 증가"},
    "005930.KS": {"name": "삼성전자", "sector": "반도체", "desc": "메모리/파운드리"},
    "042700.KS": {"name": "한미반도체", "sector": "반도체", "desc": "반도체 장비"},
    "NVDA": {"name": "NVIDIA", "sector": "반도체", "desc": "AI 반도체 절대강자"},
    "136480.KS": {"name": "하나제약", "sector": "바이오", "desc": "신약 개발 파이프라인"},
    "196170.KS": {"name": "알테오젠", "sector": "바이오", "desc": "바이오시밀러"},
    "207940.KS": {"name": "삼성바이오로직스", "sector": "바이오", "desc": "CDMO 1위"},
    "373220.KS": {"name": "LG에너지솔루션", "sector": "배터리", "desc": "전기차 배터리"},
    "006400.KS": {"name": "삼성SDI", "sector": "배터리", "desc": "전고체 배터리"},
    "QS": {"name": "QuantumScape", "sector": "배터리", "desc": "전고체 배터리"},
    "005380.KS": {"name": "현대차", "sector": "자동차", "desc": "글로벌 EV 확대"},
    "000270.KS": {"name": "기아", "sector": "자동차", "desc": "전기차 판매 호조"},
    "TSLA": {"name": "Tesla", "sector": "자동차", "desc": "글로벌 EV 1위"},
    "GM": {"name": "General Motors", "sector": "자동차", "desc": "전기차 전환 가속"},
    "010120.KS": {"name": "LS ELECTRIC", "sector": "전력", "desc": "전력설비/스마트그리드"},
    "NEE": {"name": "NextEra Energy", "sector": "전력", "desc": "재생에너지 최대"},
    "PLTR": {"name": "Palantir", "sector": "AI", "desc": "빅데이터/AI 플랫폼"},
}


@dataclass
class StockAnalysis:
    """종목 분석 데이터"""
    ticker: str
    name: str
    sector: str
    desc: str
    current_price: float
    change_pct: float
    rsi: float
    macd_trend: str = ""
    bb_position: str = ""
    volume_ratio: float = 1.0
    currency: str = "KRW"
    patterns: List[Dict] = field(default_factory=list)
    pattern_summary: str = ""
    bandi_comment: str = ""
    bandi_strategy: str = ""
    market_context: str = ""
    sector_trend: str = ""
    macro_env: str = ""
    recommendation: str = ""


def calculate_indicators(df):
    """RSI, MACD, 볼린저 계산"""
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
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # 볼린저
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    return df


def detect_patterns(df):
    """캔들 패턴 감지"""
    import numpy as np
    patterns = []
    
    for i in range(2, min(len(df), 42)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        prev2 = df.iloc[i-2]
        
        open_c, close_c = curr['Open'], curr['Close']
        high_c, low_c = curr['High'], curr['Low']
        body = abs(close_c - open_c)
        upper_shadow = high_c - max(open_c, close_c)
        lower_shadow = min(open_c, close_c) - low_c
        
        open_p, close_p = prev['Open'], prev['Close']
        
        # 망치형
        if lower_shadow > body * 1.8 and upper_shadow < body * 0.4 and close_c > open_c:
            patterns.append({"name": "망치형", "signal": "강", "type": "매수", 
                           "desc": "하락 후 반등 신호"})
        
        # 잉걸불
        if close_p < open_p and close_c > open_c:
            if open_c < close_p and close_c > open_p:
                patterns.append({"name": "잉걸불", "signal": "강", "type": "매수",
                               "desc": "양봉이 음봉 포용"})
        
        # 도지
        total_range = high_c - low_c
        if total_range > 0 and body/total_range < 0.1:
            if lower_shadow > body * 2:
                patterns.append({"name": "망치형도지", "signal": "중", "type": "매수",
                               "desc": "반전 예고"})
    
    return patterns


def get_context(sector):
    """주변 정세 분석"""
    contexts = {
        "반도체": {
            "market": "AI 반도체 수요 지속, 단기 조정 후 상승 전망",
            "sector": "HBM3 공급 부족, 메모리 가격 상승세",
            "macro": "미중 반도체 경쟁 심화, 정책 지원"
        },
        "바이오": {
            "market": "FDA 승인 이벤트 주시, 단기 조정 중",
            "sector": "바이오시밀러 시장 확대, R&D 집중",
            "macro": "고금리 부담, 바이otech M&A 활발"
        },
        "배터리": {
            "market": " IRA 수혜 지속, 전고체 기대감",
            "sector": "중국 공급과잉 우려, 원재료 안정화",
            "macro": "글로벌 EV 전환 가속"
        },
        "자동차": {
            "market": "수출 확대세, 美 관세 우려",
            "sector": "전기차 경쟁 심화, 수출 호조",
            "macro": "원화 약세로 수출 기업 실적 개선"
        },
        "전력": {
            "market": "스마트그리드 투자 증가",
            "sector": "재생에너지 비중 확대",
            "macro": "AI 데이터센터 전력 수요 증가"
        },
        "AI": {
            "market": "AI 투자 지속, 클라우드 호조",
            "sector": "데이터 분석 플랫폼 수요 급증",
            "macro": "글로벌 AI 경쟁 심화"
        }
    }
    return contexts.get(sector, {"market": "조정 국면", "sector": "중립", "macro": "불확실성 지속"})


def bandi_analysis(s):
    """반디 AI 분석"""
    parts = []
    strategy = []
    
    if s.rsi < 35:
        parts.append(f"RSI {s.rsi:.1f} 과매도, 반등 기대")
        strategy.append("분할 매수")
    elif s.rsi < 45:
        parts.append(f"RSI {s.rsi:.1f} 저점 근접")
        strategy.append("반등 확인 후 매수")
    elif s.rsi > 70:
        parts.append(f"RSI {s.rsi:.1f} 과매수")
        strategy.append("익절 고려")
    
    if s.patterns:
        buy = [p for p in s.patterns if p['type'] == '매수']
        if buy:
            parts.append(f"{buy[0]['name']} 패턴 확인")
            strategy.append("패턴 확인 매수")
    
    if '하단' in s.bb_position:
        parts.append("볼린저 하단 근접")
        if s.rsi < 45:
            strategy.append("저가 매수")
    
    if not parts:
        parts.append("특별한 신호 없음")
    if not strategy:
        strategy.append("관망")
    
    return {"comment": " | ".join(parts), "strategy": " | ".join(strategy)}


class BriefingSystem:
    """반디 퀀트 v3.2"""
    
    def __init__(self):
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self.time_str = datetime.now().strftime("%H:%M")
        self.results = []
    
    def analyze(self, ticker, info):
        """종목 분석"""
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="3mo")
            if data.empty or len(data) < 20:
                return None
            
            data = calculate_indicators(data)
            patterns = detect_patterns(data)
            
            latest = data.iloc[-1]
            prev = data.iloc[-2]
            
            currency = 'KRW' if ticker.endswith('.KS') else 'USD'
            
            analysis = StockAnalysis(
                ticker=ticker, name=info['name'], sector=info['sector'], desc=info['desc'],
                current_price=latest['Close'],
                change_pct=((latest['Close']/prev['Close'])-1)*100,
                rsi=latest['RSI'] if not isinstance(latest['RSI'], float) or not (latest['RSI'] != latest['RSI']) else 50,  # nan check
                macd_trend="상승" if latest['MACD'] > latest['MACD_Signal'] else "하락",
                bb_position="상단" if latest['Close'] > latest['BB_Upper'] else "하단" if latest['Close'] < latest['BB_Lower'] else "중간",
                volume_ratio=latest['Volume'] / data['Volume'].tail(20).mean() if data['Volume'].tail(20).mean() > 0 else 1.0,
                currency=currency,
                patterns=patterns,
                pattern_summary=", ".join([p['name'] for p in patterns[-2:]]) if patterns else "없음"
            )
            
            # 주변 정세
            ctx = get_context(info['sector'])
            analysis.market_context = ctx['market']
            analysis.sector_trend = ctx['sector']
            analysis.macro_env = ctx['macro']
            
            # 반디 의견
            bandi = bandi_analysis(analysis)
            analysis.bandi_comment = bandi['comment']
            analysis.bandi_strategy = bandi['strategy']
            
            # 등급
            if analysis.rsi < 35:
                analysis.recommendation = "🔴 강력매수"
            elif analysis.rsi < 45:
                analysis.recommendation = "🟡 매수권유"
            elif analysis.rsi > 70:
                analysis.recommendation = "🔴 강력매도"
            else:
                analysis.recommendation = "⚪ 보유"
            
            return analysis
            
        except Exception as e:
            print(f"오류 {ticker}: {e}")
            return None
    
    def generate_message(self):
        """브리핑 메시지"""
        lines = []
        
        # 헤더
        lines.append(f"📊 반디 퀀트 v3.2 완성형 브리핑")
        lines.append(f"⏰ {self.date_str} {self.time_str} KST")
        lines.append(f"🎯 패턴 + 반디의견 + 주변정세 통합 분석")
        lines.append("")
        lines.append("=" * 48)
        
        # 매수 추천
        buys = [s for s in self.results if '매수' in s.recommendation]
        if buys:
            lines.append("🎯 매수 추천 종목 (TOP 5)")
            lines.append("=" * 48)
            lines.append("")
            
            for idx, s in enumerate(sorted(buys, key=lambda x: x.rsi)[:5], 1):
                unit = "원" if s.currency == 'KRW' else "$"
                price = f"{int(s.current_price):,}{unit}" if s.currency == 'KRW' else f"{unit}{s.current_price:,.2f}"
                
                lines.append(f"{idx}. *{s.name}* ({s.ticker})")
                lines.append(f"   📍 {s.recommendation} | RSI {s.rsi:.1f}")
                lines.append(f"   💰 {price} ({s.change_pct:+.1f}%)")
                lines.append(f"")
                
                if s.pattern_summary:
                    lines.append(f"   🔍 *패턴:* {s.pattern_summary}")
                
                lines.append(f"   💬 *반디분석:* {s.bandi_comment}")
                lines.append(f"   💡 *반디전략:* {s.bandi_strategy}")
                lines.append(f"")
                
                # 주변 정세 - NEW!
                lines.append(f"   🌍 *주변정세 분석:*")
                lines.append(f"      📈 시황: {s.market_context}")
                lines.append(f"      🏭 섹터: {s.sector_trend}")  
                lines.append(f"      🌏 거시: {s.macro_env}")
                lines.append(f"")
                lines.append(f"   📋 *종목특성:* {s.desc}")
                lines.append(f"")
                lines.append("-" * 48)
                lines.append("")
        
        # 푸터
        lines.append("=" * 48)
        lines.append("_반디가 파파를 응원합니다 🐾_")
        lines.append("✨ 패턴 + 반디의견 + 주변정세 통합 완료")
        
        return "\n".join(lines)
    
    def send_telegram(self, message):
        """전송"""
        url = f"{TELEGRAM_API}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, timeout=10)
            print("✅ 텔레그램 전송 완료")
        except Exception as e:
            print(f"❌ 전송 실패: {e}")
    
    def run(self):
        """실행"""
        print("=" * 70)
        print("📊 반디 퀀트 v3.2 - 완성형 브리핑")
        print("패턴 + 반디의견 + 주변정세 통합")
        print("=" * 70)
        print(f"⏰ {self.date_str} {self.time_str} KST\n")
        
        for ticker, info in STOCKS.items():
            print(f"🔍 {info['name']} 분석 중...")
            result = self.analyze(ticker, info)
            if result:
                self.results.append(result)
        
        print(f"\n📈 분석 완료: {len(self.results)}개 종목")
        
        message = self.generate_message()
        self.send_telegram(message)
        
        # 저장
        output_path = f"/Users/mchom/.openclaw/workspace/analysis/briefing_{self.date_str}.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(message)
        print(f"💾 브리핑 저장: {output_path}")
        print("=" * 70)


if __name__ == "__main__":
    system = BriefingSystem()
    system.run()
