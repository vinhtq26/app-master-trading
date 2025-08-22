import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain.chains.llm import LLMChain

from constant.Constant import TIME_CONSTANT
import asyncio
import logging

from llm.llm_config import llm
from service.app import trading_long_signal_position, trading_short_detail_signal_position, trading_long_detail_signal_position, trading_short_signal_position
from service.binance import BinanceTradingSignals
from service.funding import fundingInfo
from utils.intent_utils import classify_intent
from utils.extract_coin_utils import extractCoin
from utils.extract_time_utils import extract_time
from prompts.PromptAI import summarize_prompt

websocket_router = APIRouter()

@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            # Run all tasks concurrently
            coinlist = await BinanceTradingSignals.getAllCoinUSDT()  # Await if async
            intent_task = classify_intent(message)
            coin_task = extractCoin(message, coinlist)  # Ensure extractCoin is async
            time_task = extract_time(message)  # Ensure extract_time is async
            intent, coins, time_info = await asyncio.gather(intent_task, coin_task, time_task)
            if time_info not in TIME_CONSTANT:
                time_info = "15m"
            response = {
                "intent": intent,
                "coins": coins,
                "time": time_info
            }
            if intent == "greeting":
                response = {
                    "type": "Greeting",
                    "message": "Chào bạn! Tôi có thể giúp gì cho bạn hôm nay?"
                }
                await websocket.send_json(response)
                continue
            elif intent == "long_signal":
                logging.info(f"Long signal intent detected with time: {time_info}")
                result = await trading_long_signal_position(interval=time_info)
                signals = result.get("buy_signals", [])
                if (signals is None or len(signals) == 0):
                    response = {
                        "type": "Other",
                        "message": "Không có tín hiệu long nào khả dụng."
                    }
                    await websocket.send_json(response)
                    continue
                # Gửi toàn bộ tín hiệu vào LLM
                summarize_chain = LLMChain(llm=llm, prompt=summarize_prompt)

                # Convert signals list thành string JSON thu gọn
                signals_input = json.dumps(signals, ensure_ascii=False)

                summary = await summarize_chain.arun(signals=signals_input)
                logging.info(f"summary: {summary}")
                response = {
                    "type": "Long",
                    "message": summary.strip()
                }

            elif intent == "long_detail_signal":
                logging.info(f"long signal intent detected with time: {time_info}")

                if not coins:
                    response = {
                        "type": "Other",
                        "message": "Không nhận diện được danh sách cần hỏi."
                    }
                    await websocket.send_json(response)
                    continue
                result = await trading_long_detail_signal_position(interval=time_info, symbols=coins)
                signals = result.get("buy_signals", [])
                if (signals is None or len(signals) == 0):
                    response = {
                        "type": "Other",
                        "message": f"Hiện tại danh sách {coins} không có tín hi���u long khả dụng với khung {time_info}."
                    }
                    await websocket.send_json(response)
                    continue
                # Gửi toàn bộ tín hiệu vào LLM
                summarize_chain = LLMChain(llm=llm, prompt=summarize_prompt)

                # Convert signals list thành string JSON thu gọn
                signals_input = json.dumps(signals, ensure_ascii=False)

                summary = await summarize_chain.arun(signals=signals_input)
                logging.info(f"summary: {summary}")
                response = {
                    "type": "Long",
                    "message": summary.strip()
                }
                logging.info(f"coin detect {coins}")
            elif intent == "short_signal":
                logging.info(f"short signal intent detected with time: {time_info}")
                result = await trading_short_signal_position(interval=time_info)
                signals = result.get("short_signals", [])
                if (signals is None or len(signals) == 0):
                    response = {
                        "type": "Other",
                        "message": "Không có tín hiệu short nào khả dụng."
                    }
                    await websocket.send_json(response)
                    continue
                # Gửi toàn bộ tín hiệu vào LLM
                summarize_chain = LLMChain(llm=llm, prompt=summarize_prompt)

                # Convert signals list thành string JSON thu gọn
                signals_input = json.dumps(signals, ensure_ascii=False)

                summary = await summarize_chain.arun(signals=signals_input)
                logging.info(f"summary: {summary}")
                response = {
                    "type": "Short",
                    "message": summary.strip()
                }
            elif intent == "short_detail_signal":
                logging.info(f"short detail signal intent detected with time: {time_info}")
                if not coins:
                    response = {
                        "type": "Other",
                        "message": "Không nhận diện được danh sách cần hỏi."
                    }
                    await websocket.send_json(response)
                    continue
                result = await trading_short_detail_signal_position(interval=time_info, symbols=coins)
                signals = result.get("short_signals", [])
                if (signals is None or len(signals) == 0):
                    response = {
                        "type": "Other",
                        "message": f"Hiện tại danh sách {coins} không có tín hiệu short khả dụng với khung {time_info}."
                    }
                    await websocket.send_json(response)
                    continue
                # Gửi toàn bộ tín hiệu vào LLM
                summarize_chain = LLMChain(llm=llm, prompt=summarize_prompt)

                # Convert signals list thành string JSON thu gọn
                signals_input = json.dumps(signals, ensure_ascii=False)

                summary = await summarize_chain.arun(signals=signals_input)
                logging.info(f"summary: {summary}")
                response = {
                    "type": "Short",
                    "message": summary.strip()
                }
                logging.info(f"coin detect {coins}")
            elif intent == "market_info":
                logging.info("Market info intent detected, get coin BTC and BTCDOM")
                listCoins = ["BTCUSDT", "BTCDOMUSDT"]
                resultLong15m = await trading_long_detail_signal_position(interval="15m", symbols=listCoins)
                signalLong15m = resultLong15m.get("buy_signals", [])
                resultLong4h = await trading_long_detail_signal_position(interval="4h", symbols=listCoins)
                signalLong4h = resultLong4h.get("buy_signals", [])

                def get_percent(signals, symbol):
                    for s in signals:
                        if s.get("symbol") == symbol:
                            return s.get("percent", 0)
                    return 0

                btc_15m = get_percent(signalLong15m, "BTCUSDT")
                btcd_15m = get_percent(signalLong15m, "BTCDOMUSDT")
                btc_4h = get_percent(signalLong4h, "BTCUSDT")
                btcd_4h = get_percent(signalLong4h, "BTCDOMUSDT")

                message_15m = ""
                message_4h = ""
                # 15m logic
                if btc_15m > 80 and btcd_15m > 80:
                    message_15m = "Khung 15m: BTC có xu hướng tăng mạnh, altcoin có xu hướng giảm do BTCDOM tăng."
                elif btc_15m > 80 and btcd_15m < 80:
                    message_15m = "Khung 15m: BTC có xu hướng tăng, thị trường altcoin có thể mua."
                elif btcd_15m < 80:
                    message_15m = "BTCDOM đang giảm khung 15m, canh mua altcoin."
                elif btcd_15m > 80:
                    message_15m = "BTCDOM đang tăng khung 15m, không nên mua altcoin."
                # 4h logic
                if btc_4h > 80 and btcd_4h > 80:
                    message_4h = "Khung 4h: BTC có xu hướng tăng mạnh, altcoin có xu hướng giảm do BTCDOM tăng."
                elif btc_4h > 80 and btcd_4h < 80:
                    message_4h = "Khung 4h: BTC có xu hướng tăng, thị trường altcoin có thể mua."
                elif btcd_4h < 80:
                    message_4h = "BTCDOM đang giảm khung 4h, canh mua altcoin."
                elif btcd_4h > 80:
                    message_4h = "BTCDOM đang tăng khung 4h, không nên mua altcoin."
                if not message_15m and not message_4h:
                    response = {
                        "type": "MarketInfo",
                        "message": "Hiện tại không có tín hiệu long nổi bật cho BTCUSDT và BTCDOM ở cả 15m và 4h."
                    }
                else:
                    response = {
                        "type": "MarketInfo",
                        "message": f"{message}\n\n{message_15m}\n{message_4h}"
                    }
            elif intent == "unknown":
                response = {
                    "type": "Unknown",
                    "message": "Xin lỗi, tôi không hiểu yêu cầu của bạn. Bạn có thể thử lại với câu hỏi khác không?"
                }
            elif intent == "gratitude":
                response = {
                    "type": "Gratitude",
                    "message": "Cảm ơn bạn! Nếu cần thêm thông tin, hãy cho tôi biết."
                }
            elif intent == "toxic":
                response = {
                    "type": "Toxic",
                    "message": "Xin lỗi, tôi không thể hỗ trợ với nội dung tiêu cực hoặc không phù hợp."
                }
            elif intent == "funding":
                logging.info(f"Funding intent detected with time: {time_info} and coins: {coins}")
                funding_rate = await fundingInfo.fundingRate()
                msg = "Funding Rates:\n"
                msg += "\nBinance:\n" + "\n".join(
                    [
                        f"{item['symbol']}: {item['fundingRatePercent']}% Price: {item['markPrice']} (Trend: {item['fundingTrend']})"
                        for item in funding_rate['binance']]
                )
                msg += "\n\nMEXC:\n" + "\n".join(
                    [
                        f"{item['symbol']}: {item['fundingRatePercent']}% Price: {item['markPrice']} (Trend: {item['fundingTrend']})"
                        for item in funding_rate['mexc']]
                )
                msg += "\n\nBybit:\n" + "\n".join(
                    [
                        f"{item['symbol']}: {item['fundingRatePercent']}% Price: {item['markPrice']} (Trend: {item['fundingTrend']})"
                        for item in funding_rate['bybit']]
                )
                listCoins = funding_rate["allSymbols"]
                resultLong = await trading_long_detail_signal_position(interval=time_info, symbols=listCoins)
                signalLong = resultLong.get("buy_signals", [])
                resultShort = await trading_short_signal_position(interval=time_info, symbols=listCoins)
                signalShort = resultShort.get("short_signals", [])
                message = "Dưới đây là thông tin về các tín hiệu long và short:\n\n"
                summarize_chain = LLMChain(llm=llm, prompt=summarize_prompt)
                signals_long_input = json.dumps(signalLong, ensure_ascii=False)
                summarylong = await summarize_chain.arun(signals=signals_long_input)
                signals_short_input = json.dumps(signalShort, ensure_ascii=False)
                summaryShort = await summarize_chain.arun(signals=signals_short_input)
                logging.info(f"summary long: {summarylong}")
                logging.info(f"summary short: {summaryShort}")
                response = {
                    "type": "Funding",
                    "message": message + "\n\n" + msg + "\n\n" + summarylong.strip() + "\n\n" + summaryShort.strip()
                }

            else:
                response = {
                    "type": "Other",
                    "message": "Xin lỗi, tôi không hiểu yêu cầu của bạn. Bạn có thể thử lại với câu hỏi khác không?"
                }
            await websocket.send_json(response)
    except WebSocketDisconnect:
        logging.info("WebSocket disconnected")

