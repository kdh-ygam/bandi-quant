# Alpha Vantage API 키 발급 가이드

## 📝 발급 방법 (3분 완료)

### Step 1: 회원가입
1. 브라우저에서 `alphavantage.co` 접속
2. 상단 메뉴 **"GET API KEY"** 클릭
3. 또는 직접: `alphavantage.co/support/#api-key`

### Step 2: 폼 작성
```
First Name: [이름]
Last Name: [성]
Email: [이메일 주소]
Organization: Personal Use (개인용)
Purpose: Personal Stock Market Analysis
```

### Step 3: API 키 수령
- 이메일로 API 키가 발송됨 (즉시 또는 5분 내)
- 형식: `ABC123DEF456GHI789` (16자리 알파벳+숫자)

### Step 4: 테스트
```bash
# API 호출 테스트
curl "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AAPL&apikey=YOUR_API_KEY"
```

---

## ⚠️ 무료 계정 제한

| 항목 | 제한 |
|:---|:---|
| **일일 호출량** | 25회 / day |
| **분당 호출량** | 5회 / min |
| **실시간 데이터** | 1일 지연 (전일 마감 기준) |
| **과거 데이터** | 20+년 무료 |

---

## 💡 반디 꿀팁

**32개 종목 분석하려면?**
- 무료로는 하루 25개만 가능 ❌
- **3일에 나눠서** 실행: 11+11+10개
- 또는 **유료 계정** ($49.99/month) - 무제한

**파파께 제안:**
1. 일단 무료 API 키 발급받기
2. 핵심 종목 10개만 Alpha Vantage로 테스트
3. 나머지는 Yahoo Finance 유지

**지금 바로 발급받으실래요?** 🐾

링크: https://www.alphavantage.co/support/#api-key
