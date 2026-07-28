"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer / Integrator)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
Chủ đề: Cupid Agent - Trợ Lý Ghép Đôi & Phân Tích Độ Tương Thích
"""

import json
import os
import re
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2 (tools), Role 3 (prompts) & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json do Role 1 biên soạn"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_action(action_str: str):
    """
    Trích xuất tên tool và tham số từ chuỗi Action.
    Ví dụ: 
        Action: get_user_profile['Anh'] -> ('get_user_profile', ['Anh'])
        Action: check_zodiac_compatibility['Sư Tử', 'Nhân Mã'] -> ('check_zodiac_compatibility', ['Sư Tử', 'Nhân Mã'])
    """
    match = re.search(r"(\w+)\s*[\[\(](.*?)[\]\)]", action_str)
    if not match:
        return None, []
        
    tool_name = match.group(1).strip()
    raw_args = match.group(2).strip()
    
    if not raw_args:
        return tool_name, []
        
    args = [arg.strip(" '\"") for arg in raw_args.split(",")]
    return tool_name, args


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline Cấp 2) - Chỉ tư vấn lý thuyết chung, không sử dụng Tool.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot Baseline trả lời:\n{response}")
    return response


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Cấp 3: Thought -> Action -> Observation) có Guardrails.
    """
    print(f"\n🧠 [CUPID REACT AGENT] Câu hỏi: {user_query}")
    
    conversation_history = f"User: {user_query}"
    step = 0
    final_response = ""
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        # 1. Gọi LLM sinh suy luận (Thought & Action)
        llm_output = provider.generate(conversation_history, system_prompt=REACT_SYSTEM_PROMPT)
        print(f"🤖 Agent Response:\n{llm_output}")
        
        # 2. Kiểm tra nếu Agent đã đưa ra Final Answer
        if "Final Answer:" in llm_output:
            final_response = llm_output.split("Final Answer:")[-1].strip()
            print(f"\n🎯 [KẾT QUẢ CUỐI CÙNG]: {final_response}")
            break
            
        # 3. Bóc tách Action và thực thi Tool
        action_line = None
        for line in llm_output.split("\n"):
            if line.strip().startswith("Action:"):
                action_line = line.strip()
                break
                
        if action_line:
            tool_name, args = parse_action(action_line)
            print(f"🛠️ Thực thi Tool: {tool_name} với tham số: {args}")
            
            if tool_name in AVAILABLE_TOOLS:
                tool_func = AVAILABLE_TOOLS[tool_name]
                try:
                    # Tránh crash app nếu truyền sai số lượng tham số
                    obs = tool_func(*args)
                except Exception as e:
                    obs = f"LỖI THỰC THI TOOL '{tool_name}': {str(e)}"
            else:
                obs = f"LỖI: Tool '{tool_name}' không tồn tại trong registry hệ thống."
                
            print(f"👁️ Observation: {obs}")
            
            # Cập nhật lịch sử hội thoại cho bước tiếp theo
            conversation_history += f"\n{llm_output}\nObservation: {obs}"
        else:
            # Nếu LLM không sinh Action rõ ràng, coi như đã xong
            final_response = llm_output
            break
            
    if step >= MAX_ITERATIONS and not final_response:
        print(f"\n🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")
        final_response = "Tôi đã vượt quá số bước suy luận tối đa mà chưa hoàn thành. Vui lòng thử lại với câu hỏi cụ thể hơn."
        
    return final_response


if __name__ == "__main__":
    print("==========================================================")
    print("💘 VINUNI AI IN ACTION - LAB 3: CUPID REACT AGENT DEMO")
    print("==========================================================")
    
    # 1. Khởi tạo Multi-Provider Adapter
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    # 2. Đọc danh sách Test Cases của Role 1
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # 3. Chọn 2 Test Cases đại diện (Test #1 đơn giản & Test #5 suy luận đa bước)
    simple_test = tests[0]["question"]  # Test #1
    multistep_test = tests[4]["question"]  # Test #5
    
    print("==========================================================")
    print("DEMO 1: CHẠY TRÊN CÂU HỎI ĐƠN GIẢN (Test Case #1)")
    print("==========================================================")
    print("--- 💬 Baseline Chatbot ---")
    run_baseline_chatbot(simple_test, provider)
    
    print("\n--- 🧠 Cupid ReAct Agent ---")
    run_react_agent(simple_test, provider)
    
    print("\n==========================================================")
    print("DEMO 2: CHẠY TRÊN CÂU HỎI CẦN TOOL & SUY LUẬN (Test Case #5)")
    print("==========================================================")
    print("--- 💬 Baseline Chatbot ---")
    run_baseline_chatbot(multistep_test, provider)
    
    print("\n--- 🧠 Cupid ReAct Agent ---")
    run_react_agent(multistep_test, provider)
