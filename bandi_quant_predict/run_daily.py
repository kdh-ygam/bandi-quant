#!/usr/bin/env python3
"""
반디 퀀트 - 자동화 시스템 v5.0
Phase 5: 차트 포함 일일 브리핑 (파파 요구사항 반영)

🔥 중요: 이 시스템에서 차트는 필수!
- 모든 브리핑에 Top 5 종목의 6개월 캔들차트 필수 포함
- 차트 없으면 브리핑 성립 안됨 (파파 직접 지시)
- run_daily.py --mode=test 실행 시 차트 자동 생성 및 전송
"""

import sys
import os

# 경로 설정
base_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(base_dir)
sys.path.append(os.path.join(base_dir, 'data'))
sys.path.append(os.path.join(base_dir, 'models'))
sys.path.append(os.path.join(base_dir, 'backtest'))
sys.path.append(os.path.join(base_dir, 'telegram'))
sys.path.append(parent_dir)  # chart_standard 임포트용

from datetime import datetime, timedelta
import pandas as pd
import time
import json

from collector import DataCollector
from features import FeatureEngineer
from predictor import StockPredictor
from news_sentiment import NewsSentimentAnalyzer
import telegram.bot as telegram_bot
from chart_standard import create_stock_chart
from stock_names import get_stock_name, STOCK_NAMES
from signal_history import SignalHistory

