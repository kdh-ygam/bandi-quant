#!/usr/bin/env python3
"""
반디 퀀트 - 백테스팅 모듈 v1.0
간단한 백테스트 프레임워크
"""

import pandas as pd
import numpy as np
from datetime import datetime

class Backtester:
    """전략 백테스터"""
    
    def __init__(self, initial_capital=100000, commission=0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.cash = initial_capital
        self.position = 0
        self.trades = []
        self.equity = []
    
    def run_strategy(self, df, signals, price_col='close'):
        """
        간단한 백테스트 실행
        signals: Series (1=매수, 0=관망, -1=매도)
        """
        print(f"📊 백테스트 시작...")
        print(f"   초기 자본: ${self.initial_capital:,.2f}")
        
        for i, (date, signal) in enumerate(signals.items()):
            price = df.loc[date, price_col]
            
            # 매수 신호
            if signal == 1 and self.cash > 0:
                # 포지션 진입 (전체 자본의 10%)
                invest_amount = self.cash * 0.1
                shares = invest_amount / price
                cost = invest_amount * self.commission
                
                self.cash -= invest_amount + cost
                self.position += shares
                
                self.trades.append({
                    'date': date,
                    'action': 'BUY',
                    'price': price,
                    'shares': shares,
                    'cost': cost
                })
            
            # 매도 신호
            elif signal == -1 and self.position > 0:
                # 포지션 정리
                sell_amount = self.position * price
                cost = sell_amount * self.commission
                
                self.cash += sell_amount - cost
                self.trades.append({
                    'date': date,
                    'action': 'SELL',
                    'price': price,
                    'shares': self.position,
                    'cost': cost
                })
                self.position = 0
            
            # 자산 가치 기록
            equity_value = self.cash + (self.position * price)
            self.equity.append({
                'date': date,
                'equity': equity_value,
                'price': price
            })
        
        return self.calculate_metrics()
    
    def calculate_metrics(self):
        """성과 메트릭 계산"""
        equity_df = pd.DataFrame(self.equity).set_index('date')
        
        # 총 수익률
        final_value = equity_df['equity'].iloc[-1]
        total_return = (final_value / self.initial_capital) - 1
        
        # 일별 수익률
        daily_returns = equity_df['equity'].pct_change().dropna()
        
        # 샤프 비율 (연율화)
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        
        # 최대 낙폭 (MDD)
        peak = equity_df['equity'].cummax()
        drawdown = (equity_df['equity'] - peak) / peak
        max_drawdown = drawdown.min()
        
        # 승률
        trades_df = pd.DataFrame(self.trades)
        if len(trades_df) >= 2:
            profits = []
            for i in range(0, len(trades_df) - 1, 2):
                if trades_df.iloc[i]['action'] == 'BUY':
                    buy_price = trades_df.iloc[i]['price']
                    sell_price = trades_df.iloc[i+1]['price']
                    profit = (sell_price - buy_price) / buy_price
                    profits.append(profit)
            
            win_rate = sum(1 for p in profits if p > 0) / len(profits) if profits else 0
        else:
            win_rate = 0
        
        metrics = {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'profit_factor': abs(sum(p for p in profits if p > 0)) / abs(sum(p for p in profits if p < 0)) if profits else 0,
            'num_trades': len(self.trades) // 2,
            'win_rate': win_rate
        }
        
        return metrics, equity_df, trades_df
    
    def print_report(self, metrics):
        """보고서 출력"""
        print(f"\n📈 백테스트 결과 보고서")
        print(f"=" * 40)
        print(f"초기 자본:        ${metrics['initial_capital']:,.2f}")
        print(f"최종 자산:        ${metrics['final_value']:,.2f}")
        print(f"총 수익률:         {metrics['total_return']:.1%}")
        print(f"샤프 비율:         {metrics['sharpe_ratio']:.2f}")
        print(f"최대 낙폭 (MDD):    {metrics['max_drawdown']:.1%}")
        print(f"거래 횟수:         {metrics['num_trades']}회")
        print(f"승률:              {metrics['win_rate']:.1%}")
        print(f"=" * 40)

if __name__ == "__main__":
    import sys
    sys.path.append('../data')
    sys.path.append('../models')
    
    from collector import DataCollector
    from features import FeatureEngineer
    from predictor import StockPredictor
    
    # 데이터 수집
    collector = DataCollector()
    df = collector.fetch_stock("PLTR", period="1y")
    
    if df is not None:
        # 특성 생성
        featurizer = FeatureEngineer()
        df_features = featurizer.create_features(df)
        feature_cols = featurizer.get_feature_columns()
        
        # 모델 학습
        predictor = StockPredictor()
        X, y, df_clean = predictor.prepare_data(df_features, feature_cols)
        predictor.train(X, y)
        
        # 예측 신호 생성
        predictions, probabilities = predictor.predict(X)
        
        # 매수/매도 신호 (신뢰도 &gt; 60%)
        signals = pd.Series(0, index=X.index)
        for i in range(len(X)):
            prob = probabilities[i][predictions[i]]
            if prob > 0.6:
                signals.iloc[i] = 1 if predictions[i] == 1 else -1
        
        # 백테스트
        backtest = Backtester(initial_capital=100000)
        metrics, equity_df, trades_df = backtest.run_strategy(df_clean, signals)
        backtest.print_report(metrics)
        
        # 차트 저장
        import matplotlib.pyplot as plt
        plt.figure(figsize=(12, 6))
        plt.plot(equity_df['equity'], label='Portfolio Value')
        plt.title('Backtest Result: Portfolio Equity')
        plt.ylabel('Value ($)')
        plt.legend()
        plt.savefig('../data/backtest_equity.png')
        print(f"\n📊 자산 그래프 저장: backtest_equity.png")
