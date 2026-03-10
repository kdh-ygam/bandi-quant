#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║              반디 RL 트레이더 (BANDI RL TRADER) v2.0 🔥             ║
║                                                                      ║
║  🤖 공격적 버전 - 거래 장려!                                       ║
║  • 보수적 보상 → 공격적 보상 변경                                  ║
║  • 관망 페널티 추가 (현금 보유 제한)                              ║
║  • 진입 타이밍 보너스 추가                                         ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import yfinance as yf
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import warnings

warnings.filterwarnings('ignore')

try:
    import gymnasium as gym
    from gymnasium import spaces
    from stable_baselines3 import PPO, DQN, A2C
    from stable_baselines3.common.vec_env import DummyVecEnv
    from stable_baselines3.common.callbacks import BaseCallback
    RL_AVAILABLE = True
except ImportError:
    print("⚠️ RL 프레임워크 미설치")
    RL_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# 43개 종목 리스트 (동일)
STOCKS = {
    "000660.KS": {"name": "SK하이닉스", "sector": "반도체"},
    "005930.KS": {"name": "삼성전자", "sector": "반도체"},
    "042700.KS": {"name": "한미반도체", "sector": "반도체"},
    "001740.KS": {"name": "SK스퀘어", "sector": "반도체"},
    "NVDA": {"name": "NVIDIA", "sector": "반도체"},
    "AMD": {"name": "AMD", "sector": "반도체"},
    "ARM": {"name": "ARM Holdings", "sector": "반도체"},
    "068270.KS": {"name": "셀트리온", "sector": "바이오"},
    "207940.KS": {"name": "삼성바이오로직스", "sector": "바이오"},
    "196170.KS": {"name": "알테오젠", "sector": "바이오"},
    "136480.KS": {"name": "하나제약", "sector": "바이오"},
    "JNJ": {"name": "Johnson & Johnson", "sector": "바이오"},
    "010120.KS": {"name": "LS ELECTRIC", "sector": "전력"},
    "267260.KS": {"name": "현대일렉트릭", "sector": "전력"},
    "051600.KS": {"name": "한전KPS", "sector": "전력"},
    "052690.KS": {"name": "한전기술", "sector": "전력"},
    "003670.KS": {"name": "포스코DX", "sector": "인프라"},
    "NEE": {"name": "NextEra Energy", "sector": "전력"},
    "TSLA": {"name": "Tesla", "sector": "자동차"},
    "005380.KS": {"name": "현대차", "sector": "자동차"},
    "000270.KS": {"name": "기아", "sector": "자동차"},
    "012330.KS": {"name": "현대모비스", "sector": "자동차"},
    "003620.KS": {"name": "KG모빌리티", "sector": "자동차"},
    "F": {"name": "Ford", "sector": "자동차"},
    "GM": {"name": "General Motors", "sector": "자동차"},
    "RIVN": {"name": "Rivian", "sector": "자동차"},
    "373220.KS": {"name": "LG에너지솔루션", "sector": "배터리"},
    "006400.KS": {"name": "삼성SDI", "sector": "배터리"},
    "005490.KS": {"name": "POSCO홀딩스", "sector": "배터리"},
    "247540.KS": {"name": "에코프로비엠", "sector": "배터리"},
    "ALB": {"name": "Albemarle", "sector": "배터리"},
    "QS": {"name": "QuantumScape", "sector": "배터리"},
    "ENPH": {"name": "Enphase Energy", "sector": "클린에너지"},
    "SEDG": {"name": "SolarEdge", "sector": "클린에너지"},
    "FSLR": {"name": "First Solar", "sector": "클린에너지"},
    "RUN": {"name": "Sunrun", "sector": "클린에너지"},
    "BE": {"name": "Bloom Energy", "sector": "클린에너지"},
    "PLTR": {"name": "Palantir", "sector": "AI"},
    "AI": {"name": "C3.ai", "sector": "AI"},
    "SNOW": {"name": "Snowflake", "sector": "AI"},
    "CRWD": {"name": "CrowdStrike", "sector": "AI"},
    "ONON": {"name": "ONON", "sector": "AI"},
}

