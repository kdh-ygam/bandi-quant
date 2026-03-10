#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║                    반디 퀀트 (BANDI QUANT) v4.1                      ║
║         🤖 AI 예측 + 뉴스 분석 + 정세 브리핑 통합 시스템            ║
║                                                                      ║
║  🎯 v4.1 핵심 업데이트:                                              ║
║  • ✅ 뉴스 수집 및 감성분석 (NEW)                                   ║
║  • ✅ 지정학적/경제정책 리스크 체크 (NEW)                           ║
║  • ✅ 시장 종합 의견 생성 (NEW)                                     ║
║  • ✅ 43개 전체 종목 분석                                          ║
║  • ✅ ML 예측 + 차트 통합                                          ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import re
import requests
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from bs4 import BeautifulSoup

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️ sklearn 미설치 - 규칙 기반 예측 사용")

# 📊 차트 v3.0 통합
try:
    from chart_standard import create_stock_chart, detect_patterns as chart_detect_patterns
    CHART_AVAILABLE = True
except ImportError:
    CHART_AVAILABLE = False
    print("⚠️ chart_standard 미설치 - 차트 생략")

# 차트 저장 경로 (GitHub Actions 환경 고려)
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", os.path.dirname(os.path.abspath(__file__)))
CHART_DIR = os.path.join(WORKSPACE_DIR, "charts")
os.makedirs(CHART_DIR, exist_ok=True)

# 텔레그램 설정
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# 뉴스 API 설정 (추가)
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# ============================================
# 📊 43개 전체 종목 리스트
# ============================================
STOCKS = {
    # 반도체 (7개)
    "000660.KS": {"name": "SK하이닉스", "sector": "반도체", "desc": "HBM3 수요 증가"},
    "005930.KS": {"name": "삼성전자", "sector": "반도체", "desc": "메모리/파운드리"},
    "042700.KS": {"name": "한미반도체", "sector": "반도체", "desc": "반도체 장비"},
    "001740.KS": {"name": "SK스퀘어", "sector": "반도체", "desc": "반도체 투자"},
    "NVDA": {"name": "NVIDIA", "sector": "반도체", "desc": "AI 반도체 절대강자"},
    "AMD": {"name": "AMD", "sector": "반도체", "desc": "CPU/GPU 경쟁력"},
    "ARM": {"name": "ARM Holdings", "sector": "반도체", "desc": "모바일 반도체 IP"},
    
    # 바이오 (5개)
    "068270.KS": {"name": "셀트리온", "sector": "바이오", "desc": "바이오시밀러 선도"},
    "207940.KS": {"name": "삼성바이오로직스", "sector": "바이오", "desc": "CDMO 1위"},
    "196170.KS": {"name": "알테오젠", "sector": "바이오", "desc": "바이오시밀러"},
    "136480.KS": {"name": "하나제약", "sector": "바이오", "desc": "신약 개발 파이프라인"},
    "JNJ": {"name": "Johnson & Johnson", "sector": "바이오", "desc": "diversified 헬스케어"},
    
    # 전력/인프라 (7개)
    "010120.KS": {"name": "LS ELECTRIC", "sector": "전력", "desc": "전력설비/스마트그리드"},
    "267260.KS": {"name": "현대일렉트릭", "sector": "전력", "desc": "중전기/전력기기"},
    "051600.KS": {"name": "한전KPS", "sector": "전력", "desc": "발전설비 정비"},
    "052690.KS": {"name": "한전기술", "sector": "전력", "desc": "전력엔지니어링"},
    "003670.KS": {"name": "포스코DX", "sector": "인프라", "desc": "스마트팩토리"},
    "NEE": {"name": "NextEra Energy", "sector": "전력", "desc": "재생에너지 최대"},
    "TSLA": {"name": "Tesla", "sector": "자동차", "desc": "글로벌 EV 1위"},
    
    # 자동차 (7개)
    "005380.KS": {"name": "현대차", "sector": "자동차", "desc": "글로벌 EV 확대"},
    "000270.KS": {"name": "기아", "sector": "자동차", "desc": "전기차 판매 호조"},
    "012330.KS": {"name": "현대모비스", "sector": "자동차", "desc": "자동차 부품"},
    "003620.KS": {"name": "KG모빌리티", "sector": "자동차", "desc": "중형 상용차"},
    "F": {"name": "Ford", "sector": "자동차", "desc": "F-150 Lightning"},
    "GM": {"name": "General Motors", "sector": "자동차", "desc": "전기차 전환 가속"},
    "RIVN": {"name": "Rivian", "sector": "자동차", "desc": "전기 픽업/SUV"},
    
    # 2차 전지 (6개)
    "373220.KS": {"name": "LG에너지솔루션", "sector": "배터리", "desc": "전기차 배터리"},
    "006400.KS": {"name": "삼성SDI", "sector": "배터리", "desc": "전고체 배터리"},
    "005490.KS": {"name": "POSCO홀딩스", "sector": "배터리", "desc": "양극재/니켈"},
    "247540.KS": {"name": "에코프로비엠", "sector": "배터리", "desc": "양극재"},
    "ALB": {"name": "Albemarle", "sector": "배터리", "desc": "리튬 채굴"},
    "QS": {"name": "QuantumScape", "sector": "배터리", "desc": "전고체 배터리"},
    
    # 클린에너지 (6개)
    "ENPH": {"name": "Enphase Energy", "sector": "클린에너지", "desc": "태양광 마이크로인버터"},
    "SEDG": {"name": "SolarEdge", "sector": "클린에너지", "desc": "태양광 인버터"},
    "FSLR": {"name": "First Solar", "sector": "클린에너지", "desc": "Thin-film 태양광"},
    "RUN": {"name": "Sunrun", "sector": "클린에너지", "desc": "住宅 태양광 설치"},
    "BE": {"name": "Bloom Energy", "sector": "클린에너지", "desc": "연료전지"},
    "NEE": {"name": "NextEra Energy", "sector": "클린에너지", "desc": "재생에너지"},
    
    # AI/소프트웨어 (5개)
    "PLTR": {"name": "Palantir", "sector": "AI", "desc": "빅데이터/AI 플랫폼"},
    "AI": {"name": "C3.ai", "sector": "AI", "desc": "엔터프라이즈 AI"},
    "SNOW": {"name": "Snowflake", "sector": "AI", "desc": "클라우드 데이터"},
    "CRWD": {"name": "CrowdStrike", "sector": "AI", "desc": "사이버보안"},
    "ONON": {"name": "ONON", "sector": "AI", "desc": "러닝화/스포츠"},
}


