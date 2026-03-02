#!/bin/zsh
# 파파의 음성 브리핑 - curl 버전

export NAVER_CLOVA_CLIENT_ID="8dqe4kfpmd"
export NAVER_CLOVA_CLIENT_SECRET="nU2AHDJ77VOoM0s7oPVd4EhPVzuVFbyLr2qRmYd6"

TODAY=$(date +%Y%m%d)
BRIEFING_TEXT="안녕하세요 파파. $(date +%Y년�%m월%d일) 월요일 아침 브리핑입니다.

비트코인 소식입니다. 비트코인이 6개월 만에 최저 네트워크 활동 수준을 기록했습니다. 고래들이 600억 달러어치 비트코인을 매도하며 6만 달러 붕괴 우려가 있습니다. 한편, 비트와이즈 최고투자책임자는 2050년까지 모든 중앙은행이 비트코인을 보유할 것이라고 전망했습니다. 멕시코 억만장자 살리나스는 폭락 후에도 비트코인 강세를 유지하고 있으며, Strategy는 지난주 3980만 달러로 592코인을 추가 매수했습니다.

다음은 팔란티어 소식입니다. 팔란티어는 방위, 정보, 의료, 에너지, 금융 분야에서 데이터 통합 및 대규모 분석 소프트웨어 플랫폼을 제공하고 있습니다.

마지막으로 테슬라 소식입니다. 테슬라 모델 와이가 호주에서 2026년 드라이브 올해의 차로 선정되었습니다. 일론 머스크는 FSD 슈퍼바이즈드의 가장 과소평가된 기능을 강조했으며, 유럽에서 세미 트럭 사업 확대를 위해 상업 충전 담당자를 채용하고 있습니다. FSD에 새로운 기능이 추가될 예정입니다.

브리핑 끝입니다. 좋은 하루 되세요."

echo "🎙️ 음성 변환 중..."

curl -s -X POST "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts" \
  -H "X-NCP-APIGW-API-KEY-ID: $NAVER_CLOVA_CLIENT_ID" \
  -H "X-NCP-APIGW-API-KEY: $NAVER_CLOVA_CLIENT_SECRET" \
  -d "speaker=njinho&volume=0&speed=0&pitch=0&format=mp3&text=$BRIEFING_TEXT" \
  -o "/Users/mchom/.openclaw/workspace/logs/briefing_${TODAY}.mp3"

if [[ -f "/Users/mchom/.openclaw/workspace/logs/briefing_${TODAY}.mp3" && -s "/Users/mchom/.openclaw/workspace/logs/briefing_${TODAY}.mp3" ]]; then
  echo "✅ 음성 파일 생성 완료!"
  ls -lh "/Users/mchom/.openclaw/workspace/logs/briefing_${TODAY}.mp3"
else
  echo "❌ 생성 실패"
fi
