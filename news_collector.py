#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║                    📰 반디 뉴스 수집 모듈 v1.0                        ║
║         🗞️ 시장 영향 뉴스 자동 수집 및 분석 시스템                     ║
║                                                                      ║
║  🎯 기능:                                                            ║
║  • ✅ Alpha Vantage News API 연동                                    ║
║  • ✅ Yahoo Finance 뉴스 수집                                      ║
║  • ✅ 뉴스 감성 분석 (긍정/부정/중립)                                 ║
║  • ✅ 지정학적/경제/기업 뉴스 분류                                    ║
║  • ✅ 시장 영향도 평가                                               ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# yfinance import
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️ yfinance 미설치 - Yahoo Finance 뉴스 생략")


@dataclass
class NewsItem:
    """개별 뉴스 아이템"""
    title: str
    summary: str
    source: str
    published_at: str
    url: str = ""
    sentiment_score: float = 0.0  # -1.0 ~ 1.0
    sentiment_label: str = "중립"  # "긍정", "부정", "중립"
    relevance_score: float = 0.0  # 0.0 ~ 1.0
    tickers: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)


@dataclass 
class MarketNewsSummary:
    """시장 뉴스 요약"""
    collection_time: str
    total_news_count: int = 0
    
    # 감성 분포
    bullish_count: int = 0
    bearish_count: int = 0
    neutral_count: int = 0
    
    # 평균 감성 점수
    avg_sentiment: float = 0.0
    
    # 영향도 판정
    market_impact: str = "중립"  # "강세", "약세", "중립", "위험"
    impact_score: float = 0.0  # -10 ~ 10
    
    # 주요 뉴스 (상위 5개)
    top_news: List[NewsItem] = field(default_factory=list)
    
    # 지정학적 리스크
    geopolitical_risk: str = "정상"  # "정상", "주의", "위험", "심각"
    risk_factors: List[str] = field(default_factory=list)


