"""
파파 주중 브리핑 시스템
모든 기능 포함: 추천 + 매도 + 추적 + 평가
"""

import sys
sys.path.append('/Users/mchom/.openclaw/workspace/quant-trader')

from data.data_pipeline import QuantDataPipeline
from datetime import datetime, timedelta
import json
import os
import urllib.request
import urllib.parse

# 매도 등급 정의
SELL_RATING_STRONG = "🔴 강력매도"      # RSI > 70, 과매수 상태
SELL_RATING_RECOMMEND = "🟠 매도권유"  # RSI 60-70, 수익 실현 구간
SELL_RATING_PREPARE = "🟡 매도대비"    # 목표가 도달 또는 손절선 접근

class PapaStockAdvisor:
    """파파 전용 주중 브리핑 + 평가 시스템"""
    
    def __init__(self):
        self.pipeline = QuantDataPipeline()
        self.watchlist = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", 
            "NFLX", "AMD", "INTC", "PLTR", "COIN", "PYPL", "SQ"
        ]
        self.data_dir = "/Users/mchom/.openclaw/workspace/quant-trader/data/weekly"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def detect_sell_signals(self, symbol, current_data, entry_data=None):
        """
        매도 신호 탐지
        Returns: (sell_rating, reasons, score) or None
        """
        try:
            tech = current_data['technical']
            prices = [p['close'] for p in current_data['prices']]
            current_price = prices[-1]
            
            sell_score = 0
            reasons = []
            rating = None
            
            # RSI 과매수 (70 이상: 강력매도, 60-70: 매도권유)
            rsi = tech.get('rsi', 50)
            if rsi > 70:
                sell_score += 40
                reasons.append(f"RSI 과매수 ({rsi:.1f})")
                rating = SELL_RATING_STRONG
            elif rsi > 65:
                sell_score += 25
                reasons.append(f"RSI 상승피로 ({rsi:.1f})")
                rating = SELL_RATING_RECOMMEND
            elif rsi > 60:
                sell_score += 15
                reasons.append(f"RSI 고점영역 ({rsi:.1f})")
                rating = SELL_RATING_PREPARE
            
            # 수익 실현 기준 (진입가 대비)
            if entry_data and 'entry_price' in entry_data:
                entry_price = entry_data['entry_price']
                return_pct = (current_price - entry_price) / entry_price * 100
                
                # 수익 + 20% 이상: 매도권유
                if return_pct >= 20:
                    sell_score += 30
                    reasons.append(f"목표수익 달성 ({return_pct:+.1f}%)")
                    if rating is None or rating == SELL_RATING_PREPARE:
                        rating = SELL_RATING_RECOMMEND
                # 수익 + 15-20%: 매도대비
                elif return_pct >= 15:
                    sell_score += 20
                    reasons.append(f"수익 구간 ({return_pct:+.1f}%)")
                    if rating is None:
                        rating = SELL_RATING_PREPARE
                # 손실 -5% 이상: 매도대비 (손절)
                elif return_pct <= -5:
                    sell_score += 20
                    reasons.append(f"손절선 접근 ({return_pct:.1f}%)")
                    if rating is None:
                        rating = SELL_RATING_PREPARE
            
            # 20일 수익률 급등 후 하� 반전 신호
            return_20d = tech.get('return_20d', 0)
            if return_20d > 30:
                sell_score += 15
                reasons.append(f"급등 후 피로 ({return_20d:+.1f}%)")
                if rating is None:
                    rating = SELL_RATING_PREPARE
            
            # 거래량 급감 (상승 동력 약화)
            if tech.get('volume_trend', 0) < -20:
                sell_score += 10
                reasons.append("거래량 감소")
            
            # 매도 신호 판정
            if sell_score >= 30 or rating == SELL_RATING_STRONG:
                return {
                    'symbol': symbol,
                    'rating': rating or SELL_RATING_PREPARE,
                    'score': sell_score,
                    'reasons': reasons,
                    'price': current_price,
                    'rsi': rsi,
                    'return_20d': return_20d
                }
            
            return None
            
        except Exception as e:
            print(f"  ⚠️ 매도 분석 오류 ({symbol}): {e}")
            return None
    
    def analyze_sell_candidates(self):
        """
        과거 추천 종목 중 매도 대상 분석
        """
        sell_candidates = []
        
        # 지난 4주치 추천 종목 확인
        for week_offset in range(1, 5):
            check_date = datetime.now() - timedelta(days=7*week_offset)
            week_id = check_date.strftime('%Y-W%U')
            filepath = f"{self.data_dir}/{week_id}_recommendations.json"
            
            if not os.path.exists(filepath):
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    past_recs = json.load(f)
                
                for rec in past_recs:
                    symbol = rec['symbol']
                    entry_price = rec.get('price', 0)
                    entry_date = rec.get('date', '')
                    
                    # 현재 데이터 조회
                    try:
                        current_data = self.pipeline.prepare_dataset(symbol, days=30)
                        
                        # 매도 신호 탐지
                        sell_signal = self.detect_sell_signals(
                            symbol, 
                            current_data,
                            {'entry_price': entry_price}
                        )
                        
                        if sell_signal:
                            sell_signal['entry_price'] = entry_price
                            sell_signal['entry_date'] = entry_date
                            sell_signal['holding_days'] = (
                                datetime.now() - datetime.strptime(entry_date, '%Y-%m-%d')
                            ).days
                            sell_candidates.append(sell_signal)
                            
                    except Exception as e:
                        continue
                        
            except Exception as e:
                continue
        
        # 중복 제거 (동일 종목은 최신만)
        seen = set()
        unique_candidates = []
        for c in sorted(sell_candidates, key=lambda x: x['score'], reverse=True):
            if c['symbol'] not in seen:
                seen.add(c['symbol'])
                unique_candidates.append(c)
        
        return unique_candidates[:5]  # 상위 5개만
    
    def create_sell_briefing_voice(self, sell_candidates):
        """
        매도 브리핑 음성 파일 생성
        """
        client_id = "8dqe4kfpmd"
        client_secret = "nU2AHDJ77VOoM0s7oPVd4EhPVzuVFbyLr2qRmYd6"
        
        if not sell_candidates:
            return None
        
        text_lines = ["파파, 매도 브리핑입니다.\n"]
        
        for i, sell in enumerate(sell_candidates[:3], 1):
            return_pct = 0
            if sell.get('entry_price'):
                return_pct = (sell['price'] - sell['entry_price']) / sell['entry_price'] * 100
            
            # 등급 설명
            if "강력매도" in sell['rating']:
                action = "강력 매도하세요"
            elif "매도권유" in sell['rating']:
                action = "매도 권고드립니다"
            else:
                action = "매도 준비하세요"
            
            text_lines.append(f"{i}번째 종목, {sell['symbol']}입니다.")
            text_lines.append(f"의견은, {action}.")
            text_lines.append(f"현재 가격은 {sell['price']:.2f}달러입니다.")
            
            if sell.get('entry_price'):
                text_lines.append(f"수익률은 {return_pct:+.1f}퍼센트입니다.")
            
            text_lines.append(f"사유는, {', '.join(sell['reasons'][:2])}.")
            text_lines.append("")
        
        text_lines.append("참고하시고 운전 조심하세요.")
        text = "\n".join(text_lines)
        
        # CLOVA API 호출 (urllib 사용)
        url = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"
        data = urllib.parse.urlencode({
            "speaker": "nshasha",
            "volume": "0",
            "speed": "-1",
            "pitch": "0",
            "text": text,
            "format": "mp3"
        }).encode('utf-8')
        
        headers = {
            "X-NCP-APIGW-API-KEY-ID": client_id,
            "X-NCP-APIGW-API-KEY": client_secret,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
        
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            response = urllib.request.urlopen(req, timeout=60)
            
            if response.status == 200:
                output_file = f"/Users/mchom/.openclaw/workspace/sell_briefing_{datetime.now().strftime('%Y%m%d')}.mp3"
                with open(output_file, 'wb') as f:
                    f.write(response.read())
                print(f"🎙️ 매도 브리핑 음성: {output_file}")
                return output_file
        except Exception as e:
            print(f"음성 생성 오류: {e}")
        
        return None
    
    def generate_weekday_briefing(self):
        """
        월-금 브리핑: 미국장 마감 후 (한국 새벽 6시)
        매수 + 매도 브리핑 포함
        """
        print("="*70)
        print("🎯 파파 주중 브리핑 (미국장 마감)")
        print(f"   📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} KST")
        print("="*70)
        
        # 1. 매도 브리핑 먼저 (보유 종목 관리)
        print("\n📉 매도 브리핑 (보유 종목 점검)")
        print("-" * 70)
        
        sell_candidates = self.analyze_sell_candidates()
        
        if sell_candidates:
            print(f"\n⚠️ 총 {len(sell_candidates)}개 종목 매도 신호 감지\n")
            for i, sell in enumerate(sell_candidates, 1):
                return_pct = 0
                if sell.get('entry_price'):
                    return_pct = (sell['price'] - sell['entry_price']) / sell['entry_price'] * 100
                
                print(f"{'='*70}")
                print(f"{sell['rating']} {i}. {sell['symbol']}")
                print(f"   💰 현재가: ${sell['price']:.2f}")
                if sell.get('entry_price'):
                    print(f"   📊 진입가: ${sell['entry_price']:.2f} ({return_pct:+.1f}%)")
                    print(f"   📅 보유기간: {sell.get('holding_days', '-')}일")
                print(f"   📉 RSI: {sell['rsi']:.1f}")
                print(f"   🎯 사유: {', '.join(sell['reasons'])}")
                print(f"   ⚡ 매도점수: {sell['score']}/100")
            print(f"{'='*70}")
        else:
            print("\n✅ 매도 대상 종목 없음 (보유 종목 양호)")
        
        # 2. 매수 추천 (기존 로직)
        print("\n📈 매수 브리핑 (신규 진입 종목)")
        print("-" * 70)
        
        recommendations = []
        
        for symbol in self.watchlist:
            try:
                data = self.pipeline.prepare_dataset(symbol, days=30)
                tech = data['technical']
                prices = [p['close'] for p in data['prices']]
                
                # 간단한 점수계산
                score = 0
                reasons = []
                
                # RSI 과매도
                if tech['rsi'] < 35:
                    score += 30
                    reasons.append("RSI 과매도")
                elif tech['rsi'] < 45:
                    score += 15
                    reasons.append("RSI 약과매도")
                
                # 하락장
                return_20d = (prices[-1] - prices[-20]) / prices[-20] * 100
                if return_20d < -10:
                    score += 20
                    reasons.append("과도한 하락")
                elif return_20d < -5:
                    score += 10
                    reasons.append("하락장")
                
                # 안정성
                if tech['volatility'] < 3:
                    score += 10
                    reasons.append("안정적")
                
                if score >= 40:
                    recommendations.append({
                        'symbol': symbol,
                        'signal': data,
                        'score': score,
                        'reasons': reasons,
                        'price': prices[-1],
                        'date': datetime.now().strftime('%Y-%m-%d')
                    })
            except:
                continue
        
        # 점수 높은 순, 상위 5개
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        top5 = recommendations[:5]
        
        # 저장 (이번주 추천 + 매도 정보도 함께)
        week_id = datetime.now().strftime('%Y-W%U')
        filepath = f"{self.data_dir}/{week_id}_recommendations.json"
        sell_filepath = f"{self.data_dir}/{week_id}_sell_signals.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(top5, f, ensure_ascii=False, indent=2)
        
        with open(sell_filepath, 'w', encoding='utf-8') as f:
            json.dump(sell_candidates, f, ensure_ascii=False, indent=2)
        
        # 브리핑 출력
        if top5:
            print(f"\n✅ 이번주 추천 종목 (상위 {len(top5)}개)\n")
            for i, rec in enumerate(top5, 1):
                print(f"{'='*70}")
                print(f"🥇 {i}. {rec['symbol']} (점수: {rec['score']})")
                print(f"   💰 현재가: ${rec['price']:.2f}")
                print(f"   🎯 시그널: {', '.join(rec['reasons'])}")
                print(f"   📉 20일수익: {rec['signal']['technical'].get('ma_diff', 0):.1f}%")
            print(f"{'='*70}")
            print(f"\n📊 저장: {filepath}")
            if sell_candidates:
                print(f"📉 매도신호: {sell_filepath}")
                # 음성 브리핑 생성
                voice_file = self.create_sell_briefing_voice(sell_candidates)
                if voice_file:
                    print(f"🎙️ 음성브리핑: {voice_file}")
            print(f"📈 다음주 금요일에 1주일 성과 평가 예정")
        
        return top5, sell_candidates
    
    def evaluate_weekly_performance(self, week_id=None):
        """
        다음주 금요일: 1주일 성과 평가
        """
        if week_id is None:
            # 지난주 기준
            last_week = (datetime.now() - timedelta(days=7)).strftime('%Y-W%U')
            week_id = last_week
        
        filepath = f"{self.data_dir}/{week_id}_recommendations.json"
        
        if not os.path.exists(filepath):
            print(f"❌ {week_id} 추천 데이터 없음")
            return None
        
        print("="*70)
        print(f"📊 주간 성과 평가 ({week_id})")
        print("="*70)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            recommendations = json.load(f)
        
        results = []
        
        for rec in recommendations:
            symbol = rec['symbol']
            entry_price = rec['price']
            
            # 현재 가격 조회 (샘플)
            try:
                current_data = self.pipeline.prepare_dataset(symbol, days=5)
                current_price = current_data['prices'][-1]['close']
                
                # 수익률 계산
                return_pct = (current_price - entry_price) / entry_price * 100
                
                results.append({
                    'symbol': symbol,
                    'entry': entry_price,
                    'current': current_price,
                    'return_pct': return_pct,
                    'success': return_pct > 0
                })
                
                print(f"\n📈 {symbol}:")
                print(f"   진입가: ${entry_price:.2f}")
                print(f"   현재가: ${current_price:.2f}")
                print(f"   수익률: {return_pct:+.2f}%")
                print(f"   {'✅ 수익' if return_pct > 0 else '❌ 손실'}")
                
            except:
                print(f"\n⚠️ {symbol}: 조회 실패")
        
        # 종합 평가
        if results:
            avg_return = sum(r['return_pct'] for r in results) / len(results)
            success_rate = len([r for r in results if r['success']]) / len(results) * 100
            
            print(f"\n{'='*70}")
            print(f"📊 종합 평가")
            print(f"{'='*70}")
            print(f"   평균 수익률: {avg_return:+.2f}%")
            print(f"   성공률: {success_rate:.1f}%")
            print(f"   종목 수: {len(results)}개")
            
            # 문제점 분석
            print(f"\n🔍 문제점 분석:")
            if success_rate < 60:
                print("   • 성공률 60% 미만 → RSI 기준 조정 필요")
            if avg_return < 0:
                print("   • 평균 손실 → 진입 타이밍 개선 필요")
            print("   • 데이터 축적 후 패턴 분석 예정")
        
        return results


def main():
    """메인 실행"""
    advisor = PapaStockAdvisor()
    
    # 인자로 구분
    if len(sys.argv) > 1 and sys.argv[1] == 'evaluate':
        advisor.evaluate_weekly_performance()
    else:
        buy_signals, sell_signals = advisor.generate_weekday_briefing()
        
        # 텔레그램 전송 (설정된 경우)
        if sell_signals:
            print("\n📱 텔레그램 전송 가능 - 매도 브리핑")
            # 텔레그램 전송 로직 추가 가능


if __name__ == "__main__":
    main()