class BandiQuantAutomation:
    """반디 퀀트 자동화 시스템 - 차트 포함"""
    
    def __init__(self):
        self.collector = DataCollector()
        self.featurizer = FeatureEngineer()
        self.predictor = StockPredictor()
        self.news = NewsSentimentAnalyzer()
        self.telegram = telegram_bot.TelegramBot(
            token='8599663503:AAGfs7Sh2vy6tfHOr9UG-O_lcaG3cjPdH2s',
            chat_id='6146433054'
        )
        
        # 신호 기록 관리
        self.signal_history = SignalHistory()
        
        # 차트 저장 디렉토리
        self.today_str = datetime.now().strftime("%Y%m%d")
        self.chart_dir = os.path.join(base_dir, 'charts', self.today_str)
        os.makedirs(self.chart_dir, exist_ok=True)
        
        # 대상 종목 (43개 전체)
        self.tickers = [
            # 반도체 (5개)
            '000660.KS', '005930.KS', '042700.KS', '001740.KS', 'NVDA',
            # 바이오 (5개)
            '068270.KS', '207940.KS', '196170.KS', '136480.KS', 'JNJ',
            # 전력/인프라 (5개)
            '010120.KS', '267260.KS', '051600.KS', '052690.KS', '003670.KS',
            # 🌞 신재생에너지 (7개)
            'NEE', 'TE', 'ENPH', 'SEDG', 'FSLR', 'RUN', 'BE',
            # 🤖 AI/소프트웨어 (6개)
            'PLTR', 'AMD', 'AI', 'SNOW', 'CRWD', 'ARM',
            # 자동차 (8개)
            '005380.KS', '000270.KS', '012330.KS', '003620.KS', 'TSLA', 'F', 'GM', 'RIVN',
            # 2차 전지 (6개)
            '373220.KS', '006400.KS', '005490.KS', '247540.KS', 'ALB', 'QS',
            # 미국 기타 (1개)
            'ONON'
        ]
        
        print(f"🐾 반디 자동화 시스템 v5.0 (차트 포함)")
        print(f"   대상 종목: {len(self.tickers)}개")
        print(f"   차트 저장: {self.chart_dir}")
    
    def run_daily_briefing(self):
        """일일 브리핑 실행 - 차트 포함"""
        print(f"\n{'='*60}")
        print(f"📊 {datetime.now().strftime('%Y-%m-%d')} 일일 브리핑 + 차트")
        print(f"{'='*60}")
        
        # 1. 예측
        predictions = self._generate_predictions()
        
        if not predictions:
            print("❌ 예측 실패")
            return []
        
        # 2. 차트 생성 (상위 종목)
        chart_paths = self._generate_charts(predictions)
        
        # 3. 브리핑 메시지 생성
        message = self._create_briefing_message(predictions)
        
        # 4. 텔레그램 전송 (텍스트 먼저)
        print(f"\n📱 텔레그램 브리핑 전송 중...")
        result = self.telegram.send_message(message)
        
        if result:
            print("✅ 브리핑 전송 완료!")
        else:
            print("❌ 텍스트 전송 실패")
        
        # 5. 차트 이미지 전송 (Top 5)
        if chart_paths:
            print(f"\n📊 차트 이미지 전송 중... ({len(chart_paths)}개)")
            for chart_path in chart_paths[:5]:  # 상위 5개만
                if os.path.exists(chart_path):
                    # 종목명 추출
                    ticker = os.path.basename(chart_path).replace('_6m.png', '')
                    caption = f"📈 {ticker} 6개월 차트"
                    self.telegram.send_photo(chart_path, caption=caption)
                    time.sleep(0.5)  # Rate limit
            print("✅ 차트 전송 완료!")
        
        return predictions
    
    def _generate_predictions(self):
        """예측 생성"""
        predictions = []
        
        # 먼저 모델 로드 또는 학습
        if not self.predictor.load_model():
            print("⚠️  모델 없음. 먼저 학습합니다...")
            self._train_model()
        
        print(f"\n🔮 {len(self.tickers)}개 종목 예측 중...")
        
        for ticker in self.tickers:
            try:
                print(f"   {ticker}...", end=' ', flush=True)
                
                # 데이터 수집
                df = self.collector.fetch_stock(ticker, period="6mo")
                if df is None:
                    print("X")
                    continue
                
                # 특성 생성
                df_features = self.featurizer.create_features(df)
                feature_cols = self.featurizer.get_feature_columns()
                
                # 뉴스 감정
                news_feat = self.news.get_sentiment_features(ticker)
                
                # 예측
                latest = df_features[feature_cols].iloc[-1:]
                price = df_features['close'].iloc[-1]
                rsi = df_features['rsi'].iloc[-1]
                
                pred, prob = self.predictor.predict(latest)
                tech_prob = prob[0][pred[0]]
                
                # 뉴스 가중
                news_adj = 0.5 + (news_feat['news_sentiment'] * 0.3)
                final_prob = (tech_prob * 0.8) + (news_adj * 0.2)
                final_pred = 1 if final_prob > 0.5 else 0
                
                predictions.append({
                    'ticker': ticker,
                    'price': price,
                    'rsi': rsi,
                    'prediction': final_pred,
                    'probability': final_prob,
                    'news_sentiment': news_feat['news_sentiment'],
                    'df': df  # 차트용 데이터 저장
                })
                
                print('✓')
                time.sleep(0.2)  # API 제한
                
            except Exception as e:
                print(f"X ({str(e)[:30]})")
        
        print(f"\n✅ {len(predictions)}개 종목 예측 완료")
        return predictions
    
    def _generate_charts(self, predictions):
        """상위 종목 차트 생성 (AI 신호 화살표 포함)"""
        print(f"\n📊 차트 생성 중...")
        
        # 매수/매도 신호 분류
        buy_signals = [p for p in predictions if p['prediction'] == 1 and p['probability'] > 0.55]
        buy_signals = sorted(buy_signals, key=lambda x: x['probability'], reverse=True)[:3]
        
        sell_signals = [p for p in predictions if p['prediction'] == 0 and p['probability'] > 0.55]
        sell_signals = sorted(sell_signals, key=lambda x: x['probability'], reverse=True)[:2]
        
        # 합쳐서 상위 5개
        top_signals = buy_signals + sell_signals
        
        chart_paths = []
        
        for i, signal in enumerate(top_signals, 1):
            ticker = signal['ticker']
            prob = signal['probability']
            is_buy = signal['prediction'] == 1
            
            print(f"   {i}. {ticker} 차트 생성...", end=' ', flush=True)
            
            try:
                # 종목명 가져오기
                name = get_stock_name(ticker)
                
                # 신호 정보 설정
                signal_type = 'buy' if is_buy else 'sell'
                signal_strength = 'strong' if prob > 0.70 else 'normal'
                
                # 신호 저장
                self.signal_history.add_signal(ticker, signal_type, signal_strength, signal['price'])
                
                # 과거 신호 가져오기
                historical = self.signal_history.get_active_signals(ticker, days=120)
                historical_signals = [
                    (s['date'], s['signal_type'], s['strength'], s['price'])
                    for s in historical
                ]
                
                # 차트 생성
                output_path = os.path.join(self.chart_dir, f"{ticker}_6m.png")
                
                # yfinance용 티커 변환
                yf_ticker = ticker.replace('.KS', '')
                
                chart_result = create_stock_chart(
                    ticker=yf_ticker,
                    name=name,
                    output_path=output_path,
                    period="6mo",
                    days_shown=120,
                    signal_type=signal_type,
                    signal_strength=signal_strength,
                    historical_signals=historical_signals
                )
                
                if chart_result and chart_result.get('success') and os.path.exists(output_path):
                    chart_paths.append(output_path)
                    print('✓')
                else:
                    print('X')
                
                time.sleep(0.3)  # API 제한
                
            except Exception as e:
                print(f'X ({str(e)[:20]})')
        
        print(f"\n✅ {len(chart_paths)}개 차트 생성 완료")
        return chart_paths
    
    def _train_model(self):
        """모델 학습"""
        print("\n🤖 모델 학습 중...")
        
        df = self.collector.fetch_stock("SPY", period="2y")
        if df is None:
            return
        
        df_features = self.featurizer.create_features(df)
        feature_cols = self.featurizer.get_feature_columns()
        
        X, y, _ = self.predictor.prepare_data(df_features, feature_cols)
        self.predictor.train(X, y)
        self.predictor.save_model()
        
        print("✅ 학습 완료")
    
    def _create_briefing_message(self, predictions):
        """브리핑 메시지 생성"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 매수/매도 분류
        buy_signals = [p for p in predictions if p['prediction'] == 1 and p['probability'] > 0.55]
        sell_signals = [p for p in predictions if p['prediction'] == 0 and p['probability'] > 0.55]
        
        # 정렬
        buy_signals = sorted(buy_signals, key=lambda x: x['probability'], reverse=True)
        sell_signals = sorted(sell_signals, key=lambda x: x['probability'], reverse=True)
        
        # Top 10만 표시
        top_buy = buy_signals[:10]
        top_sell = sell_signals[:5]
        
        # 메시지
        message = f"""🤖 **반디 AI 브리핑 v5.0**
