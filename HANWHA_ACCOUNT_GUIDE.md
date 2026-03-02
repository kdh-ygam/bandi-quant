# 한국투자증권 계좌 개설 및 API 신청 가이드

## 🎯 목표
한국투자증권 KIS API 사용을 위한 계좌 개설

---

## 📋 Step 1: 계좌 개설 (비대면)

### 1-1. 홈페이지 접속
```
https://www.hanwhawm.com/
```

### 1-2. 계좌 개설 메뉴
- 상단 "계좌개설" → "비대면 계좌개설" 클릭
- 또는 앱에서 "한국투자증권" 설치

### 1-3. 준비물
- ✅ 신분증 (주민등록증 또는 운전면허증)
- ✅ 본인 명의 휴대폰
- ✅ 입출금 계좌 (타 은행 계좌 있어야 함)
- ⏱️ 소요시간: 약 15-20분

### 1-4. 개설 절차
```
1. 본인인증 (휴대폰 인증)
2. 신분증 촬영 및 인식
3. 계좌 정보 입력
4. 전자서명
5. 계좌 개설 완료!
```

**주의사항:**
- 주식/파생상품 계좌 모두 개설 권장
- **모의투자 계좌**도 함께 신청!

---

## 📋 Step 2: 모의투자 계좌 생성

### 2-1. 홈페이지/앱 로그인
- 개설한 계정으로 로그인

### 2-2. 모의투자 접속
```
홈 → 모의투자 → 모의투자 참여
```

### 2-3. 가상 계좌 생성
- 가상 자본금: 보통 1억원 제공
- 별도 승인 없이 즉시 생성됨

---

## 📋 Step 3: API 키 발급 신청

### 3-1. API 포털 접속
```
https://apiportal.hanwhawm.com/
```

### 3-2. 회원가입
```
- 개인회원 선택
- 아이디/비밀번호 설정
- 이메일 인증
- 약관 동의
```

### 3-3. API 신청
```
1. [API 서비스] → [국내주식] 선택
2. [API Key 발급] 클릭
3. 사용 목적: 개인 투자/분석 용도
4. 계좌 정보 입력 (주식계좌번호 입력)
5. 승인 대기 (즉시~3영업일)
```

### 3-4. 필요 정보
```
발급 후 확인할 정보:
- API Key (appkey)
- API Secret (appsecret)
- Access Token (발급 후 자동 생성)
```

---

## 🔧 API 사용 예시

### Python 코드 예시
```python
import requests
import json

# 설정
APP_KEY = 'your_app_key_here'
APP_SECRET = 'your_app_secret_here'
ACCOUNT_NO = 'your_account_number_here'

# OAuth2 인증
def get_access_token():
    url = 'https://openapi.hanwhawm.com:10000/oauth2/token'
    headers = {'content-type': 'application/json'}
    body = {
        'grant_type': 'client_credentials',
        'appkey': APP_KEY,
        'appsecret': APP_SECRET
    }
    
    res = requests.post(url, headers=headers, data=json.dumps(body))
    return res.json()['access_token']

# 주식 현재가 조회
def get_stock_price(ticker):
    token = get_access_token()
    url = f'https://openapi.hanwhawm.com:10000/stock/v1/quotations/inquire-price?FID_COND_MRKT_DIV_CODE=J&FID_INPUT_ISCD={ticker}'
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'authorization': f'Bearer {token}',
        'appkey': APP_KEY,
        'appsecret': APP_SECRET
    }
    
    res = requests.get(url, headers=headers)
    return res.json()

# 사용
price_data = get_stock_price('000660')  # SK하이닉스
print(price_data)
```

---

## ⚠️ 주의사항

### 무료 vs 유료
- **모의투자 계좌**: 무료, API 사용 가능
- **실제 계좌**: API 사용 가능, 실제 거래 수수료 발생

### Rate Limit
- 실시간 시세: 초당 5건 제한
- 과거 데이터: 분당 100건 제한
- 초과시 일정 시간 차단됨

### 보안
- API 키는 절대로 코드에 하드코딩하지 말 것
- 파일로 분리 저장 후 .gitignore에 추가
```
# .gitignore
kis_api_key.txt
kis_api_secret.txt
```

---

## 📞 문의처

### 한국투자증권 고객센터
- ☎️ 1588-6100
- 상담시간: 평일 08:30~17:30

### API 개발자 문의
```
- 홈페이지: https://apiportal.hanwhawm.com/
- Q&A 게시판: API 포털 내 "문의하기"
```

---

## ✅ 완료 체크리스트

### 파파가 해야 할 일
- [ ] 한국투자증권 홈페이지 접속
- [ ] 비대면 계좌 개설 시작
- [ ] 신분증/휴대폰 준비
- [ ] 약 20분 소요 예상
- [ ] 모의투자 계좌 생성
- [ ] API 포털 가입
- [ ] API 키 신청
- [ ] 승인 대기 (최대 3일)
- [ ] 반디에게 API 키 전달 (appkey, appsecret)

---

## 🐾 반디가 할 일 (파파가 완료 후)
- [ ] API 통합 코드 작성
- [ ] 3개 오류 종목 데이터 받아오기
- [ ] 반디 퀀트에 연동
- [ ] 32개 종목 모두 브리핑 가능!

---

**지금 바로 시작할까요?** 🏦

링크: https://www.hanwhawm.com/
