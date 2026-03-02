# 경매 투자 분석 툴 - Phase 1
# 파파의 ��똘한 경매 도우미

## 프로젝트 구조
```
auction-tool/
├── config.py          # 설정 파일
├── requirements.txt   # 필요 패키지
├── scraper/          # 데이터 수집 모듈
│   ├── __init__.py
│   ├── ggi_scraper.py
│   └── court_scraper.py
├── analyzer/         # AI 분석 모듈
│   ├── __init__.py
│   ├── document_analyzer.py
│   └── rights_analyzer.py
├── calculator/       # 수익성 계산
│   ├── __init__.py
│   ├── tax_calculator.py
│   └── roi_simulator.py
├── notifier/         # 알림 모듈
│   ├── __init__.py
│   └── telegram_bot.py
├── database/         # 데이터 저장
│   └── auction_db.py
├── dashboard/        # 웹 대시보드
│   └── app.py
└── logs/            # 로그 파일
```

## Phase 1 목표
- [x] 프로젝트 구조 생성
- [x] 설정 파일 작성
- [x] requirements.txt 작성
- [x] 기본 모듈 구조 설정

## 다음 단계 (Phase 2)
- 지지옥션 크롤러 개발
- 데이터 수집 테스트
