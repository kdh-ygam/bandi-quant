#!/bin/bash
# 한국어 TTS 목소리 테스트 스크립트

test_text="안녕하세요 파파, QuantumScape 분석입니다. 현재가는 7달러 3센트입니다."
output_dir="/Users/mchom/.openclaw/workspace"

# 여러 목소리 테스트
voices=("Yuna" "Eddy" "Flo" "Grandma" "Grandpa" "Reed" "Rocko" "Sandy" "Shelley")

for voice in "${voices[@]}"; do
    echo "Testing $voice..."
    say -v "$voice (한국어(대한민국))" "$test_text" -o "$output_dir/${voice}_test.aiff" 2>/dev/null || \
    say -v "$voice" "$test_text" -o "$output_dir/${voice}_test.aiff" 2>/dev/null || \
    echo "  $voice failed"
done

echo "All tests completed!"
ls -lh $output_dir/*.aiff | grep test
