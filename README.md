# 📦 Hệ Thống Quản Lý Hàng Hóa Tích Hợp AI

Đây là dự án hệ thống quản lý kho hàng được xây dựng bằng Python (Django). Dự án nhằm mục đích tối ưu hóa quy trình nhập/xuất kho và đang trong quá trình phát triển tích hợp các tính năng AI để hỗ trợ quản lý.

## 🚀 Tính năng nổi bật
*   Quản lý danh sách sản phẩm, nhà cung cấp.
*   Theo dõi phiếu nhập, phiếu xuất kho.
*   Thống kê hàng tồn kho.
*   *(Đang phát triển)* Tích hợp AI để dự báo và tối ưu kho.

## 🛠️ Công nghệ sử dụng
*   **Backend:** Python, Django
*   **Database:** SQLite (Mặc định cho môi trường phát triển)
*   **Giao diện:** HTML/CSS (Tailwind/Bootstrap)

## 💻 Hướng dẫn cài đặt

1. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```

2. Tạo file `.env` từ `.env.example` và điền `ADMIN_USERNAME`,
   `ADMIN_PASSWORD`; điền `GEMINI_API_KEY` nếu dùng tính năng AI.

3. Chạy ứng dụng:
   ```bash
   python manage.py migrate
   python manage.py create_admin_from_env
   python manage.py runserver
   ```

   Lệnh `create_admin_from_env` tạo hoặc cập nhật tài khoản quản trị khi được
   chạy thủ công. Mật khẩu được lưu dưới dạng hash trong cơ sở dữ liệu và
   không tự động thay đổi mỗi lần khởi động máy chủ.