@dataclass
class StockAnalysis:
    """v4.1 통합 분석 데이터"""
    ticker: str
    name: str
    sector: str
    desc: str
    current_price: float
    previous_price: float
    change_pct: float
    currency: str = "KRW"
    
    # 기술적 지표
    rsi: float = 50.0
    macd_trend: str = ""
    bb_position: str = ""
    volume_ratio: float = 1.0
    
    # 패턴 분석
    patterns: List[Dict] = field(default_factory=list)
    pattern_summary: str = ""
    
    # ML 예측
    ml_prediction: str = ""
    ml_confidence: float = 0.5
    ml_features: Dict = field(default_factory=dict)
    
    # 반디 AI 의견
    bandi_opinion: str = ""
    bandi_strategy: str = ""
    recommendation: str = ""


@dataclass
class MarketNews:
    """시장 뉴스 데이터"""
    geopolitical_risk: str = "보통"
    fed_policy: str = "중립"
    major_events: List[str] = field(default_factory=list)
    sentiment: str = "중립"
    vix_level: float = 20.0
    oil_price: float = 75.0


# ============================================
# 📰 뉴스 분석 모듈 (v4.1 NEW)
# ============================================
class MarketIntelligence:
    """시장 정세 분석기"""
    
    # 지정학적 리스크 키워드
    GEOPOLITICAL_KEYWORDS = {
        "high": ["war", "conflict", "attack", "sanctions", "invasion", "missile", "bomb", "ceasefire", "iran", "middle east"],
        "medium": ["tension", "dispute", "crisis", "border", "military", "threat"],
        "oil_sensitive": ["opec", "oil supply", "energy crisis", "saudi", "gaza", "ukraine"]
    }
    
    # Fed/경제정책 키워드
    FED_KEYWORDS = {
        "hawkish": ["rate hike", "tightening", "higher rates", "inflation fight", "fed chair hawkish"],
        "dovish": ["rate cut", "easing", "pivot", "soft landing", "fed chair dovish"],
        "neutral": ["pause", "hold rates", "data dependent", "wait and see"]
    }
    
    def __init__(self):
        self.news_cache = []
        self.vix_data = None
        self.oil_data = None
    
    def fetch_vix_data(self) -> float:
        """VIX 지수 가져오기"""
        try:
            vix = yf.Ticker("^VIX")
            hist = vix.history(period="1d")
            if len(hist) > 0:
                return float(hist['Close'].iloc[-1])
        except:
            pass
        return 20.0
    
    def fetch_oil_price(self) -> float:
        """유가 가져오기"""
        try:
            oil = yf.Ticker("CL=F")
            hist = oil.history(period="1d")
            if len(hist) > 0:
                return float(hist['Close'].iloc[-1])
        except:
            pass
        return 75.0
    
    def fetch_yfinance_news(self, symbol: str = "SPY") -> List[Dict]:
        """yfinance 뉴스 수집"""
        news_items = []
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            if news:
                for item in news[:5]:
                    news_items.append({
                        'title': item.get('title', ''),
                        'publisher': item.get('publisher', ''),
                        'published': item.get('published', '')
                    })
        except Exception as e:
            print(f"⚠️ yfinance 뉴스 오류: {e}")
        return news_items
    
    def analyze_geopolitical_risk(self, news_items: List[Dict]) -> Tuple[str, List[str]]:
        """지정학적 리스크 분석"""
        risk_score = 0
        risk_events = []
        
        for news in news_items:
            title_lower = news['title'].lower()
            
            # High risk keywords
            for keyword in self.GEOPOLITICAL_KEYWORDS["high"]:
                if keyword in title_lower:
                    risk_score += 3
                    if keyword.title() not in risk_events:
                        risk_events.append(f"🚨 {keyword.title()} related tensions")
            
            # Medium risk
            for keyword in self.GEOPOLITICAL_KEYWORDS["medium"]:
                if keyword in title_lower:
                    risk_score += 1
            
            # Oil sensitive (market impact)
            for keyword in self.GEOPOLITICAL_KEYWORDS["oil_sensitive"]:
                if keyword in title_lower and "oil" in title_lower:
                    risk_score += 2
                    if "Oil/energy concerns" not in risk_events:
                        risk_events.append("⛽ Oil/energy supply concerns")
        
        # Risk level
        if risk_score >= 6:
            return "🔴 높음", risk_events
        elif risk_score >= 3:
            return "🟡 주의", risk_events
        else:
            return "🟢 안정", risk_events or ["No major geopolitical events"]
    
    def analyze_fed_policy(self, news_items: List[Dict]) -> str:
        """Fed 정책 분석"""
        hawkish_score = 0
        dovish_score = 0
        
        for news in news_items:
            title_lower = news['title'].lower()
            
            for kw in self.FED_KEYWORDS["hawkish"]:
                if kw in title_lower:
                    hawkish_score += 1
            for kw in self.FED_KEYWORDS["dovish"]:
                if kw in title_lower:
                    dovish_score += 1
        
        if hawkish_score > dovish_score:
            return "🦅 매파 (긴축 우려)"
        elif dovish_score > hawkish_score:
            return "🕊️ 비둘기파 (완화 기대)"
        else:
            return "⚖️ 중립 (관망)"
    
    def get_market_overview(self) -> str:
        """시장 개요 문자열"""
        try:
            spy = yf.Ticker("SPY")
            spy_hist = spy.history(period="2d")
            if len(spy_hist) >= 2:
                spy_change = ((spy_hist['Close'].iloc[-1] / spy_hist['Close'].iloc[-2]) - 1) * 100
            else:
                spy_change = 0
            
            nasdaq = yf.Ticker("QQQ")
            nasdaq_hist = nasdaq.history(period="2d")
            if len(nasdaq_hist) >= 2:
                nasdaq_change = ((nasdaq_hist['Close'].iloc[-1] / nasdaq_hist['Close'].iloc[-2]) - 1) * 100
            else:
                nasdaq_change = 0
            
            return f"S&P500: {spy_change:+.2f}% | Nasdaq: {nasdaq_change:+.2f}%"
        except:
            return "시장 데이터 수집 중..."
    
    def generate_market_intelligence(self) -> MarketNews:
        """통합 시장 정세 분석"""
        print("📰 시장 정세 분석 중...")
        
        # 뉴스 수집
        spy_news = self.fetch_yfinance_news("SPY")
        qqq_news = self.fetch_yfinance_news("QQQ")
        nvda_news = self.fetch_yfinance_news("NVDA")
        news_items = spy_news + qqq_news + nvda_news
        
        # 시장 데이터
        vix = self.fetch_vix_data()
        oil = self.fetch_oil_price()
        
        # 분석
        geo_risk, events = self.analyze_geopolitical_risk(news_items)
        fed = self.analyze_fed_policy(news_items)
        
        # 감성 판단
        if vix > 25:
            sentiment = "🔴 공포"
        elif vix > 20:
            sentiment = "🟡 불안"
        elif vix < 15:
            sentiment = "🟢 탐욕"
        else:
            sentiment = "⚪ 중립"
        
        return MarketNews(
            geopolitical_risk=geo_risk,
            fed_policy=fed,
            major_events=events[-3:] if events else ["No major overnight events"],
            sentiment=sentiment,
            vix_level=vix,
            oil_price=oil
        )
    
    def generate_market_opinion(self, mkt: MarketNews, avg_rsi: float, ml_bullish: int, ml_bearish: int) -> Tuple[str, str]:
        """시장 종합 의견 생성"""
        
        factors = []
        strategy = ""
        
        # VIX 기반
        if mkt.vix_level > 25:
            factors.append("VIX 25+로 시장 공포 지수 높음")
        elif mkt.vix_level < 15:
            factors.append("VIX 15-로 시장 안정적")
        
        # 지정학적 리스크
        if "높음" in mkt.geopolitical_risk:
            factors.append("지정학적 리스크 고조")
        elif "주의" in mkt.geopolitical_risk:
            factors.append("지정학적 리스크 존재")
        
        # Fed 정책
        if "매파" in mkt.fed_policy:
            factors.append("Fed 매파基調")
        elif "비둘기파" in mkt.fed_policy:
            factors.append("Fed 완화 기대감")
        
        # RSI
        if avg_rsi < 40:
            factors.append("과매도 구간, 반등 가능성")
        elif avg_rsi > 60:
            factors.append("과매수 구간, 조정 가능성")
        
        # ML 예측
        total_ml = ml_bullish + ml_bearish
        if total_ml > 0:
            bull_ratio = ml_bullish / total_ml
            if bull_ratio > 0.6:
                factors.append(f"ML 예측 상승 우세 ({bull_ratio:.0%})")
            elif bull_ratio < 0.4:
                factors.append(f"ML 예측 하락 우세 ({1-bull_ratio:.0%})")
        
        # 종합 판단
        if mkt.vix_level > 25 or "높음" in mkt.geopolitical_risk:
            opinion = "⚠️ 매우 위험"
            strategy = "현금 비중 확대, 공격적 포지션 축소"
        elif mkt.vix_level > 20 or "주의" in mkt.geopolitical_risk or "매파" in mkt.fed_policy:
            opinion = "🟡 관망 우선"
            strategy = "신규 매수 보류, 기존 포지션 관리"
        elif avg_rsi < 40 and ml_bullish > ml_bearish:
            opinion = "🟢 매수 기회"
            strategy = "분할 매수로 공격적 대응"
        elif avg_rsi > 60:
            opinion = "🟠 수익 실현"
            strategy = "익절 및 비중 조절"
        else:
            opinion = "⚪ 중립 관망"
            strategy = "현재 포지션 유지"
        
        return opinion, strategy


