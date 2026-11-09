# KỊCH BẢN DEMO B22 — UPLOAD KHÔNG AN TOÀN

Thời lượng đề xuất: 7–10 phút. Chỉ dùng trên lab cục bộ.
Tất cả tệp PHP chỉ in `B22_UFU_EXEC_SUCCESS`, không chạy lệnh hệ điều hành.
Không upload các mẫu này lên website thật. Không dùng tài liệu cá nhân để demo.

## 1. Chuẩn bị

- Thư mục tệp: `D:\UIT\NT213\doan\b22-ufu-lab\DEMO_MAU`.
- PHP: http://127.0.0.1:18081/
- Node: http://127.0.0.1:18082/
- Bật Docker Desktop. Nếu lab chưa chạy, mở PowerShell và chạy:

```powershell
docker compose -f 'D:\UIT\NT213\doan\b22-ufu-lab\docker-compose.yml' up -d --build
```

- Nhấn Ctrl+F5 nếu trình duyệt còn giữ giao diện cũ.
- Mỗi lần chuyển bước: bấm **Đặt lại**, chọn chế độ, chọn tệp, rồi mới sửa tên/MIME nếu có yêu cầu.
- Trong phần **Tùy chỉnh tên và Content-Type gửi lên**, MIME là giá trị client khai báo.
  Chọn tệp mới sẽ điền lại tên và MIME; vì vậy luôn sửa MIME sau khi chọn tệp.
- Không cần mở hay chỉnh sửa nội dung tệp trước khi gửi.

## 2. Danh sách mẫu

| Tệp | Nội dung thực | Mục đích |
|---|---|---|
| 01_anh_hop_le.png | PNG 240 × 160, nền xanh | Chứng minh chức năng bình thường hoạt động |
| 02_gia_anh.png | Văn bản nhưng mang đuôi PNG | So sánh kiểm tra yếu và kiểm tra nội dung |
| 03_marker_vo_hai.php | PHP chỉ in marker | Minh họa xử lý mã phía máy chủ trong lab |
| 04_hai_duoi.php.jpg | PHP marker với hai đuôi | Minh họa tương tác extension và Apache handler |
| 05_anh_kem_marker.png | PNG hợp lệ, nối thêm PHP marker | Minh họa tái mã hóa và xử lý lại bằng LFI simulator |
| 06_anh_vuot_2MiB.png | PNG với chunk văn bản phụ, lớn hơn 2 MiB | Kiểm tra giới hạn dung lượng |
| 07_du_lieu.csv | CSV bình thường, vô hại | Minh họa loại tệp ngoài chính sách, không phải mã độc |
| 08_html_marker.html | Chỉ một chú thích HTML | Minh họa lưu và phục vụ nội dung; không chứng minh XSS |

## 3. Mở đầu — khoảng 30 giây

Nói: “Nhóm em nghiên cứu việc website cho phép upload tệp nhưng kiểm tra không đầy đủ.
Lab có hai nhánh: cố ý có lỗ hổng và có phòng vệ. Em sẽ gửi các tệp giống nhau để đối chiếu.
Mã HTTP thành công không tự chứng minh tệp an toàn, và phản hồi từ chối không có nghĩa ứng dụng bị hỏng.”

## 4. Bước 1 — Upload ảnh bình thường trên Node

1. Mở http://127.0.0.1:18082/ và chọn **Có phòng vệ**.
2. Chọn `01_anh_hop_le.png`, bấm **Gửi tệp & kiểm tra**.
3. Kỳ vọng **HTTP 201**, `stored: true`, `marker_present: false`, có ID `.jpg`.
4. Bấm **Tải JPEG đã xử lý**, mở ảnh tải về nếu cần minh họa.

Nói: “Ảnh hợp lệ được giải mã, chuyển sang JPEG và lưu ngoài thư mục public.
Ứng dụng cấp đường dẫn tải qua endpoint riêng. Đây là đường đi sử dụng bình thường.”

## 5. Bước 2 — Cùng tệp giả ảnh, hai chính sách

### 2A. Nhánh có lỗ hổng

1. Vẫn ở Node, chọn **Có lỗ hổng → Public upload — lưu vào vùng static**.
2. Chọn `02_gia_anh.png`, gửi.
3. Kỳ vọng **HTTP 201**, `stored: true`, có URL `/uploads/...`.
4. Chỉ cần chỉ ra URL và kết quả lưu; không cần mở vì đây không phải ảnh thật.

### 2B. Nhánh có phòng vệ

1. Giữ nguyên tệp, chuyển sang **Có phòng vệ**, gửi lại.
2. Kỳ vọng **HTTP 415**. Nội dung không phù hợp chữ ký PNG nên bị từ chối.

Nói: “Đuôi PNG không chứng minh tệp là ảnh. Nhánh public nhận tệp, còn nhánh phòng vệ
kiểm tra nội dung và từ chối. Trả 415 ở đây là hành vi mong đợi, không phải lỗi chương trình.”

## 6. Bước 3 — Giả Content-Type trên PHP

1. Mở http://127.0.0.1:18081/.
2. Chọn **Có lỗ hổng → Tin Content-Type từ client**.
3. Chọn `03_marker_vo_hai.php`.
4. Mở **Tùy chỉnh tên và Content-Type gửi lên**, nhập MIME **image/jpeg**.
   Giữ nguyên tên `.php`.
