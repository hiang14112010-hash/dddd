"""FastAPI server cho TrioAI — Chạy local, song song 3 AI và phản biện chéo."""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import (
    PROVIDERS,
    PROVIDER_META,
    can_real_synthesize,
    get_provider_status,
    is_default_demo_mode,
    is_provider_configured,
)
from app.demo_data import (
    generate_demo_answer,
    generate_demo_critique,
    generate_demo_final,
)
from app.providers import (
    ProviderFriendlyError,
    ask_provider,
    run_gemini_critique,
    run_gpt_final_synthesis,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="TrioAI",
    description="So sánh 3 AI độc lập (Gemini, GPT, Perplexity) và phản biện chéo cho học sinh.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Bộ đếm số lần gọi API thật trong phiên chạy (thread-safe, không tính chế độ Demo)
_counter_lock = threading.Lock()
_session_api_calls: Dict[str, int] = {
    "total": 0,
    "gemini": 0,
    "openai": 0,
    "perplexity": 0,
}


def increment_api_call(provider: str) -> Dict[str, int]:
    """Tăng bộ đếm mỗi khi ứng dụng thực sự gọi API trả phí của một hãng."""
    with _counter_lock:
        _session_api_calls["total"] += 1
        if provider in _session_api_calls:
            _session_api_calls[provider] += 1
        return dict(_session_api_calls)


def get_session_api_calls() -> Dict[str, int]:
    """Lấy bản sao bộ đếm lượt gọi API thật trong phiên hiện tại."""
    with _counter_lock:
        return dict(_session_api_calls)


def reset_session_api_calls() -> None:
    """Đặt lại bộ đếm (dùng cho kiểm thử tự động)."""
    with _counter_lock:
        for key in _session_api_calls:
            _session_api_calls[key] = 0


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    demo: bool = False


class CitationItem(BaseModel):
    title: str = ""
    url: str


class SynthesizeRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    answers: Dict[str, str] = Field(default_factory=dict)
    citations: List[CitationItem] = Field(default_factory=list)
    demo: bool = False


def _ndjson_line(payload: Dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")


@app.exception_handler(Exception)
async def global_friendly_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    """Không bao giờ dump stack trace hay thông tin nhạy cảm lên giao diện."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Đã xảy ra lỗi không mong muốn trên máy chủ cục bộ. Hãy thử lại sau."
        },
    )


@app.get("/", include_in_schema=False)
def serve_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
def api_status() -> Dict[str, Any]:
    """Trả về trạng thái cấu hình an toàn (TUYỆT ĐỐI không trả API key)."""
    can_synth, synth_reason = can_real_synthesize()
    return {
        "app": "TrioAI",
        "default_demo_mode": is_default_demo_mode(),
        "providers": get_provider_status(),
        "can_real_synthesize": can_synth,
        "synthesize_disabled_reason": synth_reason,
        "api_calls": get_session_api_calls(),
    }


@app.post("/api/ask")
def api_ask(payload: AskRequest) -> StreamingResponse:
    """Gọi song song tối đa 3 AI bằng ThreadPoolExecutor và stream từng cột ngay khi xong."""
    question = payload.question.strip()
    if not question:
        return JSONResponse(  # type: ignore[return-value]
            status_code=400,
            content={"error": "Vui lòng nhập câu hỏi trước khi bấm chạy."},
        )

    # Nếu chưa có API key nào, bắt buộc chạy Chế độ demo để không gọi API thật
    effective_demo = payload.demo or is_default_demo_mode()

    def event_stream() -> Generator[bytes, None, None]:
        yield _ndjson_line(
            {
                "type": "meta",
                "mode": "demo" if effective_demo else "real",
                "api_calls": get_session_api_calls(),
            }
        )

        runnable: List[str] = []
        for provider in PROVIDERS:
            if effective_demo or is_provider_configured(provider):
                runnable.append(provider)
                yield _ndjson_line(
                    {
                        "type": "provider_status",
                        "provider": provider,
                        "status": "running",
                        "message": "Đang chạy...",
                    }
                )
            else:
                env_key = PROVIDER_META[provider]["env_key"]
                yield _ndjson_line(
                    {
                        "type": "provider_result",
                        "provider": provider,
                        "status": "missing_key",
                        "message": f"Chưa có {env_key} trong file .env nên tạm bỏ qua hãng này.",
                        "answer": "",
                        "citations": [],
                        "elapsed_seconds": 0,
                        "is_demo": False,
                        "api_calls": get_session_api_calls(),
                    }
                )

        def _worker(provider_name: str) -> Dict[str, Any]:
            if effective_demo:
                return generate_demo_answer(provider_name, question)

            increment_api_call(provider_name)
            try:
                return ask_provider(provider_name, question)
            except ProviderFriendlyError as err:
                return {
                    "provider": provider_name,
                    "status": "error",
                    "message": err.message,
                    "answer": "",
                    "citations": [],
                    "elapsed_seconds": 0,
                    "is_demo": False,
                }
            except Exception:
                label = PROVIDER_META[provider_name]["name"]
                return {
                    "provider": provider_name,
                    "status": "error",
                    "message": f"{label}: Có lỗi không mong muốn xảy ra. Hãy thử lại sau.",
                    "answer": "",
                    "citations": [],
                    "elapsed_seconds": 0,
                    "is_demo": False,
                }

        # Dùng ThreadPoolExecutor chạy song song và phát kết quả ngay khi từng hãng hoàn thành
        with ThreadPoolExecutor(max_workers=len(PROVIDERS)) as executor:
            future_map = {executor.submit(_worker, p): p for p in runnable}
            for future in as_completed(future_map):
                provider_name = future_map[future]
                try:
                    result = future.result()
                except Exception:
                    label = PROVIDER_META[provider_name]["name"]
                    result = {
                        "provider": provider_name,
                        "status": "error",
                        "message": f"{label}: Lỗi xử lý nội bộ. Hãy thử lại sau.",
                        "answer": "",
                        "citations": [],
                        "elapsed_seconds": 0,
                        "is_demo": effective_demo,
                    }

                yield _ndjson_line(
                    {
                        "type": "provider_result",
                        **result,
                        "api_calls": get_session_api_calls(),
                    }
                )

        yield _ndjson_line(
            {
                "type": "complete",
                "mode": "demo" if effective_demo else "real",
                "api_calls": get_session_api_calls(),
            }
        )

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/synthesize")
def api_synthesize(payload: SynthesizeRequest) -> StreamingResponse:
    """Chạy luồng 'Phản biện & chốt': Gemini phản biện -> GPT viết bản chốt tiếng Việt."""
    question = payload.question.strip()
    if not question:
        return JSONResponse(  # type: ignore[return-value]
            status_code=400,
            content={"error": "Thiếu câu hỏi gốc để phản biện."},
        )

    cleaned_answers = {
        k: v.strip()
        for k, v in payload.answers.items()
        if k in PROVIDERS and isinstance(v, str) and v.strip()
    }
    if not cleaned_answers:
        return JSONResponse(  # type: ignore[return-value]
            status_code=400,
            content={"error": "Chưa có câu trả lời nào để phản biện. Hãy chạy ít nhất 1 AI trước."},
        )

    effective_demo = payload.demo
    if not effective_demo:
        allowed, reason = can_real_synthesize()
        if not allowed:
            return JSONResponse(  # type: ignore[return-value]
                status_code=400,
                content={"error": reason},
            )

    citations_list: Optional[List[Dict[str, str]]] = [
        {"title": c.title, "url": c.url} for c in payload.citations
    ]

    def synth_stream() -> Generator[bytes, None, None]:
        # Bước 1: Gemini phản biện
        yield _ndjson_line(
            {
                "type": "step",
                "step": "critique",
                "status": "running",
                "message": "Gemini đang đọc và phản biện các câu trả lời...",
            }
        )

        critique_text = ""
        if effective_demo:
            critique_res = generate_demo_critique(question, cleaned_answers)
            critique_text = str(critique_res["text"])
            yield _ndjson_line(
                {
                    "type": "critique_result",
                    **critique_res,
                    "api_calls": get_session_api_calls(),
                }
            )
        else:
            increment_api_call("gemini")
            try:
                critique_res = run_gemini_critique(question, cleaned_answers)
                critique_text = str(critique_res["text"])
                yield _ndjson_line(
                    {
                        "type": "critique_result",
                        **critique_res,
                        "api_calls": get_session_api_calls(),
                    }
                )
            except ProviderFriendlyError as err:
                yield _ndjson_line(
                    {
                        "type": "critique_result",
                        "status": "error",
                        "message": err.message,
                        "text": "",
                        "api_calls": get_session_api_calls(),
                    }
                )
                yield _ndjson_line(
                    {
                        "type": "complete",
                        "mode": "real",
                        "api_calls": get_session_api_calls(),
                    }
                )
                return

        # Bước 2: GPT chốt câu trả lời
        yield _ndjson_line(
            {
                "type": "step",
                "step": "final",
                "status": "running",
                "message": "GPT đang tổng hợp bản chốt ngắn gọn bằng tiếng Việt...",
            }
        )

        if effective_demo:
            final_res = generate_demo_final(question, cleaned_answers, critique_text)
            yield _ndjson_line(
                {
                    "type": "final_result",
                    **final_res,
                    "api_calls": get_session_api_calls(),
                }
            )
        else:
            increment_api_call("openai")
            try:
                final_res = run_gpt_final_synthesis(
                    question,
                    cleaned_answers,
                    critique_text,
                    citations=citations_list,
                )
                yield _ndjson_line(
                    {
                        "type": "final_result",
                        **final_res,
                        "api_calls": get_session_api_calls(),
                    }
                )
            except ProviderFriendlyError as err:
                yield _ndjson_line(
                    {
                        "type": "final_result",
                        "status": "error",
                        "message": err.message,
                        "text": "",
                        "api_calls": get_session_api_calls(),
                    }
                )

        yield _ndjson_line(
            {
                "type": "complete",
                "mode": "demo" if effective_demo else "real",
                "api_calls": get_session_api_calls(),
            }
        )

    return StreamingResponse(
        synth_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
