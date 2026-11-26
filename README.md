# TrioAI — Hỏi 3 AI cùng lúc & Phản biện chéo cho học sinh

**TrioAI** là ứng dụng web chạy trực tiếp trên máy tính cá nhân (**local**), giúp học sinh nhập 1 câu hỏi, gọi song song tối đa 3 AI (**Gemini**, **GPT**, **Perplexity**), xem 3 câu trả lời độc lập theo từng cột, rồi bấm **"Phản biện & chốt"** để Gemini phản biện và GPT tổng hợp bản chốt tiếng Việt ngắn gọn.

Nếu bạn chưa có API key nào, TrioAI sẽ mặc định chạy ở **Chế độ demo** bằng dữ liệu mẫu giả lập — hoàn toàn miễn phí và không gọi API thật.

---

## Nguyên tắc an toàn tài khoản

- **Chỉ dùng API chính thức** bằng API key do chính bạn tạo từ:
  - **Gemini:** Google AI Studio (`GEMINI_API_KEY`)
  - **GPT:** OpenAI Platform (`OPENAI_API_KEY`)
  - **Perplexity:** Perplexity API Console (`PERPLEXITY_API_KEY`)
- **KHÔNG** dùng 9Router, proxy, wrapper, OAuth bridge, cookie hay session token từ tài khoản web bạn đang đăng nhập.
- **KHÔNG** tự động tạo key, không tự bật thanh toán (billing), không tự mua credit.
- **KHÔNG** lưu, in, ghi log hay hiển thị API key lên trình duyệt. File `.env` đã nằm trong `.gitignore`.
- **KHÔNG** tự động gọi API trả phí: chỉ khi bạn bấm nút mới gửi yêu cầu, và luôn hiện số lần gọi API thật trong phiên.
- Nếu thiếu hoặc lỗi API key của một hãng, các hãng còn lại vẫn hoạt động bình thường.

---

## Hướng dẫn cài đặt từng bước (cho người chưa biết code)

### Bước 1: Cài đặt Python 3.10 trở lên

1. Vào trang chính thức: https://www.python.org/downloads/
2. Tải phiên bản **Python 3.10, 3.11 hoặc 3.12** mới nhất cho máy của bạn.
3. **Quan trọng (trên Windows):** Khi mở file cài đặt, nhớ đánh dấu tích vào ô **"Add python.exe to PATH"** ở góc dưới cửa sổ cài đặt rồi mới bấm **Install Now**.
4. Kiểm tra đã cài thành công:
   - Trên Windows: mở **Command Prompt (CMD)** hoặc **PowerShell**.
   - Trên macOS / Linux: mở **Terminal**.
   - Gõ lệnh sau và nhấn Enter:
     ```bash
     python --version
     ```
     *(Trên macOS/Linux có thể gõ `python3 --version`)*
   - Nếu hiện `Python 3.10.x` trở lên là đạt.

---

### Bước 2: Mở thư mục dự án và tạo môi trường ảo (Virtual Environment)

Di chuyển vào thư mục chứa mã nguồn TrioAI rồi tạo môi trường ảo `.venv` để cài thư viện gọn gàng, không ảnh hưởng các phần mềm khác trên máy:

**Trên Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
*(Nếu dùng Command Prompt / CMD thì kích hoạt bằng lệnh `.venv\Scripts\activate.bat`)*

**Trên macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Khi thấy chữ `(.venv)` xuất hiện ở đầu dòng lệnh nghĩa là bạn đã kích hoạt thành công.

---

### Bước 3: Cài đặt các thư viện cần thiết

Trong cửa sổ đang có `(.venv)`, chạy lệnh:

```bash
pip install -r requirements.txt
```

Chờ khoảng 10–30 giây để máy tải FastAPI, Uvicorn và các thư viện cần thiết.

---

### Bước 4: Lấy API key Gemini (và tùy chọn OpenAI / Perplexity)

> **Mẹo:** Nếu bạn chỉ muốn chạy thử giao diện ngay lập tức mà chưa cần tạo key, hãy bỏ qua Bước 4 và Bước 5 rồi nhảy thẳng xuống **Bước 6** — app sẽ tự bật **Chế độ demo miễn phí**!

#### 4.1. Lấy API key Gemini từ Google AI Studio
1. Truy cập https://aistudio.google.com/ và đăng nhập bằng tài khoản Google của bạn.
2. Ở menu bên trái, chọn **Get API key** (hoặc **API keys**).
3. Bấm **Create API key** để tạo một key mới.
4. Bấm **Copy** để sao chép chuỗi key (thường bắt đầu bằng `AIza...`).
5. **Lưu ý:** Không chia sẻ key này cho người khác và không đăng lên mạng.

#### 4.2. (Tùy chọn) Lấy thêm OpenAI và Perplexity API key
- **OpenAI (GPT):** Tạo key tại https://platform.openai.com/api-keys *(cần có cả Gemini và GPT key mới bấm được nút "Phản biện & chốt" bằng API thật)*.
- **Perplexity:** Tạo key tại https://www.perplexity.ai/settings/api *(trả về kèm danh sách nguồn tham khảo nếu API có trả citations)*.

---

### Bước 5: Tạo và điền file `.env`

1. Trong thư mục dự án, sao chép file `.env.example` thành một file mới tên là `.env`:
   - **Windows (PowerShell):**
     ```powershell
     Copy-Item .env.example .env
     ```
   - **macOS / Linux:**
     ```bash
     cp .env.example .env
     ```
