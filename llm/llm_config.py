import os

from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",  # hoặc gemini-1.5-flash nếu bạn có quyền
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.3,
)