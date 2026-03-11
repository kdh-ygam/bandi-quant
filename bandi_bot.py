#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════╗
║  🤖 반디_봇 (Bandi_Bot) - 반디퀼_트레이드봇-beta1                     ║
║                                                                       ║
║  반디 알파 전략 기반 로컬 모의투자 트레이딩 봇                          ║
║  4단계 레이어: 뉴스 → 기술 → RL → 리스크                              ║
╚═══════════════════════════════════════════════════════════════════════╝

[사용법]
$ python bandi_bot.py --mode paper --interval 300

[모드]
- paper: 모의투자 (기본)
- live:  실제 매매 (⚠️ 주의)
"""

import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yfinance as yf
import torch
import torch.nn as nn
import numpy as np
import pandas as pd

# ═══════════════════════════════════════════════════════════════════════
# 설정
# ═══════════════════════════════════════════════════════════════════════
VERSION = "beta1"
NICKNAME = "반디_봇"
FULL_NAME = "반디퀼_트레이드봇-beta1"

# 목표 KPI
TARGET_ANNUAL_RETURN = "30~50%"
TARGET_SHARPE = "1.2+"
TARGET_WIN_RATE = "55~60%"

# 4단계 레이어 설정
CONFIG = {
    "news_sentiment_threshold": 0.8,
    "rsi_range": [40, 70],
    "vix_threshold": 25,
    "stop_loss": -0.05,      # -5%
    "take_profit_1": 0.10,   # +10%
    "take_profit_2": 0.20,   # +20%
    "initial_capital": 10000000,  # 1,000만원
    "max_positions": 10,
    "position_size": 0.1,    # 종목당 10%
}

# ═══════════════════════════════════════════════════════════════════════
# 로깅 설정
# ═══════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('bandi_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('반디_봇')

# ═══════════════════════════════════════════════════════════════════════
# 반디 알파 4단계 레이어
# ═══════════════════════════════════════════════════════════════════════

class Layer1_NewsFilter:
    """1단계: 뉴스 필터링 - Sentiment ≥ +0.8"""
    
    def check(self, ticker: str) -> Tuple[bool, float]:
        """뉴스 감성 분석"""
        # TODO: 실제 뉴스 API 연동
        # 임시: 랜덤 시뮬레이션
        import random
        sentiment = random.uniform(-1.0, 1.0)
        
        if sentiment >= CONFIG["news_sentiment_threshold"]:
            logger.info(f"[Layer1] ✅ {ticker}: Sentiment={sentiment:.2f} (≥{CONFIG['news_sentiment_threshold']})")
            return True, sentiment
        else:
            logger.info(f"[Layer1] ❌ {ticker}: Sentiment={sentiment:.2f} (미달)")
            return False, sentiment


class Layer2_Technical:
    """2단계: 기술적 확인 - Golden Cross + RSI 40~70 + VIX < 20"""
    
    def check(self, ticker: str) -> Tuple[bool, Dict]:
        """기술적 지표 확인"""
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="3mo")
            
            if len(df) < 50:
                return False, {"error": "데이터 부족"}
            
            # RSI 계산
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # Golden Cross (50일 > 200일)
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            golden_cross = ma50 > ma200
            
            # VIX 확인 (간단히 시뮬레이션, 실제로는 ^VIX 티커)
            vix = self._get_vix()
            
            result = {
                "rsi": round(current_rsi, 2),
                "golden_cross": golden_cross,
                "vix": vix,
                "ma50": round(ma50, 2),
                "ma200": round(ma200, 2)
            }
            
            # 조건 체크
            rsi_ok = CONFIG["rsi_range"][0] <= current_rsi <= CONFIG["rsi_range"][1]
            vix_ok = vix < CONFIG["vix_threshold"]
            
            if golden_cross and rsi_ok and vix_ok:
                logger.info(f"[Layer2] ✅ {ticker}: GoldenCross={golden_cross}, RSI={current_rsi:.1f}, VIX={vix:.1f}")
                return True, result
            else:
                logger.info(f"[Layer2] ❌ {ticker}: GoldenCross={golden_cross}, RSI={current_rsi:.1f}, VIX={vix:.1f}")
                return False, result
                
        except Exception as e:
            logger.error(f"[Layer2] ❌ {ticker}: 오류 - {e}")
            return False, {"error": str(e)}
    
    def _get_vix(self) -> float:
        """VIX 지수 (시뮬레이션 또는 실제)"""
        try:
            vix = yf.Ticker("^VIX")
            data = vix.history(period="1d")
            if not data.empty:
                return data['Close'].iloc[-1]
        except:
            pass
        return 15.0  # 기본값


class Layer3_RLAgent:
    """3단계: RL 에이전트 - PPO Action 선택"""
    
    ACTIONS = ["HOLD", "SMALL_BUY", "LARGE_BUY", "SELL_ALL"]
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.model = None
        if model_path and os.path.exists(model_path):
            # 실제 모델 로드
            pass
    
    def select_action(self, ticker: str, state: Dict) -> Tuple[str, float]:
        """PPO 기반 Action 선택"""
        # TODO: 실제 RL 모델 로드 및 추론
        # 임시: 신뢰도 기반 랜덤 선택
        import random
        
        confidence = random.uniform(0.5, 1.0)
        
        # 신뢰도가 높을수록 공격적 행동
        if confidence > 0.8:
            action = "LARGE_BUY"
        elif confidence > 0.6:
            action = "SMALL_BUY"
        elif confidence > 0.4:
            action = "HOLD"
        else:
            action = "SELL_ALL"
        
        logger.info(f"[Layer3] 🧠 {ticker}: Action={action} (Confidence={confidence:.2f})")
        return action, confidence


class Layer4_RiskManagement:
    """4단계: 리스크 관리 - -5% 손절, +10%/20% 익절"""
    
    def check_position(self, ticker: str, entry_price: float, current_price: float) -> str:
        """포지션 리스크 체크"""
        return_pct = (current_price - entry_price) / entry_price
        
        if return_pct <= CONFIG["stop_loss"]:
            logger.warning(f"[Layer4] 🚨 {ticker}: 손절 발생 {return_pct*100:.2f}%")
            return "STOP_LOSS"
        elif return_pct >= CONFIG["take_profit_2"]:
            logger.info(f"[Layer4] 🎯 {ticker}: 2차 익절 {return_pct*100:.2f}%")
            return "TAKE_PROFIT_2"
        elif return_pct >= CONFIG["take_profit_1"]:
            logger.info(f"[Layer4] 🎯 {ticker}: 1차 익절 {return_pct*100:.2f}%")
            return "TAKE_PROFIT_1"
        else:
            return "HOLD"
    
    def calculate_position_size(self, capital: float, action: str) -> int:
        """포지션 크기 계산"""
        if action == "LARGE_BUY":
            size = int(capital * CONFIG["position_size"] * 2)  # 2배
        elif action == "SMALL_BUY":
            size = int(capital * CONFIG["position_size"])
        else:
            size = 0
        return size


# ═══════════════════════════════════════════════════════════════════════
# 반디_봇 메인 클래스
# ═══════════════════════════════════════════════════════════════════════

class BandiBot:
    """반디_봇 - 반디 알파 기반 트레이딩 봇"""
    
    def __init__(self, mode: str = "paper"):
        self.mode = mode
        self.name = FULL_NAME
        self.nickname = NICKNAME
        
        # 4단계 레이어 초기화
        self.layer1 = Layer1_NewsFilter()
        self.layer2 = Layer2_Technical()
        self.layer3 = Layer3_RLAgent()
        self.layer4 = Layer4_RiskManagement()
        
        # 포트폴리오 (모의투자)
        self.portfolio = {}
        self.capital = CONFIG["initial_capital"]
        self.trade_history = []
        
        # 데이터 파일
        self.data_dir = Path("bandi_bot_data")
        self.data_dir.mkdir(exist_ok=True)
        
        logger.info(f"🤖 {self.name} ({self.nickname}) 초기화 완료")
        logger.info(f"💰 초기 자본: {self.capital:,}원")
        logger.info(f"📊 모드: {mode.upper()}")
    
    def run_4layer_strategy(self, ticker: str) -> Optional[Dict]:
        """반디 알파 4단계 전략 실행"""
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 {ticker} 분석 시작")
        logger.info(f"{'='*60}")
        
        # Layer 1: 뉴스 필터링
        news_ok, sentiment = self.layer1.check(ticker)
        if not news_ok:
            return None
        
        # Layer 2: 기술적 확인
        tech_ok, tech_data = self.layer2.check(ticker)
        if not tech_ok:
            return None
        
        # Layer 3: RL 에이전트
        action, confidence = self.layer3.select_action(ticker, tech_data)
        if action == "HOLD":
            logger.info(f"⏸️ {ticker}: 관망")
            return None
        
        # Layer 4: 리스크 체크 (진입 전)
        # TODO: 포지션 한도 체크
        
        return {
            "ticker": ticker,
            "action": action,
            "confidence": confidence,
            "sentiment": sentiment,
            **tech_data
        }
    
    def execute_paper_trade(self, signal: Dict) -> bool:
        """모의투자 매매 실행"""
        ticker = signal["ticker"]
        action = signal["action"]
        
        # 현재가 조회 (시뮬레이션)
        try:
            stock = yf.Ticker(ticker)
            price = stock.history(period="1d")['Close'].iloc[-1]
        except:
            price = 100000  # 기본값
        
        if action in ["SMALL_BUY", "LARGE_BUY"]:
            # 매수
            amount = self.layer4.calculate_position_size(self.capital, action)
            shares = int(amount / price)
            
            if shares > 0:
                self.portfolio[ticker] = {
                    "shares": shares,
                    "entry_price": price,
                    "entry_time": datetime.now().isoformat()
                }
                self.capital -= shares * price
                
                logger.info(f"💚 [PAPER] {ticker} 매수: {shares}주 @ {price:,.0f}원")
                
                self.trade_history.append({
                    "time": datetime.now().isoformat(),
                    "ticker": ticker,
                    "action": "BUY",
                    "shares": shares,
                    "price": price,
                    "mode": "PAPER"
                })
                return True
                
        elif action == "SELL_ALL":
            # 전량 매도
            if ticker in self.portfolio:
                pos = self.portfolio[ticker]
                shares = pos["shares"]
                entry = pos["entry_price"]
                return_pct = (price - entry) / entry * 100
                
                self.capital += shares * price
                del self.portfolio[ticker]
                
                logger.info(f"💔 [PAPER] {ticker} 매도: {shares}주 @ {price:,.0f}원 (수익률: {return_pct:.2f}%)")
                
                self.trade_history.append({
                    "time": datetime.now().isoformat(),
                    "ticker": ticker,
                    "action": "SELL",
                    "shares": shares,
                    "price": price,
                    "return_pct": return_pct,
                    "mode": "PAPER"
                })
                return True
        
        return False
    
    def check_existing_positions(self):
        """보유 포지션 리스크 체크"""
        for ticker, pos in list(self.portfolio.items()):
            try:
                stock = yf.Ticker(ticker)
                current_price = stock.history(period="1d")['Close'].iloc[-1]
                
                signal = self.layer4.check_position(
                    ticker, 
                    pos["entry_price"], 
                    current_price
                )
                
                if signal in ["STOP_LOSS", "TAKE_PROFIT_1", "TAKE_PROFIT_2"]:
                    # 익절/손절 실행
                    self.execute_paper_trade({
                        "ticker": ticker,
                        "action": "SELL_ALL"
                    })
                    
            except Exception as e:
                logger.error(f"리스크 체크 오류 {ticker}: {e}")
    
    def run_scan(self, tickers: List[str]):
        """종목 스캔 및 매매"""
        logger.info(f"\n{'🔥'*30}")
        logger.info(f"🔥 {self.name} 스캔 시작: {len(tickers)}개 종목")
        logger.info(f"{'🔥'*30}\n")
        
        # 1. 기존 포지션 리스크 체크
        self.check_existing_positions()
        
        # 2. 신규 진입 후보 스캔
        for ticker in tickers[:CONFIG["max_positions"] * 2]:
            if len(self.portfolio) >= CONFIG["max_positions"]:
                logger.info(f"⛔ 최대 포지션 도달 ({CONFIG['max_positions']}개)")
                break
            
            if ticker in self.portfolio:
                continue
            
            signal = self.run_4layer_strategy(ticker)
            if signal:
                self.execute_paper_trade(signal)
        
        # 결과 저장
        self.save_state()
        self.print_portfolio()
    
    def print_portfolio(self):
        """포트폴리오 출력"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 {self.nickname} 포트폴리오")
        logger.info(f"{'='*60}")
        logger.info(f"💰 현금: {self.capital:,.0f}원")
        logger.info(f"📈 보유 종목: {len(self.portfolio)}개")
        
        total_value = self.capital
        for ticker, pos in self.portfolio.items():
            try:
                stock = yf.Ticker(ticker)
                current_price = stock.history(period="1d")['Close'].iloc[-1]
                value = pos["shares"] * current_price
                return_pct = (current_price - pos["entry_price"]) / pos["entry_price"] * 100
                total_value += value
                logger.info(f"  • {ticker}: {pos['shares']}주 @ {current_price:,.0f}원 (수익률: {return_pct:+.2f}%)")
            except:
                pass
        
        logger.info(f"\n💵 총 자산: {total_value:,.0f}원")
        logger.info(f"📊 총 수익률: {(total_value - CONFIG['initial_capital']) / CONFIG['initial_capital'] * 100:+.2f}%")
        logger.info(f"{'='*60}\n")
    
    def save_state(self):
        """상태 저장"""
        state = {
            "version": VERSION,
            "timestamp": datetime.now().isoformat(),
            "capital": self.capital,
            "portfolio": self.portfolio,
            "trade_history": self.trade_history[-100:]  # 최근 100개
        }
        
        with open(self.data_dir / "bot_state.json", "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def load_state(self):
        """상태 복원"""
        try:
            with open(self.data_dir / "bot_state.json", "r", encoding="utf-8") as f:
                state = json.load(f)
                self.capital = state.get("capital", CONFIG["initial_capital"])
                self.portfolio = state.get("portfolio", {})
                logger.info(f"📂 이전 상태 로드 완료 ( capita: {self.capital:,.0f}원)")
        except FileNotFoundError:
            logger.info("📂 새로운 시작")


# ═══════════════════════════════════════════════════════════════════════
# 메인 실행
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description=FULL_NAME)
    parser.add_argument("--mode", choices=["paper", "live"], default="paper",
                       help="trading mode: paper (default) or live")
    parser.add_argument("--interval", type=int, default=300,
                       help="scan interval in seconds (default: 300s = 5min)")
    parser.add_argument("--tickers", type=str, default=None,
                       help="comma-separated tickers (default: test set)")
    
    args = parser.parse_args()
    
    # 반디퀀트 43종목 전체 리스트
    default_tickers = [
        # === 한국 종목 (22개) ===
        "005930.KS",   # 삼성전자
        "005935.KS",   # 삼성전자우
        "000660.KS",   # SK하이닉스
        "005380.KS",   # 현대차
        "000270.KS",   # 기아
        "006400.KS",   # 삼성SDI
        "010120.KS",   # LS일렉트릭
        "042700.KS",   # 한미반도체
        "051910.KS",   # LG화학
        "247540.KS",   # 에코프로비엠
        "009150.KS",   # 삼성전기
        "079550.KS",   # LIG넥스원
        "011200.KS",   # HMM
        "010130.KS",   # 고려아연
        "023530.KS",   # 롯데쇼핑
        "105560.KS",   # 미래에셋증권
        "055550.KS",   # 신한지주
        "086790.KS",   # 하나금융지주
        "032640.KS",   # LG유플러스
        "035420.KS",   # NAVER
        "035720.KS",   # 카카오
        "052690.KS",   # 한전KPS
        
        # === 미국 반도체 (3개) ===
        "NVDA",        # 엔비디아
        "AMD",         # AMD
        "ARM",         # ARM홀딩스
        
        # === 미국 테크/자동차 (9개) ===
        "TSLA",        # 테슬라
        "F",           # 포드
        "GM",          # 제너럴모터스
        "RIVN",        # 리비안
        "PLTR",        # 팰란티어
        "AI",          # C3.ai
        "SNOW",        # 스노우플레이크
        "CRWD",        # 크라우드스트라이크
        "ONON",        # On Holding
        
        # === 미국 기타 (9개) ===
        "NEE",         # 넥스트에라에너지
        "ENPH",        # 엔페이스에너지
        "SEDG",        # 솔라엣지
        "FSLR",        # 퍼스트솔라
        "RUN",         # 선런
        "BE",          # 블룸에너지
        "ALB",         # 알베마를
        "QS",          # 퀀텀스케이프
        "JNJ",         # 존슨앤드존슨
    ]
    
    if args.tickers:
        tickers = args.tickers.split(",")
    else:
        tickers = default_tickers
    
    logger.info(f"\n{'🚀'*20}")
    logger.info(f"🚀 {FULL_NAME} 시작 🚀")
    logger.info(f"🚀 버전: {VERSION}")
    logger.info(f"🚀 닉네임: {NICKNAME}")
    logger.info(f"🚀 모드: {args.mode.upper()}")
    logger.info(f"🚀 대상 종목: {len(tickers)}개")
    logger.info(f"{'🚀'*20}\n")
    
    # 봇 실행
    bot = BandiBot(mode=args.mode)
    bot.load_state()
    
    try:
        while True:
            bot.run_scan(tickers)
            logger.info(f"⏰ 다음 스캔까지 {args.interval}초 대기...")
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        logger.info(f"\n🛑 {NICKNAME} 종료됨")
        bot.save_state()
        
        # 최종 보고
        logger.info(f"\n{'='*60}")
        logger.info(f"📋 {NICKNAME} 최종 보고")
        logger.info(f"{'='*60}")
        logger.info(f"💰 최종 자본: {bot.capital:,.0f}원")
        logger.info(f"📊 총 거래 횟수: {len(bot.trade_history)}회")
        if bot.trade_history:
            returns = [t.get("return_pct", 0) for t in bot.trade_history if "return_pct" in t]
            if returns:
                logger.info(f"📈 평균 수익률: {sum(returns)/len(returns):.2f}%")
        logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
