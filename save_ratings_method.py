    def save_ratings_md(self):
        """매수/매도 평가 및 사유를 마크다운으로 저장"""
        ratings_dir = "/Users/mchom/.openclaw/workspace/analysis/ratings"
        os.makedirs(ratings_dir, exist_ok=True)
        
        filename = f"{ratings_dir}/{self.date_str}_briefing.md"
        
        # 매수/매도/보유 분류
        buys = [s for s in self.results if '매수' in s.recommendation]
        sells = [s for s in self.results if '매도' in s.recommendation]
        holds = [s for s in self.results if '보유' in s.recommendation]
        
        # 마크다운 생성
        md_content = f"""# 반디 퀀트 브리핑 - {self.date_str}

| 항목 | 수량 |
|:---|:---:|
| 총 종목 | {len(self.results)}개 |
| 매수 권유 | {len(buys)}개 |
| 매도 권고 | {len(sells)}개 |
| 보유 | {len(holds)}개 |

## 매수 권유
| 종목 | 현재가 | RSI | 등락률 | 사유 |
|:---|:---:|:---:|:---:|:---|
"""
        for stock in buys:
            unit = "원" if stock.currency == 'KRW' else "$"
            price_str = f"{int(stock.current_price):,}{unit}" if stock.currency == 'KRW' else f"{unit}{stock.current_price:,.2f}"
            md_content += f"| {stock.name} | {price_str} | {stock.rsi} | {stock.change_pct:+.2f}% | {stock.comment} |\n"
        
        md_content += "\n## 매도 권고\n| 종목 | 현재가 | RSI | 등락률 | 사유 |\n|:---|:---:|:---:|:---:|:---|\n"
        for stock in sells:
            unit = "원" if stock.currency == 'KRW' else "$"
            price_str = f"{int(stock.current_price):,}{unit}" if stock.currency == 'KRW' else f"{unit}{stock.current_price:,.2f}"
            md_content += f"| {stock.name} | {price_str} | {stock.rsi} | {stock.change_pct:+.2f}% | {stock.comment} |\n"
        
        md_content += "\n## 보유 (Top 10)\n| 종목 | 현재가 | RSI | 등락률 | 사유 |\n|:---|:---:|:---:|:---:|:---|\n"
        for stock in holds[:10]:
            unit = "원" if stock.currency == 'KRW' else "$"
            price_str = f"{int(stock.current_price):,}{unit}" if stock.currency == 'KRW' else f"{unit}{stock.current_price:,.2f}"
            md_content += f"| {stock.name} | {price_str} | {stock.rsi} | {stock.change_pct:+.2f}% | {stock.comment} |\n"
        
        md_content += f"\n\n*생성시간: {self.time_str} | 반디 퀀트*"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"📝 평가 기록 저장: {filename}")