class TechnicalIndicators:
    """기술적 지표 계산기 (동일)"""
    
    @staticmethod
    def calculate_all(df):
        """모든 지표 계산"""
        df = df.copy()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_fast = df['Close'].ewm(span=12, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 볼린저 밴드
        df['bb_middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_position'] = (df['Close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # 이동평균 비율
        df['ma_ratio'] = df['Close'] / df['Close'].rolling(window=20).mean()
        
        # 거래량 비율
        df['volume_ratio'] = df['Volume'] / df['Volume'].rolling(window=20).mean()
        
        # 수익률
        df['return_1d'] = df['Close'].pct_change(1)
        df['return_5d'] = df['Close'].pct_change(5)
        
        # 변동성
        df['volatility'] = df['return_1d'].rolling(window=20).std()
        
        return df


class StockTradingEnv(gym.Env):
    """공격적 버전 주식 거래 환경"""
    
    metadata = {'render_modes': ['human']}
    
    def __init__(self, ticker, initial_balance=10000, max_position=100, 
                 window_size=30, start_date=None, end_date=None):
        super().__init__()
        
        self.ticker = ticker
        self.initial_balance = initial_balance
        self.max_position = max_position
        self.window_size = window_size
        self.render_mode = 'human'
        
        # 데이터 로드 (⭐ Rate Limit 대비)
        for attempt in range(3):
            try:
                self.df = self._load_data(start_date, end_date)
                if self.df is not None and len(self.df) >= window_size * 2:
                    break
            except Exception as e:
                if "Rate limited" in str(e) and attempt < 2:
                    print(f"    ⏳ Rate limited, waiting {60 * (attempt + 1)}s...")
                    time.sleep(60 * (attempt + 1))
                else:
                    raise
        
        if self.df is None or len(self.df) < window_size * 2:
            raise ValueError(f"데이터 부족: {ticker}")
        
        self.df = TechnicalIndicators.calculate_all(self.df).dropna()
        
        # ⭐ 공격적 설정: 진입 타이밍 강화
        self.entry_bonus_window = 5  # 진입 후 5일 보�스
        self.no_trade_penalty = -0.1  # 관망 페널티
        self.consecutive_no_trade = 0  # 연속 관망 카운트
        
        # 상태 공간
        n_features = 15
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, 
            shape=(window_size, n_features), 
            dtype=np.float32
        )
        
        # 행동 공간: [-1, 1] (매도~매수)
        self.action_space = spaces.Box(
            low=-1, high=1, shape=(1,), dtype=np.float32
        )
        
        # 포트폴리오 상태
        self.balance = initial_balance
        self.position = 0
        self.current_step = window_size
        self.total_value = initial_balance
        self.value_history = []
        self.entry_price = 0  # 진입가 기록
        self.days_in_position = 0  # 보유일수
        
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
        """현재 상태 반환"""
        start_idx = self.current_step - self.window_size
        end_idx = self.current_step
        
        window_data = self.df.iloc[start_idx:end_idx]
        
        features = []
        
        # 기술적 지표 (10개)
        for col in ['rsi', 'macd', 'macd_hist', 'bb_position', 'ma_ratio',
                   'volume_ratio', 'return_1d', 'return_5d', 'volatility', 'Close']:
            if col in window_data.columns:
                vals = window_data[col].values
                if col == 'Close':
                    vals = vals / vals[0] - 1
                elif col == 'rsi':
                    vals = (vals - 50) / 50
                elif col in ['macd', 'macd_hist']:
                    close = window_data['Close'].values
                    vals = vals / close
                features.append(vals)
            else:
                features.append(np.zeros(self.window_size))
        
        # 시장 데이터 (3개)
        for _ in range(3):
            features.append(np.full(self.window_size, 0.0))
        
        # 포트폴리오 상태 (2개)
        position_ratio = self.position / self.max_position if self.max_position > 0 else 0
        for pf in [position_ratio, self.balance / self.initial_balance - 1]:
            features.append(np.full(self.window_size, pf))
        
        obs = np.column_stack(features).astype(np.float32)
        return obs
    
    def reset(self, seed=None, options=None):
        """환경 초기화"""
        super().reset(seed=seed)
        
        self.current_step = self.window_size
        self.balance = self.initial_balance
        self.position = 0
        self.total_value = self.initial_balance
        self.value_history = []
        self.entry_price = 0
        self.days_in_position = 0
        self.consecutive_no_trade = 0
        
        return self._get_observation(), {}
    
    def step(self, action):
        """한 스텝 진행 (⭐ 공격적 보상)"""
        action = np.clip(action[0], -1, 1)
        
        current_price = float(self.df['Close'].iloc[self.current_step])
        prev_value = self.total_value
        
        # 목표 포지션 계산
        target_position = int(action * self.max_position)
        position_diff = target_position - self.position
        
        # 거래 실행
        trade_executed = False
        if position_diff > 0:  # 매수
            cost = position_diff * current_price
            if cost <= self.balance:
                self.position += position_diff
                self.balance -= cost
                self.entry_price = current_price  # 진입가 기록
                self.days_in_position = 0
                trade_executed = True
                self.consecutive_no_trade = 0
        elif position_diff < 0:  # 매도
            sell_shares = min(abs(position_diff), self.position)
            if sell_shares > 0:
                revenue = sell_shares * current_price
                self.position -= sell_shares
                self.balance += revenue
                trade_executed = True
                self.consecutive_no_trade = 0
                self.entry_price = 0
                self.days_in_position = 0
        
        # 연속 관망 카운트
        if not trade_executed and self.position == 0:
            self.consecutive_no_trade += 1
        
        # 포지션 보유일수 증가
        if self.position > 0:
            self.days_in_position += 1
        
        # 포트폴리오 가치 업데이트
        self.total_value = self.balance + self.position * current_price
        self.value_history.append(self.total_value)
        
        # ⭐ 공격적 보상 계산
        base_reward = 0
        
        # 1. 수익률 보상 (스케일 업)
        if len(self.value_history) > 1:
            return_pct = (self.value_history[-1] - self.value_history[-2]) / self.value_history[-2]
            base_reward = return_pct * 200  # ⭐ 2배로 증가 (100 → 200)
        
        # 2. 거래 보너스 (거래 장려)
        trade_bonus = 0
        if trade_executed:
            trade_bonus = 0.5  # ⭐ 거래 시 보�스
        
        # 3. 진입 타이밍 보너스
        entry_bonus = 0
        if self.position > 0 and self.days_in_position <= self.entry_bonus_window:
            # 진입 직후 수익 보너스
            profit_pct = (current_price - self.entry_price) / self.entry_price if self.entry_price > 0 else 0
            if profit_pct > 0:
                entry_bonus = profit_pct * 100  # 수익 보너스
        
        # 4. ⭐ 관망 페널티 (현금 보유 제한)
        no_trade_penalty = 0
        if self.position == 0 and not trade_executed:
            no_trade_penalty = self.no_trade_penalty * min(self.consecutive_no_trade, 10)
        
        # 5. 포지션 유지 보너스 (상승 추세)
        trend_bonus = 0
        if self.position > 0:
            # 상승 추세일 때 포지션 유지 보너스
            rsi = self.df['rsi'].iloc[self.current_step]
            ma_ratio = self.df['ma_position'].iloc[self.current_step] if 'ma_position' in self.df.columns else 1.0
            if rsi > 50 and ma_ratio > 1.0:
                trend_bonus = 0.2  # 상승 추세 보너스
        
        # 최종 보상
        reward = base_reward + trade_bonus + entry_bonus + no_trade_penalty + trend_bonus
        
        # 다음 스텝
        self.current_step += 1
        done = self.current_step >= len(self.df) - 1
        truncated = False
        
        obs = self._get_observation()
        info = {
            'total_value': self.total_value,
            'return_pct': (self.total_value - self.initial_balance) / self.initial_balance * 100,
            'position': self.position,
            'price': current_price,
            'trade_executed': trade_executed
        }
        
        return obs, reward, done, truncated, info
    
    def render(self):
        """현재 상태 출력"""
        if self.render_mode == 'human':
            print(f"Step: {self.current_step}, Value: ${self.total_value:.2f}, "
                  f"Return: {(self.total_value/self.initial_balance-1)*100:.2f}%, "
                  f"Position: {self.position}")


# ============================================
# 🤖 RL 트레이더 (공격적 버전)
# ============================================
class BandiRLTrader:
    """반디 RL 트레이더 v2.0"""
    
    def __init__(self, model_dir: str = "rl_models_v2"):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.models = {}
        self.envs = {}
        
    def create_env(self, ticker: str, **kwargs) -> StockTradingEnv:
        """환경 생성"""
        return StockTradingEnv(ticker, **kwargs)
    
    def train(self, ticker: str, total_timesteps: int = 50000, save: bool = True):
        """RL 에이전트 학습 (공격적 버전)"""
        print(f"\n🚀 {ticker} RL 학습 시작 (v2.0 공격적)...")
        print(f"   총 스텝: {total_timesteps:,}")
        
        # ⭐ Rate Limit 대비
        time.sleep(2)
        
        env = DummyVecEnv([lambda: self.create_env(ticker)])
        
        # ⭐ 공격적 학습 설정
        model = PPO(
            "MlpPolicy",
            env,
            learning_rate=5e-4,  # ⭐ 더 높은 학습률
            n_steps=1024,         # ⭐ 더 자주 업데이트
            batch_size=64,
            n_epochs=10,
            gamma=0.98,          # ⭐ 단기 보상 더 중시
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.05,       # ⭐ 탐색 장려
            verbose=0
        )
        
        # 학습
        model.learn(total_timesteps=total_timesteps, progress_bar=False)
        
        if save:
            model_path = f"{self.model_dir}/bandi_rl_{ticker}"
            model.save(model_path)
            
            # ZIP 파일로 압축
            import zipfile
            zip_path = f"{model_path}.zip"
            print(f"   💾 모델 저장: {zip_path}")
        
        return model


if __name__ == '__main__':
    trader = BandiRLTrader()
    model = trader.train("AAPL", total_timesteps=10000)
