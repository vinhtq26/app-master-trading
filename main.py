import asyncio
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv

from constant.Constant import TIME_CONSTANT
from service.app import trading_long_signal_position, trading_short_signal_position, \
    trading_long_detail_signal_position, trading_short_detail_signal_position
from service.binance import BinanceTradingSignals
from service.funding import fundingInfo

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cấu hình LLM Gemini qua LangChain
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",  # hoặc gemini-1.5-flash nếu bạn có quyền
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.3,
)

# Prompt mẫu để phân loại intent
prompt = PromptTemplate(
    input_variables=["message"],
    template="""
Bạn là một AI có nhiệm vụ phân loại câu lệnh người dùng thành đúng **một trong các intent** sau đây:

1. **greeting** – Dùng khi người dùng chào hỏi bot, hỏi thăm, mở đầu cuộc trò chuyện.  
   ▸ Ví dụ: "Hello", "Bot ơi", "Chào buổi sáng", "Chào bạn", "Có ai ở đây không?"

2. **market_info** – Dùng khi người dùng hỏi về tình hình chung của thị trường crypto hoặc một coin cụ thể nhưng không yêu cầu phân tích long/short.  
   ▸ Ví dụ: "Thị trường hôm nay thế nào?", "BTC đang sideway à?", "Altcoin có tăng không?", "Xu hướng thị trường ra sao?"

3. **long_signal** – Dùng khi người dùng hỏi có coin nào nên mua, có tín hiệu tăng giá, hoặc cần khuyến nghị mua đơn giản.  
   ▸ Ví dụ: "Có coin nào đáng mua không?", "Cho tín hiệu long đi", "Long con nào hôm nay?", "Tín hiệu tăng hôm nay đâu?", "khung ngày tín hiệu long như nào", "tín hiệu long 15m hôm nay ra sao?", "tín hiệu long 1h hôm nay ra sao?", "tín hiệu long 4h hôm nay ra sao?", "tín hiệu long 5m hôm nay ra sao?"

4. **long_detail_signal** – Dùng khi người dùng hỏi muốn **phân tích kỹ hơn** về tín hiệu long hay còn bọi là **buy** hoặc **mua** của một hay nhiều coin cụ thể (không phải hỏi chung chung).  
   ▸ Ví dụ: "Phân tích giúp ETH có nên long không?", "ADA hôm nay có tín hiệu mua không?", "Giải thích giúp tín hiệu long của XRP", "Phân tích tín hiệu long của BTCUSDT trong khung 1h", "Phân tích tín hiệu long của ETHUSDT trong khung 15m", "Phân tích tín hiệu long của XRPUSDT trong khung 4h", "Phân tích tín hiệu long của ADAUSDT trong khung 5m"

5. **short_signal** – Dùng khi người dùng hỏi về tín hiệu bán, short coin, hoặc cảnh báo giảm giá.  
   ▸ Ví dụ: "Có coin nào nên short không?", "Tín hiệu short hôm nay đâu?", "Coin nào sắp dump?", "Tín hiệu giảm giá hôm nay ra sao?", "khung ngày tín hiệu short như nào", "tín hiệu short 15m hôm nay ra sao?", "tín hiệu short 1h hôm nay ra sao?", "tín hiệu short 4h hôm nay ra sao?", "tín hiệu short 5m hôm nay ra sao?"

6. **unknown** – Dùng khi tin nhắn không rõ ràng, không thuộc bất kỳ intent nào ở trên, hoặc không liên quan đến các chủ đề trên.  
   ▸ Ví dụ: "Bạn bao nhiêu tuổi?", "Viết bài thơ về crypto", "Tôi đang buồn", "Bạn thích màu gì?"

7. **short_detail_signal** – Dùng khi người dùng hỏi muốn **phân tích kỹ hơn** về tín hiệu short hay còn gọi là sell hoặc **bán** của một hay nhiều coin cụ thể (không phải hỏi chung chung).  
   ▸ Ví dụ: "Phân tích giúp ETH có nên short không?", "ADA và ETH hôm nay có tín hiệu bán không?", "Giải thích giúp tín hiệu short của XRP"
8. **gratitude** – Dùng khi người dùng bày tỏ lòng biết ơn, cảm ơn bot vì đã giúp đỡ.
    ▸ Ví dụ: "Cảm ơn bạn!", "Cảm ơn vì đã giúp tôi", "Rất biết ơn sự hỗ trợ của bạn"
9. **toxic** – Dùng khi người dùng sử dụng ngôn ngữ thô tục, xúc phạm, hoặc có ý định tiêu cực.
    ▸ Ví dụ: "Đồ ngu", "Mày là đồ vô dụng", "Tôi ghét bot này", "Đồ rác rưởi"
10. **funding** – Dùng khi người dùng hỏi về thông tin funding rate, lãi suất, hoặc các chi phí liên quan đến giao dịch.
    ▸ Ví dụ: "funding rate của BTCUSDT là bao nhiêu?", "Lãi suất giao dịch hôm nay thế nào?", "Chi phí funding cho ETHUSDT là bao nhiêu?", "Funding rate 15m của XRPUSDT là bao nhiêu?", "Funding rate 1h của ADAUSDT là bao nhiêu?", "Funding rate 4h của SOLUSDT là bao nhiêu?", "Funding rate 5m của DOGEUSDT là bao nhiêu?", "các coin có mức funding cao nhất sàn Binance?"
---

Chỉ trả về **một** trong các intent sau:  
`greeting`, `market_info`, `long_detail_signal`, `short_detail_signal` `long_signal`, `short_signal`, `unknown`, `gratitude`, `toxic`, `funding`

---

Message: "{message}"  
Intent:
""",
)

