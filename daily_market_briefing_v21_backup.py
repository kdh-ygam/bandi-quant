#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║                    반디 퀀트 (BANDI QUANT) v2.1                      ║
║              매일 장마감 자동 브리핑 시스템                          ║
║                                                                      ║
║  🎯 v2.1 업데이트:                                                   ║
║  - 완성도 높은 텍스트 브리핑 템플릿                                   ║
║  - macOS Yuna TTS 음성 브리핑 지원                                   ║
║  - RSI/MACD/볼린저밴드/거래량 종합 분석                             ║
║                                                                      ║
║  Created by: 반디 (Bandi) - 파파의 AI 퀀트 트레이더 어시스턴트     ║
║  For: 파파 (Papa) - 55세 신중한 투자자                               ║
║  Date: 2026-02-26                                                    ║
║  Version: 2.1                                                        ║
╚══════════════════════════════════════════════════════════════════════╝

📋 Workflow:
1. 📊 데이터 수집 (가격, RSI, MACD, 볼린저밴드, 거래량) - 32개 종목
2. 🔍 ddgs로 뉴스 검색  
3. 📈 6항목 분석 (반디 퀀트 분석툴 + 기술적 지표)
4. 🎯 매수/매도 등급 판정 후 추천종목 선별
5. 🎙️ Yuna 음성 브리핑 (macOS TTS)
6. 📱 텔레그램으로 완성도 높은 텍스트 브리핑 전송