class AlphaVantageNewsCollector:
    """Alpha Vantage News API 뉴스 수집기"""
    
    def __init__(self, api_key: Optional[str] = None):
        if api_key is None:
            # 파일에서 로드
            key_path = '/Users/mchom/.openclaw/workspace/alpha_vantage_api_key.txt'
            if os.path.exists(key_path):
                with open(key_path, 'r') as f:
                    api_key = f.read().strip()
        
        self.api_key = api_key
        self.base_url = 'https://www.alphavantage.co/query'
        self.call_count = 0
        self.max_calls_per_day = 25
    
    def get_news_sentiment(
        self, 
        tickers: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[NewsItem]:
        """
        뉴스 및 감성분석 데이터 수집
        
        Args:
            tickers: 종목 티커 리스트 (예: ["AAPL", "NVDA"])
            topics: 주제 리스트 (예: ["energy", "technology"])
            limit: 수집할 뉴스 수
        """
        if not self.api_key:
            print("  ⚠️ Alpha Vantage API 키 없음")
            return []
        
        if self.call_count >= self.max_calls_per_day:
            print(f"  ⚠️ API 호출 한도 도달")
            return []
        
        params = {
            'function': 'NEWS_SENTIMENT',
            'apikey': self.api_key,
            'limit': min(limit, 1000)  # 최대 1000개
        }
        
        if tickers:
            params['tickers'] = ','.join(tickers)
        if topics:
            params['topics'] = ','.join(topics)
        
        try:
            time.sleep(1.2)  # Rate limit 준수
            
            response = requests.get(self.base_url, params=params, timeout=30)
            data = response.json()
            
            if 'feed' not in data:
                error_msg = data.get('Note', data.get('Information', 'Unknown error'))
                print(f"  ⚠️ API 응답 오류: {error_msg}")
                return []
            
            self.call_count += 1
            
            news_items = []
            for item in data.get('feed', []):
                # 감성 점수 파싱
                sentiment_score = float(item.get('overall_sentiment_score', 0))
                sentiment_label = item.get('overall_sentiment_label', 'Neutral')
                
                # 감성 라벨 한글화
                sentiment_kr = self._translate_sentiment(sentiment_label)
                
                # 티커 추출
                tickers_list = []
                for ts in item.get('ticker_sentiment', []):
                    if 'ticker' in ts:
                        tickers_list.append(ts['ticker'])
                
                # 토픽 추출
                topics_list = []
                for topic in item.get('topics', []):
                    if 'topic' in topic:
                        topics_list.append(topic['topic'])
                
                news = NewsItem(
                    title=item.get('title', ''),
                    summary=item.get('summary', '')[:200] + '...' if len(item.get('summary', '')) > 200 else item.get('summary', ''),
                    source=item.get('source', 'Unknown'),
                    published_at=item.get('time_published', ''),
                    url=item.get('url', ''),
                    sentiment_score=sentiment_score,
                    sentiment_label=sentiment_kr,
                    relevance_score=float(item.get('overall_sentiment_score', 0)),
                    tickers=tickers_list,
                    topics=topics_list
                )
                news_items.append(news)
            
            return news_items
            
        except Exception as e:
            print(f"  ❌ 뉴스 수집 오류: {e}")
            return []
    
    def _translate_sentiment(self, label: str) -> str:
        """감성 라벨 한글화"""
        translations = {
            'Bullish': '강한긍정',
            'Somewhat-Bullish': '긍정',
            'Neutral': '중립',
            'Somewhat-Bearish': '부정',
            'Bearish': '강한부정'
        }
        return translations.get(label, '중립')
    
    def get_market_impact_news(self) -> MarketNewsSummary:
        """시장 영향 주요 뉴스 종합 수집"""
        print("\n" + "="*60)
        print("📰 Alpha Vantage 시장 뉴스 수집")
        print("="*60)
        
        all_news = []
        
        # 1. 주요 기술주 뉴스
        tech_tickers = ["NVDA", "TSLA", "AAPL", "MSFT", "GOOGL"]
        print(f"\n🔍 기술주 뉴스 수집 중... ({', '.join(tech_tickers)})")
        tech_news = self.get_news_sentiment(tickers=tech_tickers, limit=20)
        all_news.extend(tech_news)
        print(f"   ✅ {len(tech_news)}개 수집")
        
        # 2. 에너지/지정학 뉴스
        if self.call_count < self.max_calls_per_day:
            print(f"\n🌍 에너지/지정학 뉴스 수집 중...")
            energy_news = self.get_news_sentiment(
                topics=["energy_transportation","economy_macro"], 
                limit=15
            )
            all_news.extend(energy_news)
            print(f"   ✅ {len(energy_news)}개 수집")
        
        # 3. 금융/경제 뉴스
        if self.call_count < self.max_calls_per_day:
            print(f"\n💰 금융/경제 뉴스 수집 중...")
            finance_news = self.get_news_sentiment(
                topics=["financial_markets", "finance"], 
                limit=15
            )
            all_news.extend(finance_news)
            print(f"   ✅ {len(finance_news)}개 수집")
        
        return self._analyze_market_impact(all_news)
    
    def _analyze_market_impact(self, news_list: List[NewsItem]) -> MarketNewsSummary:
        """뉴스 종합 분석 및 시장 영향 평가"""
        if not news_list:
            return MarketNewsSummary(
                collection_time=datetime.now().isoformat(),
                market_impact="정보없음"
            )
        
        # 감성 분포 집계
        bullish = sum(1 for n in news_list if n.sentiment_score > 0.15)
        bearish = sum(1 for n in news_list if n.sentiment_score < -0.15)
        neutral = len(news_list) - bullish - bearish
        
        # 평균 감성 점수
        avg_sentiment = sum(n.sentiment_score for n in news_list) / len(news_list)
        
        # 영향도 점수 (-10 ~ 10)
        impact_score = avg_sentiment * 10
        
        # 영향도 판정
        if impact_score > 3:
            market_impact = "강세"
        elif impact_score > 1:
            market_impact = "약강세"
        elif impact_score < -3:
            market_impact = "약세"
        elif impact_score < -1:
            market_impact = "약약세"
        else:
            market_impact = "중립"
        
        # 리스크 요인 식별
        risk_keywords = [
            'war', 'conflict', 'attack', 'strike', 'bombing',
            'iran', 'israel', 'hamas', 'ukraine', 'russia',
            'inflation', 'recession', 'crisis', 'sanctions',
            'tariff', 'trade war', 'supply chain'
        ]
        risk_factors = []
        
        for news in news_list:
            title_lower = news.title.lower()
            summary_lower = news.summary.lower()
            for keyword in risk_keywords:
                if keyword in title_lower or keyword in summary_lower:
                    if news.sentiment_score < 0:
                        risk_factors.append(f"{keyword}: {news.title[:50]}...")
                        break
        
        # 중복 제거
        risk_factors = list(set(risk_factors))[:5]
        
        # 지정학적 리스크 수준
        if len(risk_factors) >= 3:
            geo_risk = "심각"
        elif len(risk_factors) >= 2:
            geo_risk = "위험"
        elif len(risk_factors) >= 1:
            geo_risk = "주의"
        else:
            geo_risk = "정상"
        
        # 상위 뉴스 정렬 (관련성 점수 기준)
        top_news = sorted(news_list, key=lambda x: abs(x.sentiment_score), reverse=True)[:5]
        
        summary = MarketNewsSummary(
            collection_time=datetime.now().isoformat(),
            total_news_count=len(news_list),
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            avg_sentiment=avg_sentiment,
            market_impact=market_impact,
            impact_score=impact_score,
            top_news=top_news,
            geopolitical_risk=geo_risk,
            risk_factors=risk_factors
        )
        
        return summary


class YahooFinanceNewsCollector:
    """Yahoo Finance 뉴스 수집기 (Alpha Vantage 보완용)"""
    
    def __init__(self):
        if not YFINANCE_AVAILABLE:
            print("⚠️ yfinance 미설치 - Yahoo News 수집 불가")
    
    def get_ticker_news(self, ticker: str, limit: int = 5) -> List[NewsItem]:
        """특정 종목의 Yahoo Finance 뉴스 수집"""
        if not YFINANCE_AVAILABLE:
            return []
        
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            
            if not news:
                return []
            
            news_items = []
            for item in news[:limit]:
                # 발행 시간 파싱
                pub_time = ""
                if 'published' in item:
                    pub_time = datetime.fromtimestamp(
                        item['published']
                    ).isoformat()
                
                news = NewsItem(
                    title=item.get('title', ''),
                    summary=item.get('summary', '')[:200] + '...' if len(item.get('summary', '')) > 200 else item.get('summary', ''),
                    source=item.get('publisher', 'Yahoo Finance'),
                    published_at=pub_time,
                    url=item.get('link', ''),
                    sentiment_label="중립",  # Yahoo는 감성분석 제공 안함
                    tickers=[ticker]
                )
                news_items.append(news)
            
            return news_items
            
        except Exception as e:
            print(f"  ⚠️ Yahoo Finance 뉴스 오류 ({ticker}): {e}")
            return []
    
    def get_market_news(self, tickers: List[str] = None, limit_per_ticker: int = 3) -> List[NewsItem]:
        """
        시장 전반 Yahoo Finance 뉴스 수집
        
        Args:
            tickers: 종목 리스트 (없으면 기본 시장 지표 사용)
            limit_per_ticker: 종목당 수집할 뉴스 수
        """
        if not YFINANCE_AVAILABLE:
            print("⚠️ yfinance 미설치 - Yahoo 시장 뉴스 수집 불가")
            return []
        
        # 기본 시장 대표 종목
        if tickers is None:
            tickers = [
                "SPY",    # S&P 500
                "QQQ",    # Nasdaq
                "AAPL",   # Apple
                "MSFT",   # Microsoft
                "TSLA",   # Tesla
                "NVDA",   # NVIDIA
                "GOOGL",  # Google
                "AMZN",   # Amazon
                "META",   # Meta
                "AMD",    # AMD
            ]
        
        print("\n" + "="*60)
        print("📰 Yahoo Finance 뉴스 수집")
        print("="*60)
        print(f"🔍 대상 종목: {', '.join(tickers[:5])} 등 {len(tickers)}개")
        print(f"📊 종목당 수집: {limit_per_ticker}개")
        
        all_news = []
        successful_tickers = []
        
        for ticker in tickers:
            try:
                print(f"   🔄 {ticker} 뉴스 수집 중...", end="\r")
                news_items = self.get_ticker_news(ticker, limit=limit_per_ticker)
                
                if news_items:
                    all_news.extend(news_items)
                    successful_tickers.append(ticker)
                    print(f"   ✅ {ticker}: {len(news_items)}개 수집")
                else:
                    print(f"   ⚪ {ticker}: 뉴스 없음")
                
                # Rate limit 방지 (0.5초 대기)
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ {ticker}: {str(e)[:40]}")
                continue
        
        print(f"\n✅ Yahoo 뉴스 수집 완료!")
        print(f"   • 수집 성공: {len(successful_tickers)}/{len(tickers)}개 종목")
        print(f"   • 총 뉴스: {len(all_news)}개")
        
        return all_news
    
    def get_sector_news(self, sector: str, limit: int = 10) -> List[NewsItem]:
        """섹터별 Yahoo Finance 뉴스 수집"""
        sector_tickers = {
            "반도체": ["NVDA", "AMD", "INTC", "QCOM", "AVGO"],
            "자동차": ["TSLA", "F", "GM", "RIVN", "LCID"],
            "바이오": ["JNJ", "PFE", "MRNA", "ABBV", "LLY"],
            "에너지": ["XOM", "CVX", "COP", "OXY", "SLB"],
            "금융": ["JPM", "BAC", "WFC", "GS", "MS"],
            "AI": ["PLTR", "AI", "CRWD", "SNOW", "DDOG"],
        }
        
        tickers = sector_tickers.get(sector, ["SPY"])
        print(f"\n🔍 {sector} 섹터 뉴스 수집...")
        return self.get_market_news(tickers, limit_per_ticker=2)


class NewsBriefingGenerator:
    """뉴스 브리핑 생성기 - Alpha Vantage + Yahoo Finance 통합"""
    
    def __init__(self):
        self.av_collector = AlphaVantageNewsCollector()
        self.yahoo_collector = YahooFinanceNewsCollector()
    
    def generate_market_news_briefing(self, use_yahoo: bool = True) -> str:
        """
        시장 뉴스 브리핑 생성
        
        Args:
            use_yahoo: Yahoo Finance 뉴스도 함께 수집 (기본값: True)
        """
        print("\n" + "="*70)
        print("📰 반디 뉴스 브리핑 생성")
        print("="*70)
        
        all_news = []
        sources_used = []
        
        # 1. Alpha Vantage 뉴스 수집 (감성분석 제공)
        print("\n🔄 Source 1: Alpha Vantage News API")
        av_summary = self.av_collector.get_market_impact_news()
        if av_summary and av_summary.total_news_count > 0:
            all_news.extend(av_summary.top_news)
            sources_used.append(f"Alpha Vantage ({av_summary.total_news_count}개)")
            print(f"   ✅ Alpha Vantage: {av_summary.total_news_count}개")
        
        # 2. Yahoo Finance 뉴스 수집 (보완용)
        if use_yahoo and YFINANCE_AVAILABLE:
            print("\n🔄 Source 2: Yahoo Finance")
            yahoo_news = self.yahoo_collector.get_market_news(limit_per_ticker=2)
            if yahoo_news:
                all_news.extend(yahoo_news)
                sources_used.append(f"Yahoo Finance ({len(yahoo_news)}개)")
                print(f"   ✅ Yahoo Finance: {len(yahoo_news)}개")
        
        # 통합 분석
        print(f"\n📊 통합 분석 중... (총 {len(all_news)}개)")
        combined_summary = self._analyze_combined_news(all_news, sources_used)
        
        # 브리핑 텍스트 생성
        briefing = self._format_briefing(combined_summary, sources_used)
        
        return briefing
    
    def _analyze_combined_news(self, news_list: List[NewsItem], sources: List[str]) -> MarketNewsSummary:
        """Alpha Vantage + Yahoo Finance 통합 뉴스 분석"""
        if not news_list:
            return MarketNewsSummary(
                collection_time=datetime.now().isoformat(),
                market_impact="정보없음"
            )
        
        # 중복 제거 (제목 기준)
        seen_titles = set()
        unique_news = []
        for news in news_list:
            title_key = news.title.lower()[:50]  # 앞 50자 기준
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(news)
        
        # 감성 분포 집계
        bullish = sum(1 for n in unique_news if n.sentiment_score > 0.15)
        bearish = sum(1 for n in unique_news if n.sentiment_score < -0.15)
        neutral = len(unique_news) - bullish - bearish
        
        # 평균 감성 점수 (Yahoo 뉴스는 0점으로 처리될 수 있음)
        sentiment_scores = [n.sentiment_score for n in unique_news if n.sentiment_score != 0]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        # 영향도 점수
        impact_score = avg_sentiment * 10
        
        # 영향도 판정
        if impact_score > 3:
            market_impact = "강세"
        elif impact_score > 1:
            market_impact = "약강세"
        elif impact_score < -3:
            market_impact = "약세"
        elif impact_score < -1:
            market_impact = "약약세"
        else:
            market_impact = "중립"
        
        # 리스크 요인 식별
        risk_keywords = [
            'war', 'conflict', 'attack', 'strike', 'bombing',
            'iran', 'israel', 'hamas', 'ukraine', 'russia',
            'inflation', 'recession', 'crisis', 'sanctions',
            'tariff', 'trade war', 'supply chain',
            'middle east', 'oil', 'energy', 'rate hike'
        ]
        risk_factors = []
        
        for news in unique_news:
            title_lower = news.title.lower()
            summary_lower = news.summary.lower() if news.summary else ""
            for keyword in risk_keywords:
                if keyword in title_lower or keyword in summary_lower:
                    risk_factors.append(f"{keyword}: {news.title[:50]}...")
                    break
        
        risk_factors = list(set(risk_factors))[:5]
        
        # 지정학적 리스크 수준
        if len(risk_factors) >= 3:
            geo_risk = "심각"
        elif len(risk_factors) >= 2:
            geo_risk = "위험"
        elif len(risk_factors) >= 1:
            geo_risk = "주의"
        else:
            geo_risk = "정상"
        
        # 상위 뉴스 정렬
        top_news = sorted(unique_news, key=lambda x: abs(x.sentiment_score), reverse=True)[:5]
        
        summary = MarketNewsSummary(
            collection_time=datetime.now().isoformat(),
            total_news_count=len(unique_news),
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            avg_sentiment=avg_sentiment,
            market_impact=market_impact,
            impact_score=impact_score,
            top_news=top_news,
            geopolitical_risk=geo_risk,
            risk_factors=risk_factors
        )
        
        return summary
    
    def _format_briefing(self, summary: MarketNewsSummary, sources: List[str] = None) -> str:
        """브리핑 텍스트 포맷팅"""
        lines = []
        
        lines.append("\n" + "="*60)
        lines.append("📰 반디 뉴스 브리핑")
        lines.append("="*60)
        lines.append(f"\n🕐 수집시간: {summary.collection_time[:19]}")
        
        # 뉴스 소스 정보 (v1.1 추가)
        if sources:
            lines.append(f"\n📡 수집 소스:")
            for source in sources:
                lines.append(f"   • {source}")
        
        # 시장 영향 요약
        lines.append(f"\n📊 시장 영향 판정: {summary.market_impact}")
        lines.append(f"   영향 점수: {summary.impact_score:+.1f}/10")
        
        # 감성 분포
        total = summary.total_news_count
        if total > 0:
            bull_pct = (summary.bullish_count / total) * 100
            bear_pct = (summary.bearish_count / total) * 100
            neut_pct = (summary.neutral_count / total) * 100
            lines.append(f"\n💭 뉴스 감성 분포 (총 {total}개):")
            lines.append(f"   🟢 긍정: {summary.bullish_count}개 ({bull_pct:.0f}%)")
            lines.append(f"   🔴 부정: {summary.bearish_count}개 ({bear_pct:.0f}%)")
            lines.append(f"   ⚪ 중립: {summary.neutral_count}개 ({neut_pct:.0f}%)")
        lines.append(f"   📈 평균 감성: {summary.avg_sentiment:+.2f}")
        
        # 지정학적 리스크
        emoji = {"정상": "🟢", "주의": "🟡", "위험": "🟠", "심각": "🔴"}
        risk_emoji = emoji.get(summary.geopolitical_risk, "⚪")
        lines.append(f"\n{risk_emoji} 지정학적 리스크: {summary.geopolitical_risk}")
        
        if summary.risk_factors:
            lines.append("\n⚠️ 확인된 리스크 요인:")
            for i, factor in enumerate(summary.risk_factors[:3], 1):
                lines.append(f"   {i}. {factor[:60]}...")
        
        # 주요 뉴스
        if summary.top_news:
            lines.append("\n📌 주요 뉴스:")
            for i, news in enumerate(summary.top_news[:3], 1):
                sentiment_emoji = "🔴" if news.sentiment_score < 0 else "🟢" if news.sentiment_score > 0 else "⚪"
                lines.append(f"\n   {i}. {sentiment_emoji} {news.title}")
                lines.append(f"      출처: {news.source}")
                if news.summary and len(news.summary) > 10:
                    summary_text = news.summary[:80] + "..." if len(news.summary) > 80 else news.summary
                    lines.append(f"      요약: {summary_text}")
        
        lines.append("\n" + "="*60)
        
        return '\n'.join(lines)
    
    def save_briefing(self, briefing: str, date_str: Optional[str] = None):
        """브리핑 파일 저장"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        # 저장 경로
        save_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            'news_briefings'
        )
        os.makedirs(save_dir, exist_ok=True)
        
        file_path = os.path.join(save_dir, f'news_briefing_{date_str}.txt')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(briefing)
        
        print(f"\n✅ 뉴스 브리핑 저장: {file_path}")
        return file_path


# ================================================
# 테스트 및 실행
# ================================================

def test_news_collection():
    """뉴스 수집 테스트"""
    print("\n" + "="*70)
    print("🧪 반디 뉴스 수집 모듈 v1.1 테스트")
    print("📝 Alpha Vantage + Yahoo Finance 통합")
    print("="*70)
    
    generator = NewsBriefingGenerator()
    
    # 브리핑 생성 (Yahoo Finance 포함)
    briefing = generator.generate_market_news_briefing(use_yahoo=True)
    print(briefing)
    
    # 파일 저장
    generator.save_briefing(briefing)
    
    # Yahoo Finance만 테스트 (선택적)
    print("\n" + "="*70)
    print("🧪 Yahoo Finance 단독 테스트")
    print("="*70)
    
    yahoo = YahooFinanceNewsCollector()
    if YFINANCE_AVAILABLE:
        # 특정 종목 뉴스 테스트
        print("\n🔍 TSLA 뉴스 테스트:")
        tsla_news = yahoo.get_ticker_news("TSLA", limit=3)
        for i, news in enumerate(tsla_news, 1):
            print(f"   {i}. {news.title[:50]}...")
            print(f"      출처: {news.source}")
        
        # 섹터 뉴스 테스트
        print("\n🔍 반도체 섹터 뉴스 테스트:")
        chip_news = yahoo.get_sector_news("반도체", limit=5)
        print(f"   ✅ {len(chip_news)}개 수집 완료")
    
    print("\n✅ 모든 테스트 완료!")


def quick_news_check():
    """빠른 뉴스 확인 - 명령줄용"""
    print("\n" + "="*70)
    print("📰 반디 뉴스 브리핑 (빠른 확인)")
    print("="*70)
    
    generator = NewsBriefingGenerator()
    briefing = generator.generate_market_news_briefing(use_yahoo=True)
    print(briefing)
    
    # 파일로도 저장
    generator.save_briefing(briefing)
    
    return briefing


if __name__ == "__main__":
    test_news_collection()
