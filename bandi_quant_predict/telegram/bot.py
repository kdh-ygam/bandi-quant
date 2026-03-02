#!/usr/bin/env python3
"""
반디 퀀트 - 텔레그램 알림 모듈 v1.0
실적 예측 결과 → 텔레그램 전송
"""

import requests
import pandas as pd
from datetime import datetime
import os

class TelegramBot:
    """텔레그램 브리핑 봇"""
    
    def __init__(self, token=None, chat_id=None):
        self.token = token or os.getenv('TELEGRAM_TOKEN', 'YOUR_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, message, parse_mode='Markdown'):
        """텍스트 메시지 전송"""
        url = f"{self.api_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        
        try:
            response = requests.post(url, json=payload)
            return response.json()
        except Exception as e:
            print(f"❌ 텔레그램 전송 실패: {e}")
            return None
    
    def send_photo(self, photo_path, caption=""):
        """이미지 전송"""
        url = f"{self.api_url}/sendPhoto"
        
        try:
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                data = {'chat_id': self.chat_id, 'caption': caption}
                response = requests.post(url, files=files, data=data)
                return response.json()
        except Exception as e:
            print(f"❌ 사진 전송 실패: {e}")
            return None
    
    def create_prediction_briefing(self, predictions):
        """
        예측 브리핑 생성
        predictions: [{ticker, price, prediction, probability, rsi, ma_ratio}, ...]
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 상승 예측 종목 필터
        buy_signals = [p for p in predictions if p['prediction'] == 1 
                       and p['probability'] > 0.55]
        sell_signals = [p for p in predictions if p['prediction'] == 0 
                        and p['probability'] > 0.55]
        
        # 신뢰도 정렬
        buy_signals = sorted(buy_signals, key=lambda x: x['probability'], reverse=True)[:5]
        sell_signals = sorted(sell_signals, key=lambda x: x['probability'], reverse=True)[:3]
        
        # 메시지 생성
        message = f"""
🤖 **반디 AI 예측 브리핑**
📅 {today}

📊 **시스템 성능**
• 모델: Random Forest
• 예측 정확도: {predictions[0].get('model_accuracy', 0):.1%}
• 분석 종목: {len(predictions)}개

---

🟢 **매수 신호 (BUY)** {len(buy_signals)}개
"""
        
        for i, signal in enumerate(buy_signals, 1):
            confidence = signal['probability'] * 100
            rsi = signal.get('rsi', 50)
            
            # RSI 기반 등급
            if rsi < 35:
                grade = "강력매수"
                emoji = "🔥"
            elif rsi < 50:
                grade = "매수권유"
                emoji = "✅"
            else:
                grade = "매수대비"
                emoji = "🟡"
            
            message += f"""
{i}. **{signal['ticker']}** {emoji}
   💰 ${signal['price']:.2f}
   📈 상승 확률: {confidence:.0f}%
   📊 RSI: {rsi:.1f} | {grade}
"""
        
        if sell_signals:
            message += f"""
---

🔴 **매도 신호 (SELL)** {len(sell_signals)}개
"""
            for i, signal in enumerate(sell_signals, 1):
                confidence = signal['probability'] * 100
                message += f"""
{i}. **{signal['ticker']}**
   💰 ${signal['price']:.2f}
   📉 하락 확률: {confidence:.0f}%
"""
        
        message += f"""
---

⚠️ **주의사항**
• 예측은 확률 기반, 100% 정확하지 않음
• 과거 데이터 기반, 미래 반영 안될 수 있음
• 절대 100% 믿지 말고 참고만 하세요!

💬 *Made by 반디 🐾*
"""
        
        return message
    
    def send_prediction_alert(self, predictions):
        """예측 알림 전송"""
        message = self.create_prediction_briefing(predictions)
        return self.send_message(message)
    
    def test_connection(self):
        """연결 테스트"""
        url = f"{self.api_url}/getMe"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 봇 연결 성공: @{data['result']['username']}")
                return True
            else:
                print(f"❌ 봇 연결 실패: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 연결 테스트 실패: {e}")
            return False

if __name__ == "__main__":
    import sys
    sys.path.append('../data')
    sys.path.append('../models')
    
    from collector import DataCollector
    from features import FeatureEngineer
    from predictor import StockPredictor
    
    # 테스트용 샘플 예측 데이터
    sample_predictions = [
        {'ticker': 'PLTR', 'price': 137.19, 'prediction': 1, 'probability': 0.62, 'rsi': 48.5, 'model_accuracy': 0.58},
        {'ticker': 'TSLA', 'price': 402.51, 'prediction': 0, 'probability': 0.58, 'rsi': 44.7, 'model_accuracy': 0.58},
        {'ticker': 'NVDA', 'price': 177.19, 'prediction': 1, 'probability': 0.64, 'rsi': 41.1, 'model_accuracy': 0.58},
        {'ticker': 'TE', 'price': 6.16, 'prediction': 1, 'probability': 0.75, 'rsi': 28.7, 'model_accuracy': 0.58},
    ]
    
    # 봇 테스트
    bot = TelegramBot(
        token='8599663503:AAGfs7Sh2vy6tfHOr9UG-O_lcaG3cjPdH2s',
        chat_id='6146433054'
    )
    
    print("🤖 반디 AI 예측 브리핑 테스트")
    print("=" * 40)
    
    # 연결 테스트
    if bot.test_connection():
        # 브리핑 전송
        message = bot.create_prediction_briefing(sample_predictions)
        print(f"\n전송할 메시지:")
        print(message)
        
        result = bot.send_prediction_alert(sample_predictions)
        if result:
            print("✅ 브리핑 전송 성공!")
        else:
            print("❌ 브리핑 전송 실패")
    else:
        print("❌ 봇 설정을 확인해주세요")
