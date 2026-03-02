#!/usr/bin/env python3
"""
반디 퀀트 - 앙상블 예측 모듈 v2.0
Phase 2: XGBoost + Random Forest 앙상블
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import warnings
warnings.filterwarnings('ignore')

# XGBoost 설치 확인
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    print("⚠️  XGBoost 없음. pip install xgboost 필요")
    XGBOOST_AVAILABLE = False

class EnsemblePredictor:
    """앙상블 예측기 (XGBoost + Random Forest)"""
    
    def __init__(self, model_path='../models/ensemble_model.pkl'):
        self.model_path = model_path
        self.rf_model = None
        self.xgb_model = None
        self.feature_names = []
        self.rf_weight = 0.4
        self.xgb_weight = 0.6
        self.accuracy = 0
    
    def prepare_data(self, df, feature_cols, target_col='target'):
        """데이터 준비"""
        df_clean = df[feature_cols + [target_col]].dropna()
        
        X = df_clean[feature_cols]
        y = df_clean[target_col]
        
        self.feature_names = feature_cols
        return X, y, df_clean
    
    def train(self, X, y):
        """앙상블 모델 학습"""
        print(f"\n🤖 앙상블 모델 학습 시작...")
        print(f"   전체 샘플: {len(X)}개")
        
        # 데이터 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False, random_state=42
        )
        
        print(f"   학습: {len(X_train)}개, 테스트: {len(X_test)}개")
        
        # 1. Random Forest (Regularized)
        print("\n🌲 Random Forest 학습 중...")
        self.rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=5,              # 과적합 방지
            min_samples_split=20,     # 리프 노드 분할 최소 샘플
            min_samples_leaf=10,      # 리프 노드 최소 샘플
            max_features='sqrt',       # 특성 서브샘플링
            bootstrap=True,
            random_state=42
        )
        self.rf_model.fit(X_train, y_train)
        rf_pred = self.rf_model.predict(X_test)
        rf_acc = accuracy_score(y_test, rf_pred)
        print(f"   RF 정확도: {rf_acc:.1%}")
        
        # 2. XGBoost (with regularization)
        if XGBOOST_AVAILABLE:
            print("\n⚡ XGBoost 학습 중...")
            self.xgb_model = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=4,              # 얕은 트리
                learning_rate=0.05,       # 보수적인 학습
                subsample=0.8,            # 데이터 서브샘플링
                colsample_bytree=0.8,     # 특성 서브샘플링
                reg_alpha=0.5,            # L1 정규화
                reg_lambda=1.0,           # L2 정규화
                random_state=42
            )
            self.xgb_model.fit(X_train, y_train)
            xgb_pred = self.xgb_model.predict(X_test)
            xgb_acc = accuracy_score(y_test, xgb_pred)
            print(f"   XGB 정확도: {xgb_acc:.1%}")
        else:
            # XGBoost 없으면 RF 2개로 앙상블
            self.xgb_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=6,
                min_samples_split=10,
                random_state=24
            )
            self.xgb_model.fit(X_train, y_train)
            xgb_pred = self.xgb_model.predict(X_test)
            xgb_acc = accuracy_score(y_test, xgb_pred)
            print(f"   RF2 정확도: {xgb_acc:.1%}")
        
        # 3. 앙상블 평가
        print(f"\n🎯 앙상블 평가 (가중치: RF {self.rf_weight:.0%}, XGB {self.xgb_weight:.0%})")
        ensemble_pred = self._ensemble_predict(X_test)
        ensemble_acc = accuracy_score(y_test, ensemble_pred)
        
        # 정확도 저장
        self.accuracy = ensemble_acc
        
        print(f"\n📊 최종 결과:")
        print(f"   앙상블 정확도: {ensemble_acc:.1%}")
        print(f"   Precision: {classification_report(y_test, ensemble_pred, output_dict=True)['1']['precision']:.1%}")
        print(f"   Recall: {classification_report(y_test, ensemble_pred, output_dict=True)['1']['recall']:.1%}")
        
        return ensemble_acc
    
    def _ensemble_predict(self, X):
        """앙상블 예측"""
        # 각 모델 확률
        rf_prob = self.rf_model.predict_proba(X)
        xgb_prob = self.xgb_model.predict_proba(X)
        
        # 가중 평균
        ensemble_prob = (rf_prob * self.rf_weight + xgb_prob * self.xgb_weight)
        ensemble_pred = np.argmax(ensemble_prob, axis=1)
        
        return ensemble_pred
    
    def predict(self, X):
        """예측 수행"""
        # 확률 반환
        rf_prob = self.rf_model.predict_proba(X)
        xgb_prob = self.xgb_model.predict_proba(X)
        
        ensemble_prob = (rf_prob * self.rf_weight + xgb_prob * self.xgb_weight)
        predictions = np.argmax(ensemble_prob, axis=1)
        
        return predictions, ensemble_prob
    
    def feature_importance(self):
        """특성 중요도 (XGBoost 기준)"""
        if hasattr(self.xgb_model, 'feature_importances_'):
            importance = self.xgb_model.feature_importances_
        else:
            importance = self.rf_model.feature_importances_
        
        df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return df
    
    def save_model(self):
        """모델 저장"""
        if self.rf_model is not None and self.xgb_model is not None:
            # 디렉토리 생성
            import os
            os.makedirs(os.path.dirname(self.model_path) if os.path.dirname(self.model_path) else '.', exist_ok=True)
            joblib.dump({
                'rf_model': self.rf_model,
                'xgb_model': self.xgb_model,
                'feature_names': self.feature_names,
                'rf_weight': self.rf_weight,
                'xgb_weight': self.xgb_weight,
                'accuracy': self.accuracy
            }, self.model_path)
            print(f"💾 앙상블 모델 저장: {self.model_path}")
    
    def load_model(self):
        """모델 로드"""
        import os
        if os.path.exists(self.model_path):
            data = joblib.load(self.model_path)
            self.rf_model = data['rf_model']
            self.xgb_model = data['xgb_model']
            self.feature_names = data['feature_names']
            self.rf_weight = data['rf_weight']
            self.xgb_weight = data['xgb_weight']
            self.accuracy = data['accuracy']
            print(f"✅ 모델 로드: 정확도 {self.accuracy:.1%}")
            return True
        else:
            print(f"⚠️  모델 없음: {self.model_path}")
            return False

if __name__ == "__main__":
    import sys
    sys.path.append('../data')
    from collector import DataCollector
    from features import FeatureEngineer
    
    # 데이터 수집
    collector = DataCollector()
    df = collector.fetch_stock("SPY", period="2y")
    
    if df is not None:
        # 특성 생성
        featurizer = FeatureEngineer()
        df_features = featurizer.create_features(df)
        feature_cols = featurizer.get_feature_columns()
        
        # 모델 학습
        predictor = EnsemblePredictor(model_path='../models/ensemble_model.pkl')
        X, y, _ = predictor.prepare_data(df_features, feature_cols)
        accuracy = predictor.train(X, y)
        predictor.save_model()
        
        # 특성 중요도
        print(f"\n4️⃣ 특성 중요도 TOP 5:")
        importance = predictor.feature_importance()
        for _, row in importance.head().iterrows():
            print(f"   {row['feature']}: {row['importance']:.3f}")
