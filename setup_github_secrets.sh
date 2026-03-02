#!/bin/zsh
# GitHub Secrets 설정 스크립트
# 파파가 직접 실행하면 GitHub 저장소에 Secrets가 등록됩니다

echo "=========================================="
echo "🚀 반디 퀀트 - GitHub Secrets 설정"
echo "=========================================="
echo ""

# 환경 변수 확인
if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "❌ TELEGRAM_TOKEN이 설정되지 않았습니다"
    echo "   먼저 .env 파일을 설정하세요"
    exit 1
fi

echo "✅ 환경 변수 확인 완료"
echo ""
echo "📝 등록될 Secrets:"
echo "   • TELEGRAM_TOKEN"
echo "   • TELEGRAM_CHAT_ID"  
echo "   • NAVER_CLOVA_CLIENT_ID"
echo "   • NAVER_CLOVA_CLIENT_SECRET"
echo ""
echo "⚠️  GitHub 계정 kdh-ygam의 패스워드를 물어볼 수 있습니다"
echo ""

# GitHub CLI로 Secrets 등록
echo "🔄 Secrets 등록 중..."

# TELEGRAM_TOKEN
echo -n "   TELEGRAM_TOKEN... "
echo "$TELEGRAM_TOKEN" | gh secret set TELEGRAM_TOKEN --repo kdh-ygam/bandi-quant
echo "✅"

# TELEGRAM_CHAT_ID
echo -n "   TELEGRAM_CHAT_ID... "
echo "$TELEGRAM_CHAT_ID" | gh secret set TELEGRAM_CHAT_ID --repo kdh-ygam/bandi-quant
echo "✅"

# NAVER_CLOVA_CLIENT_ID
echo -n "   NAVER_CLOVA_CLIENT_ID... "
echo "$NAVER_CLOVA_CLIENT_ID" | gh secret set NAVER_CLOVA_CLIENT_ID --repo kdh-ygam/bandi-quant
echo "✅"

# NAVER_CLOVA_CLIENT_SECRET
echo -n "   NAVER_CLOVA_CLIENT_SECRET... "
echo "$NAVER_CLOVA_CLIENT_SECRET" | gh secret set NAVER_CLOVA_CLIENT_SECRET --repo kdh-ygam/bandi-quant
echo "✅"

echo ""
echo "=========================================="
echo "✅ GitHub Secrets 등록 완료!"
echo "=========================================="
echo ""
echo "📋 확인 방법:"
echo "   https://github.com/kdh-ygam/bandi-quant/settings/secrets/actions"
echo ""
echo "🎯 다음 단계:"
echo "   1. GitHub 저장소 → Actions 탭 확인"
echo "   2. 'Daily Market Briefing' 워크플로우 확인"
echo "   3. 'Run workflow' 버튼으로 테스트"
echo ""
