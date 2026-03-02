#!/bin/zsh
# 파파 주중 브리핑 - 월-금 새벽 6시 (미국장 마감 후)

cd /Users/mchom/.openclaw/workspace/quant-trader

# 요일 확인 (1=월요일, 5=금요일)
DOW=$(date +%u)

if [ "$DOW" -ge 6 ]; then
    # 주말이면 실행 안함
    exit 0
fi

# 브리핑 실행
/Users/mchom/.openclaw/.venv/bin/python3 weekly_recommender.py > "/Users/mchom/.openclaw/workspace/quant-trader/logs/briefing_$(date +%Y%m%d).log" 2>&1

# 결과 파일로 저장
TIMESTAMP=$(date +"%Y-%m-%d %H:%M")
echo "=== 파파 주중 브리핑 $TIMESTAMP ===" >> /Users/mchom/.openclaw/workspace/quant-trader/logs/weekday_briefing.txt
python3 weekly_recommender.py >> /Users/mchom/.openclaw/workspace/quant-trader/logs/weekday_briefing.txt 2>&1

# 금요일이면 평가도 실행
if [ "$DOW" -eq 5 ]; then
    echo "" >> /Users/mchom/.openclaw/workspace/quant-trader/logs/weekday_briefing.txt
    echo "=== 주간 성과 평가 ===" >> /Users/mchom/.openclaw/workspace/quant-trader/logs/weekday_briefing.txt
    python3 weekly_recommender.py evaluate >> /Users/mchom/.openclaw/workspace/quant-trader/logs/weekday_briefing.txt 2>&1
fi
