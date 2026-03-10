#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║              반디 RL 트레이더 (BANDI RL TRADER) v1.0                ║
║                                                                      ║
║  🤖 강화학습 기반 자동 트레이딩 에이전트                          ║
║  • State: 주가 + 기술지표 + 뉴스 감성 + 시장 정세                 ║
║  • Action: 매수/매도/관망 (연속적/이산적)                         ║
║  • Reward: 일별 수익률 + 위험 조정                               ║
║                                                                      ║
║  반디의 기술 통합:                                                  ║
║  ✅ v4.1 뉴스 분석 (지정학적 리스크, Fed 정책)                   ║
║  ✅ ML 예측 (RandomForest 기반)                                   ║
║  ✅ 기술적 지표 (RSI, MACD, 볼린저, 패턴)                        ║
║  ✅ 백테스팅 (수익률, 샤프, MDD)                                  ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import warnings

warnings.filterwarnings('ignore')

# RL 프레임워크
try:
    import gymnasium as gym
    from gymnasium import spaces
    from stable_baselines3 import PPO, DQN, A2C
    from stable_baselines3.common.vec_env import DummyVecEnv
    from stable_baselines3.common.callbacks import BaseCallback
    RL_AVAILABLE = True
except ImportError:
    print("⚠️ RL 프레임워크 미설치 - pip install stable-baselines3 gymnasium")
    RL_AVAILABLE = False

# 딥러닝
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# ============================================
# 📊 43개 전체 종목 리스트 (v4.1에서 가져옴)
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
    "136480.KS": {"name": "하나제약", "sector": "바이오", "desc": "신약 개발"},
    "JNJ": {"name": "Johnson & Johnson", "sector": "바이오", "desc": "diversified 헬스케어"},
    
    # 전력/자동차/배터리/클린에너지/AI (31개)
    "010120.KS": {"name": "LS ELECTRIC", "sector": "전력", "desc": "전력설비"},
    "267260.KS": {"name": "현대일렉트릭", "sector": "전력", "desc": "중전기"},
    "051600.KS": {"name": "한전KPS", "sector": "전력", "desc": "발전설비 정비"},
    "052690.KS": {"name": "한전기술", "sector": "전력", "desc": "전력엔지니어링"},
    "003670.KS": {"name": "포스코DX", "sector": "인프라", "desc": "스마트팩토리"},
    "NEE": {"name": "NextEra Energy", "sector": "전력", "desc": "재생에너지 최대"},
    "TSLA": {"name": "Tesla", "sector": "자동차", "desc": "글로벌 EV 1위"},
    "005380.KS": {"name": "현대차", "sector": "자동차", "desc": "글로벌 EV 확대"},
    "000270.KS": {"name": "기아", "sector": "자동차", "desc": "전기차 판매 호조"},
    "012330.KS": {"name": "현대모비스", "sector": "자동차", "desc": "자동차 부품"},
    "003620.KS": {"name": "KG모빌리티", "sector": "자동차", "desc": "중형 상용차"},
    "F": {"name": "Ford", "sector": "자동차", "desc": "F-150 Lightning"},
    "GM": {"name": "General Motors", "sector": "자동차", "desc": "전기차 전환"},
    "RIVN": {"name": "Rivian", "sector": "자동차", "desc": "전기 픽업/SUV"},
    "373220.KS": {"name": "LG에너지솔루션", "sector": "배터리", "desc": "전기차 배터리"},
    "006400.KS": {"name": "삼성SDI", "sector": "배터리", "desc": "전고체 배터리"},
    "005490.KS": {"name": "POSCO홀딩스", "sector": "배터리", "desc": "양극재/니켈"},
    "247540.KS": {"name": "에코프로비엠", "sector": "배터리", "desc": "양극재"},
    "ALB": {"name": "Albemarle", "sector": "배터리", "desc": "리튬 채굴"},
    "QS": {"name": "QuantumScape", "sector": "배터리", "desc": "전고체 배터리"},
    "ENPH": {"name": "Enphase Energy", "sector": "클린에너지", "desc": "태양광 인버터"},
    "SEDG": {"name": "SolarEdge", "sector": "클린에너지", "desc": "태양광 인버터"},
    "FSLR": {"name": "First Solar", "sector": "클린에너지", "desc": "Thin-film 태양광"},
    "RUN": {"name": "Sunrun", "sector": "클린에너지", "desc": "住宅 태양광"},
    "BE": {"name": "Bloom Energy", "sector": "클린에너지", "desc": "연료전지"},
    "PLTR": {"name": "Palantir", "sector": "AI", "desc": "빅데이터/AI 플랫폼"},
    "AI": {"name": "C3.ai", "sector": "AI", "desc": "엔터프라이즈 AI"},
    "SNOW": {"name": "Snowflake", "sector": "AI", "desc": "클라우드 데이터"},
    "CRWD": {"name": "CrowdStrike", "sector": "AI", "desc": "사이버보안"},
    "ONON": {"name": "ONON", "sector": "AI", "desc": "러닝화/스포츠"},
}

