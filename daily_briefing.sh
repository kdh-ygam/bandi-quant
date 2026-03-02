#!/bin/zsh
# 파파의 아침 브리핑 - 매일 7시 실행

cd /Users/mchom/.openclaw/workspace

# 환경 변수 로드 (보안을 위해 .env 파일에서)
if [ -f .env ]; then
    source .env
fi

# Python 브리핑 실행
python3 bandi_quant_v40.py 2>&1 | tee -a logs/briefing_cron.log
