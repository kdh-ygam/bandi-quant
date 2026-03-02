#!/usr/bin/env python3
"""
파파의 아침 브리핑 - 음성/텍스트 버전
- 평일: 네이버 CLOVA 음성
- 주말: 텍스트만
"""

import os
import sys
import json
import requests
import subprocess
from datetime import datetime
from pathlib import Path

# 설정
CACHE_DIR = Path("/Users/mchom/.openclaw/workspace/cache")
LOG_DIR = Path("/Users/mchom/.openclaw/workspace/logs")
CACHE_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# API 키
NAVER_CLIENT_ID = os.getenv("NAVER_CLOVA_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLOVA_CLIENT_SECRET", "")

def search_x(keyword, count=3):
    """X에서 검색"""
    try:
        result = subprocess.run(
            ["xurl", "search", f"{keyword} -is:retweet", "-n", str(count * 2)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            tweets = data.get("data", [])
            results = []
            for tweet in tweets[:count]:
                text = tweet.get("text", "").replace("\n", " ")[:150]
                author = tweet.get("author_id", "unknown")
                results.append(f"@{author}: {text}")
            return results
    except:
        pass
    return ["검색 결과 없음"]

def create_briefing_text():
    """브리핑 텍스트 생성"""
    today = datetime.now().strftime("%Y년 %m월 %d일")
    weekday = ["월","화","수","목","금","토","일"][datetime.now().weekday()]
    
    lines = [
        f"안녕하세요 파파. {today} {weekday}요일 아침 브리핑입니다.",
        "",
        "📊 비트코인 소식:",
    ]
    lines.extend(search_x("Bitcoin OR BTC", 2))
    lines.extend(["", "🎯 팔란티어 소식:"])
    lines.extend(search_x("Palantir OR PLTR", 2))
    lines.extend(["", "🚗 테슬라 소식:"])
    lines.extend(search_x("Tesla OR TSLA", 2))
    lines.extend(["", "브리핑 끝. 좋은 아침 되세요!"])
    
    return "\n".join(lines)

def text_to_speech_naver(text, output_file):
    """네이버 CLOVA 음성 변환"""
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("⚠️ 네이버 API 키 없음")
        return False
    
    url = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"
    data = {
        "speaker": "nshasha",  # 샤샤 (여성)
        "volume": "0",
        "speed": "-1",
        "pitch": "0",
        "format": "mp3",
        "text": text[:1000]  # 너무 길면 자름
    }
    headers = {
        "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET,
    }
    
    try:
        response = requests.post(url, data=data, headers=headers, timeout=60)
        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"❌ TTS 실패: {e}")
    return False

def send_telegram_text(text, caption=""):
    """텔레그램 텍스트 전송"""
    try:
        msg = f"{caption}\n\n{text}" if caption else text
        for chunk in [msg[i:i+3000] for i in range(0, len(msg), 3000)]:
            subprocess.run(
                ["openclaw", "message", "send", "--channel", "telegram",
                 "--target", "6146433054", "--message", chunk],
                capture_output=True, timeout=30
            )
        return True
    except:
        return False

def send_telegram_audio(audio_file, caption=""):
    """텔레그램 음성 전송"""
    try:
        subprocess.run(
            ["openclaw", "message", "send", "--channel", "telegram",
             "--target", "6146433054", "--file", str(audio_file), "--caption", caption],
            capture_output=True, timeout=30
        )
        return True
    except:
        return False

def is_weekend():
    """주말 체크 (토=5, 일=6)"""
    return datetime.now().weekday() >= 5

def main():
    print("🌅 브리핑 시작...")
    
    # 브리핑 텍스트 생성
    text = create_briefing_text()
    text_file = LOG_DIR / f"briefing_{datetime.now():%Y%m%d}.txt"
    text_file.write_text(text, encoding='utf-8')
    print(f"📝 저장: {text_file}")
    
    caption = f"📅 {datetime.now():%Y-%m-%d} 아침 브리핑"
    
    if is_weekend():
        # 주말: 텍스트
        print("📅 주말 → 텍스트 전송")
        send_telegram_text(text, caption)
    else:
        # 평일: 음성
        print("📅 평일 → 음성 전송")
        audio_file = LOG_DIR / f"briefing_{datetime.now():%Y%m%d}.mp3"
        if text_to_speech_naver(text, audio_file):
            if not send_telegram_audio(audio_file, caption):
                send_telegram_text(text, caption)
        else:
            send_telegram_text(text, caption)
    
    print("✅ 완료!")

if __name__ == "__main__":
    main()
