#!/usr/bin/env python3
"""
반디 퀀트 - 통합 예측 모듈 v3.0
Phase 3: 기술적 + 감정 특성 통합
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data'))

import pandas as pd
import numpy as np
import time

# Import after path setup
from collector import DataCollector
from features import FeatureEngineer
from news_sentiment import NewsSentimentAnalyzer
from predictor import StockPredictor

class IntegratedPredictor:
    """기술적 + 뉴스 감정 통합 예측기"""
    
    def __init__(self, model_path='../models/integrated_model.pkl'):
        self.tech_predictor = StockPredictor(model_path)
        self.news_analyzer = NewsSentimentAnalyzer()
        self.collector = DataCollector()
        self.featurizer = FeatureEngineer()
        self.model_path = model_path
    
    def prepare_enhanced_features(self, ticker, period="6mo"):
        """강화된 특성 준비 (기술적 + 뉴스)"""
        # 1. 기술적 특성
        df = self.collector.fetch_stock(ticker, period=period)
        if df is None:
            return None
        
        df_tech = self.featurizer.create_features(df)
        
        # 2. 뉴스 감정 특성
        news_features = self.news_analyzer.get_sentiment_features(ticker)
        
        # 3. 통합 (뉴스 특성 추가)
        for key, value in news_features.items():
            if key != 'ticker':
                df_tech[f'news_{key}'] = value
        
        return df_tech
    
    def train_with_sentiment(self, ticker='SPY'):
        """뉴스 감정 포함 학습"""
        print("=" * 50)
        print("🤖 반디 퀀트 v3.0 - 통합 모델 학습")
        print("=" * 50)
        
        # 기술적 특성만으로 학습 (뉴스는 실시간)
        df = self.collector.fetch_stock(ticker, period="2y")
        if df is None:
            return False
        
        print("\n1️⃣ 기술적 특성 생성")
        df_features = self.featurizer.create_features(df)
        feature_cols = self.featurizer.get_feature_columns()
        
        # 확장된 특성 목록 (뉴스용 placeholder)
        self.extended_features = feature_cols + [
            'news_sentiment', 'news_count', 'pos_ratio', 'neg_ratio', 'sentiment_volatility'
        ]
        
        print(f"   기술적 특성: {len(feature_cols)}개")
        print(f"   뉴스 특성: 5개")
        print(f"   총 특성: {len(self.extended_features)}개")
        
        print("\n2️⃣ 모델 학습")
        X, y, _ = self.tech_predictor.prepare_data(df_features, feature_cols)
        self.tech_predictor.train(X, y)
        
        self.tech_predictor.save_model()
        
        print("\n✅ 통합 모델 학습 완료!")
        return True
    
    def predict_with_sentiment(self, tickers=None):
        """뉴스 감정 포함 예측"""
        if tickers is None:
            tickers = ['PLTR', 'TSLA', 'NVDA', 'TE', 'ENPH']
        
        print("=" * 50)
        print("🔮 반디 통합 예측 (기술적 + 뉴스)")
        print("=" * 50)
        
        results = []
        
        for ticker in tickers:
            print(f"\n📊 분석 중: {ticker}")
            
            try:
                # 기술적 특성
                df = self.collector.fetch_stock(ticker, period="6mo")
                if df is None:
                    continue
                
                df_tech = self.featurizer.create_features(df)
                feature_cols = self.featurizer.get_feature_columns()
                
                # 뉴스 감정
                news_feat = self.news_analyzer.get_sentiment_features(ticker)
                
                # 최신 데이터
                latest = df_tech[feature_cols].iloc[-1:]
                latest_price = df_tech['close'].iloc[-1]
                latest_rsi = df_tech['rsi'].iloc[-1]
                
                # 기술적 예측
                pred, prob = self.tech_predictor.predict(latest)
                tech_prob = prob[0][pred[0]]
                
                # 뉴스 조정
                news_adj = self._adjust_by_sentiment(news_feat)
                final_prob = (tech_prob * 0.8) + (news_adj * 0.2)  # 가중 평균
                final_pred = 1 if final_prob > 0.5 else 0
                
                result = {
                    'ticker': ticker,
                    'price': latest_price,
                    'rsi': latest_rsi,
                    'tech_prediction': pred[0],
                    'tech_confidence': tech_prob,
                    'news_sentiment': news_feat['news_sentiment'],
                    'news_pos_ratio': news_feat['pos_ratio'],
                    'final_prediction': final_pred,
                    'final_confidence': final_prob
                }
                
                results.append(result)
                
                # 출력
                direction = "📈 상승" if final_pred == 1 else "📉 하�"
                print(f"   기술적: {tech_prob:.1%} | 뉴스: {news_feat['news_sentiment']:+.2f}")
                print(f"   {direction} 최종: {final_prob:.1%}")
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ 오류: {e}")
        
        print(f"\n✅ 예측 완료: {len(results)}개 종목")
        return results
    
    def _adjust_by_sentiment(self, news_feat):
        """뉴스 감정 기반 확률 조정"""
        sentiment = news_feat['news_sentiment']
        pos_ratio = news_feat['pos_ratio']
        
        # 감정 점수를 확률로 변환 (0~1)
        adjusted = 0.5 + (sentiment * 0.3)  # ±0.3 범위 조정
        adjusted = max(0.1, min(0.9, adjusted))  # 범위 제한
        
        if pos_ratio > 0.6:
            adjusted += 0.1
        elif pos_ratio < 0.3:
            adjusted -= 0.1
        
        return adjusted

if __name__ == "__main__":
    import time
    
    predictor = IntegratedPredictor()
    
    # 학습
    predictor.train_with_sentiment('SPY')
    
    # 예측
    predictor.predict_with_sentiment(['PLTR', 'TSLA', 'NVDA', 'TE'])
