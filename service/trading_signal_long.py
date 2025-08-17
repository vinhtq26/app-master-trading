from datetime import datetime, timezone
import pytz
from binance.client import Client
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import logging

from service.binance.BinanceTradingSignals import analyze_buy_signal

client = Client("ASdfASakKdajNsjdf82JCL8IocUd9hdmmfnSJHAN89dHfnasNN27Ajasd245FAHJ",
                    "JAdsfgakKdajNsjdf82JCL8IocUd9hdmmfnSJHAN89dHfnasNN27elAjda221ASA")
import pandas as pd
from binance.client import Client

def process_klines(klines):
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                       'close_time', 'quote_asset_volume', 'number_of_trades',
                                       'taker_buy_base', 'taker_buy_quote', 'ignore'])

    # Chuyển đổi kiểu dữ liệu
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    df[numeric_cols] = df[numeric_cols].astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    # Tính toán các chỉ báo kỹ thuật
    df['EMA_10'] = df['close'].ewm(span=10, adjust=False).mean()
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['RSI_30'] = RSIIndicator(df['close'], window=30).rsi()
    df['RSI_50'] = RSIIndicator(df['close'], window=50).rsi()
    df['RSI_70'] = RSIIndicator(df['close'], window=70).rsi()

    ema_12 = df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD_line'] = ema_12 - ema_26
    df['Signal_line'] = df['MACD_line'].ewm(span=9, adjust=False).mean()
    df['Histogram'] = df['MACD_line'] - df['Signal_line']

    # Tạo data_historyß
    data_history = []
    for _, row in df.iterrows():
        data_history.append({
            "time": row['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
            "open": row['open'],
            "close": row['close'],
            "high": row['high'],
            "low": row['low'],
            "volume": row['volume'],
            "macd": {
                "MACD": row['MACD_line'],
                "Signal": row['Signal_line'],
                "Histogram": row['Histogram']
            },
            "ema": {
                "EMA_10": row['EMA_10'],
                "EMA_20": row['EMA_20'],
                "EMA_50": row['EMA_50']
            },
            "rsi": {
                "RSI30": row['RSI_30'],
                "RSI50": row['RSI_50'],
                "RSI70": row['RSI_70']
            }
        })

    return {"data_history": data_history}

def calculate_technical_indicators(coin_symbol='BTCUSDT', interval=Client.KLINE_INTERVAL_5MINUTE, limit=500):
    klines = client.futures_klines(symbol=coin_symbol, interval=interval, limit=limit)
    df = process_klines(klines)

    return df

def get_coin_technical_data(coin_symbol='BTCUSDT', interval=Client.KLINE_INTERVAL_5MINUTE, limit=500):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    """
    Lấy thông tin kỹ thuật của coin bao gồm MACD và EMA

    Parameters:
        coin_symbol (str): Mã cặp giao dịch (mặc định BTCUSDT)
        interval (str): Khung thời gian (mặc định 15 phút)
        limit (int): Số lượng nến trả về (mặc định 5)

    Returns:
        dict: Dữ liệu theo format yêu cầu
    """
    # Lấy dữ liệu giá hiện tại
    ticker = client.futures_ticker(symbol=coin_symbol)
    current_price = ticker['lastPrice']



    df = calculate_technical_indicators(coin_symbol, interval, limit)

    # Chuẩn bị dữ liệu trả về
    data_history = []
    # lấy dữ liệu 10 nến khung interval để set
    for _, row in df.tail(10).iterrows():
        utc_timestamp = row['timestamp'].tz_localize('UTC')
        # Chuyển sang múi giờ Việt Nam
        vn_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
        vn_timestamp = utc_timestamp.tz_convert(vn_timezone)
        data_history.append({
            "time": vn_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "open": str(row['open']),
            "close": str(row['close']),
            "high": str(row['high']),
            "low": str(row['low']),
            "volume": str(row['volume']),
            "macd": {
                "MACD": str(row['MACD_line']),
                "Signal": str(row['Signal_line']),
                "Histogram": str(row['Histogram'])
            },
            "ema": {
                "EMA_10": str(row['EMA_10']),
                "EMA_20": str(row['EMA_20']),
                "EMA_50": str(row['EMA_50'])
            },
            "rsi": {
                "RSI30": str(row['RSI_30']),
                "RSI50": str(row['RSI_50']),
                "RSI70": str(row['RSI_70'])
            }
        })

    response = {
        "symbol": coin_symbol,
        "currentPrice": current_price,
        "current-time": current_time,
        "data_history": data_history
    }

    return response


def get_long_signal(exchange, timeframe, symbol):
    # Fetch historical market data for analysis
    klines = client.get_klines(symbol=symbol, interval=timeframe, limit=100)
    processed_data = process_klines(klines)

    # Generate long trade signals
    long_signal = analyze_buy_signal(processed_data, timeframe)

    return {
        "data": processed_data,
        "signal": {
            "percent": long_signal.get('percent', 0),
            "reason": long_signal.get('reason', 'Không rõ lý do.')
        }
    }


# Sử dụng hàm
if __name__ == "__main__": # Khởi tạo client Binance

    klines = client.get_klines(symbol="BTCUSDT", interval="15m", limit=100)
    processed_data = process_klines(klines)
    logging.info(analyze_buy_signal(processed_data))
