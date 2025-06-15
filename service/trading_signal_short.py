
import pandas as pd

from service import trading_signal_long


def analyze_short_signal(data, interval):
    df = pd.DataFrame(data['data_history'])
    df['EMA_10'] = df['ema'].apply(lambda x: float(x['EMA_10']))
    df['EMA_20'] = df['ema'].apply(lambda x: float(x['EMA_20']))
    df['EMA_50'] = df['ema'].apply(lambda x: float(x['EMA_50']))
    df['RSI_30'] = df['rsi'].apply(lambda x: float(x['RSI30']))
    df['RSI_50'] = df['rsi'].apply(lambda x: float(x['RSI50']))
    df['RSI_70'] = df['rsi'].apply(lambda x: float(x['RSI70']))
    df['MACD'] = df['macd'].apply(lambda x: float(x['MACD']))
    df['Signal'] = df['macd'].apply(lambda x: float(x['Signal']))
    df['Histogram'] = df['macd'].apply(lambda x: float(x['Histogram']))

    ranking_short = 0
    reason = ""

    if interval == '5m':
        # EMA10 < EMA20 & EMA50, but in last 5 candles EMA10 > EMA20 or EMA50
        # Check if EMA10 is below EMA20 and EMA50 - kiểm tra xem ema10 < ema20 & ema50 khôn
        cond1 = (df.iloc[-1]['EMA_10'] < df.iloc[-1]['EMA_20']) and (df.iloc[-1]['EMA_10'] < df.iloc[-1]['EMA_50'])
        # Check nếu trong 5 nến gần nhất trước đó có nến nào EMA10 > EMA20 hoặc EMA50
        cond2 = any(
            (df.iloc[-i]['EMA_10'] > df.iloc[-i]['EMA_20']) or (df.iloc[-i]['EMA_10'] > df.iloc[-i]['EMA_50'])
            for i in range(2, 7)
        )
        if cond1 and cond2:
            ranking_short = 10
            reason = "EMA10 < EMA20 & EMA50, but in last 5 candles EMA10 > EMA20 or EMA50"
        # MACD just crossed below signal (not more than 3rd negative candle) and histogram negative
        macd_cross = False
        for i in range(1, 4):
            if (df.iloc[-i]['MACD'] < df.iloc[-i]['Signal']) and (df.iloc[-i]['Histogram'] < 0):
                if (df.iloc[-i-1]['MACD'] > df.iloc[-i-1]['Signal']):
                    macd_cross = True
                    break
        if macd_cross:
            ranking_short = 10
            reason = "MACD just crossed below signal and histogram negative (within last 3 candles)"

    elif interval == '15m':
        cond1 = (df.iloc[-1]['EMA_10'] < df.iloc[-1]['EMA_20']) and (df.iloc[-1]['EMA_10'] < df.iloc[-1]['EMA_50']) \
            and (df.iloc[-1]['RSI_30'] < df.iloc[-1]['RSI_50']) and (df.iloc[-1]['RSI_30'] < df.iloc[-1]['RSI_70']) \
            and (df.iloc[-1]['MACD'] < df.iloc[-1]['Signal']) and (df.iloc[-1]['Histogram'] < 0)
        cond1b = any(df.iloc[-i]['EMA_10'] > df.iloc[-i]['EMA_20'] for i in range(2, 7))
        if cond1 and cond1b:
            ranking_short = 10
            reason = "EMA10 < EMA20 & EMA50, RSI30 < RSI50 & RSI70, MACD < Signal, Histogram < 0, and EMA10 > EMA20 in last 5"
        if cond1:
            hist = [df.iloc[-i]['Histogram'] for i in range(2, 7)]
            if all(h < 0 for h in hist) and all(hist[i] < hist[i + 1] or abs(hist[i + 1] - hist[i]) <= abs(hist[i]) * 0.01 for i in range(len(hist) - 1)):
                ranking_short = 8
                reason = "Histogram negative and increasing (closer to 0) in last 5 candles"
            else:
                ranking_short = 9
                reason = "EMA10 < EMA20 & EMA50, RSI30 < RSI50 & RSI70, MACD < Signal, Histogram < 0. careful if chain of histogram is negative greater"

    elif interval == '4h':
        cond1 = (df.iloc[-1]['RSI_30'] < df.iloc[-1]['RSI_50']) and (df.iloc[-1]['RSI_30'] < df.iloc[-1]['RSI_70']) \
            and any((df.iloc[-i]['RSI_30'] > df.iloc[-i]['RSI_50']) or (df.iloc[-i]['RSI_30'] > df.iloc[-i]['RSI_70']) for i in range(2, 5))
        cond2 = (df.iloc[-1]['MACD'] < df.iloc[-1]['Signal']) and (df.iloc[-1]['Histogram'] < 0) \
            and any(df.iloc[-i]['Histogram'] < 0 for i in range(1, 5))
        cond3 = (df.iloc[-1]['EMA_10'] < df.iloc[-1]['EMA_20']) and any(df.iloc[-i]['EMA_10'] > df.iloc[-i]['EMA_20'] for i in range(2, 5))
        conds = [cond1, cond2, cond3]
        if sum(conds) == 3:
            ranking_short = 10
            reason = "All 3 short conditions met (RSI, MACD, EMA) in 4h"
        elif any(conds):
            ranking_short = 9
            reason = "At least 1 of 3 short conditions met (RSI, MACD, EMA) in 4h"

    elif interval == '1d':
        if (df.iloc[-1]['EMA_10'] < df.iloc[-1]['EMA_20']) and (df.iloc[-1]['EMA_10'] < df.iloc[-1]['EMA_50']):
            ranking_short = 10
            reason = "EMA10 < EMA20 & EMA50 in 1d"
        if ((df.iloc[-1]['EMA_10'] < df.iloc[-1]['EMA_20']) or (df.iloc[-1]['EMA_10'] < df.iloc[-1]['EMA_50'])):
            ranking_short = 9
            reason = "EMA10 < EMA20 or EMA50 in 1d"

    return {
        "ranking_short": ranking_short,
        "reason": reason
    }

if __name__ == '__main__':
    data = trading_signal_long.get_coin_technical_data(coin_symbol='BTCUSDT', interval='15m')
    signal = analyze_short_signal(data, interval='15m')
    print(signal)