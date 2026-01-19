# Path: src/cabin_app/model_manager.py
import logging
import os
from typing import List, Dict

# Import Clients
try:
    from google import genai
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

from cabin_app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ModelManager:
    @staticmethod
    def get_google_models() -> List[Dict[str, str]]:
        if not HAS_GOOGLE or not settings.GOOGLE_API_KEY:
            return []
        
        try:
            client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            models = list(client.models.list(config={'page_size': 100}))
            
            results = []
            for m in models:
                # Lọc model generateContent (Gemini)
                if 'generateContent' in getattr(m, 'supported_generation_methods', []):
                    # Làm sạch tên hiển thị
                    display_name = m.display_name if hasattr(m, 'display_name') else m.name
                    # m.name thường có dạng "models/gemini-..."
                    # ID ta dùng cần phải xem API yêu cầu gì. google-genai thường chấp nhận cả 2.
                    # Ta dùng m.name (có prefix models/) cho chắc chắn với list trả về.
                    # Tuy nhiên config hiện tại đang dùng "gemini-2.0-flash" (ko prefix).
                    # Để an toàn, ta lấy phần tên sau "models/".
                    
                    model_id = m.name.replace("models/", "")
                    
                    # Chỉ lấy các model Gemini phổ biến để tránh list quá dài
                    if "gemini" in model_id.lower():
                         results.append({"id": model_id, "name": f"✨ {display_name} ({model_id})"})
            
            # Sort: Ưu tiên Flash -> Pro -> Exp
            results.sort(key=lambda x: x['id'])
            return results
        except Exception as e:
            logger.error(f"Error fetching Google models: {e}")
            return []

    @staticmethod
    def refresh_models() -> Dict[str, List[Dict[str, str]]]:
        """
        Fetch models từ các provider và trả về dict update cho settings
        """
        logger.info("Refreshing models from providers...")
        
        # 1. Google
        google_models = ModelManager.get_google_models()
        
        # 2. Update Settings (In-memory)
        # Chúng ta sẽ merge vào list AI_OPTIONS hiện có
        
        # Lọc bỏ các mục Google cũ trong danh sách hiện tại
        new_ai_options = [opt for opt in settings.AI_OPTIONS if opt['id'] != 'google' and not opt['name'].startswith("✨")]
        
        # Thêm các model Google mới tìm được
        # Nếu không tìm được thì giữ fallback
        if google_models:
            for gm in google_models:
                # Add 'google' prefix to ID if needed logic in services?
                # Hiện tại service google dùng settings.GOOGLE_MODEL.
                # Dropdown value change -> update settings.GOOGLE_MODEL?
                # Cấu trúc hiện tại: Frontend gửi 'provider'='google', Backend dùng 'settings.GOOGLE_MODEL'.
                # Đây là hạn chế: Frontend chỉ gửi Provider ID (google), Backend tự lấy Model ID.
                # -> Cần sửa: Frontend phải gửi Model ID cụ thể.
                
                # Để hỗ trợ chọn model cụ thể từ frontend, ta cần sửa logic backend:
                # Frontend gửi: provider="google", model_id="gemini-2.0-flash"
                pass
        
        # Tạm thời: Trả về danh sách Google Models để Frontend hiển thị trong Dropdown 'AI Provider'
        # Nhưng lưu ý logic backend hiện tại chọn Translator dựa trên Provider Name (google, openai).
        # Ta cần Refactor Backend để nhận `model_id` từ client.
        
        return {
            "google": google_models
        }
