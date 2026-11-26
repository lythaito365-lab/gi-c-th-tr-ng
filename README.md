# Bảng giá hôm nay

GitHub Actions chạy `collector/collect.py` mỗi 30 phút, ghi `data/prices.json`, rồi `index.html` đọc file đó.

## Cài đặt
1. Tạo repo mới trên GitHub, tải toàn bộ thư mục này lên.
2. Settings → Pages → Deploy from branch → `main` / `/ (root)`.
3. Tab Actions → `update-prices` → Run workflow (chạy lần đầu để thay dữ liệu mẫu).
4. Mở `https://<tên-bạn>.github.io/<tên-repo>/`. Thêm `?tv=1` để mở thẳng chế độ bản tin.

## Nguồn dữ liệu
- Tự động: tỷ giá Vietcombank, USD/VND và vàng thế giới (open.er-api.com), vàng SJC.
- Nhập tay: sửa `data/manual.json` (điền `price` và `asof`), commit là trang cập nhật. Dùng cho cà phê, hồ tiêu, lúa gạo, heo hơi, trứng, xăng dầu, giá chợ theo vùng.

## Thêm nguồn mới
Viết một hàm trả về danh sách `item(...)` trong `collect.py`, rồi thêm vào `SOURCES`. Nguồn lỗi chỉ làm các mục của nó hiện “giá cũ”, không làm hỏng nguồn khác.

## Lưu ý
- Các nguồn tự động là trang/API công khai không có cam kết ổn định; địa chỉ hoặc định dạng có thể đổi. Kiểm tra điều khoản sử dụng của từng nguồn trước khi dùng cho kênh.
- Nếu Pages không tự dựng lại sau commit của bot, đổi `DATA_URL` trong `index.html` thành địa chỉ `raw.githubusercontent.com` của file `prices.json`.
- GitHub có thể tắt workflow định kỳ khi repo không có hoạt động trong 60 ngày.
