# 반디 퀀트 v4.0 리팩토링 제안서

## 📋 파일 개요

| 항목 | 내용 |
|------|------|
| 파일명 | `bandi_quant_v40.py` |
| 라인 수 | 약 930줄 |
| 주요 기능 | 43개 종목 기술적 분석 + ML 예측 + 텔레그램 브리핑 |

---

## 🔍 주요 기능 분석

### 1. 시스템 아키텍처
```
┌─────────────────────────────────────────────────────────────┐
│                    BandiQuantV40 (메인 클래스)               │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ FeatureEngineer│ │ PatternDetector│ │ BandiAI      │      │
│  │ (24가지 지표)  │  │ (14가지 패턴)  │  │ (AI 의견)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ MLPredictor  │  │ StockAnalysis│ │ Telegram     │      │
│  │ (RandomForest)│  │ (데이터클래스)│  │ (알림 전송)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 2. 핵심 기능

| 모듈 | 설명 | 비고 |
|------|------|------|
| **FeatureEngineer** | RSI, MACD, 볼린저밴드 등 24가지 기술지표 계산 | 중복 계산 존재 |
| **MLPredictor** | Random Forest 기반 5일 후 상승/하락 예측 | 규칙 기반 Fallback |
| **PatternDetector** | 망치형, 잉걸불 등 14가지 캔들 패턴 감지 | |
| **BandiAI** | 기술지표 기반 의견 및 전략 생성 | 단순 조건문 |
| **차트 생성** | chart_standard 연동 (신호 표시) | 외부 모듈 의존 |

---

## ⚠️ 주요 문제점

### 1. 코드 중복 (DRY 위반)

```python
# ❌ FeatureEngineer.calculate_all_features()에서 RSI 계산
# ❌ analyze_stock()에서 RSI 다시 계산
delta = df['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
# ... 같은 코드 반복
```

### 2. 설정값 하드코딩

```python
# ❌ 민감정보 노출
TELEGRAM_TOKEN = "8599663503:AAGfs7Sh2vy6tfHOr9UG..."
CHAT_ID = "6146433054"

# ❌ 매직넘버
if rsi < 35:  score += 3
elif rsi < 45:  score += 2
elif rsi < 50:  score += 1
```

### 3. 긴 메서드 (Single Responsibility 위반)

| 메서드 | 라인 수 | 책임 |
|--------|---------|------|
| `analyze_stock` | ~180줄 | 데이터 수집 + 지표 계산 + 패턴 감지 + 분석 |
| `generate_and_send` | ~120줄 | 메시지 생성 + 차트 호출 + 전송 + 저장 |

### 4. 예외 처리 불일치

```python
# ✅ 일관된 예외 처리 필요
try:
    df = yf.download(ticker, period="6mo")
except Exception as e:  # 너무 광범위
    print(f"❌ 오류: {e}")  # 단순 출력만
```

### 5. 테스트 불가능한 구조
- 외부 API(yfinance, 텔레그램)와 직접 결합
- Mock/Stub 대체 어려움

---

## 🛠️ 리팩토링 제안

### 1. 구조적 개선 (모듈 분리)

```
bandi_quant/
├── __init__.py
├── config.py              # 설정 중앙화
├── models/
│   ├── __init__.py
│   ├── stock_data.py      # StockAnalysis dataclass
│   └── signals.py         # 매매신호 Enum
├── services/
│   ├── __init__.py
│   ├── data_fetcher.py    # yfinance 래퍼
│   ├── technical.py       # 기술지표 계산
│   ├── predictor.py       # ML 예측
│   ├── pattern.py         # 패턴 감지
│   └── notifier.py        # 텔레그램 전송
├── analysis/
│   ├── __init__.py
│   ├── bandi_ai.py        # 의견 생성
│   └── grader.py          # 등급 판정
└── cli.py
```

### 2. 설정값 추출 (config.py)

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    telegram_token: str
    chat_id: str
    min_data_days: int = 30
    rsi_threshold_buy: float = 35.0
    rsi_threshold_sell: float = 70.0
    ml_confidence_threshold: float = 0.6
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
```

### 3. 의존성 역전 (Interface 분리)

```python
from abc import ABC, abstractmethod

class DataProvider(ABC):
    @abstractmethod
    def fetch(self, ticker: str, period: str) -> pd.DataFrame:
        ...

class YFinanceProvider(DataProvider):
    def fetch(self, ticker: str, period: str) -> pd.DataFrame:
        return yf.download(ticker, period=period, progress=False)

class MLModel(ABC):
    @abstractmethod
    def predict(self, features: Dict) -> Tuple[str, float]:
        ...
```

### 4. 기술지표 캐싱 (중복 제거)

```python
class TechnicalAnalyzer:
    def __init__(self):
        self._cache: Dict[str, pd.DataFrame] = {}
    
    def analyze(self, ticker: str, df: pd.DataFrame) -> TechnicalIndicators:
        if ticker in self._cache:
            return self._cache[ticker]
        
        indicators = TechnicalIndicators(
            rsi=self._calc_rsi(df),
            macd=self._calc_macd(df),
            bb=self._calc_bollinger(df),
            # ...
        )
        self._cache[ticker] = indicators
        return indicators
```

### 5. 메서드 분해 (analyze_stock 예시)

```python
# 리팩토링 전: 하나의 긴 메서드
def analyze_stock(self, ticker, info):
    df = yf.download(...)          # 20줄
    # 지표 계산 (RSI, MACD...)      # 80줄
    # 패턴 감지                      # 20줄
    # ML 예측                        # 15줄
    # 의견 생성                      # 10줄

# 리팩토링 후: 작고 명확한 메서드들
def analyze_stock(self, ticker: str, info: Dict) -> Optional[StockAnalysis]:
    df = self.data_fetcher.fetch(ticker)
    if not self._validate_data(df):
        return None
    
    indicators = self.technical_analyzer.analyze(ticker, df)
    patterns = self.pattern_detector.detect(df)
    prediction = self.ml_predictor.predict(indicators)
    
    return self._build_analysis(ticker, info, indicators, patterns, prediction)
```

### 6. 결과 객체 일관화

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from decimal import Decimal

class SignalType(Enum):
    STRONG_BUY = "🟢 강력매수"
    BUY = "🟡 매수권유"
    HOLD = "⚪ 보유"
    SELL = "🟠 매도권유"
    STRONG_SELL = "🔴 강력매도"

@dataclass(frozen=True)
class StockAnalysis:
    ticker: str
    name: str
    current_price: Decimal
    change_pct: float
    rsi: float
    signal: SignalType
    ml_prediction: Optional[PredictionResult]
    patterns: List[Pattern]
    recommendation: str
    
    @property
    def is_buy_signal(self) -> bool:
        return self.signal in (SignalType.STRONG_BUY, SignalType.BUY)
```

### 7. 책임 기반 클래스 재설계

```python
# 기술 지표 계산만 담당
class TechnicalAnalyzer:
    def __init__(self, config: TechnicalConfig):
        self.rsi_period = config.rsi_period
        self.bb_period = config.bb_period
    
    def calculate_all(self, df: pd.DataFrame) -> TechnicalMetrics:
        return TechnicalMetrics(
            rsi=self._rsi(df),
            macd=self._macd(df),
            bollinger=self._bollinger(df),
        )

# 등급 판정만 담당
class GradeCalculator:
    def calculate(self, metrics: TechnicalMetrics, 
                  prediction: MLPrediction) -> SignalType:
        score = self._calculate_score(metrics, prediction)
        return self._score_to_signal(score)
```

### 8. 테스트 가능한 설계

```python
# 테스트 가능하도록 인터페이스 기반 설계
class TestDataProvider(DataProvider):
    def __init__(self, fixture_data: Dict):
        self._data = fixture_data
    
    def fetch(self, ticker: str, period: str) -> pd.DataFrame:
        return self._data.get(ticker, pd.DataFrame())

# 단위 테스트 예시
def test_rsi_calculation():
    analyzer = TechnicalAnalyzer()
    df = load_test_data("sample_stock.csv")
    
    rsi = analyzer._calc_rsi(df)
    
    assert rsi == pytest.approx(45.2, rel=0.01)
```

---

## 📊 우선순위 및 작업 순서

| 우선순위 | 항목 | 예상 소요 | 효과 |
|----------|------|-----------|------|
| P0 | 민감정보 환경변수 분리 | 1시간 | 보안 |
| P0 | 기술지표 중복 계산 제거 | 2시간 | 성능 |
| P1 | 메서드 분해 | 4시간 | 유지보수 |
| P1 | 설정값 상수화 | 2시간 | 가독성 |
| P2 | 모듈 분리 | 8시간 | 확장성 |
| P2 | 인터페이스 추출 | 4시간 | 테스트 |
| P3 | 캐싱 레이어 추가 | 4시간 | 성능 |

---

## 💡 간단한 개선 예시 (Quick Win)

### before
```python
# 같은 RSI 계산 3곳에서 반복
# 예외 처리 일관성 없음
# 매직넘버 하드코딩
```

### after (간소화)
```python
# config.py
RSI_CONFIG = {
    "period": 14,
    "oversold": 35,
    "overbought": 70,
}

# technical.py
class TechnicalCalculator:
    CALC_METHODS = {
        "rsi": _calc_rsi,
        "macd": _calc_macd,
        "bb": _calc_bollinger,
    }
    
    def calculate(self, df: pd.DataFrame, 
                  indicators: List[str]) -> Dict:
        return {
            name: method(df) 
            for name, method in self.CALC_METHODS.items()
            if name in indicators
        }
```

---

## 🎯 요약

| 현재 상태 | 개선 후 기대 효과 |
|-----------|------------------|
| 단일 파일 ~930줄 | 모듈화된 구조 (6~8개 파일) |
| 코드 중복 다수 | 중복 제거 + 캐싱 적용 |
| 설정 하드코딩 | 환경변수 기반 설정 |
| 긴 메서드 | 평균 20줄 이하 메서드 |
| 테스트 불가능 | 단위 테스트 가능 구조 |

> **요약**: 설정 분리 → 중복 제거 → 메서드 분해 → 모듈화 순서로 단계적으로 리팩토링 권장