# LangChain pipeline
intent_chain = LLMChain(llm=llm, prompt=prompt)


# Hàm phân loại intent
async def classify_intent(message: str) -> str:
    result = await intent_chain.arun(message=message)
    return result.strip()


# WebSocket endpoint
@app.websocket("/ws")
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
                print(f"Long signal intent detected with time: {time_info}")
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
                print("summary: ", summary)
                response = {
                    "type": "Long",
                    "message": summary.strip()
                }

            elif intent == "long_detail_signal":
                print(f"long signal intent detected with time: {time_info}")

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
                        "message": f"Hiện tại danh sách {coins} không có tín hiệu long khả dụng với khung {time_info}."
                    }
                    await websocket.send_json(response)
                    continue
                # Gửi toàn bộ tín hiệu vào LLM
                summarize_chain = LLMChain(llm=llm, prompt=summarize_prompt)

                # Convert signals list thành string JSON thu gọn
                signals_input = json.dumps(signals, ensure_ascii=False)

                summary = await summarize_chain.arun(signals=signals_input)
                print("summary: ", summary)
                response = {
                    "type": "Long",
                    "message": summary.strip()
                }
                print("coin detect", coins)
            elif intent == "short_signal":
                print(f"short signal intent detected with time: {time_info}")
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
                print("summary: ", summary)
                response = {
                    "type": "Short",
                    "message": summary.strip()
                }
            elif intent == "short_detail_signal":
                print(f"short detail signal intent detected with time: {time_info}")
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
                print("summary: ", summary)
                response = {
                    "type": "Short",
                    "message": summary.strip()
                }
                print("coin detect", coins)
            elif intent == "market_info":
                print("Market info intent detected, get coin BTC and BTCDOM")
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
                print(f"Funding intent detected with time: {time_info} and coins: {coins}")
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
                resultShort = await trading_short_detail_signal_position(interval=time_info, symbols=listCoins)
                signalShort = resultShort.get("short_signals", [])
                message = "Dưới đây là thông tin về các tín hiệu long và short:\n\n"
                summarize_chain = LLMChain(llm=llm, prompt=summarize_prompt)
                signals_long_input = json.dumps(signalLong, ensure_ascii=False)
                summarylong = await summarize_chain.arun(signals=signals_long_input)
                signals_short_input = json.dumps(signalShort, ensure_ascii=False)
                summaryShort = await summarize_chain.arun(signals=signals_short_input)
                print("summary long: ", summarylong)
                print("summary short: ", summaryShort)
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
        print("WebSocket disconnected")


