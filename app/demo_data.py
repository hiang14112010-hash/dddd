"""Dữ liệu mẫu giả lập cho Chế độ demo (không gọi bất kỳ API thật nào)."""

from __future__ import annotations

import time
from typing import Dict, List


# Độ trễ nhỏ khác nhau để học sinh thấy 3 cột chạy song song và hiện kết quả ngay khi từng AI xong
DEMO_DELAYS_SECONDS: Dict[str, float] = {
    "gemini": 0.45,
    "openai": 0.75,
    "perplexity": 1.05,
}


def generate_demo_answer(provider: str, question: str) -> Dict[str, object]:
    """Tạo câu trả lời giả lập bằng tiếng Việt cho chế độ Demo không tốn tiền."""
    delay = DEMO_DELAYS_SECONDS.get(provider, 0.5)
    started = time.perf_counter()
    time.sleep(delay)

    clean_q = question.strip()
    lower_q = clean_q.lower()

    if "quang hợp" in lower_q or "hô hấp" in lower_q:
        answers = _photosynthesis_demo()
    elif "từ vựng" in lower_q or "tiếng anh" in lower_q:
        answers = _vocab_demo()
    else:
        answers = _generic_demo(clean_q)

    item = answers[provider]
    elapsed = round(time.perf_counter() - started, 2)
    return {
        "provider": provider,
        "status": "done",
        "answer": item["answer"],
        "citations": item.get("citations", []),
        "elapsed_seconds": elapsed,
        "is_demo": True,
    }


def generate_demo_critique(question: str, answers: Dict[str, str]) -> Dict[str, object]:
    """Phản biện giả lập từ Gemini (tối đa 3 điểm) trong chế độ Demo."""
    started = time.perf_counter()
    time.sleep(0.55)

    present_names = []
    if answers.get("gemini"):
        present_names.append("Gemini")
    if answers.get("openai"):
        present_names.append("GPT")
    if answers.get("perplexity"):
        present_names.append("Perplexity")

    names_str = ", ".join(present_names) if present_names else "các AI"
    critique = (
        f"[Chế độ Demo — Phản biện giả lập từ Gemini cho {names_str}]\n\n"
        "1. **Mức độ chi tiết chưa đồng đều:** Một câu trả lời giải thích khá ngắn nên dễ thiếu ví dụ minh họa cụ thể để học sinh nhớ lâu.\n"
        "2. **Thiếu nguồn kiểm chứng ở một số ý:** Ngoại trừ phần có đường dẫn tham khảo từ Perplexity, các khẳng định còn lại chưa đính kèm sách giáo khoa hay tài liệu gốc để đối chiếu.\n"
        "3. **Một vài thuật ngữ có thể đơn giản hóa hơn:** Nên tách rõ ý chính thành 3 gạch đầu dòng ngắn gọn thay vì viết thành đoạn dài."
    )
    return {
        "status": "done",
        "text": critique,
        "elapsed_seconds": round(time.perf_counter() - started, 2),
        "is_demo": True,
    }


def generate_demo_final(question: str, answers: Dict[str, str], critique: str) -> Dict[str, object]:
    """Bản chốt giả lập từ GPT bằng tiếng Việt ngắn gọn trong chế độ Demo."""
    started = time.perf_counter()
    time.sleep(0.6)

    clean_q = question.strip()
    lower_q = clean_q.lower()

    if "quang hợp" in lower_q or "hô hấp" in lower_q:
        core = (
            "- **Quang hợp** diễn ra ở lục lạp (chủ yếu ở lá xanh khi có ánh sáng): cây lấy khí CO₂ + nước + năng lượng ánh sáng để tạo chất hữu cơ (glucose) và thải khí O₂.\n"
            "- **Hô hấp tế bào** diễn ra ở ti thể (cả ngày lẫn đêm ở hầu hết sinh vật): tế bào phân giải chất hữu cơ cùng O₂ để giải phóng năng lượng (ATP) cho hoạt động sống, đồng thời thải CO₂ và nước.\n"
            "- **Mẹo nhớ nhanh:** Quang hợp là quá trình *tích lũy năng lượng*, còn hô hấp tế bào là quá trình *giải phóng năng lượng* — hai quá trình bổ trợ ngược chiều nhau."
        )
    elif "từ vựng" in lower_q or "tiếng anh" in lower_q:
        core = (
            "- **Học theo cụm từ & ngữ cảnh** thay vì học từng từ rời rạc (ví dụ học cả câu ngắn).\n"
            "- **Ôn lặp lại ngắt quãng (Spaced Repetition):** Ôn lại sau 1 ngày, 3 ngày, 7 ngày và 14 ngày bằng flashcard giấy hoặc ứng dụng.\n"
            "- **Tự kiểm tra chủ động (Active Recall):** Che nghĩa tiếng Việt và tự đặt 1 câu đơn giản với từ mới mỗi tối (chỉ cần 5–10 từ/ngày)."
        )
    else:
        core = (
            f"Với câu hỏi *\"{clean_q}\"*, bản chốt ngắn gọn từ các góc nhìn mẫu:\n"
            "- **Ý chính 1:** Xác định đúng khái niệm cốt lõi trước khi đi vào chi tiết hoặc công thức.\n"
            "- **Ý chính 2:** Chia vấn đề thành các bước nhỏ, gắn với một ví dụ quen thuộc hằng ngày để dễ kiểm tra lại.\n"
            "- **Ý chính 3:** Luôn đối chiếu thêm với sách giáo khoa hoặc nguồn chính thống khi làm bài tập quan trọng."
        )

    final_text = (
        f"[Chế độ Demo — Bản chốt giả lập từ GPT]\n\n"
        f"**Tóm tắt ngắn gọn:**\n{core}\n\n"
        "**Điều chưa chắc chắn / Cần kiểm tra thêm:**\n"
        "- Đây là câu trả lời mẫu ở **Chế độ demo** (chưa gọi API thật), nên không thay thế cho việc tra cứu trực tiếp từ sách giáo khoa hoặc kết quả chạy API thật.\n"
        "- Nếu câu hỏi liên quan đến số liệu thời sự hoặc chương trình học từng lớp cụ thể, hãy kiểm tra lại trong tài liệu học chính thức."
    )
    return {
        "status": "done",
        "text": final_text,
        "elapsed_seconds": round(time.perf_counter() - started, 2),
        "is_demo": True,
    }


