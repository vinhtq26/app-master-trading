from fastapi import APIRouter, Body
from pydantic import BaseModel

from service.app import trading_long_signal_position, trading_short_signal_position
from service.mexc.app import trading_long_signal_position_mexc, trading_short_signal_position_mexc

router = APIRouter()

class SignalRequest(BaseModel):
    timeframe: str
    exchange: str = "binance"
    direction: str

@router.post("/signal")
async def get_signal_post(req: SignalRequest = Body(...)):
    # Xử lý cho sàn binance và mexc
    if req.exchange.lower() == "binance":
        if req.direction.lower() == "long":
            result = await trading_long_signal_position(interval=req.timeframe)
            return result
        elif req.direction.lower() == "short":
            result = await trading_short_signal_position(interval=req.timeframe)
            return result
        else:
            return {"error": "Direction phải là 'long' hoặc 'short'"}
    elif req.exchange.lower() == "mexc":
        if req.direction.lower() == "long":
            result = await trading_long_signal_position_mexc(interval=req.timeframe)
            return result
        elif req.direction.lower() == "short":
            result = await trading_short_signal_position_mexc(interval=req.timeframe)
            return result
        else:
            return {"error": "Direction phải là 'long' hoặc 'short'"}
    else:
        return {"error": "Chỉ hỗ trợ sàn binance và mexc ở phiên bản này."}
