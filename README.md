# B22 — Unrestricted File Upload Lab

Đồ án thực nghiệm upload tệp không an toàn trên PHP/Apache và Node.js/Express,
đối chiếu với phòng vệ bằng kiểm tra nội dung, tái mã hóa ảnh và lưu ngoài webroot.

## An toàn và phạm vi

Chỉ chạy trên máy cá nhân. Compose chỉ publish cổng lên `127.0.0.1`.
Không đưa lab lên Internet, không dùng dữ liệu thật và không đổi sang bind mọi interface.
Các endpoint `vuln` cố ý không an toàn; không dùng làm mã mẫu production.
Payload PHP chỉ in marker, không chạy lệnh hệ điều hành. HTML marker không chứng minh XSS.
Null-byte là mô phỏng hành vi cũ, không phải bypass PHP hiện đại.

## Chạy trên Windows PowerShell

### Lấy mã nguồn từ GitHub

```powershell
git clone https://github.com/NhatHui/do-an-nt213.git 'D:\UIT\NT213\do-an-nt213'
docker compose -f 'D:\UIT\NT213\do-an-nt213\docker-compose.yml' up -d --build
python 'D:\UIT\NT213\do-an-nt213\tests\run_experiments.py'
```

Đường dẫn trong các ví dụ còn lại là vị trí máy phát triển ban đầu.
Nếu clone ở vị trí khác, thay tiền tố `D:\UIT\NT213\doan\b22-ufu-lab`
bằng đường dẫn tuyệt đối tới thư mục vừa clone. Các script chính tự xác định thư mục dự án.
Thư mục `DEMO_MAU` chứa tệp mẫu và kịch bản; `docs` chứa báo cáo và ảnh giao diện.
Video và tệp nén demo cục bộ `1109.mp4`, `1109.rar` không được đưa vào Git.

Yêu cầu Docker Desktop đang chạy Linux containers, Docker Compose và Python 3.11+.
Runner sử dụng thư viện chuẩn Python, không cần cài thêm package.

```powershell
docker compose -f 'D:\UIT\NT213\doan\b22-ufu-lab\docker-compose.yml' up -d --build
docker compose -f 'D:\UIT\NT213\doan\b22-ufu-lab\docker-compose.yml' ps
python 'D:\UIT\NT213\doan\b22-ufu-lab\tests\run_experiments.py'
```

- PHP: http://127.0.0.1:18081
- Node: http://127.0.0.1:18082
- Lần đầu cần Internet để tải image, dependency và image Semgrep.
- Exit `0`: tất cả kiểm tra đạt; `1`: có kiểm tra thất bại; `2`: hạ tầng chưa sẵn sàng.
- Preflight bị chặn sẽ giữ nguyên báo cáo trước đó. Không diễn giải báo cáo cũ là kết quả mới.
- Runner ghi báo cáo Markdown, JSON và log Semgrep vào thư mục
  `D:\UIT\NT213\doan\b22-ufu-lab\docs` khi thực nghiệm chạy được.

Kiểm tra runner không cần Docker:

```powershell
python -m unittest discover -s 'D:\UIT\NT213\doan\b22-ufu-lab\tests' -p 'test_*.py' -v
node --check 'D:\UIT\NT213\doan\b22-ufu-lab\node-lab\server.js'
```

Dừng và xóa container lab (các tệp upload trong container sẽ mất):

```powershell
docker compose -f 'D:\UIT\NT213\doan\b22-ufu-lab\docker-compose.yml' down
```

## Kịch bản demo / bảo vệ

### Giao diện demo tương tác

Hai trang chủ PHP và Node hiện có form upload tiếng Việt, hai chế độ phòng vệ/có lỗ hổng,
chọn hoặc kéo thả tệp, mẫu vô hại tạo trong trình duyệt, tùy chỉnh tên/MIME,
kết quả HTTP/JSON/header, tải kết quả JSON và lịch sử tối đa 10 request trong phiên.
Không tự mở tệp tải lên. PHP phòng vệ chưa có endpoint tải xuống; Node có liên kết tải JPEG.

