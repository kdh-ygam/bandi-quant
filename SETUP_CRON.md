# ⚙️ 반디 퀀트 (BANDI QUANT) - Cron 설정 가이드

> **반디 퀀트 자동화 설정**  
> 매일 6시 30분 자동 브리핑을 위한 설정

---

## 🕐 매일 자동 실행 설정

### 1. Cron 편집기 열기
```bash
crontab -e
```

### 2. 매일 오전 6:30 KST 실행 설정 추가
```cron
# 📊 반디 퀀트 - 매일 평일 06:30 KST 실행
30 6 * * 1-5 /opt/homebrew/bin/python3 /Users/mchom/.openclaw/workspace/daily_market_briefing.py >> /Users/mchom/.openclaw/workspace/logs/cron.log 2>&1

# 🔍 테스트용: 5분마다 실행
# */5 * * * * /opt/homebrew/bin/python3 /Users/mchom/.openclaw/workspace/daily_market_briefing.py >> /Users/mchom/.openclaw/workspace/logs/cron.log 2>&1
```

### 3. 로그 디렉토리 생성
```bash
mkdir -p /Users/mchom/.openclaw/workspace/logs
mkdir -p /Users/mchom/.openclaw/workspace/analysis
```

### 4. Cron 설정 확인
```bash
crontab -l
```

### 5. Cron 서비스 재시작 (macOS)
```bash
# macOS에서는 launchd 사용
# 크론 설정하면 자동으로 적용됨
```

---

## 📋 수동 실행 방법

### 지금 바로 테스트
```bash
python3 /Users/mchom/.openclaw/workspace/daily_market_briefing.py
```

### 백그라운드 실행
```bash
nohup python3 /Users/mchom/.openclaw/workspace/daily_market_briefing.py &
```

---

## 🔔 알림 설정 (추가)

### 급등/급락 알림 (실시간)
```cron
# 매 30분마다 급등주 체크
*/30 9-16 * * 1-5 /opt/homebrew/bin/python3 /Users/mchom/.openclaw/workspace/alert_system.py
```

---

## 📁 파일 구조

```
/Users/mchom/.openclaw/workspace/
├── daily_market_briefing.py    # 메인 스크립트
├── telegram_stock_bot.py       # 실시간 시세 봇
├── analysis/                   # 분석 결과 저장
│   ├── daily_briefing_2026-02-26.json
│   └── daily_briefing_2026-02-27.json
├── logs/                       # 실행 로그
│   └── cron.log
└── HEARTBEAT.md               # 매일 체크리스트
```

---

## ⚠️ 주의사항

1. **ddgs API**: 분당 요청 제한 준수 (1초 간격)
2. **Yahoo Finance**: IP 제한 방지를 위한 딜레이 (1초)
3. **Telegram Rate Limit**: 초당 30메시지 제한
4. **CLOVA TTS**: 월 10,000자 한도 확인

---

## 🎯 최종 설정 요약

| 기능 | 설정값 | 실행 시간 |
|------|--------|----------|
| **장마감 브리핑** | 매일 평일 06:30 KST | 미국 장 마감 30분 후 |
| **급등 알림** | +/- 5% 이상 | 실시간 (30분 간격) |
| **음성 브리핑** | 파파 승인 후 | 수동 트리거 |

---

## 🚀 빠른 시작

```bash
# 1. 로그 디렉토리 생성
mkdir -p ~/logs

# 2. Cron 설정
crontab -e

# 3. 아래 라인 추가
30 6 * * 1-5 /opt/homebrew/bin/python3 /Users/mchom/.openclaw/workspace/daily_market_briefing.py 2>&1

# 4. 저장 후 종료 (Ctrl+X, Y, Enter)

# 5. Cron 확인
crontab -l
```

---

*설정 완료! 매일 아침 6시 30분 자동으로 브리핑 도착!* 📱

---

🐾 반디 퀀트 (BANDI QUANT) v1.0
Created by 반디 for 파파 | 2026-02-25
