"""
OpenClaw AI 분석기
반디가 직접 분석!

비용: 0원 (이미 존재하는 AI 사용)
"""

from datetime import datetime
from pathlib import Path


class OpenClawAnalyzer:
    """
    OpenClaw AI (반디) 분석기
    """
    
    def __init__(self):
        print("🤖 OpenClaw AI 분석기 준비! (반디가 직접 분석)")
    
    def prepare_analysis_prompt(self, document_text, auction_info=None):
        """
        분석 프롬프트 준비
        """
        if auction_info is None:
            auction_info = {}
        
        prompt = f"""안녕 반디! 이 경매 물건 분석해줘.

[물건 정보]
- 주소: {auction_info.get('address', '미확인')}
- 감정가: {auction_info.get('appraisal_price', '미확인')}
- 최저입찰가: {auction_info.get('min_bid_price', '미확인')}

[등기부등본 / 매각물건명세서]
{document_text[:2000]}

분석 요청:
1. 말소기준권리 날짜 찾고 (가장 오래된 저당/가압류)
2. 인수해야 할 권리 목록 (임차인, 유치권 등)
3. 위험 요소 3가지 추려서
4. 예상 추가 비용 계산
5. 입찰 추천 여부 (추천/주의/불가)
6. 한줄 조언

JSON 형식으로 답변:
{{
    "risk_score": 0-100,
    "malso_date": "YYYY-MM-DD",
    "accepted_rights": ["권리1", "권리2"],
    "risks": ["위험1", "위험2", "위험3"],
    "estimated_cost": 숫자(원),
    "recommend": "추천/주의/불가",
    "advice": "한줄 조언"
}}
"""
        return prompt
    
    def save_for_analysis(self, document_text, filename=None):
        """
        분석 대기 파일 저장
        """
        if filename is None:
            filename = f"analysis_request_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        
        filepath = Path(__file__).parent.parent / "logs" / filename
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(document_text)
        
        print(f"💾 분석 요청 저장: {filepath}")
        return filepath


def main():
    """테스트"""
    print("="*50)
    print("OpenClaw AI 분석기 - 반디 테스터")
    print("="*50)
    
    # 샘플 데이터
    sample = """
    [등기부등본]
    소재지: 서울 마포구 서교동 123-45
    
    [저당권]
    채권자: 국민은행
    채권액: 5억원
    설정일: 2022년 8월 15일
    
    [임차권]
    임차인: 김OO
    임대차기간: 2023년 3월 1일 ~ 2025년 2월 28일
    보증금: 3천만원
    대항력 있음
    
    [가압류]
    채권자: OO캐피탈
    채무자: 김OO
    채권액: 2천만원
    설정일: 2024년 1월 10일
    """
    
    auction_info = {
        "address": "서울 마포구 서교동",
        "appraisal_price": "7억원",
        "min_bid_price": "4.9억원"
    }
    
    analyzer = OpenClawAnalyzer()
    prompt = analyzer.prepare_analysis_prompt(sample, auction_info)
    
    print("\n📝 파파에게 보낼 분석 요청:")
    print("="*50)
    print(prompt)
    print("="*50)
    print("\n✅ 이거 파파가 반디한테 보내면 분석해줌!")


if __name__ == "__main__":
    main()
