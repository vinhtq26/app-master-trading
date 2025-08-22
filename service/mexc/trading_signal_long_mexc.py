from datetime import datetime, timezone
import pytz
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from binance.client import Client
from service.binance.BinanceTradingSignals import analyze_buy_signal
from service.mexc.MexcTradingSignals import MexcTradingSignals
import logging
client = Client("ASdfASakKdajNsjdf82JCL8IocUd9hdmmfnSJHAN89dHfnasNN27Ajasd245FAHJ",
                    "JAdsfgakKdajNsjdf82JCL8IocUd9hdmmfnSJHAN89dHfnasNN27elAjda221ASA")
def calculate_technical_indicators(coin_symbol='BTCUSDT', interval='5m', limit=500):
    if coin_symbol == 'BTCDOMUSDT':
        klines = client.futures_klines(symbol=coin_symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df = MexcTradingSignals.calculate_technical_indicators(df)
    else:
        df = MexcTradingSignals.get_klines(symbol=coin_symbol, interval=interval, limit=limit)
        df = MexcTradingSignals.calculate_technical_indicators(df)
    return df
def get_coin_technical_data(coin_symbol='BTCUSDT', interval='5m', limit=500):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    """
    Lấy thông tin kỹ thuật của coin bao gồm MACD và EMA

    Parameters: 
        coin_symbol (str): Mã cặp giao dịch (mặc định BTCUSDT)
        interval (str): Khung thời gian (mặc định 5 phút)
        limit (int): Số lượng nến trả về (mặc định 500)

    Returns:
        dict: Dữ liệu theo format yêu cầu
    """
    df = calculate_technical_indicators(coin_symbol, interval, limit)
    data_history = []
    for _, row in df.tail(10).iterrows():
        utc_timestamp = row['timestamp'].tz_localize('UTC')
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
    return {
        "symbol": coin_symbol,
        "interval": interval,
        "data_history": data_history,
        "current_time": current_time
    }


# Sử dụng hàm
if __name__ == "__main__": # Khởi tạo client Binance

    technical_data = get_coin_technical_data()
    print(analyze_buy_signal(technical_data))
    logging.info(analyze_buy_signal(technical_data))
