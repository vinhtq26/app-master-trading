import google.generativeai as genai

from prompts import PromptAI

gemini_key = "AIzaSyBG0nBHA-OTGaherKu9bFCIr3_PDIoGBiY"
gemini_model = "gemini-2.0-flash"  # Hoặc "gemini-1.
genai.configure(api_key=gemini_key)

model = genai.GenerativeModel(gemini_model)
class Gemini:
    @staticmethod
    def analyze(data):
        # Tạo prompt từ dữ liệu đầu vào
        prompt_text = PromptAI.prompt_long_15m.replace("{content}", str(data))
        # Gọi Gemini API
        import google.generativeai as genai
        gemini_key = "AIzaSyBG0nBHA-OTGaherKu9bFCIr3_PDIoGBiY"
        gemini_model = "gemini-2.0-flash"
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel(gemini_model)
        response = model.generate_content(prompt_text)
        return response.text