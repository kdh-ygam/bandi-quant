#!/bin/zsh
# 파파의 일일 주식 브리핑 - 매일 저녁 8시 실행

cd /Users/mchom/.openclaw/workspace/quant-trader

# 로그 파일
LOG_FILE="/Users/mchom/.openclaw/workspace/quant-trader/logs/stock_briefing_$(date +%Y%m%d).log"
RESULT_FILE="/Users/mchom/.openclaw/workspace/quant-trader/logs/today_stocks.txt"

echo "🚀 $(date): 주식 브리핑 시작" >> "$LOG_FILE"

# 종목 추천 실행
/Users/mchom/.openclaw/.venv/bin/python3 recommender.py > "$RESULT_FILE" 2>> "$LOG_FILE"

# 텔레그램으로 결과 전송 (간단 버전)
if [ -s "$RESULT_FILE" ]; then
    echo "✅ $(date): 브리핑 완료" >> "$LOG_FILE"
    echo "파파! 오늘의 추천 종목이 준비됐어요!" >> "$LOG_FILE"
else
    echo "❌ $(date): 실행 실패" >> "$LOG_FILE"
fi
