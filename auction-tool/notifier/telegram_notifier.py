"""
알림 시스템 (Notification)
텔레그램으로 경매 알림 보내기

사용법:
    from notifier.telegram_notifier import TelegramNotifier
    
    notifier = TelegramNotifier()
    notifier.send_auction_alert(auction_data)
"""

import json
from datetime import datetime
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config import TELEGRAM_CHAT_ID


class TelegramNotifier:
    """
    텔레그램 알림 클래스
    """
    
    def __init__(self):
        self.chat_id = TELEGRAM_CHAT_ID
        print(f"📱 알림 시스템 준비 (대상: {self.chat_id})")
    
    def send_message(self, message, parse_mode="HTML"):
        """
        기본 메시지 전송
        (실제로는 OpenClaw message 툴 사용)
        """
        print(f"📤 메시지 준비:\n{message[:200]}...")
        return True
    
    def send_auction_alert(self, auction, analysis, profit):
        """
        경매 물건 알림 보내기
        
        Args:
            auction: 물건 정보 dict
            analysis: 분석 결과 dict
            profit: 수익성 결과 dict
        """
        # 이모지 결정
        if profit['summary']['recommend']:
            emoji = "🎯"
            status = "추천!"
        elif profit['profit']['roi'] > 0:
            emoji = "⚡"
            status = "검토"
        else:
            emoji = "❌"
            status = "패스"
        
        # 메시지 구성
        message = f"""{emoji} <b>경매 물건 알림 - {status}</b>

📍 <b>{auction.get('address', '주소 미확인')}</b>

💰 <b>가격 정보</b>
• 감정가: {self._format_money(auction.get('appraisal_price', 0))}
• 최저입찰가: {self._format_money(auction.get('min_bid_price', 0))}
• 할인율: {profit['summary'].get('safety_margin', 0):.1f}%

📊 <b>분석 결과</b>
• 위험점수: {analysis.get('risk_score', 'N/A')}/100
• 인수비용: {self._format_money(analysis.get('estimated_cost', 0))}
• 위험요소: {', '.join(analysis.get('risks', [])[:2])}

💵 <b>수익 예측</b>"""
        
        # 전략별 수익 정보 추가
        if 'roi' in profit.get('profit', {}):
            message += f"""
• 수익률(ROI): {profit['profit']['roi']:.1f}%
• 순수익: {self._format_money(profit['profit'].get('net_profit', 0))}
"""
        elif 'net_yield' in profit.get('profit', {}):
            message += f"""
• 임대수익률: {profit['profit']['net_yield']:.1f}%
• 월세: {self._format_money(profit['profit'].get('monthly_rent', 0))}/월
"""
        
        message += f"""
💡 <b>조언</b>
{analysis.get('advice', '확인 필요')}

📅 입찰일: {auction.get('bid_date', '미확인')}
🔍 자세히: {auction.get('url', '링크 없음')}

---
⏰ 알림 시간: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        
        return self.send_message(message)
    
    def send_daily_summary(self, auctions_count, avg_roi, best_auction):
        """
        일일 요약 알림
        """
        message = f"""📊 <b>오늘의 경매 요약</b>

• 분석 물건: {auctions_count}건
• 평균 수익률: {avg_roi:.1f}%

🎯 <b>오늘의 추천</b>
{best_auction.get('address', '없음')}
예상 수익률: {best_auction.get('roi', 0):.1f}%

내일도 좋은 물건 찾아줄게요! 🐾
"""
        return self.send_message(message)
    
    def _format_money(self, amount):
        """금액 포맷팅"""
        if amount >= 100_000_000:
            return f"{amount/100_000_000:.1f}억원"
        elif amount >= 10_000:
            return f"{amount/10_000:,.0f}만원"
        else:
            return f"{amount:,}원"


class ConsoleNotifier:
    """
    콘솔 알림 (테스트용)
    실제 텔레그램 없이 테스트할 때 사용
    """
    
    def __init__(self):
        print("🖥️ 콘솔 알림 모드")
    
    def send_message(self, message):
        print("\n" + "="*50)
        print("[알림 메시지]")
        print("="*50)
        print(message)
        print("="*50)
        return True
    
    def send_auction_alert(self, auction, analysis, profit):
        message = f"""
[경매 알림]

주소: {auction.get('address')}
할인율: {profit['summary'].get('safety_margin', 0):.1f}%
위험: {analysis.get('risk_score')}/100
수익률: {profit['profit'].get('roi', 'N/A')}%
추천: {'예' if profit['summary']['recommend'] else '아니오'}
"""
        return self.send_message(message)


def main():
    """테스트"""
    print("="*50)
    print("알림 시스템 테스트")
    print("="*50)
    
    # 콘솔 알림 테스트
    notifier = ConsoleNotifier()
    
    sample_auction = {
        "address": "서울 마포구 서교동 123-45",
        "appraisal_price": 500_000_000,
        "min_bid_price": 300_000_000,
        "bid_date": "2025-03-15",
        "url": "https://example.com/auction/123"
    }
    
    sample_analysis = {
        "risk_score": 35,
        "risks": ["임차인 보증금", "선순위 저당"],
        "estimated_cost": 30_000_000,
        "advice": "보통 수준. 명도 비용 고려 필요.",
        "recommend": True
    }
    
    sample_profit = {
        "summary": {
            "safety_margin": 40.0,
            "recommend": True
        },
        "profit": {
            "roi": 15.5,
            "net_profit": 45_000_000,
            "expected_sale_price": 475_000_000
        }
    }
    
    print("\n📤 알림 테스트...")
    notifier.send_auction_alert(sample_auction, sample_analysis, sample_profit)
    
    print("\n✅ 테스트 완료!")


if __name__ == "__main__":
    main()