5. Gửi: kỳ vọng **HTTP 200**, `stored: true`.
6. Bấm **Mở tệp đã lưu**: trang trả `B22_UFU_EXEC_SUCCESS`.
7. Quay lại lab, chuyển **Có phòng vệ**, gửi lại cùng tệp: kỳ vọng **415**.

Nói: “MIME do client khai báo có thể giả mạo. Trong cấu hình PHP/Apache của lab,
tệp đã upload được diễn giải và in marker. Payload không chạy lệnh hệ điều hành.
Nhánh phòng vệ không tin MIME này và từ chối nội dung không phải ảnh.”

## 7. Bước 4 — Ảnh chứa dữ liệu bổ sung

1. Ở PHP, chọn **Có lỗ hổng → Ảnh có dữ liệu bổ sung**.
2. Chọn `05_anh_kem_marker.png`, gửi: kỳ vọng **200**.
3. Có thể bấm **LFI simulator (chỉ trong lab)**: cuối phản hồi có marker.
   Phần đầu có thể là ký tự nhị phân của ảnh vì simulator trả text/plain.
4. Quay lại, chọn **Có phòng vệ**, gửi lại: kỳ vọng **201**, `marker_present: false`.
5. Có thể lặp lại trên Node ở chế độ phòng vệ để tải ảnh JPEG đầu ra.

Nói: “Nhận diện được ảnh chưa có nghĩa mọi byte trong tệp đều an toàn.
Việc xử lý lại tệp bằng include tạo ra ngữ cảnh nguy hiểm. Tái mã hóa tạo lại ảnh
và loại bỏ marker nối thêm trong mẫu này. Không suy ra rằng cơ chế đó loại bỏ mọi loại mã độc.”

Lưu ý: mở ảnh trực tiếp không đồng nghĩa thực thi PHP; bước có marker là do LFI simulator dùng include.
PHP phòng vệ chưa cung cấp nút tải xuống vì tệp được lưu ngoài webroot.

## 8. Bước 5 — Kiểm soát dung lượng và định dạng

Trên Node, chọn **Có phòng vệ**:

- Gửi `06_anh_vuot_2MiB.png`: kỳ vọng **413** vì vượt 2 MiB.
- Gửi `07_du_lieu.csv`: kỳ vọng **415** vì chính sách chỉ cho JPEG/PNG.

Nói: “Giới hạn dung lượng giảm nguy cơ tiêu tốn tài nguyên. CSV này không chứa mã độc,
nhưng không thuộc loại tệp mà nghiệp vụ nhận ảnh cho phép.”

## 9. Phần bổ sung nếu còn thời gian

### Double extension (PHP)

- Chọn **Có lỗ hổng → Double extension**.
- Gửi `04_hai_duoi.php.jpg`, kỳ vọng 200.
- Bấm **Mở tệp đã lưu**: marker được in trong cấu hình Apache hiện tại.
- Chuyển phòng vệ, gửi lại: 415.
- Giải thích: tác động phụ thuộc cấu hình handler của lab, không phải mọi Apache đều xử lý giống nhau.

### HTML marker (Node)

- Chọn **Có lỗ hổng → Public upload**, gửi `08_html_marker.html`: 201.
- Mẫu chỉ có chú thích HTML; mở tệp có thể thấy trang trắng hoặc tải xuống tùy cách phục vụ.
- Không dùng mẫu này để tuyên bố XSS. Nó chỉ chứng minh tệp được nhận và phục vụ.

### Kiểm thử tự động và Semgrep

```powershell
python 'D:\UIT\NT213\doan\b22-ufu-lab\tests\run_experiments.py'
```

Trình bày kết quả thực tế của lần chạy, không đọc số liệu cũ nếu Docker chưa sẵn sàng.
Rule Semgrep phát hiện hai mẫu cố ý yếu; không chứng minh mọi lỗ hổng đã được tìm thấy.

## 10. Kết luận — khoảng 30 giây

“Upload an toàn không chỉ kiểm tra đuôi tệp. Nhóm phối hợp kiểm tra nội dung,
giới hạn kích thước và pixel, tái mã hóa, tên ngẫu nhiên và lưu ngoài vùng public.
Kết quả có giá trị trong bộ mẫu và cấu hình đã kiểm thử; lab chưa có xác thực,
phân quyền và các cơ chế hoàn chỉnh để dùng cho production.”

## 11. Khi kết quả khác mong đợi

- **400:** kiểm tra đã chọn tệp và dùng đúng form.
- **413:** vượt ngưỡng byte hoặc giới hạn ảnh; PHP tối đa 1 MiB, Node tối đa 2 MiB.
- **415 ở bước PHP MIME giả:** sau khi chọn `.php`, phải sửa MIME thành `image/jpeg`.
- **415 ở phòng vệ:** thường là kết quả đúng với tệp giả, CSV hoặc PHP.
- **500 / lỗi kết nối:** không gọi đây là phòng vệ thành công; kiểm tra Docker và log.
- **Không có nút tải ở PHP phòng vệ:** đúng thiết kế hiện tại, không phải mất tệp.
- **Choose File hiện No file chosen sau kéo thả:** xem dòng tên tệp bên dưới; giao diện dùng tệp kéo thả riêng.
- Bấm **Lưu JSON** để lưu bằng chứng mỗi bước; lưu ảnh chụp cả chế độ, tên tệp, HTTP và phản hồi.

## 12. Tạo lại bộ mẫu

```powershell
python 'D:\UIT\NT213\doan\b22-ufu-lab\tests\prepare_demo.py'
```

Lệnh chỉ tạo lại tám tệp mẫu trong thư mục này, không thay đổi mã ứng dụng.