async def extractCoin(message: str, coinlist: list) -> list:
    prompt_template = PromptTemplate(
        input_variables=["message", "coin_list"],
        template="""
Bạn là một AI thông minh, có nhiệm vụ phân tích nội dung câu hỏi của người dùng và phát hiện ra những đồng coin nào có liên quan đến câu hỏi đó.  
Chỉ sử dụng danh sách coin cho trước, không được tự bịa thêm coin.

---
Danh sách coin hợp lệ:  
{coin_list}

---
Câu hỏi của người dùng:  
"{message}"

---
Hãy trả về danh sách các coin (ký hiệu) liên quan đến câu hỏi, coin trong danh sách có thêm ký hiệu USDT ở cuối, dưới dạng JSON list.  
Nếu không có coin nào được nhắc tới, trả về mảng rỗng [].  

Chỉ trả về JSON, ví dụ:  
["BTCUSDT", "ETHUSDT"]  
hoặc  
[]
        """
    )
    # clean_coin_list = [coin.replace("USDT", "") for coin in coinlist]
    chain = LLMChain(llm=llm, prompt=prompt_template)

    response = chain.run(message=message, coin_list=", ".join(coinlist))

    try:
        return json.loads(response)
    except:
        return []


summarize_prompt = PromptTemplate(
    input_variables=["signals"],
    template="""
Bạn là một AI phân tích giao dịch crypto.

Dưới đây là danh sách các tín hiệu mua (long signal), mỗi mục chứa:  
- `symbol`: tên coin  
- `current_price`: giá hiện tại  
- `entry_price`: giá vào lệnh  
- `take_profit`: chốt lời  
- `percent`: tỉ lệ thắng dự đoán  
- `ranking_histogram`, `ranking_macd`, `ranking_rsi`, `ranking_ema`: điểm số các chỉ báo (thang 0-10) giúp bạn đưa ra lý do long

---
Dữ liệu:  
{signals}

---
Yêu cầu:
- Với mỗi coin, trình bày theo định dạng sau:
  - Tên coin: [symbol]
  - Thời gian: [time] (ví dụ: 15m, 1h, 4h, 1d)
  - Giá hiện tại: [current_price] USDT
  - Tỉ lệ thắng dự đoán: [percent]%
  - Entry: [entry_price] | TP: [take_profit] | SL: [tự động suy ra SL ≈ entry - (TP - entry)]
  - Tóm tắt lý do [position]: dựa trên các chỉ báo có điểm cao (nêu MACD, RSI... nếu từ 9 trở lên)

Chỉ trả về thông tin, không giải thích thêm.
    """
)

# Prompt for extracting time interval
extract_time_prompt = PromptTemplate(
    input_variables=["message"],
    template="""
Bạn là một AI có nhiệm vụ xác định khung thời gian (interval) được nhắc đến trong câu hỏi của người dùng về giao dịch crypto.

- Nếu người dùng nói về "hôm nay", "ngày", "khung ngày", "daily" => trả về "1d"
- Nếu nói về "15m", "15 phút", "khung 15m", "nến 15m" => trả về "15m"
- Nếu nói về "1h", "1 giờ", "khung 1h", "nến 1h" => trả về "1h"
- Nếu nói về "4h", "4 giờ", "khung 4h", "nến 4h" => trả về "4h"
- Nếu không nhắc đến khung thời gian nào, trả về "5m"

Chỉ trả về một trong các giá trị: "1d", "15m", "1h", "4h", "5m".

---
Câu hỏi: "{message}"
Interval:
"""
)

extract_time_chain = LLMChain(llm=llm, prompt=extract_time_prompt)


async def extract_time(message: str) -> str:
    result = await extract_time_chain.arun(message=message)
    return result.strip()