def _photosynthesis_demo() -> Dict[str, Dict[str, object]]:
    return {
        "gemini": {
            "answer": (
                "[Dữ liệu mẫu Demo · Gemini]\n\n"
                "Quang hợp và hô hấp tế bào là hai quá trình ngược chiều nhưng bổ trợ cho nhau:\n"
                "- **Quang hợp:** Cây xanh dùng ánh sáng mặt trời, CO₂ và nước để tạo ra đường (glucose) và thải khí O₂. Xảy ra ở **lục lạp**.\n"
                "- **Hô hấp tế bào:** Tế bào dùng glucose và O₂ để tạo ra năng lượng (ATP) cho cơ thể hoạt động, thải ra CO₂ và nước. Xảy ra ở **ti thể**.\n"
                "- **Thời điểm:** Quang hợp cần ánh sáng, còn hô hấp diễn ra liên tục cả ngày lẫn đêm."
            ),
            "citations": [],
        },
        "openai": {
            "answer": (
                "[Dữ liệu mẫu Demo · GPT]\n\n"
                "Bạn có thể so sánh nhanh theo 4 tiêu chí:\n"
                "1. **Mục đích:** Quang hợp tạo chất hữu cơ và tích trữ năng lượng; Hô hấp tế bào phân giải chất hữu cơ để lấy năng lượng dùng ngay.\n"
                "2. **Nguyên liệu:** Quang hợp dùng CO₂ + H₂O; Hô hấp dùng Glucose + O₂.\n"
                "3. **Sản phẩm:** Quang hợp tạo Glucose + O₂; Hô hấp tạo CO₂ + H₂O + năng lượng (ATP).\n"
                "4. **Đối tượng:** Quang hợp có ở thực vật, tảo, một số vi khuẩn; Hô hấp có ở hầu hết mọi sinh vật sống (kể cả cây xanh!)."
            ),
            "citations": [],
        },
        "perplexity": {
            "answer": (
                "[Dữ liệu mẫu Demo · Perplexity]\n\n"
                "Theo tài liệu sinh học phổ thông:\n"
                "- **Quang hợp** chuyển hóa quang năng thành hóa năng tích lũy trong liên kết hóa học của phân tử đường, diễn ra chủ yếu tại lục lạp tế bào lá.\n"
                "- **Hô hấp tế bào** oxy hóa glucose qua các giai đoạn (đường phân, chu trình Krebs, chuỗi truyền electron) để sinh ATP, diễn ra ở tế bào chất và ti thể.\n"
                "- Hai quá trình này tạo thành vòng tuần hoàn khí O₂ và CO₂ trong tự nhiên."
            ),
            "citations": [
                {
                    "title": "Wikipedia Tiếng Việt — Quang hợp (Mẫu Demo)",
                    "url": "https://vi.wikipedia.org/wiki/Quang_h%E1%BB%A3p",
                },
                {
                    "title": "Wikipedia Tiếng Việt — Hô hấp tế bào (Mẫu Demo)",
                    "url": "https://vi.wikipedia.org/wiki/H%C3%B4_h%E1%BA%A5p_t%E1%BA%BF_b%C3%A0o",
                },
            ],
        },
    }