2. Mở file `.env` bằng Notepad (Windows) hoặc TextEdit/VS Code và dán API key của bạn vào sau dấu `=` (không thêm dấu ngoặc kép, không thừa dấu cách):

```env
GEMINI_API_KEY=AIza...dan_key_cua_ban_vao_day
OPENAI_API_KEY=
PERPLEXITY_API_KEY=
GEMINI_MODEL=gemini-3.8-flash
OPENAI_MODEL=gpt-6.2-astra
PERPLEXITY_MODEL=sonar
```

> **Lưu ý về tên model:** Nếu khi chạy, app báo tài khoản chưa có quyền dùng model mặc định (ví dụ `gemini-3.8-flash` hoặc `gpt-6.2-astra`), bạn chỉ cần đổi tên model trong `.env` sang model tài khoản bạn đang có quyền (ví dụ `gemini-2.5-flash` hoặc `gpt-4o-mini`) rồi khởi động lại app.

---

### Bước 6: Chạy ứng dụng và mở trình duyệt

Trong cửa sổ dòng lệnh (đã kích hoạt `.venv`), chạy lệnh:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Sau đó mở trình duyệt (Chrome, Edge, Safari...) và truy cập địa chỉ:

**http://localhost:8000**

Để dừng ứng dụng, quay lại cửa sổ dòng lệnh và nhấn **`Ctrl + C`**.

---

## Cách sử dụng TrioAI

1. Nhập câu hỏi vào ô trống (hoặc bấm 1 trong 3 câu hỏi mẫu bên dưới ô nhập).
2. Chọn 1 trong 2 nút:
   - **"Chạy cả ba"**: Gọi song song các hãng đã có key trong `.env` bằng `ThreadPoolExecutor` và hiển thị kết quả từng cột ngay khi hãng đó trả lời xong. *(Nếu chưa có key nào trong `.env`, app tự động chạy Chế độ demo để không gọi API thật.)*
   - **"Chạy demo không tốn tiền"**: Luôn dùng dữ liệu mẫu giả lập cho cả 3 AI, số lượt gọi API thật tăng `0`.
3. Bấm **"Phản biện & chốt"**:
   - **Bước 1 (Gemini):** Đọc tất cả câu trả lời đã có và chỉ ra tối đa 3 điểm sai, mâu thuẫn, thiếu nguồn hoặc quá phức tạp (có rào chắn chống prompt injection để Gemini không làm theo chỉ dẫn ẩn nằm trong bài của AI khác).
   - **Bước 2 (GPT):** Tổng hợp bản chốt ngắn gọn bằng tiếng Việt, nêu rõ mục *Điều chưa chắc chắn / Cần kiểm tra thêm* và tuyệt đối không bịa nguồn.
   - Nếu chạy bằng API thật mà thiếu `GEMINI_API_KEY` hoặc `OPENAI_API_KEY`, nút này sẽ tự động bị khóa kèm lý do cụ thể.

---

## Các quyết định đơn giản hóa kỹ thuật

Để ứng dụng thật gọn nhẹ, dễ cài cho học sinh chưa biết code:

1. **Gọi thẳng HTTPS REST API chính thức bằng `httpx`:** Không cài thêm SDK nặng nhiều phiên bản khác nhau; đặt cố định `timeout = 60 giây` và truyền key qua HTTP header (`x-goog-api-key` cho Gemini, `Authorization: Bearer` cho OpenAI/Perplexity) để key không xuất hiện trên URL.
2. **Stream kết quả từng cột bằng NDJSON (`StreamingResponse` + `ThreadPoolExecutor`):** Khi một AI trả lời xong trước, cột của AI đó hiện ngay lập tức mà không phải chờ 2 AI còn lại.
3. **Tailwind CSS qua CDN & JavaScript thuần (không React, không cần Node.js):** Học sinh chỉ cần cài duy nhất Python là chạy được toàn bộ giao diện.
4. **Bộ đếm lượt gọi API lưu trong bộ nhớ phiên chạy (in-memory):** Tự reset về `0` khi tắt và bật lại server, không tạo file cơ sở dữ liệu phức tạp.
5. **Chế độ Demo hỗ trợ cả bước "Phản biện & chốt (Demo)":** Khi câu trả lời hiện tại đến từ Chế độ Demo, bạn có thể bấm nút này để xem trọn vẹn luồng 2 bước bằng dữ liệu giả lập (0 lượt API); còn khi chạy API thật mà thiếu Gemini hoặc GPT key thì nút bị khóa kèm lý do.

---

## Xử lý sự cố thường gặp

- **Báo lỗi `python` không được nhận diện (Windows):** Cài lại Python và nhớ tích ô **Add python.exe to PATH**, sau đó đóng mở lại PowerShell/CMD.
- **PowerShell báo lỗi không cho chạy `Activate.ps1`:** Chạy lệnh `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` một lần rồi kích hoạt lại, hoặc dùng **Command Prompt (CMD)** với lệnh `.venv\Scripts\activate.bat`.
- **Cổng 8000 đang bận:** Đổi sang cổng khác, ví dụ `uvicorn app.main:app --host 127.0.0.1 --port 8001` rồi mở `http://localhost:8001`.
- **Lỗi sai key / hết hạn mức / model chưa có quyền:** Đọc thông báo tiếng Việt ngay trong cột của hãng bị lỗi và kiểm tra lại file `.env`.
