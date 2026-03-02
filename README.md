# 반디 퀀트 (Bandi Quant) v4.0

🤖 **AI 예측 통합 주식 브리핑 시스템**

---

## ✨ 주요 기능

- ✅ **43개 전체 종목 분석** (국내 + 미국)
- ✅ **ML 예측** (상승/하락 방향 + 신뢰도)
- ✅ **14가지 캔들 패턴** 자동 감지
- ✅ **차트 자동 생성** (6개월 캔들차트)
- ✅ **텔레그램 브리핑** (텍스트 + 이미지)
- ✅ **매일 아침 자동 실행** (오전 6:30 KST)

---

## 🚀 빠른 시작

### 1. 저장소 클론

```bash
git clone https://github.com/kdh-ygam/bandi-quant.git
cd bandi-quant
```

### 2. Python 환경 설정

```bash
pip install -r requirements.txt
```

### 3. API 키 설정

`.env` 파일을 생성하고 API 키를 입력하세요:

```bash
cp .env.example .env
# .env 파일을 편집하여 키 입력
```

**필수 환경 변수:**
- `TELEGRAM_TOKEN` - 텔레그램 봇 토큰
- `TELEGRAM_CHAT_ID` - 발송할 채팅방 ID
- `NAVER_CLOVA_CLIENT_ID` - 네이버 클로바 TTS
- `NAVER_CLOVA_CLIENT_SECRET` - 네이버 클로바 TTS

### 4. 실행

```bash
source .env
python3 bandi_quant_v40.py
```

---

## 🤖 GitHub Actions 자동 브리핑

GitHub Actions로 매일 아침 자동 브리핑을 받을 수 있습니다.

### 설정 방법

1. **GitHub 저장소 → Settings → Secrets and variables → Actions**

2. **New repository secret** 클릭하여 다음 추가:
   - `TELEGRAM_TOKEN`: 텔레그램 봇 토큰
   - `TELEGRAM_CHAT_ID`: 채팅방 ID (예: 6146433054)
   - `NAVER_CLOVA_CLIENT_ID`: 네이버 클로바 Client ID
   - `NAVER_CLOVA_CLIENT_SECRET`: 네이버 클로바 Client Secret

3. **Actions 탭**에서 "Daily Market Briefing" 확인

4. **수동 실행**: "Run workflow" 버튼 클릭

### 스케줄

- **한국 시간**: 평일 오전 6:30
- **크론 표현**: `30 21 * * 0-4` (UTC 기준)

---

## 📁 파일 구조

```
bandi-quant/
├── bandi_quant_v40.py          # 메인 브리핑 시스템
├── chart_standard.py           # 차트 생성 모듈
├── daily_briefing.sh           # 로컬 실행 스크립트
├── .env.example                # 환경 변수 예시
├── .github/workflows/          # GitHub Actions
│   └── daily_briefing.yml
├── analysis/                   # 분석 결과 저장
├── charts/                     # 생성된 차트 저장
└── memory/                     # 대화 기록
```

---

## 🛠️ 개발 가이드

### 새로운 종목 추가

`bandi_quant_v40.py`에서 `STOCKS` 목록 수정:

```python
STOCKS = [
    ("ticker", "Korean Name", "Sector"),
    # ...
]
```

### 차트 커스터마이징

`chart_standard.py`의 `create_stock_chart()` 함수 수정

---

## 📊 분석 등급 체계

| 등급 | 조건 | 추천 |
|:---:|:---:|:---|
| 🟢 강력매수 | RSI < 35 | 즉시 분할 매수 |
| 🟡 매수권유 | RSI 35-45 | 참여 매수 |
| 🟠 매수대비 | RSI 45-50 | 관망 후 진입 |
| ⚪ 보유 | 중립 | 현 포지션 유지 |
| 🟡 매도대비 | RSI 60+ | 매도 준비 |
| 🟠 매도권유 | RSI 60-70 + 수익 20%+ | 점진적 익절 |
| 🔴 강력매도 | RSI > 70 + 수익 50%+ | 즉시 50% 익절 |

---

## 📝 업데이트 히스토리

- **v4.0** (2026-03-02): ML 예측 + 차트 통합
- **v3.2** (2026-02-28): 패턴 분석 + 의견 추가
- **v3.0** (2026-02-27): 차트 통합
- **v2.1** (2026-02-25): 기본 RSI/MACD/BB 분석

---

## 👤 제작자

- **반디 (Bandi)** - AI 어시스턴트 🤖
- **파파 (Papa)** - 프로젝트 오너 👨

---

*© 2026 Bandi Quant. All rights reserved.*
