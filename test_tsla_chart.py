from chart_module import ChartGenerator
import json

gen = ChartGenerator()

# 오늘 분석 결과에서 TSLA 정보 가져오기
with open('analysis/daily_briefing_2026-02-26.json', 'r') as f:
    data = json.load(f)

tsla_info = next((s for s in data['stocks'] if s['ticker'] == 'TSLA'), None)

if tsla_info:
    print(f"🚗 {tsla_info['name']} (TSLA) 차트 + 패턴 분석 중...")
    print(f"   현재: ${tsla_info['current_price']:.2f} ({tsla_info['change_pct']:+.2f}%)")
    print(f"   RSI: {tsla_info['rsi']} | MACD: {tsla_info['macd_trend']}")
    
    ohlcv_data = gen.fetch_ohlcv_data('TSLA', days=60)
    if ohlcv_data:
        chart_path = 'charts/chart_TSLA_pattern.png'
        success = gen.create_candlestick_chart(ohlcv_data, tsla_info, chart_path)
        
        if success:
            print(f"\n✅ 패턴 포함 차트 생성 완료!")
            print(f"📁 저장 위치: {chart_path}")
