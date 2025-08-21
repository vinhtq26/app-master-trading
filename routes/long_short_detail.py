from fastapi import APIRouter, Request

from service.app import trading_long_detail_signal_position, trading_short_detail_signal_position
from service.long_short_detail_service import get_long_short_detail
from service.mexc.app import trading_long_detail_signal_position_mexc, trading_short_detail_signal_position_mexc

router = APIRouter()

@router.post("/long_short_detail")
async def handle_long_short_detail(request: Request):
    body = await request.json()
    exchange = body.get("exchange")
    timeframe = body.get("timeframe")
    symbol = body.get("symbol")
    direction = body.get("direction")
    if exchange.lower() == "binance":
        # Call Binance-specific logic
        if direction.lower() == "long":
            return await trading_long_detail_signal_position(interval=timeframe, symbols=[symbol])
        elif direction.lower() == "short":
            return await trading_short_detail_signal_position(interval=timeframe, symbols=[symbol])
    elif exchange.lower() == "mexc":
        # Call MEXC-specific logic
        if direction.lower() == "long":
            return await trading_long_detail_signal_position_mexc(interval=timeframe, symbols=[symbol])
        elif direction.lower() == "short":
            return await trading_short_detail_signal_position_mexc(interval=timeframe, symbols=[symbol])
    return None
