# 네이버 CLOVA 설정 확인 체크리스트

## 1. 서비스 활성화 확인
👉 https://www.ncloud.com 접속
- 로그인 → 콘솔 → AI Services → CLOVA Speech
- "서비스 활성화" 버튼 클릭 (비활성화 상태면 버튼 보임)

## 2. API 키 재발급
- 좌측 메뉴 "인증키 관리"
- 기존 키 삭제 후 "인증키 발급" 
- 또는 새 Application 생성

## 3. 권한 확인
- Application 클릭 → "API 설정"
- CLOVA Speech (CSpeech) 체크되어 있는지 확인

## 4. IP 제한 확인
- "환경 설정" → 접근 IP 제한 해제 또는 현재 IP 추가

## 테스트 명령어 (터미널에서 직접 실행)

```bash
curl -X POST "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts" \
  -H "X-NCP-APIGW-API-KEY-ID: 여기에_새_Client_ID" \
  -H "X-NCP-APIGW-API-KEY: 여기에_새_Client_Secret" \
  -d "speaker=nara&volume=0&speed=0&pitch=0&format=mp3&text=안녕하세요" \
  -o test.mp3 && afplay test.mp3
```

✅ test.mp3 재생되면 성공!
