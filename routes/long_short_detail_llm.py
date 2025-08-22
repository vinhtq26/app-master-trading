from fastapi import APIRouter, Request

from service.app import trading_long_detail_signal_position, trading_short_detail_signal_position
from service.long_short_detail_service_llm_binance import get_long_short_detail_llm_binance
from service.long_short_detail_service_llm_mexc import get_long_short_detail_llm_mexc
from service.mexc.app import trading_long_detail_signal_position_mexc, trading_short_detail_signal_position_mexc

router = APIRouter()

@router.post("/long_short_detail_llm")
async def long_short_detail_llm(request: Request):
    global result
    body = await request.json()
    exchange = body.get("exchange")
    timeframe = body.get("timeframe")
    symbol = body.get("symbol")
    if exchange == "binance":
        result = get_long_short_detail_llm_binance(exchange, timeframe, symbol)
    elif exchange == "mexc":
        result = get_long_short_detail_llm_mexc(exchange, timeframe, symbol)
    return result