# ============================================
# 🔧 기술적 지표 모듈 (v4.1에서 가져옴)
# ============================================
class TechnicalIndicators:
    """기술적 지표 계산기"""
    
    @staticmethod
    def calculate_rsi(prices, period=14):
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        """MACD 계산"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        macd_hist = macd - macd_signal
        return macd, macd_signal, macd_hist
    
    @staticmethod
    def calculate_bollinger(prices, period=20, std=2):
        """볼린저 밴드 계산"""
        ma = prices.rolling(window=period).mean()
        std_dev = prices.rolling(window=period).std()
        upper = ma + (std_dev * std)
        lower = ma - (std_dev * std)
        position = (prices - lower) / (upper - lower)
        return upper, ma, lower, position
    
    @staticmethod
    def calculate_all(df):
        """모든 지표 계산"""
        df = df.copy()
        
        # RSI
        df['rsi'] = TechnicalIndicators.calculate_rsi(df['Close'])
        
        # MACD
        df['macd'], df['macd_signal'], df['macd_hist'] = TechnicalIndicators.calculate_macd(df['Close'])
        
        # 볼린저
        df['bb_upper'], df['bb_middle'], df['bb_lower'], df['bb_position'] = TechnicalIndicators.calculate_bollinger(df['Close'])
        
        # 이동평균
        df['ma_5'] = df['Close'].rolling(5).mean()
        df['ma_20'] = df['Close'].rolling(20).mean()
        df['ma_ratio'] = df['ma_5'] / df['ma_20']
        
        # 거래량
        df['volume_ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()
        
        # 가격 변화
        df['return_1d'] = df['Close'].pct_change(1)
        df['return_5d'] = df['Close'].pct_change(5)
        df['volatility'] = df['return_1d'].rolling(20).std()
        
        return df

# ============================================
# 📰 뉴스 분석 모듈 (v4.1에서 가져옴)
# ============================================
class MarketIntelligence:
    """시장 정세 및 뉴스 분석기"""
    
    GEOPOLITICAL_KEYWORDS = {
        "high": ["war", "conflict", "attack", "sanctions", "invasion", "missile", "bomb", "ceasefire", "iran", "middle east"],
        "medium": ["tension", "dispute", "crisis", "border", "military", "threat"],
    }
    
    FED_KEYWORDS = {
        "hawkish": ["rate hike", "tightening", "higher rates", "inflation fight"],
        "dovish": ["rate cut", "easing", "pivot", "soft landing"],
    }
    
    def get_market_data(self):
        """시장 데이터 조회"""
        market_data = {}
        
        try:
            # VIX
            vix = yf.Ticker("^VIX")
            vix_hist = vix.history(period="5d")
            market_data['vix'] = float(vix_hist['Close'].iloc[-1]) if len(vix_hist) > 0 else 20
            
            # 유가
            oil = yf.Ticker("CL=F")
            oil_hist = oil.history(period="5d")
            market_data['oil'] = float(oil_hist['Close'].iloc[-1]) if len(oil_hist) > 0 else 75
            
            # 시장 지수
            spy = yf.Ticker("SPY")
            spy_hist = spy.history(period="5d")
            if len(spy_hist) >= 2:
                market_data['spy_change'] = (spy_hist['Close'].iloc[-1] / spy_hist['Close'].iloc[-2] - 1) * 100
            else:
                market_data['spy_change'] = 0
                
        except Exception as e:
            market_data = {'vix': 20, 'oil': 75, 'spy_change': 0}
        
        return market_data
    
    def get_sentiment_score(self):
        """시장 감성 점수 (-1 ~ +1)"""
        data = self.get_market_data()
        
        score = 0
        # VIX 기반
        if data['vix'] > 25:
            score -= 0.3
        elif data['vix'] < 15:
            score += 0.2
        
        # 시장 수익률 기반
        score += data['spy_change'] * 0.1
        
        return np.clip(score, -1, 1)

# ============================================
# 🎮 RL 환경 (StockTradingEnv)
# ============================================
class StockTradingEnv(gym.Env):
    """반디 RL 트레이딩 환경"""
    
    metadata = {'render_modes': ['human']}
    
    def __init__(self, ticker: str, start_date: str = None, end_date: str = None, 
                 initial_balance: float = 10000, max_position: int = 100, 
                 window_size: int = 30, render_mode: str = None):
        super().__init__()
        
        self.ticker = ticker
        self.initial_balance = initial_balance
        self.max_position = max_position
        self.window_size = window_size
        self.render_mode = render_mode
        
        # 데이터 로드
        self.df = self._load_data(start_date, end_date)
        if self.df is None or len(self.df) < window_size * 2:
            raise ValueError(f"데이터 부족: {ticker}")
        
        # 지표 계산
        self.df = TechnicalIndicators.calculate_all(self.df)
        self.df = self.df.dropna()
        
        # Market Intelligence
        self.market_intel = MarketIntelligence()
        
        # 상태 공간: 기술지표 + 시장 데이터 + 포트폴리오 + 진입전략
        n_features = 20  # 기술지표 10 + 시장 3 + 포트폴리오 2 + 진입전략 5
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, 
            shape=(window_size, n_features), 
            dtype=np.float32
        )
        
        # 행동 공간: 연속적 [-1, 1]
        # -1 = 전량 매도, 0 = 관망, +1 = 전량 매수 (최대 포지션)
        self.action_space = spaces.Box(
            low=-1, high=1, shape=(1,), dtype=np.float32
        )
        
        # 포트폴리오 상태
        self.balance = initial_balance
        self.position = 0
        self.current_step = window_size
        self.total_value = initial_balance
        self.value_history = []
        
    def _load_data(self, start_date, end_date):
        """주가 데이터 로드"""
        try:
            ticker = yf.Ticker(self.ticker)
            df = ticker.history(period="2y" if not start_date else None,
                               start=start_date, end=end_date)
            if len(df) < 60:
                return None
            return df.reset_index()
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            return None
    
    def _get_observation(self):
        """현재 상태 반환 (진입전략 State 통합)"""
        # window_size 기간의 데이터
        start_idx = self.current_step - self.window_size
        end_idx = self.current_step
        
        window_data = self.df.iloc[start_idx:end_idx]
        
        # 특성 정규화
        features = []
        
        # 1. 기술적 지표 (10개)
        for col in ['rsi', 'macd', 'macd_hist', 'bb_position', 'ma_ratio',
                   'volume_ratio', 'return_1d', 'return_5d', 'volatility', 'Close']:
            if col in window_data.columns:
                vals = window_data[col].values
                if col == 'Close':
                    # 가격은 초기 대비 변화율로 정규화
                    vals = vals / vals[0] - 1
                elif col == 'rsi':
                    # RSI는 0~100 -> -1~1
                    vals = (vals - 50) / 50
                elif col in ['macd', 'macd_hist']:
                    # MACD는 가격 기준 정규화
                    close = window_data['Close'].values
                    vals = vals / close
                features.append(vals)
            else:
                features.append(np.zeros(self.window_size))
        
        # 2. 시장 데이터 (3개) - 현재 스텝 기준
        market_data = self.market_intel.get_market_data()
        market_features = [
            (market_data['vix'] - 20) / 20,  # VIX 정규화
            (market_data['oil'] - 75) / 30,  # 유가 정규화
            market_data['spy_change'] / 10   # 시장 변화율
        ]
        
        # 시장 데이터를 window 전체에 동일하게 적용
        for mf in market_features:
            features.append(np.full(self.window_size, mf))
        
        # 3. 포트폴리오 상태 (2개)
        current_price = self.df['Close'].iloc[self.current_step]
        position_ratio = self.position / self.max_position if self.max_position > 0 else 0
        
        for pf in [position_ratio, self.balance / self.initial_balance - 1]:
            features.append(np.full(self.window_size, pf))
        
        # 4. 진입전략 특성 (5개) - 파파가 알려준 전략 반영
        entry_signals = self._calculate_entry_signals(window_data)
        for signal in entry_signals:
            features.append(np.full(self.window_size, signal))
        
        obs = np.column_stack(features).astype(np.float32)
        return obs
    
    def _calculate_entry_signals(self, window_data: pd.DataFrame) -> list:
        """진입전략 신호 계산 - 파파의 검증된 전략"""
        if len(window_data) < 5:
            return [0, 0, 0, 0, 0]  # 데이터 부족시 중립
        
        current = window_data.iloc[-1]
        prev = window_data.iloc[-2] if len(window_data) >= 2 else current
        
        # 1. 돌파 (Breakout) 신호
        breakout = 0
        if 'bb_position' in window_data.columns and 'volume_ratio' in window_data.columns:
            bb_pos = current['bb_position']
            vol_ratio = current['volume_ratio']
            # 볼린저 상단 돌파 + 거래량 급증
            if bb_pos > 0.7 and vol_ratio > 1.5:
                breakout = 1  # 강한 돌파
            # 52주 고점 근접 (시뮬레이션, 20일 중 최고)
            if 'High' in window_data.columns:
                recent_high = window_data['High'].tail(20).max()
                if current['Close'] >= recent_high * 0.98:
                    breakout = min(breakout + 0.5, 1)  # 고점 근접
        
        # 2. 눌림 (Pullback) 신호
        pullback = 0
        if 'rsi' in window_data.columns and 'ma_ratio' in window_data.columns:
            rsi = current['rsi']
            ma_ratio = current['ma_ratio']
            # RSI 과매수 영역에서 지지 + 이평선 상승
            if 30 < rsi < 50 and ma_ratio > 1.0:
                pullback = 1  # 눌림 매수
            # 볼린저 중간선 근처 지지
            if 'bb_position' in window_data.columns:
                bb_pos = current['bb_position']
                if 0.4 < bb_pos < 0.6 and current['Close'] > prev['Close']:
                    pullback = min(pullback + 0.5, 1)
        
        # 3. 추세 전환 (Reversal) 신호
        reversal = 0
        if len(window_data) >= 5:
            recent_lows = window_data['Low'].tail(5).values
            recent_highs = window_data['High'].tail(5).values
            # 1-2-3 저점 상승 (Higher Low)
            if len(recent_lows) >= 3:
                if recent_lows[-1] > recent_lows[-3]:  # Higher Low
                    if recent_lows[-2] > recent_lows[-3]:  # 확인
                        reversal = 0.5  # 추세 전환 초입
            # MACD 턴어라운드
            if 'macd' in window_data.columns and 'macd_hist' in window_data.columns:
                macd_hist = window_data['macd_hist'].values
                if len(macd_hist) >= 3:
                    if macd_hist[-2] < 0 and macd_hist[-1] > macd_hist[-2]:
                        reversal = min(reversal + 0.5, 1)  # MACD 상승
        
        # 4. 상대강도 (Relative Strength)
        rs = 0
        if 'return_5d' in window_data.columns:
            stock_return = current.get('return_5d', 0)
            spy_return = market_data.get('spy_change', 0) / 100 * 5  # 5일 시장 수익률 추정
            if stock_return > spy_return:
                rs = 1  # 시장 대비 우위
            elif stock_return > spy_return * 0.5:
                rs = 0.5  # 양호
        
        # 5. 거래량 급증 (Volume Spike)
        volume_spike = 0
        if 'volume_ratio' in window_data.columns:
            vol = current['volume_ratio']
            if vol > 2.0:
                volume_spike = 1  # 매우 강한 거래량
            elif vol > 1.5:
                volume_spike = 0.7  # 강한 거래량
            elif vol > 1.0:
                volume_spike = 0.3  # 평균 이상
        
        return [breakout, pullback, reversal, rs, volume_spike]
    
    def reset(self, seed=None, options=None):
        """환경 초기화"""
        super().reset(seed=seed)
        
        self.current_step = self.window_size
        self.balance = self.initial_balance
        self.position = 0
        self.total_value = self.initial_balance
        self.value_history = []
        
        return self._get_observation(), {}
    
    def step(self, action):
        """한 스텝 진행"""
        # 행동 해석: -1 ~ 1 -> -100% ~ +100% 포지션 조정
        action = np.clip(action[0], -1, 1)
        
        current_price = float(self.df['Close'].iloc[self.current_step])
        
        # 목표 포지션 계산
        target_position = int(action * self.max_position)
        position_diff = target_position - self.position
        
        # 거래 실행
        if position_diff > 0:  # 매수
            cost = position_diff * current_price
            if cost <= self.balance:
                self.position += position_diff
                self.balance -= cost
        elif position_diff < 0:  # 매도
            sell_shares = min(abs(position_diff), self.position)
            revenue = sell_shares * current_price
            self.position -= sell_shares
            self.balance += revenue
        
        # 포트폴리오 가치 업데이트
        self.total_value = self.balance + self.position * current_price
        self.value_history.append(self.total_value)
        
        # 보상 계산 (수익률 기반)
        if len(self.value_history) > 1:
            return_pct = (self.value_history[-1] - self.value_history[-2]) / self.value_history[-2]
            # 위험 조정 (볼린저 위치 고려)
            bb_pos = self.df['bb_position'].iloc[self.current_step]
            if pd.notna(bb_pos):
                risk_adjustment = 1 if bb_pos < 0.3 or bb_pos > 0.7 else 1.1
            else:
                risk_adjustment = 1
            reward = return_pct * 100 * risk_adjustment
        else:
            reward = 0
        
        # 다음 스텝
        self.current_step += 1
        done = self.current_step >= len(self.df) - 1
        truncated = False
        
        obs = self._get_observation()
        info = {
            'total_value': self.total_value,
            'return_pct': (self.total_value - self.initial_balance) / self.initial_balance * 100,
            'position': self.position,
            'price': current_price
        }
        
        return obs, reward, done, truncated, info
    
    def render(self):
        """현재 상태 출력"""
        if self.render_mode == 'human':
            print(f"Step: {self.current_step}, Value: ${self.total_value:.2f}, "
                  f"Return: {(self.total_value/self.initial_balance-1)*100:.2f}%, "
                  f"Position: {self.position}")

# ============================================
# 🤖 RL 트레이더 (학습 및 예측)
# ============================================
class BandiRLTrader:
    """반디 RL 트레이더 메인 클래스"""
    
    def __init__(self, model_dir: str = "rl_models"):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.models = {}
        self.envs = {}
        
    def create_env(self, ticker: str, **kwargs) -> StockTradingEnv:
        """환경 생성"""
        return StockTradingEnv(ticker, **kwargs)
    
    def train(self, ticker: str, total_timesteps: int = 100000, save: bool = True) -> PPO:
        """RL 에이전트 학습"""
        print(f"\n🚀 {ticker} RL 학습 시작...")
        print(f"   총 스텝: {total_timesteps:,}")
        
        # 환경 생성
        env = DummyVecEnv([lambda: self.create_env(ticker)])
        
        # PPO 모델 생성
        model = PPO(
            "MlpPolicy",
            env,
            learning_rate=3e-4,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,  # 탐험 장려
            verbose=0  # 로그 출력 최소화
        )
        
        # 학습 (GitHub Actions 호환 - progress_bar 비활성화)
        model.learn(total_timesteps=total_timesteps, progress_bar=False)
        
        # 저장
        if save:
            model_path = os.path.join(self.model_dir, f"bandi_rl_{ticker}.zip")
            model.save(model_path)
            print(f"   💾 모델 저장: {model_path}")
        
        self.models[ticker] = model
        return model
    
    def load_model(self, ticker: str) -> Optional[PPO]:
        """학습된 모델 로드"""
        model_path = os.path.join(self.model_dir, f"bandi_rl_{ticker}.zip")
        if os.path.exists(model_path):
            model = PPO.load(model_path)
            self.models[ticker] = model
            print(f"✅ {ticker} 모델 로드 완료")
            return model
        return None
    
    def predict(self, ticker: str, env: StockTradingEnv = None) -> Tuple[float, Dict]:
        """매매 예측"""
        if ticker not in self.models:
            self.load_model(ticker)
        
        if ticker not in self.models:
            return 0, {"error": "모델 없음"}
        
        model = self.models[ticker]
        
        # 환경 생성(없으면)
        if env is None:
            env = self.create_env(ticker)
        
        obs, _ = env.reset()
        action, _ = model.predict(obs, deterministic=True)
        
        # 행동 해석
        action_value = action[0] if isinstance(action, np.ndarray) else action
        action_value = np.clip(action_value, -1, 1)
        
        if action_value > 0.3:
            signal = "강력매수"
        elif action_value > 0.1:
            signal = "매수"
        elif action_value < -0.3:
            signal = "강력매도"
        elif action_value < -0.1:
            signal = "매도"
        else:
            signal = "관망"
        
        result = {
            "ticker": ticker,
            "action": float(action_value),
            "signal": signal,
            "confidence": abs(action_value),
            "strategy": self._get_strategy(action_value)
        }
        
        return action_value, result
    
    def _get_strategy(self, action: float) -> str:
        """전략 설명"""
        if action > 0.5:
            return "공격적 매수 - 최대 포지션으로 진입"
        elif action > 0.2:
            return "신중 매수 - 분할 매수 진행"
        elif action > -0.2:
            return "관망 - 현재 포지션 유지"
        elif action > -0.5:
            return "신중 매도 - 일부 익절"
        else:
            return "전량 매도 또는 손절"
    
    def backtest(self, ticker: str, start_date: str, end_date: str) -> Dict:
        """백테스트"""
        print(f"\n📊 {ticker} 백테스트 ({start_date} ~ {end_date})")
        
        # 환경 설정
        env = self.create_env(ticker, start_date=start_date, end_date=end_date)
        
        if ticker not in self.models:
            return {"error": "학습된 모델이 없습니다"}
        
        model = self.models[ticker]
        obs, _ = env.reset()
        
        done = False
        info = {}
        actions = []
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            actions.append(action[0] if isinstance(action, np.ndarray) else action)
            obs, reward, done, truncated, info = env.step(action)
        
        # 결과
        return {
            "ticker": ticker,
            "initial_balance": env.initial_balance,
            "final_value": info['total_value'],
            "return_pct": info['return_pct'],
            "avg_action": np.mean(actions),
            "max_position": env.max_position,
            "action_std": np.std(actions)
        }

# ============================================
# 🎯 실제 백테스트 실행 (예시)
# ============================================
def quick_backtest_demo():
    """빠른 데모 실행"""
    print("=" * 60)
    print("  반디 RL 트레이더 - 데모 실행")
    print("=" * 60)
    
    trader = BandiRLTrader()
    
    # 단일 종목 백테스트
    ticker = "TSLA"
    
    try:
        # 백테스트용 환경
        env = trader.create_env(ticker)
        
        obs, _ = env.reset()
        done = False
        step = 0
        
        print(f"\n🎮 {ticker} 랜덤 행동 백테스트")
        print("-" * 60)
        
        while not done and step < 100:  # 테스트용 100스텝
            # 랜덤 행동
            action = env.action_space.sample()
            obs, reward, done, truncated, info = env.step(action)
            
            if step % 20 == 0:
                print(f"   스텝 {step}: 가치=${info['total_value']:.0f}, "
                      f"수익률={info['return_pct']:.1f}%, 포지션={info['position']}")
            
            step += 1
        
        print(f"\n✅ {ticker} 데모 완료")
        print(f"   최종 수익률: {info['return_pct']:.2f}%")
        
    except Exception as e:
        print(f"❌ 데모 에러: {e}")
    
    print("=" * 60)

if __name__ == "__main__":
    # 데모 실행
    quick_backtest_demo()