# ============================================
# 🎯 기존 모듈들 (FeatureEngineer, MLPredictor, PatternDetector, BandiAI)
# ============================================
class FeatureEngineer:
    """24가지 기술지표 생성기"""
    
    def _flatten_columns(self, df):
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    
    def calculate_all_features(self, df):
        df = df.copy()
        df = self._flatten_columns(df)
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        df['ma_5'] = df['Close'].rolling(window=5).mean()
        df['ma_20'] = df['Close'].rolling(window=20).mean()
        df['ma_ratio'] = df['ma_5'] / df['ma_20']
        
        ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        df['bb_middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_position'] = (df['Close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        df['volume_ma'] = df['Volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['Volume'] / df['volume_ma']
        
        df['return_1d'] = df['Close'].pct_change(1)
        df['return_5d'] = df['Close'].pct_change(5)
        df['return_20d'] = df['Close'].pct_change(20)
        df['volatility'] = df['return_1d'].rolling(window=20).std()
        
        low_min = df['Low'].rolling(window=14).min()
        high_max = df['High'].rolling(window=14).max()
        df['stoch_k'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
        df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
        
        df['future_return'] = df['Close'].shift(-5).pct_change(5)
        df['target'] = np.where(df['future_return'] > 0, 1, 0)
        
        return df
    
    def get_feature_columns(self):
        return ['rsi', 'ma_ratio', 'macd', 'macd_hist', 'bb_position', 
                'volume_ratio', 'return_5d', 'return_20d', 'volatility', 
                'stoch_k', 'stoch_d']


class MLPredictor:
    """ML 예측 모듈"""
    
    def __init__(self):
        self.model = None
        self.featurizer = FeatureEngineer()
        self.is_trained = False
    
    def train_global_model(self):
        print("🤖 글로벌 ML 모델 학습 중...")
        
        if not SKLEARN_AVAILABLE:
            print("   ⚠️ sklearn 미설치")
            self._create_simple_model()
            return
        
        training_tickers = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA', 'NVDA', 'PLTR']
        all_data = []
        
        for ticker in training_tickers:
            try:
                df = yf.download(ticker, period="2y", progress=False)
                if len(df) > 60:
                    df_features = self.featurizer.calculate_all_features(df)
                    all_data.append(df_features)
                    print(f"   ✅ {ticker} 데이터 수집 완료")
            except:
                continue
        
        if not all_data:
            self._create_simple_model()
            return
        
        combined = pd.concat(all_data, ignore_index=True)
        feature_cols = self.featurizer.get_feature_columns()
        combined = combined.dropna()
        
        X = combined[feature_cols]
        y = combined['target']
        
        if len(X) < 100:
            self._create_simple_model()
            return
        
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        self.model = RandomForestClassifier(
            n_estimators=100, max_depth=5, min_samples_split=20, random_state=42
        )
        self.model.fit(X_train, y_train)
        
        test_acc = self.model.score(X_test, y_test)
        print(f"   📊 테스트 정확도: {test_acc:.1%}")
        self.is_trained = True
    
    def _create_simple_model(self):
        self.is_trained = False
    
    def predict(self, df):
        if len(df) < 30:
            return "N/A", 0.5, {}
        
        df_features = self.featurizer.calculate_all_features(df)
        feature_cols = self.featurizer.get_feature_columns()
        
        latest = df_features.dropna().iloc[-1:]
        if len(latest) == 0:
            return "N/A", 0.5, {}
        
        features = {col: latest[col].iloc[0] for col in feature_cols}
        
        if not self.is_trained:
            return self._rule_based_predict(features)
        
        X = latest[feature_cols]
        pred = self.model.predict(X)[0]
        prob = self.model.predict_proba(X)[0]
        
        direction = "상승" if pred == 1 else "하락"
        confidence = prob[pred]
        
        return direction, confidence, features
    
    def _rule_based_predict(self, features):
        score = 0.5
        
        rsi = features.get('rsi', 50)
        if rsi < 35: score += 0.2
        elif rsi > 70: score -= 0.2
        
        macd_hist = features.get('macd_hist', 0)
        if macd_hist > 0: score += 0.15
        else: score -= 0.15
        
        stoch_k = features.get('stoch_k', 50)
        if stoch_k < 30: score += 0.1
        elif stoch_k > 70: score -= 0.1
        
        bb_pos = features.get('bb_position', 0.5)
        if bb_pos < 0.2: score += 0.1
        elif bb_pos > 0.8: score -= 0.1
        
        score = max(0, min(1, score))
        direction = "상승" if score > 0.5 else "하락"
        confidence = abs(score - 0.5) * 2
        
        return direction, confidence, features


class PatternDetector:
    """14가지 고급 캔들 패턴 감지"""
    
    def detect_patterns(self, df):
        patterns = []
        if len(df) < 3:
            return patterns
        
        def to_float(val):
            if hasattr(val, 'item'):
                return float(val.item())
            return float(val)
        
        for i in range(2, min(len(df), 10)):
            curr = df.iloc[-i]
            prev = df.iloc[-i-1] if i+1 < len(df) else curr
            
            open_c = to_float(curr['Open'])
            close_c = to_float(curr['Close'])
            high_c = to_float(curr['High'])
            low_c = to_float(curr['Low'])
            
            body = abs(close_c - open_c)
            upper_shadow = high_c - max(open_c, close_c)
            lower_shadow = min(open_c, close_c) - low_c
            total_range = high_c - low_c
            
            if total_range == 0:
                continue
            
            if lower_shadow > body * 2 and upper_shadow < body * 0.3 and close_c > open_c:
                patterns.append({"name": "망치형", "signal": "매수", "strength": "강함"})
            
            if body < total_range * 0.1:
                patterns.append({"name": "도지", "signal": "관망", "strength": "중간"})
            
            close_p = to_float(prev['Close'])
            open_p = to_float(prev['Open'])
            if close_p < open_p and close_c > open_c and open_c < close_p and close_c > open_p:
                patterns.append({"name": "잉걸불", "signal": "매수", "strength": "강함"})
            
            if body < total_range * 0.1 and lower_shadow > total_range * 0.6:
                patterns.append({"name": "드래곤플라이", "signal": "매수", "strength": "중간"})
            
            if upper_shadow > body * 2 and lower_shadow < body * 0.3 and close_c < open_c:
                patterns.append({"name": "슈팅스타", "signal": "매도", "strength": "중간"})
        
        return patterns


class BandiAI:
    """반디 AI 의견 생성"""
    
    def generate_opinion(self, analysis: StockAnalysis) -> Tuple[str, str]:
        factors = []
        strategy = []
        
        if analysis.rsi < 35:
            factors.append("RSI 과매도 구간, 반등 가능성")
            strategy.append("분할 매수 고려")
        elif analysis.rsi > 70:
            factors.append("RSI 과매수 구간, 조정 가능성")
            strategy.append("익절 및 관망")
        
        if analysis.ml_prediction == "상승" and analysis.ml_confidence > 0.6:
            factors.append(f"ML 예측 상승 확률 {analysis.ml_confidence:.0%}")
            strategy.append("추가 매수 검토")
        elif analysis.ml_prediction == "하락" and analysis.ml_confidence > 0.6:
            factors.append(f"ML 예측 하락 확률 {analysis.ml_confidence:.0%}")
            strategy.append("매도 및 관망")
        
        if analysis.patterns:
            pattern_names = [p['name'] for p in analysis.patterns[:2]]
            factors.append(f"캔들 패턴: {', '.join(pattern_names)}")
        
        if analysis.volume_ratio > 2:
            factors.append("거래량 급증, 주목 필요")
        
        opinion = factors[0] if factors else "중립적 관망"
        strategy_text = strategy[0] if strategy else "현재 포지션 유지"
        
        return opinion, strategy_text


# ============================================
# 🚀 v4.1 메인 시스템
# ============================================
class BandiQuantV41:
    """반디 퀀트 v4.1 메인 시스템 - 뉴스/정세 분석 통합"""
    
    def __init__(self):
        self.results = []
        self.ml_predictor = MLPredictor()
        self.pattern_detector = PatternDetector()
        self.bandi_ai = BandiAI()
        self.market_intel = MarketIntelligence()  # NEW
        self.date_str = datetime.now().strftime('%Y-%m-%d')
        self.time_str = datetime.now().strftime('%H:%M')
        self.market_news = None  # NEW
    
    def run(self):
        """메인 실행"""
        print("=" * 70)
        print("📊 반디 퀀트 v4.1 - AI + 뉴스 + 정세 브리핑")
        print("=" * 70)
        print(f"⏰ 실행: {self.date_str} {self.time_str} KST")
        print(f"📈 종목: {len(STOCKS)}개\n")
        
        # 🆕 시장 정세 분석 (맨 먼저 실행)
        print("🌍 시장 정세 분석 중...")
        self.market_news = self.market_intel.generate_market_intelligence()
        print(f"   VIX: {self.market_news.vix_level:.1f}")
        print(f"   유가: ${self.market_news.oil_price:.2f}")
        print(f"   지정학적 리스크: {self.market_news.geopolitical_risk}")
        print(f"   Fed 정책: {self.market_news.fed_policy}\n")
        
        # ML 모델 학습
        print("🤖 ML 모델 학습 중...")
        self.ml_predictor.train_global_model()
        print()
        
        # 전체 종목 분석
        for i, (ticker, info) in enumerate(STOCKS.items(), 1):
            print(f"\r[{i}/{len(STOCKS)}] {info['name']} 분석 중...", end="", flush=True)
            analysis = self.analyze_stock(ticker, info)
            if analysis:
                self.results.append(analysis)
        
        print(f"\n\n✅ 분석 완료: {len(self.results)}개 종목")
        
        # 브리핑 생성 및 전송
        self.generate_and_send()
    
    def analyze_stock(self, ticker, info) -> Optional[StockAnalysis]:
        """개별 종목 분석 (v4.0과 동일)"""
        try:
            df = yf.download(ticker, period="6mo", progress=False)
            if len(df) < 30:
                return None
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_cols:
                if col not in df.columns:
                    return None
            
            current_raw = df['Close'].iloc[-1]
            previous_raw = df['Close'].iloc[-2]
            current = float(current_raw.item() if hasattr(current_raw, 'item') else current_raw)
            previous = float(previous_raw.item() if hasattr(previous_raw, 'item') else previous_raw)
            change_pct = ((current - previous) / previous) * 100
            currency = 'KRW' if '.KS' in ticker else 'USD'
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs_vals = gain / loss
            rsi_vals = 100 - (100 / (1 + rs_vals))
            rsi_val = float(rsi_vals.iloc[-1]) if not pd.isna(rsi_vals.iloc[-1]) else 50.0
            
            # Volume
            vol_val = df['Volume'].iloc[-1]
            vol_ma = df['Volume'].rolling(20).mean().iloc[-1]
            vol_val = vol_val.item() if hasattr(vol_val, 'item') else vol_val
            vol_ma = vol_ma.item() if hasattr(vol_ma, 'item') else vol_ma
            volume_ratio_val = float(vol_val) / float(vol_ma) if vol_ma and vol_ma != 0 else 1.0
            
            # MACD
            ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
            ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
            macd_line = ema_12 - ema_26
            macd_signal_line = macd_line.ewm(span=9, adjust=False).mean()
            macd_val = float(macd_line.iloc[-1].item() if hasattr(macd_line.iloc[-1], 'item') else macd_line.iloc[-1])
            macd_sig_val = float(macd_signal_line.iloc[-1].item() if hasattr(macd_signal_line.iloc[-1], 'item') else macd_signal_line.iloc[-1])
            macd_trend = "상승" if macd_val > macd_sig_val else "하락"
            
            # Bollinger
            bb_mid = df['Close'].rolling(20).mean().iloc[-1]
            bb_std = df['Close'].rolling(20).std().iloc[-1]
            bb_mid = bb_mid.item() if hasattr(bb_mid, 'item') else bb_mid
            bb_std = bb_std.item() if hasattr(bb_std, 'item') else bb_std
            bb_mid = float(bb_mid)
            bb_std = float(bb_std)
            bb_upper = bb_mid + (bb_std * 2)
            bb_lower = bb_mid - (bb_std * 2)
            bb_pos = (current - bb_lower) / (bb_upper - bb_lower) if abs(bb_upper - bb_lower) > 0.0001 else 0.5
            
            if bb_pos > 0.95:
                bb_position = "상단돌파"
            elif bb_pos < 0.05:
                bb_position = "하단이탈"
            elif bb_pos > 0.7:
                bb_position = "상단접근"
            elif bb_pos < 0.3:
                bb_position = "하단접근"
            else:
                bb_position = "중간"
            
            # ML 예측
            ml_pred, ml_conf, ml_feats = self.ml_predictor.predict(df)
            
            # 패턴 감지
            patterns = self.pattern_detector.detect_patterns(df)
            
            analysis = StockAnalysis(
                ticker=ticker, name=info['name'], sector=info['sector'], desc=info['desc'],
                current_price=current, previous_price=previous, change_pct=change_pct,
                currency=currency, rsi=round(rsi_val, 1), macd_trend=macd_trend,
                bb_position=bb_position, volume_ratio=round(volume_ratio_val, 2),
                patterns=patterns, ml_prediction=ml_pred, ml_confidence=round(ml_conf, 2),
                ml_features=ml_feats
            )
            
            analysis.bandi_opinion, analysis.bandi_strategy = self.bandi_ai.generate_opinion(analysis)
            analysis.recommendation = self.determine_grade(analysis)
            
            return analysis
            
        except Exception as e:
            print(f"\n  ❌ {ticker} 오류: {str(e)[:50]}")
            return None
    
    def determine_grade(self, analysis: StockAnalysis) -> str:
        """등급 판정"""
        score = 0
        
        if analysis.rsi < 35:
            score += 3
        elif analysis.rsi < 45:
            score += 2
        elif analysis.rsi < 50:
            score += 1
        elif analysis.rsi > 70:
            score -= 3
        elif analysis.rsi > 60:
            score -= 1
        
        if analysis.ml_prediction == "상승":
            score += 2 if analysis.ml_confidence > 0.6 else 1
        elif analysis.ml_prediction == "하락":
            score -= 2 if analysis.ml_confidence > 0.6 else 1
        
        if analysis.patterns:
            for p in analysis.patterns:
                if p['signal'] == '매수':
                    score += 1
                elif p['signal'] == '매도':
                    score -= 1
        
        if score >= 4:
            return "🟢 강력매수"
        elif score >= 2:
            return "🟡 매수권유"
        elif score >= 1:
            return "🟠 매수대비"
        elif score <= -4:
            return "🔴 강력매도"
        elif score <= -2:
            return "🟠 매도권유"
        elif score <= -1:
            return "🟡 매도대비"
        else:
            return "⚪ 보유"
    
    def generate_and_send(self):
        """브리핑 생성 및 전송 - v4.1 정세 분석 포함"""
        print("\n📱 텔레그램 브리핑 생성 중...")
        
        lines = []
        lines.append(f"🤖 반디 퀀트 v4.1 브리핑")
        lines.append(f"📅 {self.date_str}  ⏰ {self.time_str} KST")
        lines.append("")
        
        # 🆕 시장 정세 요약
        if self.market_news:
            lines.append("═" * 40)
            lines.append("🌍 시장 정세 분석")
            lines.append("═" * 40)
            
            mkt_overview = self.market_intel.get_market_overview()
            lines.append(f"📊 {mkt_overview}")
            lines.append(f"🌡️ VIX 공포지수: {self.market_news.vix_level:.1f} {self.market_news.sentiment}")
            lines.append(f"🛢️ WTI 유가: ${self.market_news.oil_price:.2f}")
            lines.append("")
            lines.append(f"🔥 지정학적 리스크: {self.market_news.geopolitical_risk}")
            lines.append(f"🏛️ Fed 정책: {self.market_news.fed_policy}")
            
            if self.market_news.major_events:
                lines.append("")
                lines.append("📰 주요 이벤트:")
                for event in self.market_news.major_events[:3]:
                    lines.append(f"   {event}")
            
            lines.append("")
        
        # 종합 시장 의견
        avg_rsi = sum(s.rsi for s in self.results) / len(self.results) if self.results else 50
        ml_up = sum(1 for s in self.results if s.ml_prediction == "상승")
        ml_down = sum(1 for s in self.results if s.ml_prediction == "하락")
        
        if self.market_news:
            market_opinion, market_strategy = self.market_intel.generate_market_opinion(
                self.market_news, avg_rsi, ml_up, ml_down
            )
            
            lines.append("═" * 40)
            lines.append("🎯 반디 종합 시장 의견")
            lines.append("═" * 40)
            lines.append(f"종합 판단: {market_opinion}")
            lines.append(f"전략: {market_strategy}")
            lines.append("")
        
        # 기존 내용
        lines.append("═" * 40)
        lines.append("📊 시장 요약")
        lines.append("═" * 40)
        up_count = sum(1 for s in self.results if s.change_pct > 0)
        down_count = len(self.results) - up_count
        lines.append(f"- 분석: {len(self.results)}개 종목")
        lines.append(f"- 상승: {up_count}개 | 하락: {down_count}개")
        lines.append(f"- 평균 RSI: {avg_rsi:.1f}")
        lines.append(f"- ML 예측: 상승 {ml_up}개 | 하락 {ml_down}개")
        lines.append("")
        
        # 급등 TOP 5
        lines.append("═" * 40)
        lines.append("🔥 오늘의 급등 TOP 5")
        lines.append("═" * 40)
        surging = sorted(self.results, key=lambda x: x.change_pct, reverse=True)[:5]
        for i, s in enumerate(surging, 1):
            unit = "원" if s.currency == 'KRW' else "$"
            price_str = f"{int(s.current_price):,}{unit}" if s.currency == 'KRW' else f"{s.current_price:.2f}{unit}"
            ml_icon = "[ML추천]" if s.ml_confidence > 0.6 else ""
            lines.append(f"{i}. {s.name}: {price_str} ({s.change_pct:+.1f}%)")
            lines.append(f"   RSI {s.rsi} | {s.ml_prediction} 신뢰{s.ml_confidence:.0%} {ml_icon}")
        lines.append("")
        
        # ML 강력 추천
        strong_signals = [s for s in self.results if s.ml_confidence > 0.6]
        strong_signals.sort(key=lambda x: x.ml_confidence, reverse=True)
        
        if strong_signals:
            lines.append("═" * 40)
            lines.append("🎯 AI 강력 추천 (ML 신뢰도 60%+)")
            lines.append("═" * 40)
            for s in strong_signals[:5]:
                unit = "원" if s.currency == 'KRW' else "$"
                price_str = f"{int(s.current_price):,}{unit}" if s.currency == 'KRW' else f"{s.current_price:.2f}{unit}"
                ticker_clean = s.ticker.replace('.KS', '')
                
                lines.append(f"")
                lines.append(f"• {s.name} ({ticker_clean})")
                lines.append(f"  가격: {price_str} ({s.change_pct:+.1f}%)")
                lines.append(f"  ML: {s.ml_prediction} (신뢰{s.ml_confidence:.0%})")
                lines.append(f"  RSI: {s.rsi} | 거래량: {s.volume_ratio:.1f}x")
                
                if s.patterns:
                    pattern_str = ", ".join([p['name'] for p in s.patterns[:2]])
                    lines.append(f"  패턴: {pattern_str}")
                
                lines.append(f"  의견: {s.bandi_opinion}")
                lines.append(f"  전략: {s.bandi_strategy}")
        
        lines.append("")
        
        # 매도 권고
        sells = [s for s in self.results if '매도' in s.recommendation]
        if sells:
            lines.append("═" * 40)
            lines.append("🔴 매도 주의 종목")
            lines.append("═" * 40)
            for s in sells[:5]:
                lines.append(f"• {s.name}: {s.recommendation}")
        
        lines.append("")
        lines.append("═" * 40)
        lines.append(f"📎 상세: /analysis/briefing_{self.date_str}.json")
        lines.append("🤖 반디 AI v4.1 | 뉴스 + 정세 + 43종목 분석")
        lines.append("")
        lines.append("반디가 파파를 응원해요 🐾")
        
        message = "\n".join(lines)
        
        # 차트 생성 및 전송
        if CHART_AVAILABLE:
            chart_paths = self.generate_charts(self.results, max_charts=5)
            self.send_telegram_with_charts(message, chart_paths)
        else:
            self.send_telegram(message)
        
        self.save_results()
    
    def generate_charts(self, stocks: List[StockAnalysis], max_charts: int = 5):
        """상위 종목 차트 생성"""
        if not CHART_AVAILABLE:
            print("⚠️ 차트 모듈 없음")
            return []
        
        print(f"\n📊 차트 생성 중... (최대 {max_charts}개)")
        chart_paths = []
        
        sorted_stocks = sorted(stocks, key=lambda x: x.ml_confidence, reverse=True)
        
        for i, s in enumerate(sorted_stocks[:max_charts]):
            try:
                if s.ml_prediction == "상승":
                    signal_type = 'buy'
                    signal_strength = 'strong' if s.ml_confidence > 0.7 else 'normal'
                elif s.ml_prediction == "하락":
                    signal_type = 'sell'
                    signal_strength = 'strong' if s.ml_confidence > 0.7 else 'normal'
                else:
                    signal_type = None
                    signal_strength = None
                
                safe_name = re.sub(r'[^\w]', '', s.name.replace(' ', '_').replace('&', 'and'))
                chart_path = f"{CHART_DIR}/{safe_name}_{self.date_str}.png"
                
                result = create_stock_chart(
                    ticker=s.ticker, name=s.name, output_path=chart_path,
                    signal_type=signal_type, signal_strength=signal_strength
                )
                
                if result.get('success'):
                    chart_paths.append(chart_path)
                    print(f"   ✅ {s.name} 차트 생성 완료")
                else:
                    print(f"   ⚠️ {s.name} 차트 실패: {result.get('error')}")
                    
            except Exception as e:
                print(f"   ❌ {s.name} 차트 오류: {str(e)[:50]}")
                continue
        
        print(f"📊 총 {len(chart_paths)}개 차트 생성 완료")
        return chart_paths
    
    def send_telegram_with_charts(self, message: str, chart_paths: List[str]):
        """텍스트 + 차트 전송"""
        url_msg = f"{TELEGRAM_API}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        
        try:
            response = requests.post(url_msg, json=payload, timeout=30)
            if response.status_code == 200:
                print("✅ 텔레그램 텍스트 전송 완료!")
            else:
                print(f"❌ 텍스트 전송 실패: {response.text[:100]}")
        except Exception as e:
            print(f"❌ 텍스트 오류: {e}")
        
        if chart_paths:
            print(f"\n📸 차트 이미지 {len(chart_paths)}개 전송 중...")
            url_photo = f"{TELEGRAM_API}/sendPhoto"
            
            for chart_path in chart_paths:
                try:
                    if os.path.exists(chart_path):
                        with open(chart_path, 'rb') as f:
                            files = {'photo': f}
                            data = {'chat_id': CHAT_ID}
                            filename = os.path.basename(chart_path)
                            stock_name = filename.replace(f'_{self.date_str}.png', '')
                            data['caption'] = f"📊 {stock_name} 분석 차트"
                            
                            response = requests.post(url_photo, data=data, files=files, timeout=30)
                            if response.status_code == 200:
                                print(f"   ✅ {filename} 전송 완료")
                            else:
                                print(f"   ⚠️ {filename} 전송 실패: {response.text[:50]}")
                    else:
                        print(f"   ⚠️ 파일 없음: {chart_path}")
                        
                except Exception as e:
                    print(f"   ❌ 차트 전송 오류: {str(e)[:50]}")
    
    def send_telegram(self, message: str):
        """텔레그램 전송"""
        url = f"{TELEGRAM_API}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                print("✅ 텔레그램 전송 완료!")
            else:
                print(f"❌ 전송 실패: {response.text[:100]}")
        except Exception as e:
            print(f"❌ 오류: {e}")
    
    def save_results(self):
        """결과 저장"""
        output_dir = os.path.join(WORKSPACE_DIR, "analysis")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{output_dir}/briefing_v41_{self.date_str}.json"
        
        data = {
            "version": "4.1",
            "date": self.date_str,
            "time": self.time_str,
            "market_news": {
                "vix": self.market_news.vix_level if self.market_news else None,
                "oil_price": self.market_news.oil_price if self.market_news else None,
                "geopolitical_risk": self.market_news.geopolitical_risk if self.market_news else None,
                "fed_policy": self.market_news.fed_policy if self.market_news else None,
                "major_events": self.market_news.major_events if self.market_news else []
            },
            "total_stocks": len(self.results),
            "stocks": [
                {
                    "ticker": s.ticker, "name": s.name,
                    "current_price": s.current_price, "change_pct": s.change_pct,
                    "rsi": s.rsi, "ml_prediction": s.ml_prediction,
                    "ml_confidence": s.ml_confidence, "patterns": s.patterns,
                    "recommendation": s.recommendation, "bandi_opinion": s.bandi_opinion
                } for s in self.results
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 결과 저장: {filename}")


if __name__ == "__main__":
    system = BandiQuantV41()
    system.run()