def _vocab_demo() -> Dict[str, Dict[str, object]]:
    return {
        "gemini": {
            "answer": (
                "[Dữ liệu mẫu Demo · Gemini]\n\n"
                "Để nhớ từ vựng tiếng Anh lâu mà không bị ngán:\n"
                "- Học **5–8 từ mỗi ngày** thay vì nhồi 50 từ một lúc.\n"
                "- Gắn mỗi từ với **1 câu ngắn về bản thân** (ví dụ liên quan đến lớp học hoặc sở thích).\n"
                "- Nghe phát âm chuẩn và đọc to 3 lần để nhớ cả mặt chữ lẫn âm thanh."
            ),
            "citations": [],
        },
        "openai": {
            "answer": (
                "[Dữ liệu mẫu Demo · GPT]\n\n"
                "Ba bước học từ vựng khoa học cho học sinh:\n"
                "1. **Học theo cụm từ (Collocations):** Ví dụ thay vì chỉ học 'decision', hãy học 'make a decision'.\n"
                "2. **Ôn ngắt quãng (Spaced Repetition):** Xem lại từ cũ sau 1 ngày, 3 ngày và 1 tuần.\n"
                "3. **Tự kiểm tra (Active Recall):** Nhìn nghĩa tiếng Việt rồi tự viết lại từ tiếng Anh mà không nhìn vở."
            ),
            "citations": [],
        },
        "perplexity": {
            "answer": (
                "[Dữ liệu mẫu Demo · Perplexity]\n\n"
                "Các nghiên cứu về trí nhớ học tập chỉ ra rằng **lặp lại ngắt quãng** kết hợp **gợi nhớ chủ động** (tự kiểm tra bằng thẻ flashcard) giúp ghi nhớ từ vựng lâu hơn nhiều so với chỉ đọc đi đọc lại danh sách từ.\n"
                "Bạn cũng nên học từ trong đoạn đọc ngắn phù hợp trình độ để hiểu đúng ngữ cảnh sử dụng."
            ),
            "citations": [
                {
                    "title": "Wikipedia — Spaced repetition (Mẫu Demo)",
                    "url": "https://en.wikipedia.org/wiki/Spaced_repetition",
                },
                {
                    "title": "Cambridge Dictionary — Từ điển tra phát âm & ví dụ (Mẫu Demo)",
                    "url": "https://dictionary.cambridge.org/",
                },
            ],
        },
    }


def _generic_demo(question: str) -> Dict[str, Dict[str, object]]:
    return {
        "gemini": {
            "answer": (
                "[Dữ liệu mẫu Demo · Gemini]\n\n"
                f"Đây là câu trả lời mô phỏng cho câu hỏi: *\"{question}\"*.\n"
                "- **Góc nhìn giải thích dễ hiểu:** Bắt đầu từ định nghĩa đơn giản nhất, sau đó liên hệ với một ví dụ quen thuộc trong đời sống học sinh.\n"
                "- **Gợi ý tự học:** Hãy thử tự tóm tắt lại câu trả lời bằng 2 câu theo cách hiểu của riêng bạn.\n\n"
                "*(Bạn đang ở Chế độ demo nên hoàn toàn không tốn phí API.)*"
            ),
            "citations": [],
        },
        "openai": {
            "answer": (
                "[Dữ liệu mẫu Demo · GPT]\n\n"
                f"Phân tích mẫu theo từng bước cho câu hỏi: *\"{question}\"*.\n"
                "1. **Hiểu đúng yêu cầu:** Xác định từ khóa chính trong câu hỏi.\n"
                "2. **Lập dàn ý 3 điểm:** Nguyên nhân / Bản chất -> Ví dụ cụ thể -> Lưu ý dễ nhầm lẫn.\n"
                "3. **Kiểm tra lại:** Đối chiếu với sách giáo khoa hoặc ghi chú trên lớp.\n\n"
                "*(Khi bạn điền API key vào file `.env`, bấm \"Chạy cả ba\" để nhận câu trả lời thật từ các hãng AI.)*"
            ),
            "citations": [],
        },
        "perplexity": {
            "answer": (
                "[Dữ liệu mẫu Demo · Perplexity]\n\n"
                f"Tóm tắt mẫu có dẫn nguồn cho câu hỏi: *\"{question}\"*.\n"
                "- Perplexity thường tìm kiếm thông tin công khai và đính kèm **danh sách nguồn tham khảo** ngay bên dưới câu trả lời để bạn tự bấm kiểm chứng.\n"
                "- Trong Chế độ thật, TrioAI chỉ hiển thị đúng các đường dẫn mà API Perplexity trả về, tuyệt đối không bịa link."
            ),
            "citations": [
                {
                    "title": "Wikipedia Tiếng Việt — Bách khoa toàn thư mở (Mẫu Demo)",
                    "url": "https://vi.wikipedia.org/",
                }
            ],
        },
    }
