"""
간단한 테스트 - pandas 없이
"""

import json
from datetime import datetime
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

# 샘플 데이터 생성
test_data = [
    {
        "auction_id": "2025-001234",
        "address": "서울특별시 강남구 삼성동 123-45",
        "building_type": "아파트",
        "appraisal_price": 1200000000,
        "min_bid_price": 840000000,
        "bid_date": "2025-03-15",
        "court": "서울중앙지방법원",
        "status": "진행중"
    },
    {
        "auction_id": "2025-001235",
        "address": "서울특별시 서초구 반포동 456-78",
        "building_type": "빌라",
        "appraisal_price": 800000000,
        "min_bid_price": 560000000,
        "bid_date": "2025-03-20",
        "court": "서울중앙지방법원",
        "status": "진행중"
    }
]

# JSON 저장
data_dir = Path(__file__).parent.parent / "data"
data_dir.mkdir(exist_ok=True)

filename = data_dir / f"test_auctions_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(test_data, f, ensure_ascii=False, indent=2)

print("✅ 테스트 성공!")
print(f"   저장 위치: {filename}")
print(f"   총 {len(test_data)}건")

# 간단한 분석
total_appraisal = sum(a["appraisal_price"] for a in test_data)
total_min_bid = sum(a["min_bid_price"] for a in test_data)
savings = total_appraisal - total_min_bid

print(f"\n📊 간단 분석:")
print(f"   감정가 총합: {total_appraisal:,}원")
print(f"   최저입찰가 총합: {total_min_bid:,}원")
print(f"   절약 가능 금액: {savings:,}원 ({savings/total_appraisal*100:.1f}%)")
