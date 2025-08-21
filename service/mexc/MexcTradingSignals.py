import requests
import pandas as pd
from ta.momentum import RSIIndicator
import asyncio
import aiohttp

from service import trading_signal_long
from service.utils.utils import get_coin_image_url


class MexcTradingSignals:
    BASE_URL = "https://api.mexc.com/api/v3/"

    @staticmethod
    def get_klines(symbol='BTCUSDT', interval='5m', limit=500):
        url = f"{MexcTradingSignals.BASE_URL}klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        klines = response.json()
        # Each kline is a list, not a dict. Adjust columns accordingly.
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume'
        ])
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume']
        df[numeric_cols] = df[numeric_cols].astype(float)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    @staticmethod
    def calculate_technical_indicators(df):
        df['EMA_10'] = df['close'].ewm(span=10, adjust=False).mean()
        df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['close'] = df['close'].astype(float)
        df['RSI_30'] = RSIIndicator(df['close'], window=30).rsi()
        df['RSI_50'] = RSIIndicator(df['close'], window=50).rsi()
        df['RSI_70'] = RSIIndicator(df['close'], window=70).rsi()
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD_line'] = ema_12 - ema_26
        df['Signal_line'] = df['MACD_line'].ewm(span=9, adjust=False).mean()
        df['Histogram'] = df['MACD_line'] - df['Signal_line']
        return df
    async def getAllCoinMexc(limit = 10):
        """
                Fetch all USDT-margined futures tickers from MEXC, sort by 24h quote volume, and return top symbols.
                """
        url = "https://contract.mexc.com/api/v1/contract/ticker"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        tickers = data.get('data', [])
        # Sort by quote volume (as float), descending
        sorted_tickers = sorted(
            tickers, key=lambda x: float(x.get('amount24', 0)), reverse=True
        )
        # Get top symbols ending with 'USDT'
        top_symbols = [t['symbol'].replace('_', '') for t in sorted_tickers if t['symbol'].endswith('USDT')][:limit]
        return top_symbols
