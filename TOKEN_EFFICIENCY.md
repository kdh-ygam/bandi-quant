# Token Efficiency & Caching

파파의 요구사항: 토큰을 최대한 절약해서 사용하기!

## 적용 전략

### 1. 파일 캐싱
- 세션 내에서 같은 파일 반복 읽기 방지
- `read_cache` 사용하여 이미 읽은 파일은 메모리에서 재사용

### 2. 웹 검색 캐싱
- 자주 검색하는 주제는 결과 캐싱
- 동일 쿼리는 1시간 내 재검색 안 함

### 3. 응답 최적화
- 불필요한 서론/결론 생략
- 핵심만 간결하게
- 코드 블록 활용 (텍스트보다 효율적)

### 4. 스마트 도구 선택
- 복잡한 브라우저 자동화 대신 `web_fetch` 우선 사용
- `summarize`로 긴 내용 압축 후 분석

---

## 캐시 저장소

`/Users/mchom/.openclaw/workspace/cache/` 디렉토리 사용
- `search_cache.json` - 검색 결과 캐시
- `file_cache.json` - 파일 내용 캐시
- `web_cache.json` - 웹 페이지 캐시

TTL (Time To Live):
- 검색: 1시간
- 파일: 세션 종료 시
- 웹 페이지: 30분
