#!/usr/bin/env python3
"""
반디 퀀트 - 통합 메인 실행 시스템 v2.0
앙상블 모델 지원
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'data'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'models'))

from collector import DataCollector
from features import FeatureEngineer
from ensemble_predictor import EnsemblePredictor

class BandiQuantSystemV2:
    """반디 퀀트 v2.0 - 앙상블 모델"""
    
    def __init__(self):
        self.collector = DataCollector()
        self.featurizer = FeatureEngineer()
        self.predictor = EnsemblePredictor()
        self.predictions = []
    
    def train(self, ticker='SPY'):
        """모델 학습"""
        print("=" * 50)
        print("🤖 반디 퀀트 v2.0 - 앙상블 학습")
        print("=" * 50)
        
        # 데이터 수집
        print(f"\n1️⃣ 데이터 수집: {ticker}")
        df = self.collector.fetch_stock(ticker, period="2y")
        
        if df is None:
            print("❌ 데이터 수집 실패")
            return False
        
        # 특성 생성
        print(f"\n2️⃣ 특성 생성")
        df_features = self.featurizer.create_features(df)
        feature_cols = self.featurizer.get_feature_columns()
        print(f"   특성 수: {len(feature_cols)}개")
        
        # 모델 학습
        print(f"\n3️⃣ 앙상블 모델 학습")
        X, y, _ = self.predictor.prepare_data(df_features, feature_cols)
        self.predictor.train(X, y)
        
        # 특성 중요도
        importance = self.predictor.feature_importance()
        print(f"\n4️⃣ 특성 중요도 TOP 5:")
        for _, row in importance.head(5).iterrows():
            print(f"   {row['feature']}: {row['importance']:.3f}")
        
        # 모델 저장
        self.predictor.save_model()
        print(f"\n✅ 앙상블 모델 학습 완료!")
        return True
    
    def predict(self, tickers=None):
        """종목 예측"""
        if tickers is None:
            tickers = ['PLTR', 'TSLA', 'NVDA', 'TE', 'ENPH']
        
        print("=" * 50)
        print("🔮 반디 앙상블 예측")
        print("=" * 50)
        
        self.predictions = []
        
        for ticker in tickers:
            print(f"\n📊 분석 중: {ticker}")
            
            try:
                # 데이터 수집
                df = self.collector.fetch_stock(ticker, period="6mo")
                if df is None:
                    continue
                
                # 특성 생성
                df_features = self.featurizer.create_features(df)
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
                    'model_accuracy': self.predictor.accuracy
                }
                
                self.predictions.append(prediction_result)
                
                # 출력
                direction = "📈 상승" if pred_value == 1 else "📉 하락"
                print(f"   {direction} {prob_value:.1%}")
                
            except Exception as e:
                print(f"   ❌ 오류: {e}")
        
        print(f"\n✅ 예측 완료: {len(self.predictions)}개 종목")
        return self.predictions

if __name__ == "__main__":
    system = BandiQuantSystemV2()
    
    # 먼저 학습
    print("\n🎓 모델 학습 모드")
    if system.train('SPY'):
        # 학습 후 예측
        print("\n🔮 종목 예측 모드")
        system.predict(['PLTR', 'TSLA', 'NVDA', 'TE', 'ENPH'])
