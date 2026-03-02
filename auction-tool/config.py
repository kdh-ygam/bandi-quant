"""
경매 투자 분석 툴 - 설정 파일
파파의 �똥한 경매 도우미
"""

import os
from pathlib import Path

# .env 파일 로드 (선택적)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent

# 로그/데이터 디렉토리
LOG_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "6146433054")  # 파파의 챗 ID

# 효율 설정 - 파파의 토큰 절약 원칙!
MAX_TOKENS_PER_ANALYSIS = 2000  # 분석당 최대 토큰
CACHE_DURATION_HOURS = 24       # 캐시 유지 시간

# 경매 사이트 설정
AUCTION_SITES = {
    "ggi": {
        "name": "지지옥션",
        "url": "https://www.ggi.co.kr",
        "enabled": True,
    },
    "court": {
        "name": "대법원 경매정보",
        "url": "https://www.courtauction.go.kr",
        "enabled": False,  # 별도 인증 필요
    }
}

# 수익성 분석 설정
PROFITABILITY = {
    "min_safety_margin": 0.15,      # 최소 안전마진 15%
    "min_yield_rate": 0.05,         # 최소 수익률 5%
    "loan_interest_rate": 0.06,     # 대출 이자율 6%
    "brokerage_fee_rate": 0.009,    # 중개수수료 0.9%
    "repair_cost_per_pyeong": 500000,  # 평당 수리비 50만원
    "eviction_cost_per_pyeong": 300000, # 평당 명도비 30만원
}

# 세금 설정 (2024년 기준)
TAX_RATES = {
    "acquisition_high": 0.022,      # 취득세 (고가 주택)
    "acquisition_normal": 0.011,    # 취득세 (일반)
    "education_tax": 0.002,         # 지방교육세
    "agriculture_tax": 0.002,       # 농특세
    "capital_gains_short": 0.50,    # 양도소득세 (단기)
    "capital_gains_long": 0.06,     # 양도소득세 (장기)
}

# 알림 설정
NOTIFICATION = {
    "daily_time": "08:00",          # 일일 브리핑 시간
    "min_profit_alert": 50000000,   # 5천만원 이상 수익 시 알림
    "filter_keywords": ["임차인", "유치권", "법정지상권"],  # 위험 키워드
}

def check_config():
    """설정 확인"""
    print("🔧 경매 분석 툴 설정 확인")
    print(f"   OpenAI API: {'✅ 설정됨' if OPENAI_API_KEY else '❌ 미설정'}")
    print(f"   Telegram: {'✅ 설정됨' if TELEGRAM_BOT_TOKEN else '❌ 미설정'}")
    print(f"   데이터 저장: {DATA_DIR}")
    print(f"   로그 저장: {LOG_DIR}")

if __name__ == "__main__":
    check_config()
