# AI-Agent-Trading

## Overview
This project is designed to provide trading signals and insights for various cryptocurrency exchanges, including Binance, MEXC, and Bybit. It includes APIs for fetching long/short trading signals, analyzing market data, and interacting with exchange-specific configurations.

## APIs

### 1. Long/Short Ratio API
**File:** `routes/long_short_ratio_api.py`
- **Purpose:** Fetches the long-short ratio for a given symbol, timeframe, and exchange.
- **Key Parameters:**
  - `exchange`: The exchange to query (e.g., Binance, MEXC, Bybit).
  - `symbol`: The trading pair symbol (e.g., BTCUSDT).
  - `timeframe`: The timeframe for the data (e.g., 15m, 1h).
- **Response:** Returns the long-short ratio data or an error message if the exchange is unsupported.

### 2. Long/Short Detail API
**File:** `routes/long_short_detail.py`
- **Purpose:** Provides detailed long/short trading signals for a specific exchange, symbol, and timeframe.
- **Key Parameters:**
  - `exchange`: The exchange to query.
  - `symbol`: The trading pair symbol.
  - `timeframe`: The timeframe for the data.
- **Response:** Returns detailed trading signals categorized by exchange, symbol, and type (long/short).

### 3. Signal API
**File:** `routes/signal_api.py`
- **Purpose:** Fetches trading signals for multiple symbols and intervals.
- **Key Features:**
  - Supports batch processing for faster execution.
  - Categorizes signals by exchange and symbol.

## Functional Methods

### 1. `get_long_short_detail`
**File:** `service/long_short_detail_service_llm_binance.py` and `service/long_short_detail_service_llm_mexc.py`
- **Purpose:** Fetches detailed long/short trading signals for Binance and MEXC.
- **Key Features:**
  - Normalizes data for different exchanges.
  - Handles exchange-specific symbol formatting.

### 2. `fetch_batch_klines_optimized`
**File:** `service/trading_signal_long.py`
- **Purpose:** Fetches kline (candlestick) data in batches for multiple symbols.
- **Key Features:**
  - Optimized for performance.
  - Supports configurable intervals and limits.

### 3. `analyze_buy_signal` and `analyze_short_signal`
**File:** `service/trading_signal_long.py` and `service/trading_signal_short.py`
- **Purpose:** Analyzes market data to generate buy or short signals.
- **Key Features:**
  - Uses historical candlestick data.
  - Calculates entry price, take profit, and other metrics.

### 4. `CacheWithTTL`
**File:** `cache/CacheWithTTL.py`
- **Purpose:** Implements a caching mechanism with time-to-live (TTL) support.
- **Key Features:**
  - Reduces redundant API calls.
  - Configurable TTL for different intervals.

## Service Functions Overview

### 1. `service/app.py`
- **Purpose:** Provides utility functions for fetching and processing trading data.
- **Key Function:**
  - `fetch_batch_klines_optimized`: Fetches kline (candlestick) data for multiple symbols in an optimized manner using asynchronous requests.

### 2. `service/binance_long_short_service.py`
- **Purpose:** Handles long/short signal processing for Binance.
- **Key Function:**
  - `fetch_with_retry`: Fetches data from Binance with retry logic to handle rate limits and errors.

### 3. `service/long_short_detail_service_llm_binance.py`
- **Purpose:** Provides detailed long/short analysis for Binance.
- **Key Function:**
  - `get_long_short_detail_llm_binance`: Combines long/short signals with additional analysis like support/resistance, volume, and candle patterns.

### 4. `service/long_short_detail_service_llm_mexc.py`
- **Purpose:** Provides detailed long/short analysis for MEXC.
- **Key Function:**
  - `get_long_short_detail_llm_mexc`: Similar to the Binance version but tailored for MEXC, including exchange-specific data handling.

### 5. `service/long_short_ratio_service.py`
- **Purpose:** Fetches long/short ratio data for multiple exchanges (Binance, MEXC, Bybit).
- **Key Features:** Uses exchange-specific endpoints to retrieve and normalize ratio data.

### 6. `service/trading_signal_long.py`
- **Purpose:** Processes and analyzes long trading signals.
- **Key Function:**
  - `process_klines`: Converts kline data into a DataFrame for further analysis.
  - `analyze_buy_signal`: Evaluates buy signals based on technical indicators.

### 7. `service/trading_signal_short.py`
- **Purpose:** Processes and analyzes short trading signals.
- **Key Function:**
  - `analyze_short_signal`: Evaluates short signals using EMA, RSI, MACD, and other indicators.

## Configuration

### 1. Exchange Configurations
- **Files:**
  - `config/binance_config.py`
  - `config/mexc_config.py`
  - `config/bybit_config.py`
- **Purpose:** Stores API keys, endpoints, and other exchange-specific settings.

### 2. Logging
- **File:** `config/logging_config.py`
- **Purpose:** Configures logging for the application.

## How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the application:
   ```bash
   python main.py
   ```

## API Request and Response Examples

### 1. Long/Short Ratio API
**Request:**
```http
POST /api/long-short-ratio
Content-Type: application/json

{
  "exchange": "binance",
  "symbol": "BTCUSDT",
  "timeframe": "15m"
}
```
**Response:**
```json
{
  "long_ratio": 0.65,
  "short_ratio": 0.35,
  "timestamp": "2025-08-23T12:00:00Z"
}
```

### 2. Long/Short Detail API
**Request:**
```http
POST /api/long-short-detail
Content-Type: application/json

{
  "exchange": "mexc",
  "symbol": "ETHUSDT",
  "timeframe": "1h"
}
```
**Response:**
```json
{
  "symbol": "ETHUSDT",
  "exchange": "mexc",
  "timeframe": "1h",
  "long_signals": [
    {
      "entry_price": 1800.5,
      "take_profit": 1890.5,
      "current_price": 1820.0,
      "time": "2025-08-23T12:00:00Z"
    }
  ],
  "short_signals": [
    {
      "entry_price": 1820.0,
      "take_profit": 1729.0,
      "current_price": 1820.0,
      "time": "2025-08-23T12:00:00Z"
    }
  ]
}
```

### 3. Signal API
**Request:**
```http
POST /api/signal
Content-Type: application/json

{
  "exchange": "binance",
  "interval": "5m"
}
```
**Response:**
```json
{
  "buy_signals": [
    {
      "symbol": "BTCUSDT",
      "entry_price": 29000.0,
      "take_profit": 30450.0,
      "current_price": 29200.0,
      "time": "2025-08-23T12:00:00Z"
    }
  ]
}
```

## Future Enhancements
- Add support for more exchanges.
- Improve signal analysis algorithms.
- Enhance caching mechanisms for better performance.
