"""
AI 권리 분석기 (간단 버전)
OpenAI API 직접 호출

파파가 이해하기 쉽게!
"""

import os
import json
import urllib.request
import ssl
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config import OPENAI_API_KEY


class RightsAnalyzer:
    """
    AI 권리 분석기
    """
    
    def __init__(self):
        """초기화"""
        print("🤖 권리 분석기 준비...")
        self.api_key = OPENAI_API_KEY
        
        if self.api_key:
            print("✅ OpenAI API 키 확인!")
        else:
            print("⚠️ OpenAI API 키 없음 - 테스트 모드")
    
    def analyze_document(self, document_text):
        """
        문서 분석
        
        Args:
            document_text: 등기부등본 텍스트
        
        Returns:
            dict: 분석 결과
        """
        if not self.api_key:
            print("📝 테스트 모드로 실행...")
            return self._mock_analysis()
        
        print("📝 AI에게 문서 분석 요청...")
        
        try:
            # API 요청 준비
            url = "https://api.openai.com/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""당신은 부동산 경매 전문가입니다.
다음 등기부등본을 분석하고 JSON으로 답변해주세요.

문서:
{document_text[:1500]}

답변 형식:
{{
    "risk_score": 0-100 숫자,
    "malso_date": "말소기준 날짜",
    "accepted_rights": ["인수 권리1", "인수 권리2"],
    "risks": ["위험1", "위험2"],
    "advice": "한줄 조언",
    "recommend": true/false
}}"""
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "부동산 경매 전문가. JSON만 출력."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 600
            }
            
            # 요청 보내기
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            # SSL 인증서 검증 비활성화 (맥에서 필요할 수 있음)
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(req, context=context, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                ai_answer = result["choices"][0]["message"]["content"]
                
                # JSON 파싱
                try:
                    return json.loads(ai_answer)
                except:
                    # JSON이 아니면 텍스트에서 추출
                    return {
                        "risk_score": 50,
                        "advice": ai_answer[:100],
                        "recommend": False
                    }
                    
        except Exception as e:
            print(f"⚠️ API 실패, 테스트 모드: {e}")
            return self._mock_analysis()
    
    def _mock_analysis(self):
        """테스트용 예시 데이터"""
        return {
            "risk_score": 65,
            "malso_date": "2023년 1월 15일",
            "accepted_rights": ["임차인 (보증금 5천만원)"],
            "risks": ["임차인 거주 중", "선순위 저당권"],
            "advice": "임차인 명도 비용 5천만원 추가 예상. 신중히 검토하세요.",
            "recommend": False
        }


def main():
    """테스트"""
    print("="*50)
    print("AI 권리 분석기 테스트")
    print("="*50)
    
    analyzer = RightsAnalyzer()
    
    # 샘플 등기부
    sample = """
    [등기부등본]
    소재지: 서울시 강남구 삼성동 123-45
    
    [저당권] OO은행, 8억원, 2023년 1월 15일
    [임차권] 박OO, 2023년 3월 ~ 2025년 2월, 보증금 5천만원
    [가압류] 캐피탈, 2024년 5월 10일
    """
    
    print("\n📝 문서 분석 중...")
    result = analyzer.analyze_document(sample)
    
    print("\n📊 분석 결과:")
    print(f"   위험 점수: {result.get('risk_score', 'N/A')}/100")
    print(f"   말소기준: {result.get('malso_date', 'N/A')}")
    print(f"   인수 권리: {', '.join(result.get('accepted_rights', []))}")
    print(f"   위험 요소: {', '.join(result.get('risks', []))}")
    print(f"   조언: {result.get('advice', 'N/A')}")
    print(f"   입찰 추천: {'✅' if result.get('recommend') else '❌'}")
    
    print("\n✅ 테스트 완료!")


if __name__ == "__main__":
    main()