📅 {today}

📊 **분석 종목**: {len(predictions)}개
📈 **매수 신호**: {len(buy_signals)}개
🔴 **매도 신호**: {len(sell_signals)}개

"""
        
        # 매수 TOP 10 (한글 종목명 사용! 상승/하락 확률 표시)
        if top_buy:
            message += "🟢 **매수 추천 TOP 10** (↑상승 / ↓하락)\n```\n"
            message += f"{'순위':<4} {'종목명':<8} {'가격':>9} {'↑상승':>6} {'↓하락':>6} {'RS':>3}\n"
            message += "-" * 46 + "\n"
            for i, s in enumerate(top_buy, 1):
                emoji = "🔥" if s['probability'] > 0.75 else "✅" if s['probability'] > 0.65 else "🟡"
                name = get_stock_name(s['ticker'])
                name_display = name[:7]  # 7글자까지만
                up_prob = s['probability'] * 100
                down_prob = (1 - s['probability']) * 100
                rsi_val = int(s['rsi'])
                message += f"{i:<4} {name_display:<8} ${s['price']:>8.1f} {up_prob:>5.0f}% {down_prob:>5.0f}% {emoji}\n"
            message += "```\n"
        
        # 매도 경고 (상승/하락 확률 표시)
        if top_sell:
            message += "\n🔴 **매도 주의 TOP 5** (↑상승 / ↓하락)\n```\n"
            message += f"{'순위':<4} {'종목명':<8} {'가격':>9} {'↑상승':>6} {'↓하락':>6}\n"
            message += "-" * 44 + "\n"
            for i, s in enumerate(top_sell, 1):
                name = get_stock_name(s['ticker'])
                name_display = name[:7]
                up_prob = (1 - s['probability']) * 100  # 매도는 하락 확률이 높음
                down_prob = s['probability'] * 100
                message += f"{i}.   {name_display:<8} ${s['price']:>8.1f} {up_prob:>5.0f}% {down_prob:>5.0f}%\n"
            message += "```\n"
        
        # 차트 안내
        message += """
📊 **차트 안내**
상위 5개 종목의 6개월 캔들스틱 차트를 함께 전송합니다.
(차트 확인 후 투자 결정하세요)

⚠️ **주의 사항**
• 예측 정확도: ~60% (참고용)
• 6개월 차트: RSI, 볼린저밴드, 이동평균선 포함
• 투자는 본인 책임

_🐾 Made by 반디_
"""
        
        return message

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', default='test', choices=['test', 'schedule'])
    args = parser.parse_args()
    
    auto = BandiQuantAutomation()
    
    if args.mode == 'test':
        auto.run_daily_briefing()
    elif args.mode == 'schedule':
        auto.schedule_daily_run()
