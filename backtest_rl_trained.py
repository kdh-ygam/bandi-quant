#!/usr/bin/env python3
"""RL 트레이더 백테스팅 스크립트"""

import os
import json
import pandas as pd
import numpy as np
import yfinance as yf
from stable_baselines3 import PPO
from datetime import datetime, timedelta

# 모델 파일 패턴
MODEL_DIR = './trained_models'
INITIAL_CAPITAL = 10000
TEST_DAYS = 180

def calculate_indicators(df):
    """기술적 지표 계산"""
    df = df.copy()
    
    # Flatten MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std.squeeze() * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std.squeeze() * 2)
    
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    
    return df

def build_state(df, i, position, capital):
    """RL State 구성"""
    row = df.iloc[i]
    
    state = [
        float(row['Close'] / row['SMA_20'] - 1) if row['SMA_20'] > 0 else 0,
        float(row['SMA_20'] / row['SMA_50'] - 1) if row['SMA_50'] > 0 else 0,
        float(row['RSI'] / 100),
        float((row['Close'] - row['BB_Lower']) / (row['BB_Upper'] - row['BB_Lower']) if row['BB_Upper'] != row['BB_Lower'] else 0.5),
        float(row['MACD_Hist'] / row['Close'] if row['Close'] > 0 else 0),
        float(row['ATR'] / row['Close'] if row['Close'] > 0 else 0),
        float(row['Volume'] / df['Volume'].iloc[i-20:i].mean() - 1) if 'Volume' in df else 1.0,
        float((row['Close'] - df['Close'].iloc[i-10]) / df['Close'].iloc[i-10]) if i >= 10 else 0,
        float((row['Close'] - df['Close'].iloc[i-20]) / df['Close'].iloc[i-20]) if i >= 20 else 0,
        float(position > 0),
        float(position * row['Close'] / capital if position > 0 else 0),
        float(1 if row['Close'] > row['SMA_20'] else 0),
        float(row['RSI'] / 50 - 1),
        float(1 if row['MACD_Hist'] > 0 else 0),
        float(0)
    ]
    return np.array(state, dtype=np.float32)

