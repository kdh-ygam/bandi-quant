"""
규칙 기반 권리 분석기
AI 없이도 작동하는 엔진

비용: 0원 💰
"""

import re
from datetime import datetime
from pathlib import Path


class RuleBasedAnalyzer:
    """
    규칙 기반 권리 분석기
    키워드 매칭으로 위험 요소 찾기
    """
    
    # 위험 키워드 사전
    RISK_KEYWORDS = {
        "임차인": {"risk": 30, "message": "임차인 있음", "cost": "보증금"},
        "유치권": {"risk": 40, "message": "유치권 있음", "cost": "공사비"},
        "법정지상권": {"risk": 50, "message": "법정지상권", "cost": "지료"},
        "선순위": {"risk": 20, "message": "선순위 권리", "cost": "선순위 금액"},
        "대항력": {"risk": 25, "message": "대항력 임차인", "cost": "보증금"},
        "점유": {"risk": 20, "message": "점유자 있음", "cost": "명도 비용"},
    }
    
    def __init__(self):
        print("🎯 규칙 기반 분석기 (비용 0원)")
    
    def analyze_document(self, text):
        """문서 분석"""
        print("🔍 키워드 분석...")
        
        risks = []
        accepted = []
        score = 0
        
        for keyword, info in self.RISK_KEYWORDS.items():
            if keyword in text:
                risks.append(info["message"])
                accepted.append(info["cost"])
                score += info["risk"]
        
        # 임차인 보증금만 계산 (간단 버전)
        extra_cost = 0
        if "임차인" in text or "보증금" in text:
            # 보증금 찾기
            match = re.search(r'(\d{1,3}(?:,\d{3})*|\d+)\s*(만원|천만원)', text)
            if match:
                num = int(match.group(1).replace(',', ''))
                if '천만원' in match.group(0):
                    extra_cost = num * 10_000_000
                else:
                    extra_cost = num * 10_000
        
        # 유치권 금액
        if "유치권" in text:
            match = re.search(r'(\d)\s*천만원', text)
            if match:
                extra_cost += int(match.group(1)) * 10_000_000
        
        score = min(score, 100)
        
        # 말소기준 날짜
        dates = re.findall(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', text)
        malso = f"{dates[0][0]}-{dates[0][1]}-{dates[0][2]}" if dates else "확인 필요"
        
        # 조언
        if score >= 60:
            advice = "⚠️ 고위험!"
        elif score >= 40:
            advice = "⚡ 중위험"
        else:
            advice = "✅ 양호"
        
        if extra_cost > 0:
            advice += f" (추가비용: {extra_cost//10_000}만원)"
        
        return {
            "risk_score": score,
            "malso_date": malso,
            "accepted_rights": accepted if accepted else ["없음"],
            "risks": risks if risks else ["특별한 위험 없음"],
            "estimated_cost": extra_cost,
            "advice": advice,
            "recommend": score < 60
        }


def main():
    """테스트"""
    print("="*50)
    print("규칙 기반 분석기 (무료)")
    print("="*50)
    
    analyzer = RuleBasedAnalyzer()
    
    sample = """
    [등기부등본]
    소재지: 서울시 강남구 삼성동 123-45
    
    [저당권] OO은행, 8억원, 설정일 2023년 1월 15일
    [임차권] 박OO, 보증금 5천만원
    [유치권] 공사비 3천만원
    """
    
    result = analyzer.analyze_document(sample)
    
    print(f"\n📊 결과:")
    print(f"   위험점수: {result['risk_score']}/100")
    print(f"   말소기준: {result['malso_date']}")
    print(f"   인수권리: {', '.join(result['accepted_rights'])}")
    print(f"   위험요소: {', '.join(result['risks'])}")
    print(f"   추가비용: {result['estimated_cost']:,}원")
    print(f"   조언: {result['advice']}")
    print(f"   추천: {'✅' if result['recommend'] else '❌'}")


if __name__ == "__main__":
    main()
