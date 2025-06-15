# import os
#
# from langchain_core.prompts import PromptTemplate
# from langchain.chains import LLMChain
# from langchain_google_genai import ChatGoogleGenerativeAI
#
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.0-flash",  # hoặc gemini-1.5-flash nếu bạn có quyền
#     google_api_key=os.getenv("GEMINI_API_KEY"),
#     temperature=0.3,
# )
#
# # Prompt for extracting time interval
# extract_time_prompt = PromptTemplate(
#     input_variables=["message"],
#     template="""
# Bạn là một AI có nhiệm vụ xác định khung thời gian (interval) được nhắc đến trong câu hỏi của người dùng về giao dịch crypto.
#
# - Nếu người dùng nói về "hôm nay", "ngày", "khung ngày", "daily" => trả về "1d"
# - Nếu nói về "15m", "15 phút", "khung 15m", "nến 15m" => trả về "15m"
# - Nếu nói về "1h", "1 giờ", "khung 1h", "nến 1h" => trả về "1h"
# - Nếu nói về "4h", "4 giờ", "khung 4h", "nến 4h" => trả về "4h"
# - Nếu không nhắc đến khung thời gian nào, trả về "5m"
#
# Chỉ trả về một trong các giá trị: "1d", "15m", "1h", "4h", "5m".
#
# ---
# Câu hỏi: "{message}"
# Interval:
# """
# )
#
# extract_time_chain = LLMChain(llm=llm, prompt=extract_time_prompt)
#
#
# async def extract_time(message: str) -> str:
#     result = await extract_time_chain.arun(message=message)
#     return result.strip()
