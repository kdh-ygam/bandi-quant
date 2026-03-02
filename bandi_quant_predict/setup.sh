#!/bin/bash
# 반디 퀀트 - 패키지 설치 스크립트
# macOS용 가이드

echo "🐾 반디 퀀트 - 패키지 설치 시작"
echo "================================"

# 1. 홈 디렉토리로 이동
cd ~

# 2. 가상환경 생성
echo "1️⃣ Python 가상환경 생성 중..."
python3 -m venv bandi_env

# 3. 가상환경 활성화
echo "2️⃣ 가상환경 활성화 중..."
source bandi_env/bin/activate

# 4. 패키지 업그레이드
echo "3️⃣ pip 업그레이드 중..."
pip install --upgrade pip

# 5. 필요한 패키지 설치
echo "4️⃣ 필요한 패키지 설치 중..."
pip install yfinance pandas numpy scikit-learn joblib requests matplotlib

echo ""
echo "✅ 설치 완료!"
echo ""
echo "💡 이제 시스템 실행:"
echo "  source ~/bandi_env/bin/activate"
echo "  cd ~/.openclaw/workspace/bandi_quant_predict"
echo "  python main.py --mode=train"
