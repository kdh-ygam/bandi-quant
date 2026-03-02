# 네이버 CLOVA Voice 설정 가이드

## 1. 네이버 클라우드 플랫폼 가입
👉 https://www.ncloud.com

## 2. AI Services → CLOVA Speech 활성화
- 콘솔 로그인 → AI Services → CLOVA Speech
- "서비스 활성화" 클릭

## 3. API 키 발급
- 좌측 메뉴 "인증키 관리" 클릭
- "인증키 발급" 버튼 클릭
- **Application 이름**: 파파브리핑 (아무 이름 가능)
- **Service 선택**: CLOVA Speech (CSpeech)
- 발급 완료 시 **Client ID**와 **Client Secret** 확인

## 4. 환경 변수 설정 (터미널에서 실행)

```bash
# .zshrc에 추가
echo 'export NAVER_CLOVA_CLIENT_ID="발급받은_Client_ID"' >> ~/.zshrc
echo 'export NAVER_CLOVA_CLIENT_SECRET="발급받은_Client_Secret"' >> ~/.zshrc

# 즉시 적용
source ~/.zshrc
```

## 5. 테스트
```bash
cd /Users/mchom/.openclaw/workspace
python3 briefing_voice.py
```

## 💰 요금
- CLOVA Voice: 매월 10,000자 묵음 (이후 유료)
- 브리핑 1회 약 1,000자 → 월 10회 묵음

## 🔊 음성 옵션
- `njinho`: 진호 (남성) ← 기본 설정
- `nara`: 아라 (여성)
- `nhajun`: 하준 (남성)
- `ndonghyun`: 동현 (남성)

## ⚠️ 주의사항
- Client Secret은 절대 타인과 공유하지 마세요
- API 키는 `~/.zshrc`에 저장하고, GitHub 등에 올리지 마세요
