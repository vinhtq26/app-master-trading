import os
import google.generativeai as genai

from model.long_ai import trading_long_signal_ai_position

gemini_key = os.getenv("GEMINI_API_KEY")
gemini_model = "gemini-2.0-flash"

genai.configure(api_key=gemini_key)

model = genai.GenerativeModel(gemini_model)  # Hoặc "gemini-1.5-flash"


class Gemini:
    @staticmethod
    def analyze(prompt_text: str) -> str:
        """
        Gửi prompt đến mô hình Gemini và nhận kết quả phân tích.
        """
        try:
            response = model.generate(prompt=prompt_text, temperature=0.3)
            return response["text"]  # Trả về kết quả dạng text
        except Exception as e:
            return f"Error: {str(e)}"
