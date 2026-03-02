#!/usr/bin/env python3
"""
반디 퀀트 - 머신러닝 모델 v1.0
Random Forest 기반 방향 예측
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import os

class StockPredictor:
    """주가 방향 예측 모델"""
    
    def __init__(self, model_path="../models/stock_model.pkl"):
        self.model = None
        self.model_path = model_path
        self.feature_names = []
        self.accuracy = 0
    
    def prepare_data(self, df, feature_cols, target_col='target'):
        """학습 데이터 준비"""
        # NaN 제거
        df_clean = df.dropna()
        
        X = df_clean[feature_cols]
        y = df_clean[target_col]
        
        return X, y, df_clean
    
    def train(self, X, y, test_size=0.2):
        """모델 학습"""
        print(f"🤖 모델 학습 시작...")
        print(f"   전체 샘플: {len(X)}개")
        
        # 데이터 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False  # 시간 순서 유지
        )
        
        print(f"   학습: {len(X_train)}개, 테스트: {len(X_test)}개")
        
        # Random Forest (개선된 정규화)
        self.model = RandomForestClassifier(
            n_estimators=200,           # 더 많은 트리
            max_depth=5,                # 얕은 트리로 과적합 방지
            min_samples_split=20,       # 분할 최소 샘플 증가
            min_samples_leaf=10,        # 리프 최소 샘플 증가
            max_features='sqrt',        # 특성 서브샘플링
            bootstrap=True,
            random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        # 성능 평가
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)
        
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        
        print(f"\n📊 학습 결과:")
        print(f"   학습 정확도: {train_acc:.1%}")
        print(f"   테스트 정확도: {test_acc:.1%}")
        print(f"   Precision: {precision_score(y_test, test_pred):.1%}")
        print(f"   Recall: {recall_score(y_test, test_pred):.1%}")
        
        self.accuracy = test_acc
        self.feature_names = X.columns.tolist()
        
        return self.model
    
    def predict(self, X):
        """예측 실행"""
        if self.model is None:
            raise ValueError("모델이 학습되지 않았습니다!")
        
        prediction = self.model.predict(X)
        probability = self.model.predict_proba(X)
        
        return prediction, probability
    
    def feature_importance(self):
        """특성 중요도 분석"""
        if self.model is None:
            return None
        
        importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return importance
    
    def save_model(self):
        """모델 저장"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'feature_names': self.feature_names,
            'accuracy': self.accuracy
        }, self.model_path)
        print(f"💾 모델 저장: {self.model_path}")
    
    def load_model(self):
        """모델 로드"""
        if os.path.exists(self.model_path):
            data = joblib.load(self.model_path)
            self.model = data['model']
            self.feature_names = data['feature_names']
            self.accuracy = data['accuracy']
            print(f"📂 모델 로드: {self.model_path}")
            print(f"   정확도: {self.accuracy:.1%}")
            return True
        return False

if __name__ == "__main__":
    import sys
    sys.path.append('../data')
    
    from collector import DataCollector
    from features import FeatureEngineer
    
    # 데이터 수집
    collector = DataCollector()
    df = collector.fetch_stock("PLTR", period="1y")
    
    if df is not None:
        # 특성 생성
        featurizer = FeatureEngineer()
        df_features = featurizer.create_features(df)
        feature_cols = featurizer.get_feature_columns()
        
        # 모델 학습
        predictor = StockPredictor()
        X, y, _ = predictor.prepare_data(df_features, feature_cols)
        predictor.train(X, y)
        
        # 특성 중요도
        importance = predictor.feature_importance()
        print(f"\n🔍 특성 중요도 TOP 5:")
        print(importance.head())
        
        # 모델 저장
        predictor.save_model()
        
        # 최신 예측
        latest = X.iloc[-1:]
        pred, prob = predictor.predict(latest)
        print(f"\n🔮 다음 5일 예측:")
        print(f"   방향: {'상승' if pred[0] == 1 else '하�'}")
        print(f"   신뢰도: {prob[0][pred[0]]:.1%}")
