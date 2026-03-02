# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## 🎯 파바의 필수 요구사항 (반디가 반드시 지켜야 함)

### 📈 반디 퀀트 시스템 - 차트 필수 정책

**⚠️ 중요: 모든 브리핑/예측/테스트 시 차트는 필수!**

> 🔥 **반디퀀트(자동화 시스템)에서 차트 없으면 브리핑 성립 안됨!**
> 파파가 직접 여러번 강조한 핵심 요구사항!

**차트 표시 규칙 (최종 확정 - 2026-02-28):**
```
AI 신호 표시 위치:
├─ 매수(BUY): 큰 ☝️ 파란 마커 → 캔들 바로 밑
│              └─ ⬆ STRONG BUY (작은 글씨, 마커 아래)
│
└─ 매도(SELL): 큰 👇 빨간 마커 → 캔들 바로 위
               └─ ⬇ STRONG SELL (작은 글씨, 마커 위)

위치 계산: Y축 기준 고정 간격
- 화살표: 캔들에서 Y축 범위의 1.5%
- 텍스트: 화살표에서 Y축 범위의 4%
```

**필수 체크리스트:**
- [ ] **43개 종목** 분석 시 모두 차트 생성
- [ ] **추천 종목 Top 5**는 반드시 차트와 함께 제공
- [ ] **텔레그램 브리핑**에는 차트 이미지 필수 첨부
- [ ] **6개월(120일)** 캔들스틱 차트
- [ ] **큰 화살촉 마커** (사이즈 400)
- [ ] **작은 테두리 글씨** (8pt)
- [ ] **차트 저장 위치**: `charts/{YYYYMMDD}/{ticker}_6m.png`

**확인 사항:**
- ✅ Y축 기준 위치 계산?
- ✅ 화살표: 캔들 바로 밑/위?
- ✅ 텍스트: 화살표 크기만큼 아래/위?
- ✅ 6개월 캔들스틱?
- ✅ RSI, 볼린저밴드, 이동평균선 포함?
- ✅ 텔레그램 전송 완료?

**이유**: 파파는 차트로 직구적으로 확인하고 싶어함

---

Add whatever helps you do your job. This is your cheat sheet.
