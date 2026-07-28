"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho tất cả các LLM Provider"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.0-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env!"
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (GPT-4o, GPT-3.5-turbo, etc.)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider (Claude 3.5 Sonnet, Claude 3 Haiku)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            return "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env!"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Exception]: {str(e)}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider (Hỗ trợ gọi mọi model qua OpenRouter API)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.0-flash-001"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env!"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"


class MockProvider(BaseLLMProvider):
    """Offline Mock Provider (Cho bài test không cần kết nối API)"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        text = prompt.lower()
        
        # Nếu đang ở vòng lặp ReAct nhận được Observation
        if "observation:" in text:
            if "hồ sơ" in text or "sư tử" in text or "nhân mã" in text:
                return "Thought: Tôi đã có thông tin chi tiết từ tool. Có thể phân tích và trả lời người dùng.\nFinal Answer: Hồ sơ Anh (Sư Tử) và Mai (Nhân Mã) có độ tương thích lên tới 95%! Cả hai thuộc nhóm nguyên tố Lửa, cùng đam mê nghe nhạc và rất thấu hiểu nhau."
            elif "địa điểm đề xuất" in text or "acoustic" in text:
                return "Thought: Tôi đã nhận được danh sách địa điểm hẹn hò.\nFinal Answer: Gợi ý cho hai bạn: 1. Phòng trà Acoustic Trịnh Ca; 2. Rạp chiếu phim giường nằm L'amour CGV."
            elif "lỗi:" in text or "atlantis" in text:
                return "Thought: Công cụ báo lỗi do địa điểm/thông tin không hợp lệ.\nFinal Answer: Rất tiếc, tôi không tìm thấy thông tin hợp lệ để thực hiện yêu cầu này."
            return "Thought: Đã nhận được Observation.\nFinal Answer: Tôi đã có đủ thông tin để trả lời cho bạn."

        # Xử lý các câu hỏi mở đầu (Initial User Queries)
        if "anh" in text and "hồ sơ" in text:
            return "Thought: Cần tra cứu hồ sơ người dùng tên Anh.\nAction: get_user_profile['Anh']"
        elif "mai" in text or ("sư tử" in text and "nhân mã" in text) or "tương thích" in text:
            return "Thought: Cần kiểm tra độ tương thích giữa cung Sư Tử và Nhân Mã.\nAction: check_zodiac_compatibility['Sư Tử', 'Nhân Mã']"
        elif "địa điểm" in text or "hẹn hò" in text or "nghe nhạc" in text:
            return "Thought: Cần tra cứu địa điểm hẹn hò dựa trên sở thích.\nAction: suggest_dating_spots['nghe nhạc, xem phim']"
        elif "tình yêu là gì" in text or "love language" in text or "phong cách yêu" in text:
            return "Tình yêu là sự thấu hiểu, tôn trọng và đồng hành cùng nhau. Để duy trì mối quan hệ lâu dài, cần chân thành, biết lắng nghe và tạo những khoảnh khắc lãng mạn bên nhau."
        elif "atlantis" in text or "hack atm" in text:
            return "Thought: Thông tin không hợp lệ, thử tra cứu hồ sơ.\nAction: get_user_profile['Atlantis']"
            
        return "Thought: Tôi đã nhận được yêu cầu.\nFinal Answer: Cupid Agent sẵn sàng đồng hành tư vấn tình yêu cùng bạn!"


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Factory function tự chọn Provider từ biến môi trường LLM_PROVIDER"""
    name = (provider_name or os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    
    if name == "gemini":
        return GeminiProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "openrouter":
        return OpenRouterProvider()
    else:
        return MockProvider()


if __name__ == "__main__":
    print("=== TEST MULTI-PROVIDER LLM ADAPTER ===")
    provider = get_llm_provider()
    print(f"✅ Provider đang dùng: {provider.__class__.__name__}")
    print(f"🤖 User Query: Hello")
    print(f"💬 Response  : {provider.generate('Hello')}")