Mẫu giao diện và CSS/JS dùng chung nằm tại `D:\UIT\NT213\doan\b22-ufu-lab\ui`.
Sau khi chỉnh nguồn giao diện, sinh lại các tệp được đóng gói vào hai container:

```powershell
python 'D:\UIT\NT213\doan\b22-ufu-lab\ui\build_ui.py'
docker compose -f 'D:\UIT\NT213\doan\b22-ufu-lab\docker-compose.yml' up -d --build
```

Kiểm thử trình duyệt tùy chọn sử dụng Selenium và Chrome đã cài trên máy:

```powershell
python 'D:\UIT\NT213\doan\b22-ufu-lab\tests\browser_smoke.py'
```

Selenium chỉ phục vụ kiểm thử giao diện, không cần để chạy ứng dụng hoặc runner chính.
Ảnh chụp desktop/mobile và kết quả kiểm thử giao diện được ghi vào thư mục docs.

1. Giải thích vì sao extension hoặc Content-Type do client gửi không đủ tin cậy.
2. Chạy runner: so sánh PHP chấp nhận tệp chứa marker với endpoint phòng vệ từ chối tệp giả ảnh.
3. Trình bày các tình huống double extension, magic bytes, polyglot và traversal.
4. Chứng minh tái mã hóa loại bỏ marker và tệp được lưu ngoài webroot.
5. Trình bày download an toàn ở Node: ID ngẫu nhiên, attachment, nosniff và CSP.
6. Đối chiếu hai cảnh báo Semgrep với mã cố ý có lỗ hổng; nêu giới hạn rule dạng structural heuristic.

## Trạng thái và giới hạn

Đánh giá ngày 2026-11-02: phần lõi và báo cáo cũ 25 PASS đã có.
Đợt bổ sung này thêm 11 kiểm tra tích hợp biên (ảnh rỗng/hỏng, extension lệch,
field sai và ba ngưỡng kích thước PHP), chuẩn hóa phản hồi 400/413,
preflight bảo toàn báo cáo và 6 unit test cho preflight.

Đã chạy đạt 6 unit test, kiểm tra cú pháp Node/Python và kiểm tra cấu hình Compose.
Đã xác nhận runner trả exit 2 và không thay đổi hash báo cáo khi Docker Engine tắt.
Trạng thái cập nhật ngày 2026-11-03: đã build lại hai container và chạy đạt 36/36
kiểm tra tích hợp HTTP/Semgrep, gồm 11 kiểm tra biên bổ sung. Đã tắt display_errors
và bật log_errors ở PHP để cảnh báo post_max_size không gửi body trước HTTP 413.
Giao diện tương tác của cả hai nền tảng đã qua kiểm thử Chrome tự động:
ảnh hợp lệ, ảnh giả, ảnh có marker nối thêm, chọn tệp thật, reset, lịch sử và
kiểm tra không tràn ngang ở viewport điện thoại. 6 unit test preflight vẫn đạt.

Trước khi nộp cần:

- Chạy lại bộ thực nghiệm sau mỗi thay đổi tiếp theo; xử lý mọi FAIL/BLOCKED.
- Cập nhật báo cáo Word/PDF trong docs với giao diện và kết quả 36 PASS mới;
  bản báo cáo đã xuất trước đó vẫn mô tả trạng thái lịch sử. Ảnh giao diện có trong docs/ui-*.png.
- Chốt phiên bản dependency/image để tăng khả năng tái lập; hiện chưa có npm lockfile.
- Không tuyên bố phòng vệ production hoàn chỉnh: lab chưa có xác thực, phân quyền tải tệp,
  CSRF protection cho ứng dụng dùng cookie, rate limit/quota và quét malware.
- Quản lý mã nguồn tại https://github.com/NhatHui/do-an-nt213; không commit thông tin bí mật hoặc dữ liệu cá nhân.