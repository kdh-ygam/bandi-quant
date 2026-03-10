#!/usr/bin/env python3
"""RL 트레이더 백테스팅 스크립트"""

import os
import json
import pandas as pd
import numpy as np
import yfinance as yf
from stable_baselines3 import PPO
from datetime import datetime, timedelta

MODEL_DIR = './trained_models'
INITIAL_CAPITAL = 10000
TEST_DAYS = 180

def calculate_indicators(df):
    df = df.copy()
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
    df['Returns'] = df['Close'].pct_change()
    df['Volatility'] = df['Returns'].rolling(window=20).std()
    
    return df

def build_state(df, i, position, capital):
    """Build 15 features - matches training"""
    row = df.iloc[i]
    
    sma20 = row['SMA_20'] if pd.notna(row['SMA_20']) else row['Close']
    sma50 = row['SMA_50'] if pd.notna(row['SMA_50']) else row['Close']
    rsi = row['RSI'] if pd.notna(row['RSI']) else 50
    bb_upper = row['BB_Upper'] if pd.notna(row['BB_Upper']) else row['Close'] * 1.1
    bb_lower = row['BB_Lower'] if pd.notna(row['BB_Lower']) else row['Close'] * 0.9
    atr = row['ATR'] if pd.notna(row['ATR']) else row['Close'] * 0.02
    
    # Calculate volume ratio
    vol_mean = df['Volume'].iloc[max(0,i-20):i].mean() if 'Volume' in df else 1
    vol_ratio = row['Volume'] / vol_mean if vol_mean > 0 and 'Volume' in df else 1
    
    # Price changes
    price_10d = df['Close'].iloc[max(0,i-10)] if i >= 10 else df['Close'].iloc[0]
    price_20d = df['Close'].iloc[max(0,i-20)] if i >= 20 else df['Close'].iloc[0]
    change_10d = (row['Close'] - price_10d) / price_10d if price_10d > 0 else 0
    change_20d = (row['Close'] - price_20d) / price_20d if price_20d > 0 else 0
    
    # Volatility
    vol_20d = df['Returns'].iloc[max(0,i-20):i].std() if i >= 20 else 0.01
    
    bb_position = (row['Close'] - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
    macd_hist = row['MACD_Hist'] if pd.notna(row['MACD_Hist']) else 0
    price_normalized = row['Close']
    if len(str(int(price_normalized))) > 3:
        divisor = 10**(len(str(int(price_normalized))) - 3)
        price_normalized = price_normalized / divisor
    
    state = [
        float(row['Close'] / sma20 - 1),
        float(sma20 / sma50 - 1),
        float(rsi / 100),
        float(bb_position),
        float(macd_hist / row['Close']) if row['Close'] > 0 else 0,
        float(atr / row['Close']) if row['Close'] > 0 else 0.02,
        float(vol_ratio - 1),
        float(change_10d),
        float(change_20d),
        float(vol_20d * np.sqrt(252)),
        float(1 if position > 0 else 0),
        float(position * row['Close'] / capital if position > 0 else 0),
        float(1 if row['Close'] > sma20 else 0),
        float(rsi / 50 - 1),
        float(1 if macd_hist > 0 else 0)
    ]
    
    return np.array(state, dtype=np.float32)

def backtest_ticker(ticker, model_path):
    """Backtest single ticker"""
    print(f"\n📊 {ticker}")
    
    try:
        model = PPO.load(model_path)
    except Exception as e:
        print(f"  ❌ Model load failed: {e}")
        return None
    
    end = datetime.now()
    start = end - timedelta(days=TEST_DAYS + 60)
    
    try:
        df = yf.download(ticker, start=start, end=end, progress_bar=False)
    except:
        df = yf.download(ticker, start=start, end=end)
    
    if len(df) < 60:
        print(f"  ❌ Insufficient data: {len(df)} rows")
        return None
    
    df = calculate_indicators(df).dropna()
    if len(df) < 30:
        print(f"  ❌ After processing: {len(df)} rows")
        return None
    
    capital = INITIAL_CAPITAL
    position = 0
    trades = []
    values = [INITIAL_CAPITAL]
    
    # Backtest requires 30-day lookback
    for i in range(30, len(df)):
        try:
            state = build_state(df, i, position, capital)
            
            # The model expects batch dimension - reshape to (1, 15)
            state_batch = state.reshape(1, -1)
            action, _ = model.predict(state_batch, deterministic=True)
            
            price = float(row['Close'])
            
            if action == 1 and position == 0:
                shares = capital / price
                position = shares
                trades.append({'type': 'BUY', 'price': price, 'date': str(df.index[i])[:10]})
                
            elif action == 2 and position > 0:
                sell_value = position * price
                pnl = sell_value - INITIAL_CAPITAL
                capital = sell_value
                trades.append({'type': 'SELL', 'price': price, 'pnl': pnl, 'date': str(df.index[i])[:10]})
                position = 0
            
            current_value = capital if position == 0 else position * price
            values.append(current_value)
            
        except Exception as e:
            print(f"    Error at {i}: {e}")
            continue
    
    final_price = float(df.iloc[-1]['Close'])
    final_value = capital if position == 0 else position * final_price
    
    total_return = (final_value - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    buy_hold = (final_price - float(df.iloc[30]['Close'])) / float(df.iloc[30]['Close']) * 100
    alpha = total_return - buy_hold
    
    peak = INITIAL_CAPITAL
    max_dd = 0
    for v in values:
        if v > peak:
            peak = v
        dd = (peak - v) / peak * 100
        if dd > max_dd:
            max_dd = dd
    
    sells = [t for t in trades if t['type'] == 'SELL']
    wins = len([t for t in sells if t.get('pnl', -1) > 0])
    win_rate = wins / len(sells) * 100 if sells else 0
    
    print(f"  ✅ Return: {total_return:+.1f}% | Alpha: {alpha:+.1f}% | Trades: {len(sells)}")
    
    return {
        'ticker': ticker,
        'initial': INITIAL_CAPITAL,
        'final': final_value,
        'return_pct': total_return,
        'buy_hold_pct': buy_hold,
        'alpha': alpha,
        'max_drawdown_pct': max_dd,
        'num_trades': len(sells),
        'win_rate_pct': win_rate,
        'trades': sells[:10]
    }

def main():
    print("="*60)
    print("🚀 RL Trader Backtest")
    print("="*60)
    
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
    
    results = []
    for ticker, path in models:
        result = backtest_ticker(ticker, path)
        if result:
            results.append(result)
    
    if not results:
        print("❌ No successful backtests")
        return
    
    print("\n" + "="*60)
    print("📊 RESULTS SUMMARY")
    print("="*60)
    print(f"{'Ticker':<12} {'Return':<10} {'B&H':<10} {'Alpha':<10} {'DD':<8} {'Trades':<8} {'Win%':<8}")
    print("-"*60)
    
    for r in sorted(results, key=lambda x: x['return_pct'], reverse=True):
        print(f"{r['ticker']:<12} {r['return_pct']:>+8.1f}% {r['buy_hold_pct']:>+8.1f}% "
              f"{r['alpha']:>+8.1f}% {r['max_drawdown_pct']:>+6.1f}% "
              f"{r['num_trades']:>6} {r['win_rate_pct']:>+6.0f}%")
    
    print("-"*60)
    avg_ret = sum(r['return_pct'] for r in results) / len(results)
    avg_bh = sum(r['buy_hold_pct'] for r in results) / len(results)
    
    print(f"\nAverage Return: {avg_ret:+.2f}%")
    print(f"Average Buy&Hold: {avg_bh:+.2f}%")
    print(f"Average Alpha: {avg_ret - avg_bh:+.2f}%")
    print(f"Best: {max(results, key=lambda x: x['return_pct'])['ticker']}")
    print(f"Worst: {min(results, key=lambda x: x['return_pct'])['ticker']}")
    print("="*60)
    
    with open('backtest_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    with open('backtest_summary.txt', 'w') as f:
        f.write("="*60 + "\n")
        f.write("RL Trader Backtest Report\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write("="*60 + "\n\n")
        f.write(f"Models: {len(models)}\n")
        f.write(f"Successful: {len(results)}\n")
        f.write(f"Avg Return: {avg_ret:+.2f}%\n")
        f.write(f"Avg Alpha: {avg_ret - avg_bh:+.2f}%\n\n")
        f.write("Top Performers:\n")
        for r in sorted(results, key=lambda x: x['return_pct'], reverse=True)[:5]:
            f.write(f"  {r['ticker']}: {r['return_pct']:+.1f}% (Alpha: {r['alpha']:+.1f}%)\n")
    
    print("\n💾 Saved: backtest_results.json, backtest_summary.txt")

if __name__ == '__main__':
    main()