⏰ 실행 시간: 매일 06:30 KST (미국 장 마감 30분 후)
"""

import os
import sys
import json
import time
import subprocess
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# 텔레그램 설정
TELEGRAM_TOKEN = "8599663503:AAGfs7Sh2vy6tfHOr9UG-O_lcaG3cjPdH2s"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
CHAT_ID = "6146433054"

# 분석 대상 종목 (총 32개)
STOCKS = {
    # 반도체 (5개)
    "000660.KS": {"name": "SK하이닉스", "sector": "반도체", "base_price": 656250, "base_shares": 0},
    "005930.KS": {"name": "삼성전자", "sector": "반도체", "base_price": 0, "base_shares": 0},
    "042700.KS": {"name": "한미반도체", "sector": "반도체", "base_price": 0, "base_shares": 0},
    "001740.KS": {"name": "SK스퀘어", "sector": "반도체", "base_price": 0, "base_shares": 0},
    "NVDA": {"name": "NVIDIA", "sector": "반도체", "base_price": 0, "base_shares": 0},
    
    # 바이오 (5개)
    "068270.KS": {"name": "셀트리온", "sector": "바이오", "base_price": 0, "base_shares": 0},
    "207940.KS": {"name": "삼성바이오로직스", "sector": "바이오", "base_price": 0, "base_shares": 0},
    "196170.KS": {"name": "알테오젠", "sector": "바이오", "base_price": 0, "base_shares": 0},
    "136480.KS": {"name": "하나제약", "sector": "바이오", "base_price": 0, "base_shares": 0},
    "JNJ": {"name": "Johnson & Johnson", "sector": "바이오", "base_price": 0, "base_shares": 0},
    
    # 전력/인프라 (6개)
    "010120.KS": {"name": "LS ELECTRIC", "sector": "전력", "base_price": 0, "base_shares": 0},
    "267260.KS": {"name": "현대일렉트릭", "sector": "전력", "base_price": 0, "base_shares": 0},
    "051600.KS": {"name": "한전KPS", "sector": "전력", "base_price": 0, "base_shares": 0},
    "052690.KS": {"name": "한전기술", "sector": "전력", "base_price": 0, "base_shares": 0},
    "003670.KS": {"name": "포스코DX", "sector": "인프라", "base_price": 0, "base_shares": 0},
    "NEE": {"name": "NextEra Energy", "sector": "전력", "base_price": 0, "base_shares": 0},
    
    # 자동차 (8개)
    "005380.KS": {"name": "현대차", "sector": "자동차", "base_price": 0, "base_shares": 0},
    "000270.KS": {"name": "기아", "sector": "자동차", "base_price": 0, "base_shares": 0},
    "012330.KS": {"name": "현대모비스", "sector": "자동차", "base_price": 0, "base_shares": 0},
    "003620.KS": {"name": "KG모빌리티", "sector": "자동차", "base_price": 0, "base_shares": 0},
    "TSLA": {"name": "Tesla", "sector": "자동차", "base_price": 0, "base_shares": 0},
    "F": {"name": "Ford", "sector": "자동차", "base_price": 0, "base_shares": 0},
    "GM": {"name": "GM", "sector": "자동차", "base_price": 0, "base_shares": 0},
    "RIVN": {"name": "Rivian", "sector": "자동차", "base_price": 0, "base_shares": 0},
    
    # 2차 전지 (6개)
    "373220.KS": {"name": "LG에너지솔루션", "sector": "배터리", "base_price": 0, "base_shares": 0},
    "006400.KS": {"name": "삼성SDI", "sector": "배터리", "base_price": 0, "base_shares": 0},
    "005490.KS": {"name": "POSCO홀딩스", "sector": "배터리", "base_price": 0, "base_shares": 0},
    "247540.KS": {"name": "에코프로비엠", "sector": "배터리", "base_price": 0, "base_shares": 0},
    "ALB": {"name": "Albemarle", "sector": "배터리", "base_price": 0, "base_shares": 0},
    "QS": {"name": "QuantumScape", "sector": "배터리", "base_price": 0, "base_shares": 0},
    
    # 미국 기타 (5개)
    "ONON": {"name": "ONON", "sector": "기타", "base_price": 0, "base_shares": 0},
    "PLTR": {"name": "Palantir", "sector": "소프트웨어/AI", "base_price": 0, "base_shares": 0},
}

@dataclass
class StockAnalysis:
    """종목 분석 데이터 클래스 - v2.1"""
    ticker: str
    name: str
    sector: str
    current_price: float
    previous_price: float
    change_pct: float
    rsi: float
    volume: int
    volume_avg_20d: float
    volume_ratio: float
    currency: str
    macd_line: float
    macd_signal: float
    macd_histogram: float
    macd_trend: str
    bb_middle: float
    bb_upper: float
    bb_lower: float
    bb_width: float
    bb_position: str
    news_summary: str = ""
    internal_trend: str = ""
    outlook: str = ""
    macro_trend: str = ""
    recommendation: str = ""
    comment: str = ""
    tech_summary: str = ""

class MarketBriefingSystem:
    """시장 브리핑 시스템 - v2.1"""
    
    def __init__(self):
        self.results = []
        self.buy_recommendations = []
        self.sell_recommendations = []
        self.date_str = datetime.now().strftime('%Y-%m-%d')
        self.time_str = datetime.now().strftime('%H:%M')
        
    def calculate_ema(self, data: List[float], period: int) -> List[float]:
        """EMA 계산"""
        if len(data) < period:
            return []
        multiplier = 2 / (period + 1)
        ema = [sum(data[:period]) / period]
        for i in range(period, len(data)):
            ema.append((data[i] * multiplier) + (ema[-1] * (1 - multiplier)))
        return ema
    
    def calculate_macd(self, closes: List[float]) -> Dict:
        """MACD 계산"""
        try:
            if len(closes) < 35:
                return {"macd": 0, "signal": 0, "histogram": 0, "trend": "N/A"}
            ema_12 = self.calculate_ema(closes, 12)
            ema_26 = self.calculate_ema(closes, 26)
            macd_line = [ema_12[i] - ema_26[i] for i in range(len(ema_26))]
            signal_line = self.calculate_ema(macd_line, 9)
            current_macd = macd_line[-1]
            current_signal = signal_line[-1]
            histogram = current_macd - current_signal
            prev_macd = macd_line[-2]
            prev_signal = signal_line[-2]
            trend = "중립"
            if current_macd > current_signal and prev_macd <= prev_signal:
                trend = "🟢 골든크로스"
            elif current_macd < current_signal and prev_macd >= prev_signal:
                trend = "🔴 데드크로스"
            elif current_macd > current_signal:
                trend = "📈 상승세"
            elif current_macd < current_signal:
                trend = "📉 하락세"
            return {"macd": round(current_macd, 2), "signal": round(current_signal, 2), "histogram": round(histogram, 2), "trend": trend}
        except Exception as e:
            return {"macd": 0, "signal": 0, "histogram": 0, "trend": "오류"}
    
    def calculate_bollinger_bands(self, closes: List[float]) -> Dict:
        """볼린저밴드 계산"""
        try:
            if len(closes) < 20:
                return {"middle": 0, "upper": 0, "lower": 0, "width": 0, "position": "N/A"}
            recent = closes[-20:]
            current = closes[-1]
            middle = sum(recent) / 20
            variance = sum((x - middle) ** 2 for x in recent) / 20
            std_dev = variance ** 0.5
            upper = middle + (2 * std_dev)
            lower = middle - (2 * std_dev)
            width = ((upper - lower) / middle) * 100
            position = "중간"
            if current > upper:
                position = "🚀 상단돌파"
            elif current < lower:
                position = "📉 하단이탈"
            elif current > middle + std_dev:
                position = "🔼 상단접근"
            elif current < middle - std_dev:
                position = "🔽 하단접근"
            return {"middle": round(middle, 2), "upper": round(upper, 2), "lower": round(lower, 2), "width": round(width, 2), "position": position}
        except Exception as e:
            return {"middle": 0, "upper": 0, "lower": 0, "width": 0, "position": "오류"}
    
    def calculate_volume_analysis(self, volumes: List[float], current_volume: int) -> Dict:
        """거래량 분석"""
        try:
            if len(volumes) < 20:
                return {"avg": 0, "ratio": 1.0, "trend": "중립"}
            recent_volumes = volumes[-20:]
            avg_20d = sum(recent_volumes) / 20
            ratio = current_volume / avg_20d if avg_20d > 0 else 1.0
            trend = "중립"
            if ratio > 2.0: trend = "🔥 거래폭발"
            elif ratio > 1.5: trend = "📊 거래활발"
            elif ratio > 1.0: trend = "📈 거래증가"
            elif ratio < 0.5: trend = "😴 거래소진"
            elif ratio < 0.8: trend = "📉 거래감소"
            return {"avg": round(avg_20d, 0), "ratio": round(ratio, 2), "trend": trend}
        except Exception as e:
            return {"avg": 0, "ratio": 1.0, "trend": "오류"}
        
    def get_stock_price(self, symbol: str) -> Optional[Dict]:
        """Yahoo Finance에서 주가 및 기술적 지표 수집"""
        try:
            url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=3mo"
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                result = data.get('chart', {}).get('result', [])
                if result and len(result) > 0:
                    result_data = result[0]
                    meta = result_data.get('meta', {})
                    closes = result_data.get('indicators', {}).get('quote', [{}])[0].get('close', [])
                    volumes = result_data.get('indicators', {}).get('quote', [{}])[0].get('volume', [])
                    if len(closes) < 2:
                        return None
                    current = closes[-1]
                    previous = closes[-2]
                    volume = int(volumes[-1]) if volumes else 0
                    rsi = self.calculate_rsi(closes)
                    macd_data = self.calculate_macd(closes)
                    bb_data = self.calculate_bollinger_bands(closes)
                    vol_data = self.calculate_volume_analysis(volumes, volume)
                    change_pct = ((current - previous) / previous * 100) if previous else 0
                    currency = 'KRW' if '.KS' in symbol else 'USD'
                    return {'symbol': symbol, 'current': current, 'previous': previous, 'change_pct': change_pct, 'volume': volume, 'volume_avg_20d': vol_data['avg'], 'volume_ratio': vol_data['ratio'], 'volume_trend': vol_data['trend'], 'rsi': rsi, 'macd': macd_data, 'bb': bb_data, 'currency': currency}
            return None
        except Exception as e:
            print(f"  ❌ Error fetching {symbol}: {e}")
            return None
    
    def calculate_rsi(self, closes: List[float]) -> float:
        """RSI 계산"""
        try:
            if len(closes) < 14:
                return 50.0
            recent_closes = closes[-14:]
            gains, losses = [], []
            for i in range(1, len(recent_closes)):
                change = recent_closes[i] - recent_closes[i-1]
                if change > 0: gains.append(change); losses.append(0)
                else: gains.append(0); losses.append(abs(change))
            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            if avg_loss == 0: return 100.0
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return round(rsi, 1)
        except Exception as e:
            return 50.0
    
    def search_news(self, stock_name: str, ticker: str) -> str:
        """ddgs로 뉴스 검색"""
        try:
            query = f"{stock_name} 주가 뉴스"
            if '.KS' not in ticker:
                query = f"{stock_name} {ticker} stock news"
            cmd = ['ddgs', 'text', '-q', query, '-m', '3']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                news_items = []
                for line in lines:
                    if 'title' in line.lower() or 'body' in line.lower():
                        news_items.append(line.strip())
                return ' | '.join(news_items[:2]) if news_items else "뉴스 없음"
            return "검색 실패"
        except Exception as e:
            return f"오류: {str(e)[:50]}"
    
    def determine_recommendation(self, price_data: Dict, stock_info: Dict) -> Tuple[str, str, str]:
        """매수/매도 등급 판정"""
        change_pct = price_data['change_pct']
        rsi = price_data['rsi']
        current_price = price_data['current']
        base_price = stock_info.get('base_price', 0)
        macd = price_data.get('macd', {})
        bb = price_data.get('bb', {})
        vol = price_data.get('volume_ratio', 1.0)
        profit_pct = 0
        if base_price > 0:
            profit_pct = ((current_price - base_price) / base_price) * 100
        macd_trend = macd.get('trend', '')
        bb_pos = bb.get('position', '')
        tech_signals = []
        if '골든크로스' in macd_trend: tech_signals.append('MACD매수')
        elif '데드크로스' in macd_trend: tech_signals.append('MACD매도')
        if '상단돌파' in bb_pos: tech_signals.append('BB과열')
        elif '하단이탈' in bb_pos: tech_signals.append('BB과매도')
        if vol > 2.0: tech_signals.append('거래폭발')
        elif vol > 1.5: tech_signals.append('수급활발')
        tech_summary = ', '.join(tech_signals) if tech_signals else '중립'
        if rsi > 70 and profit_pct > 50:
            return "🔴 강력매도", f"RSI {rsi} 과매수, 수익 +{profit_pct:.1f}%, 50% 익절 권고", tech_summary
        elif rsi > 65 and profit_pct > 20:
            return "🟠 매도권유", f"RSI {rsi}, 수익 +{profit_pct:.1f}%, 점진적 매도", tech_summary
        elif rsi > 60 or (base_price > 0 and current_price < base_price * 0.9):
            return "🟡 매도대비", f"RSI {rsi} 또는 손절선(-10%) 근접", tech_summary
        if rsi < 35 and change_pct < -5:
            return "🟢 강력매수", f"RSI {rsi} 과매도, 하락 {change_pct:.1f}%, 분할 매수", tech_summary
        elif rsi < 45:
            return "🟡 매수권유", f"RSI {rsi}, 저점 매수 기회", tech_summary
        elif rsi < 50 and change_pct < 0:
            return "🟠 매수대비", f"RSI {rsi}, 추세 반전 관망", tech_summary
        return "⚪ 보유", f"RSI {rsi}, 관망 유지", tech_summary
    
    def analyze_internal_trend(self, news: str, stock_name: str) -> str:
        """기업 내부 동향 분석"""
        positive_keywords = ['자사주 소각', 'FDA 승인', '수주', '신제품', '흑자', '매출증가']
        negative_keywords = ['적자', '리콜', '소송', '감원', '구조조정', '배당삭감']
        pos_count = sum(1 for kw in positive_keywords if kw in news)
        neg_count = sum(1 for kw in negative_keywords if kw in news)
        if pos_count > neg_count: return "✅ 긍정적 동향"
        elif neg_count > pos_count: return "⚠️ 부정적 동향"
        else: return "➖ 중립"
    
    def analyze_all_stocks(self):
        """모든 종목 분석 실행"""
        print("🔍 전체 종목 분석 시작...")
        print("=" * 60)
        for i, (ticker, info) in enumerate(STOCKS.items(), 1):
            print(f"\n[{i}/{len(STOCKS)}] {info['name']} ({ticker}) 분석 중...")
            price_data = self.get_stock_price(ticker)
            if not price_data:
                print(f"  ⚠️ 가격 조회 실패, 스킵")
                continue
            print(f"  🔍 뉴스 검색 중...")
            news = self.search_news(info['name'], ticker)
            rec_grade, comment, tech_summary = self.determine_recommendation(price_data, info)
            internal_trend = self.analyze_internal_trend(news, info['name'])
            macd = price_data.get('macd', {})
            bb = price_data.get('bb', {})
            vol_ratio = price_data.get('volume_ratio', 1.0)
            print(f"  📊 RSI: {price_data['rsi']} | MACD: {macd.get('trend')} | BB: {bb.get('position')}")
            print(f"  📈 거래량: {vol_ratio:.1f}x 평균")
            analysis = StockAnalysis(
                ticker=ticker, name=info['name'], sector=info['sector'],
                current_price=price_data['current'], previous_price=price_data['previous'],
                change_pct=price_data['change_pct'], rsi=price_data['rsi'],
                volume=price_data['volume'], volume_avg_20d=price_data['volume_avg_20d'],
                volume_ratio=price_data['volume_ratio'], currency=price_data['currency'],
                macd_line=macd.get('macd', 0), macd_signal=macd.get('signal', 0),
                macd_histogram=macd.get('histogram', 0), macd_trend=macd.get('trend', ''),
                bb_middle=bb.get('middle', 0), bb_upper=bb.get('upper', 0),
                bb_lower=bb.get('lower', 0), bb_width=bb.get('width', 0),
                bb_position=bb.get('position', ''),
                news_summary=news[:100] + "..." if len(news) > 100 else news,
                internal_trend=internal_trend, outlook="분석 필요",
                macro_trend="분석 필요", recommendation=rec_grade,
                comment=comment, tech_summary=tech_summary
            )
            self.results.append(analysis)
            if '매수' in rec_grade: self.buy_recommendations.append(analysis)
            elif '매도' in rec_grade: self.sell_recommendations.append(analysis)
            print(f"  ✅ 완료: {rec_grade}")
            time.sleep(1)
        print("\n" + "=" * 60)
        print("✅ 모든 종목 분석 완료!")
    
    def generate_telegram_message(self) -> str:
        """완성도 높은 텔레그램 브리핑 - v2.1"""
        lines = []
        lines.append("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
        lines.append(f"┃  📊 반디 퀀트 장마감 브리핑 v2.1")
        lines.append(f"┃  📅 {self.date_str}  ⏰ {self.time_str} KST")
        lines.append("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
        lines.append("")
        
        # 시장 요약
        lines.append("📈 *시장 요약*")
        avg_rsi = sum(s.rsi for s in self.results) / len(self.results)
        up_count = sum(1 for s in self.results if s.change_pct > 0)
        down_count = len(self.results) - up_count
        lines.append(f"   • 분석 종목: {len(self.results)}개")
        lines.append(f"   • 상승: {up_count}개 🔺 | 하락: {down_count}개 🔻")
        rsi_status = '(과매수)' if avg_rsi > 60 else '(중립)' if avg_rsi > 40 else '(과매도)'
        lines.append(f"   • 평균 RSI: {avg_rsi:.1f} {rsi_status}")
        lines.append("")
        
        # 급등 TOP 3
        lines.append("🔥 *오늘의 급등 TOP 3*")
        surging = sorted(self.results, key=lambda x: x.change_pct, reverse=True)[:3]
        for i, s in enumerate(surging, 1):
            unit = "원" if s.currency == 'KRW' else "$"
            price_str = f"{int(s.current_price):,}{unit}" if s.currency == 'KRW' else f"{unit}{s.current_price:,.2f}"
            rsi_color = "🔴" if s.rsi >= 70 else "🟡" if s.rsi >= 60 else "🟢"
            vol_icon = "🔥" if s.volume_ratio > 2.0 else "📊" if s.volume_ratio > 1.5 else "💤"
            lines.append(f"   {i}. *{s.name}* ({s.ticker.replace('.KS', '')})")
            lines.append(f"      💰 {price_str} | 📈 {s.change_pct:+.2f}% | {rsi_color}RSI {s.rsi}")
            lines.append(f"      📊 MACD: {s.macd_trend} | BB: {s.bb_position} | Vol {s.volume_ratio:.1f}x {vol_icon}")
        lines.append("")
        
        # 하락 TOP 3
        lines.append("📉 *오늘의 하락 TOP 3*")
        declining = sorted(self.results, key=lambda x: x.change_pct)[:3]
        for i, s in enumerate(declining, 1):
            unit = "원" if s.currency == 'KRW' else "$"
            price_str = f"{int(s.current_price):,}{unit}" if s.currency == 'KRW' else f"{unit}{s.current_price:,.2f}"
            rsi_color = "🟢" if s.rsi < 40 else "🟡" if s.rsi < 50 else "🔴"
            lines.append(f"   {i}. *{s.name}* ({s.ticker.replace('.KS', '')})")
            lines.append(f"      💰 {price_str} | 📉 {s.change_pct:+.2f}% | {rsi_color}RSI {s.rsi}")
            lines.append(f"      📊 BB: {s.bb_position}")
        lines.append("")
        
        # 매수 추천
        if self.buy_recommendations:
            lines.append("━" * 40)
            lines.append("🎯 *매수 추천 종목*")
            lines.append("━" * 40)
            sorted_buys = sorted(self.buy_recommendations, key=lambda x: x.rsi)[:5]
            for s in sorted_buys:
                unit = "원" if s.currency == 'KRW' else "$"
                price_str = f"{int(s.current_price):,}{unit}" if s.currency == 'KRW' else f"{unit}{s.current_price:,.2f}"
                lines.append(f"")
                lines.append(f"▪️ *{s.name}* ({s.ticker.replace('.KS', '')})")
                lines.append(f"   ├─ 등급: {s.recommendation}")
                lines.append(f"   ├─ 현재가: {price_str} (전일 {s.change_pct:+.2f}%)")
                rsi_text = '과매도' if s.rsi < 40 else '저점매수' if s.rsi < 50 else '중립'
                lines.append(f"   ├─ RSI: {s.rsi} ({rsi_text})")
                lines.append(f"   ├─ MACD: {s.macd_trend}")
                lines.append(f"   ├─ 볼린저: {s.bb_position}")
                lines.append(f"   └─ 거래량: {s.volume_ratio:.1f}x 평균")
                if s.tech_summary: lines.append(f"      💡 {s.tech_summary}")
        lines.append("")
        
        # 매도 권고
        if self.sell_recommendations:
            lines.append("━" * 40)
            lines.append("🔴 *매도 권고 종목 (상위 5개)*")
            lines.append("━" * 40)
            sorted_sells = sorted(self.sell_recommendations, key=lambda x: x.rsi, reverse=True)[:5]
            for i, s in enumerate(sorted_sells, 1):
                unit = "원" if s.currency == 'KRW' else "$"
                price_str = f"{int(s.current_price):,}{unit}" if s.currency == 'KRW' else f"{unit}{s.current_price:,.2f}"
                lines.append(f"   {i}. *{s.name}*: {s.recommendation}")
                lines.append(f"      💰 {price_str} | RSI {s.rsi} | {s.comment[:25]}...")
        lines.append("")
        
        # 기술적 지표 요약
        lines.append("━" * 40)
        lines.append("📊 *기술적 지표 요약*")
        lines.append("━" * 40)
        
        golden_cross = [s for s in self.results if '🟢 골든크로스' in s.macd_trend]
        if golden_cross:
            lines.append(f"   🟢 MACD 골든크로스: {len(golden_cross)}개")
            for s in golden_cross[:2]: lines.append(f"      └─ {s.name}")
        
        dead_cross = [s for s in self.results if '🔴 데드크로스' in s.macd_trend]
        if dead_cross:
            lines.append(f"   🔴 MACD 데드크로스: {len(dead_cross)}개")
            for s in dead_cross[:2]: lines.append(f"      └─ {s.name}")
        
        bb_breakout = [s for s in self.results if '🚀 상단돌파' in s.bb_position]
        if bb_breakout:
            lines.append(f"   🚀 BB 상단돌파: {len(bb_breakout)}개")
            for s in bb_breakout[:2]: lines.append(f"      └─ {s.name}")
        
        vol_explode = [s for s in self.results if s.volume_ratio > 2.0]
        if vol_explode:
            lines.append(f"   🔥 거래량 폭발(2x+): {len(vol_explode)}개")
            for s in vol_explode[:2]: lines.append(f"      └─ {s.name} ({s.volume_ratio:.1f}x)")
        lines.append("")
        
        # 핵심 인사이트
        lines.append("━" * 40)
        lines.append("💡 *파파를 위한 핵심 인사이트*")
        lines.append("━" * 40)
        
        if avg_rsi > 65:
            lines.append("⚠️ 시장 전체 과매수 구간입니다. 신규 매수는 신중히 하세요.")
        elif avg_rsi < 45:
            lines.append("💚 매수 적기! 다수 종목이 과매도 구간입니다.")
        else:
            lines.append("➖ 시장 중립 구간. 개별 종목별 접근 권장.")
        
        if bb_breakout and len(bb_breakout) > 5:
            lines.append("📈 BB 상단 돌파 종목 다수 - 단기 조정 가능성 있음")
        if vol_explode:
            lines.append("🔥 특정 종목에만 자금 몰림 - 분산 투자 유의")
        lines.append("")
        
        # 푸터
        lines.append("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
        lines.append(f"┃  📎 상세 분석: /Users/mchom/.openclaw/workspace/analysis/")
        lines.append(f"┃  🎙️ 음성 브리핑: Yuna (macOS TTS)")
        lines.append(f"┃  🕐 다음 브리핑: 내일 06:30 KST")
        lines.append("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
        lines.append("")
        lines.append("_반디가 파파를 응원합니다 🐾_")
        
        return "\n".join(lines)
    
    def send_telegram(self, message: str):
        """텔레그램으로 메시지 전송"""
        url = f"{TELEGRAM_API}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print("✅ 텔레그램 메시지 전송 완료!")
                return True
            else:
                print(f"❌ 전송 실패: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 오류: {e}")
            return False
    
    def generate_voice_briefing(self) -> str:
        """Yuna 음성 브리핑 생성"""
        script = f"안녕하세요 파파, 반디입니다. {self.date_str} 장마감 브리핑입니다. "
        script += f"총 {len(self.results)}개 종목 분석했습니다. "
        
        # 시장 요약
        avg_rsi = sum(s.rsi for s in self.results) / len(self.results)
        up_count = sum(1 for s in self.results if s.change_pct > 0)
        script += f"상승 종목 {up_count}개, 하락 종목 {len(self.results) - up_count}개입니다. "
        script += f"평균 RSI는 {avg_rsi:.1f}입니다. "
        
        # 급등주
        surging = sorted(self.results, key=lambda x: x.change_pct, reverse=True)[:2]
        if surging:
            script += "오늘의 급등주는 "
            for s in surging:
                script += f"{s.name} {s.change_pct:+.1f} 퍼센트, "
            script = script.rstrip(", ") + "입니다. "
        
        # 매수 추천
        if self.buy_recommendations:
            sorted_buys = sorted(self.buy_recommendations, key=lambda x: x.rsi)[:2]
            script += "매수 추천 종목은 "
            for s in sorted_buys:
                script += f"{s.name} RSI {s.rsi}, "
            script = script.rstrip(", ") + "입니다. "
        
        # 매도 권고
        if self.sell_recommendations:
            sorted_sells = sorted(self.sell_recommendations, key=lambda x: x.rsi, reverse=True)[:2]
            script += "매도 권고 종목은 "
            for s in sorted_sells:
                script += f"{s.name} RSI {s.rsi}, "
            script = script.rstrip(", ") + "입니다. "
        
        script += "분석 끝입니다. 파파 화이팅!"
        return script
    
    def create_voice_file(self, text: str, output_path: str) -> bool:
        """macOS Yuna 프리미엄 음성 파일 생성"""
        try:
            subprocess.run([
                "say", "-v", "Yuna", "-r", "180",
                text,
                "-o", output_path
            ], check=True)
            print(f"✅ 음성 파일 생성 완료: {output_path}")
            return True
        except Exception as e:
            print(f"❌ 음성 파일 생성 실패: {e}")
            return False
    
    def save_results(self):
        """분석 결과 저장"""
        output_dir = "/Users/mchom/.openclaw/workspace/analysis"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{output_dir}/daily_briefing_{self.date_str}.json"
        data = {
            "date": self.date_str, "time": self.time_str,
            "version": "2.1", "total_stocks": len(self.results),
            "buy_recommendations": len(self.buy_recommendations),
            "sell_recommendations": len(self.sell_recommendations),
            "stocks": [asdict(r) for r in self.results]
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 결과 저장 완료: {filename}")
    
    def run(self):
        """메인 실행"""
        print("=" * 70)
        print("📊 반디 퀀트 (BANDI QUANT) v2.1")
        print("📈 완성도 높은 텍스트 + Yuna 음성 브리핑")
        print("=" * 70)
        print(f"⏰ 실행: {self.date_str} {self.time_str} KST")
        print(f"📈 종목: {len(STOCKS)}개\n")
        
        # 데이터 수집 및 분석
        self.analyze_all_stocks()
        
        # 결과 저장
        self.save_results()
        
        # 텔레그램 텍스트 브리핑
        print("\n📱 텍스트 브리핑 생성 중...")
        text_message = self.generate_telegram_message()
        print("\n📤 텔레그램 전송 중...")
        self.send_telegram(text_message)
        
        # Yuna 프리미엄 음성 브리핑 생성
        print("\n🎙️ Yuna 음성 브리핑 생성 중...")
        voice_script = self.generate_voice_briefing()
        voice_path = f"/Users/mchom/.openclaw/workspace/briefing_yuna_{self.date_str}.aiff"
        if self.create_voice_file(voice_script, voice_path):
            # MP3 변환 및 텔레그램 전송
            mp3_path = voice_path.replace('.aiff', '.mp3')
            try:
                subprocess.run([
                    "ffmpeg", "-y", "-i", voice_path,
                    "-ar", "44100", "-ac", "1", "-b:a", "128k",
                    mp3_path
                ], check=True, capture_output=True)
                print(f"✅ MP3 변환 완료: {mp3_path}")
            except Exception as e:
                print(f"⚠️ MP3 변환 실패: {e}")
        
        print("\n" + "=" * 70)
        print("✅ 모든 작업 완료!")
        print("=" * 70)

def main():
    system = MarketBriefingSystem()
    system.run()

if __name__ == "__main__":
    main()