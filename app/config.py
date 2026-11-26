"""Quản lý cấu hình môi trường an toàn cho TrioAI.

Nguyên tắc an toàn:
- Chỉ đọc API key từ biến môi trường / file .env cục bộ.
- KHÔNG BAO GIỜ lưu, in, log hay trả API key ra ngoài API hoặc giao diện.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

# Nạp .env nếu tồn tại (không ghi đè biến môi trường đã đặt sẵn trong shell)
load_dotenv(dotenv_path=ENV_FILE_PATH, override=False)

PROVIDERS: Tuple[str, ...] = ("gemini", "openai", "perplexity")

PROVIDER_META: Dict[str, Dict[str, str]] = {
    "gemini": {
        "name": "Gemini",
        "vendor": "Google AI Studio",
        "env_key": "GEMINI_API_KEY",
        "env_model": "GEMINI_MODEL",
        "default_model": "gemini-3.8-flash",
    },
    "openai": {
        "name": "GPT",
        "vendor": "OpenAI Platform",
        "env_key": "OPENAI_API_KEY",
        "env_model": "OPENAI_MODEL",
        "default_model": "gpt-6.2-astra",
    },
    "perplexity": {
        "name": "Perplexity",
        "vendor": "Perplexity API",
        "env_key": "PERPLEXITY_API_KEY",
        "env_model": "PERPLEXITY_MODEL",
        "default_model": "sonar",
    },
}

REQUEST_TIMEOUT_SECONDS: float = 60.0


def get_api_key(provider: str) -> Optional[str]:
    """Đọc API key của hãng theo tên nội bộ. Trả về None nếu trống."""
    meta = PROVIDER_META.get(provider)
    if not meta:
        return None
    raw = os.getenv(meta["env_key"], "")
    cleaned = raw.strip()
    return cleaned if cleaned else None


def get_model(provider: str) -> str:
    """Đọc tên model đã cấu hình trong .env hoặc dùng giá trị mặc định."""
    meta = PROVIDER_META[provider]
    configured = os.getenv(meta["env_model"], "").strip()
    return configured if configured else meta["default_model"]


def is_provider_configured(provider: str) -> bool:
    """Kiểm tra hãng có API key hay chưa (không trả về nội dung key)."""
    return get_api_key(provider) is not None


def get_provider_status() -> Dict[str, Dict[str, object]]:
    """Trả về trạng thái công khai của từng hãng (TUYỆT ĐỐI không chứa API key)."""
    status: Dict[str, Dict[str, object]] = {}
    for provider in PROVIDERS:
        meta = PROVIDER_META[provider]
        status[provider] = {
            "id": provider,
            "name": meta["name"],
            "vendor": meta["vendor"],
            "model": get_model(provider),
            "configured": is_provider_configured(provider),
        }
    return status


def get_configured_providers() -> List[str]:
    """Danh sách các hãng đã có API key."""
    return [p for p in PROVIDERS if is_provider_configured(p)]


def is_default_demo_mode() -> bool:
    """Nếu chưa có API key nào, mặc định chạy Chế độ demo."""
    return len(get_configured_providers()) == 0


def can_real_synthesize() -> Tuple[bool, str]:
    """Kiểm tra điều kiện chạy 'Phản biện & chốt' bằng API thật (cần cả Gemini và GPT)."""
    missing: List[str] = []
    if not is_provider_configured("gemini"):
        missing.append("GEMINI_API_KEY")
    if not is_provider_configured("openai"):
        missing.append("OPENAI_API_KEY")

    if not missing:
        return True, ""

    missing_text = " và ".join(missing)
    return (
        False,
        f"Thiếu {missing_text} trong file .env nên chưa thể chạy Phản biện & chốt bằng API thật.",
    )