def backtest_ticker(ticker, model_path):
    """개별 종목 백테스팅"""
    print(f"\n📊 {ticker}")
    
    try:
        model = PPO.load(model_path)
    except Exception as e:
        print(f"  ❌ Model load failed: {e}")
        return None
    
    # Download data
    end = datetime.now()
    start = end - timedelta(days=TEST_DAYS + 60)
    
    try:
        df = yf.download(ticker, start=start, end=end, progress_bar=False)
    except:
        df = yf.download(ticker, start=start, end=end)
    
    if len(df) < 60:
        return None
    
    df = calculate_indicators(df).dropna()
    if len(df) < 30:
        return None
    
    # Run simulation
    capital = INITIAL_CAPITAL
    position = 0
    trades = []
    values = [INITIAL_CAPITAL]
    
    for i in range(60, len(df)):
        row = df.iloc[i]
        state = build_state(df, i, position, capital)
        
        action, _ = model.predict(state, deterministic=True)
        price = float(row['Close'])
        
        if action == 1 and position == 0:  # Buy
            position = capital / price
            trades.append({'type': 'BUY', 'price': price, 'date': str(df.index[i])})
        elif action == 2 and position > 0:  # Sell
            capital = position * price
            pnl = capital - INITIAL_CAPITAL
            trades.append({'type': 'SELL', 'price': price, 'pnl': pnl, 'date': str(df.index[i])})
            position = 0
        
        current_value = capital if position == 0 else position * price
        values.append(current_value)
    
    # Final value
    final_price = float(df.iloc[-1]['Close'])
    if position > 0:
        capital = position * final_price
    
    # Calculate metrics
    total_return = (capital - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    buy_hold = (final_price - float(df.iloc[60]['Close'])) / float(df.iloc[60]['Close']) * 100
    alpha = total_return - buy_hold
    
    # Drawdown
    peak = INITIAL_CAPITAL
    max_dd = 0
    for v in values:
        if v > peak:
            peak = v
        dd = (peak - v) / peak * 100
        if dd > max_dd:
            max_dd = dd
    
    sells = [t for t in trades if t['type'] == 'SELL']
    wins = len([t for t in sells if t.get('pnl', 0) > 0])
    win_rate = wins / len(sells) * 100 if sells else 0
    
    return {
        'ticker': ticker,
        'initial': INITIAL_CAPITAL,
        'final': capital,
        'return_pct': total_return,
        'buy_hold_pct': buy_hold,
        'alpha': alpha,
        'max_drawdown_pct': max_dd,
        'num_trades': len(sells),
        'win_rate_pct': win_rate,
        'trades': sells
    }

def main():
    print("="*60)
    print("🚀 RL Trader Backtest")
    print("="*60)
    
    # Find all trained models
    models = []
    if os.path.exists(MODEL_DIR):
        for f in os.listdir(MODEL_DIR):
            if f.startswith('bandi_rl_') and f.endswith('.zip'):
                ticker = f.replace('bandi_rl_', '').replace('.zip', '')
                models.append((ticker, os.path.join(MODEL_DIR, f)))
    
    print(f"Found {len(models)} models")
    
    if not models:
        print("❌ No models found")
        return
    
    # Run backtests
    results = []
    for ticker, path in models:
        result = backtest_ticker(ticker, path)
        if result:
            results.append(result)
            print(f"  Return: {result['return_pct']:+.1f}% | Alpha: {result['alpha']:+.1f}% | Trades: {result['num_trades']}")
    
    if not results:
        print("❌ No successful backtests")
        return
    
    # Summary
    print("\n" + "="*60)
    print("📊 RESULTS SUMMARY")
    print("="*60)
    print(f"{'Ticker':<12} {'Return':<10} {'B&H':<10} {'Alpha':<10} {'DD':<8} {'Trades':<8} {'Win%':<8}")
    print("-"*60)
    
    for r in sorted(results, key=lambda x: x['return_pct'], reverse=True):
        print(f"{r['ticker']:<12} {r['return_pct']:>+8.1f}% {r['buy_hold_pct']:>+8.1f}% {r['alpha']:>+8.1f}% "
              f"{r['max_drawdown_pct']:>+6.1f}% {r['num_trades']:>6} {r['win_rate_pct']:>+6.0f}%")
    
    print("-"*60)
    avg_ret = sum(r['return_pct'] for r in results) / len(results)
    avg_bh = sum(r['buy_hold_pct'] for r in results) / len(results)
    avg_alpha = avg_ret - avg_bh
    
    print(f"\nAverage Return: {avg_ret:+.2f}%")
    print(f"Average Buy&Hold: {avg_bh:+.2f}%")
    print(f"Average Alpha: {avg_alpha:+.2f}%")
    print(f"Best: {max(results, key=lambda x: x['return_pct'])['ticker']}")
    print(f"Worst: {min(results, key=lambda x: x['return_pct'])['ticker']}")
    print("="*60)
    
    # Save to JSON
    with open('backtest_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Save summary to TXT
    with open('backtest_summary.txt', 'w') as f:
        f.write("="*60 + "\n")
        f.write("RL Trader Backtest Report\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write("="*60 + "\n\n")
        f.write(f"Models Tested: {len(models)}\n")
        f.write(f"Successful: {len(results)}\n")
        f.write(f"Average Return: {avg_ret:+.2f}%\n")
        f.write(f"Average Alpha: {avg_alpha:+.2f}%\n")
        f.write(f"Best Ticker: {max(results, key=lambda x: x['return_pct'])['ticker']}\n")
        f.write(f"Worst Ticker: {min(results, key=lambda x: x['return_pct'])['ticker']}\n\n")
        
        f.write("Detailed Results:\n")
        f.write("-"*60 + "\n")
        for r in sorted(results, key=lambda x: x['return_pct'], reverse=True):
            f.write(f"{r['ticker']}: {r['return_pct']:+.1f}% (Alpha: {r['alpha']:+.1f}%, Trades: {r['num_trades']})\n")
    
    print("\n💾 Results saved to backtest_results.json and backtest_summary.txt")

if __name__ == '__main__':
    main()
