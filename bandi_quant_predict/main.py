#!/usr/bin/env python3
"""
반디 퀀트 - 메인 실행 시스템 v1.0
전체 파이프라인 관리
"""

import sys
import os
import json
from datetime import datetime

# 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'data'))
sys.path.append(os.path.join(BASE_DIR, 'models'))
sys.path.append(os.path.join(BASE_DIR, 'backtest'))
sys.path.append(os.path.join(BASE_DIR, 'telegram'))

from collector import DataCollector
from features import FeatureEngineer
from predictor import StockPredictor
from backtester import Backtester
from bot import TelegramBot

class BandiQuantSystem:
    """반디 퀀트 메인 시스템"""
    
    def __init__(self, config_path='config/settings.yaml'):
        # 하드코딩된 설정 (yaml 없이)
        self.config = {
            'tickers': {
                'core': ['PLTR', 'TSLA', 'NVDA', 'TE', 'ENPH'],
                'korean': ['005930.KS', '000660.KS', '005380.KS']
            },
            'model': {'type': 'random_forest'},
            'trading': {'initial_capital': 100000}
        }
        
        self.collector = DataCollector(
            cache_dir=os.path.join(BASE_DIR, 'data/cache')
        )
        self.featurizer = FeatureEngineer()
        self.predictor = StockPredictor(
            model_path=os.path.join(BASE_DIR, 'models/bandi_model.pkl')
        )
        self.telegram = TelegramBot()
        
        self.predictions = []
    
    def train_model(self, ticker='SPY'):
        """모델 학습"""
        print("=" * 50)
        print("🤖 반디 퀀트 - 모델 학습")
        print("=" * 50)
        
        # 예시 데이터로 학습 (S&P 500)
        print(f"\n1️⃣ 데이터 수집: {ticker}")
        df = self.collector.fetch_stock(ticker, period='2y')
        
        if df is None:
            print("❌ 데이터 수집 실패")
            return False
        
        # 특성 생성
        print(f"\n2️⃣ 특성 생성")
        df_features = self.featurizer.create_features(df, future_days=5)
        feature_cols = self.featurizer.get_feature_columns()
        
        # 모델 학습
        print(f"\n3️⃣ 모델 학습")
        X, y, _ = self.predictor.prepare_data(df_features, feature_cols)
        self.predictor.train(X, y)
        
        # 특성 중요도
        importance = self.predictor.feature_importance()
        print(f"\n4️⃣ 특성 중요도 TOP 5:")
        for _, row in importance.head().iterrows():
            print(f"   {row['feature']}: {row['importance']:.3f}")
        
        # 모델 저장
        self.predictor.save_model()
        print(f"\n✅ 모델 학습 완료!")
        return True
    
    def predict_stocks(self, tickers=None):
        """종목 예측"""
        if tickers is None:
            tickers = self.config['tickers']['core']
        
        print("=" * 50)
        print("🔮 반디 예측 시스템")
        print("=" * 50)
        
        self.predictions = []
        
        for ticker in tickers:
            print(f"\n📊 분석 중: {ticker}")
            
            try:
                # 데이터 수집
                df = self.collector.fetch_stock(ticker, period='6mo')
                if df is None:
                    continue
                
                # 특성 생성
                df_features = self.featurizer.create_features(df, future_days=5)
                feature_cols = self.featurizer.get_feature_columns()
                
                # 최신 데이터
                latest_data = df_features[feature_cols].iloc[-1:]
                latest_price = df_features['close'].iloc[-1]
                latest_rsi = df_features['rsi'].iloc[-1]
                
                # 예측
                pred, prob = self.predictor.predict(latest_data)
                pred_value = pred[0]
                prob_value = prob[0][pred_value]
                
                prediction_result = {
                    'ticker': ticker,
                    'price': latest_price,
                    'prediction': pred_value,
                    'probability': prob_value,
                    'rsi': latest_rsi,
                    'ma_ratio': df_features['ma_ratio'].iloc[-1],
                    'model_accuracy': self.predictor.accuracy
                }
                
                self.predictions.append(prediction_result)
                
                # 출력
                direction = "📈 상승" if pred_value == 1 else "📉 하�"
                print(f"   {direction} {prob_value:.1%}")
                
            except Exception as e:
                print(f"   ❌ 오류: {e}")
        
        print(f"\n✅ 예측 완료: {len(self.predictions)}개 종목")
        return self.predictions
    
    def run_backtest(self, ticker='SPY'):
        """백테스트 실행"""
        print("=" * 50)
        print("📈 반디 백테스트")
        print("=" * 50)
        
        # 데이터 수집
        df = self.collector.fetch_stock(ticker, period='2y')
        if df is None:
            return None
        
        # 특성 생성
        df_features = self.featurizer.create_features(df)
        feature_cols = self.featurizer.get_feature_columns()
        
        # 모델 예측
        X, y, df_clean = self.predictor.prepare_data(df_features, feature_cols)
        predictions, probabilities = self.predictor.predict(X)
        
        # 신호 생성 (신뢰도 60% 이상)
        signals = []
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            prob_val = prob[pred]
            if prob_val > 0.60:
                signals.append(1 if pred == 1 else -1)
            else:
                signals.append(0)
        
        signals_series = pd.Series(signals, index=X.index)
        
        # 백테스트
        backtest = Backtester(initial_capital=100000)
        metrics, equity_df, trades_df = backtest.run_strategy(
            df_clean, signals_series
        )
        
        backtest.print_report(metrics)
        
        return metrics, equity_df
    
    def send_briefing(self):
        """브리핑 전송"""
        print("=" * 50)
        print("📱 반디 브리핑 전송")
        print("=" * 50)
        
        if not self.predictions:
            print("❌ 예측 데이터 없음")
            return False
        
        # 연결 테스트
        if not self.telegram.test_connection():
            print("❌ 텔레그램 연결 실패")
            return False
        
        # 브리핑 전송
        result = self.telegram.send_prediction_alert(self.predictions)
        
        if result:
            print("✅ 브리핑 전송 완료!")
            return True
        else:
            print("❌ 브리핑 전송 실패")
            return False
    
    def run_pipeline(self, mode='predict'):
        """
        전체 파이프라인 실행
        mode: 'train', 'predict', 'backtest', 'briefing'
        """
        print("\n" + "=" * 50)
        print("🐾 반디 퀀트 예측 시스템 v1.0")
        print("=" * 50)
        
        if mode == 'train':
            # 모델 학습
            self.train_model()
            
        elif mode == 'predict':
            # 예측 실행
            if not self.predictor.load_model():
                print("⚠️  학습된 모델 없음. 먼저 학습 필요!")
                self.train_model()
            
            self.predict_stocks()
            
        elif mode == 'backtest':
            # 백테스트
            self.run_backtest()
            
        elif mode == 'briefing':
            # 예측 + 브리핑
            if not self.predictor.load_model():
                self.train_model()
            
            self.predict_stocks()
            self.send_briefing()
            
        elif mode == 'full':
            # 전체 실행
            self.train_model()
            self.run_backtest()
            self.predict_stocks()
            self.send_briefing()
        
        print("\n" + "=" * 50)
        print("✅ 파이프라인 완료!")
        print("=" * 50)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='반디 퀀트 예측 시스템')
    parser.add_argument('--mode', default='predict', 
                       choices=['train', 'predict', 'backtest', 'briefing', 'full'],
                       help='실행 모드')
    
    args = parser.parse_args()
    
    # 시스템 실행
    system = BandiQuantSystem()
    system.run_pipeline(mode=args.mode)
