import requests


def get_top_negative_funding_coins_info(n=5):
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"
    response = requests.get(url)
    data = response.json()
    # Filter only symbols with negative funding rate
    negative_funding = [item for item in data if float(item['lastFundingRate']) < 0]
    # Sort by funding rate ascending (most negative first)
    sorted_data = sorted(negative_funding, key=lambda x: float(x['lastFundingRate']))
    top_n = sorted_data[:n]
    result = []
    for item in top_n:
        symbol = item['symbol']
        trend, rates = get_funding_trend(symbol)
        result.append({
            'symbol': symbol,
            'fundingRate': float(item['lastFundingRate']),
            'fundingRatePercent': round(float(item['lastFundingRate']) * 100, 6),
            'markPrice': float(item['markPrice']),
            'time': item['time'],
            'fundingTrend': trend,
            'recentRates': rates
        })
    return result


def get_funding_trend(symbol, limit=3):
    """
    Lấy funding rate lịch sử gần nhất cho symbol và xác định xu hướng funding.
    Trả về: (trend, rates)
    trend: 'decreasing' (âm tăng dần), 'increasing' (âm giảm dần), 'flat', hoặc 'not enough data'
    rates: danh sách funding rate dạng phần trăm, mới nhất ở đầu
    """
    url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    if len(data) < 2:
        return 'not enough data', []
    # Lấy funding rate, mới nhất ở cuối, đảo ngược lại cho mới nhất lên đầu
    rates = [float(item['fundingRate']) * 100 for item in data][::-1]
    # So sánh xu hướng
    if all(rates[i] < rates[i + 1] for i in range(len(rates) - 1)):
        trend = 'decreasing'  # funding âm tăng dần (ví dụ -1 -> -2)
    elif all(rates[i] > rates[i + 1] for i in range(len(rates) - 1)):
        trend = 'increasing'  # funding âm giảm dần (ví dụ -2 -> -1)
    elif all(rates[i] == rates[i + 1] for i in range(len(rates) - 1)):
        trend = 'flat'
    else:
        trend = 'mixed'
    return trend, rates


def get_funding_trend_mexc(symbol, limit=3):
    # MEXC không có public API funding history, trả về 'not available'
    return 'not available', []


# Hàm lấy funding trend cho Bybit

def get_funding_trend_bybit(symbol, limit=3):
    # Bybit funding history public API không có, trả về 'not available'
    return 'not available', []


# Hàm lấy funding rate MEXC nhanh như Binance

def get_top_negative_funding_coins_info_mexc(n=5):
    url = "https://contract.mexc.com/api/v1/contract/funding_rate"
    response = requests.get(url)
    data = response.json()
    if isinstance(data, dict) and 'data' in data:
        data = data['data']
    # Filter only symbols with negative funding rate
    negative_funding = [item for item in data if float(item.get('fundingRate', 0)) < 0]
    # Sort by funding rate ascending (most negative first)
    sorted_data = sorted(negative_funding, key=lambda x: float(x['fundingRate']))
    top_n = sorted_data[:n]
    result = []
    for item in top_n:
        symbol = item['symbol']
        trend, rates = get_funding_trend_mexc(symbol)
        result.append({
            'symbol': symbol,
            'fundingRate': float(item['fundingRate']),
            'fundingRatePercent': round(float(item['fundingRate']) * 100, 6),
            'markPrice': float(item.get('indexPrice', 0)),
            'time': item.get('timestamp', None),
            'fundingTrend': trend,
            'recentRates': rates
        })
    return result


async def fundingRate():
    """
    Hàm này sẽ lấy thông tin funding rate của các đồng coin trên Binance, MEXC và Bybit.
    Tr��� về danh sách các đồng coin có funding rate âm, sắp xếp theo funding rate âm từ cao xuống thấp.
    """
    resultFundingInBinance = get_top_negative_funding_coins_info(5)
    resultFundingInMexc = get_top_negative_funding_coins_info_mexc(5)
    combineCoinsFundingRate = resultFundingInBinance + resultFundingInMexc
    categoryParamsBybit = ['linear', 'inverse']
    resultFundingInBybit = []
    for item in combineCoinsFundingRate:
        symbol = item['symbol']
        url = "https://api.bybit.com/v5/market/funding/history"
        params = {
            "symbol": symbol,
            "category": categoryParamsBybit[0],  # Chọn category, có thể là 'linear' hoặc 'inverse'
            "limit": 1
        }
        response = requests.get(url, params=params)
        data = response.json()
        if data.get("result") and data["result"].get("list"):
            latest = data["result"]["list"][0]
            resultFundingInBybit.append(
                {
                    "symbol": latest["symbol"],
                    "fundingRate": float(latest["fundingRate"]),
                    'time': item.get('fundingTimestamp', None),
                    "fundingRatePercent": round(float(latest["fundingRate"]) * 100, 6),
                    "markPrice": item["markPrice"],
                    "recentRates": item["recentRates"],
                    "fundingTrend": item["fundingTrend"],
                }
            )
    allSymbols = set(
        item['symbol'] for item in resultFundingInBinance + resultFundingInMexc + resultFundingInBybit
    )
    # Trả về kết quả funding rate từ 3 sàn
    return {
        "allSymbols": list(allSymbols),
        'binance': resultFundingInBinance,
        'mexc': resultFundingInMexc,
        'bybit': resultFundingInBybit
    }
