from django.urls import path

from . import views


urlpatterns = [

    # =========================================================
    # 1. ĐĂNG NHẬP / ĐĂNG XUẤT
    # =========================================================

    path(
        '',
        views.login_view,
        name='login'
    ),

    path(
        'login/',
        views.login_view,
        name='login'
    ),

    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),


    # =========================================================
    # 2. DASHBOARD
    # =========================================================

    path(
        'dashboard/',
        views.dashboard_view,
        name='dashboard'
    ),


    # =========================================================
    # 3. SẢN PHẨM / HÀNG HÓA
    # =========================================================

    # Danh sách sản phẩm
    path(
        'san-pham/',
        views.san_pham_list_view,
        name='san_pham_list'
    ),

    # Thêm sản phẩm
    path(
        'san-pham/them/',
        views.san_pham_form_view,
        name='san_pham_add'
    ),

    # Sửa sản phẩm
    path(
        'san-pham/sua/<int:pk>/',
        views.san_pham_form_view,
        name='san_pham_edit'
    ),

    # Xóa sản phẩm
    path(
        'san-pham/xoa/<int:pk>/',
        views.san_pham_delete_view,
        name='san_pham_delete'
    ),

    # Cập nhật tồn kho
    path(
        'san-pham/cap-nhat-kho/',
        views.cap_nhat_kho_view,
        name='cap_nhat_kho'
    ),


    # =========================================================
    # 4. PHIẾU NHẬP
    # =========================================================

    # Danh sách phiếu nhập
    path(
        'phieu-nhap/',
        views.phieu_nhap_list_view,
        name='phieu_nhap_list'
    ),

    # Tạo phiếu nhập
    path(
        'phieu-nhap/them/',
        views.phieu_nhap_create_view,
        name='phieu_nhap_create'
    ),


    # =========================================================
    # 5. PHIẾU XUẤT
    # =========================================================

    # Danh sách phiếu xuất
    path(
        'phieu-xuat/',
        views.phieu_xuat_list_view,
        name='phieu_xuat_list'
    ),

    # Tạo phiếu xuất
    path(
        'phieu-xuat/them/',
        views.phieu_xuat_create_view,
        name='phieu_xuat_create'
    ),


    # =========================================================
    # 6. THỐNG KÊ NHẬP - XUẤT - TỒN
    # =========================================================

    # Báo cáo NXT
    path(
        'thong-ke-nxt/',
        views.thong_ke_nxt_view,
        name='thong_ke_nxt'
    ),

    # Xuất CSV
    path(
        'thong-ke-nxt/xuat-csv/',
        views.export_csv_view,
        name='export_csv'
    ),


    # =========================================================
    # 7. CHI TIẾT PHIẾU / LÔ HÀNG
    # =========================================================

    # Chi tiết phiếu
    path(
        'phieu/<int:pk>/',
        views.phieu_detail_view,
        name='phieu_detail'
    ),

    # Chi tiết lô hàng
    path(
        'lo-hang/<int:pk>/',
        views.chi_tiet_lo_hang_view,
        name='chi_tiet_lo_hang'
    ),


    # =========================================================
    # 8. NHÓM HÀNG
    # =========================================================

    # Danh sách nhóm hàng
    path(
        'nhom-hang/',
        views.nhom_hang_list_view,
        name='nhom_hang_list'
    ),

    # Thêm nhóm hàng
    path(
        'nhom-hang/them/',
        views.nhom_hang_form_view,
        name='nhom_hang_add'
    ),

    # Sửa nhóm hàng
    path(
        'nhom-hang/sua/<int:pk>/',
        views.nhom_hang_form_view,
        name='nhom_hang_edit'
    ),

    # Xóa nhóm hàng
    path(
        'nhom-hang/xoa/<int:pk>/',
        views.nhom_hang_delete_view,
        name='nhom_hang_delete'
    ),


    # =========================================================
    # 9. NHÀ CUNG CẤP
    # =========================================================

    # Danh sách nhà cung cấp
    path(
        'nha-cung-cap/',
        views.nha_cung_cap_list_view,
        name='nha_cung_cap_list'
    ),

    # Thêm nhà cung cấp
    path(
        'nha-cung-cap/them/',
        views.nha_cung_cap_form_view,
        name='nha_cung_cap_add'
    ),

    # Sửa nhà cung cấp
    path(
        'nha-cung-cap/sua/<int:pk>/',
        views.nha_cung_cap_form_view,
        name='nha_cung_cap_edit'
    ),

    # Xóa nhà cung cấp
    path(
        'nha-cung-cap/xoa/<int:pk>/',
        views.nha_cung_cap_delete_view,
        name='nha_cung_cap_delete'
    ),


    # =========================================================
    # 10. TRỢ LÝ AI
    # =========================================================

    path(
        'ai-assistant/',
        views.ai_assistant_view,
        name='ai_assistant'
    ),


    # =========================================================
    # 11. QUẢN LÝ TÀI KHOẢN - ADMIN
    # =========================================================

    # Danh sách tài khoản
    path(
        'quan-ly-tai-khoan/',
        views.quan_ly_tai_khoan_view,
        name='quan_ly_tai_khoan'
    ),

    # Đổi quyền
    path(
        'quan-ly-tai-khoan/doi-quyen/<int:user_id>/',
        views.doi_quyen_user_view,
        name='doi_quyen_user'
    ),

    # Đổi trạng thái
    path(
        'quan-ly-tai-khoan/doi-trang-thai/<int:user_id>/',
        views.doi_trang_thai_user_view,
        name='doi_trang_thai_user'
    ),

    # Xóa tài khoản
    path(
        'quan-ly-tai-khoan/xoa/<int:user_id>/',
        views.admin_delete_user,
        name='admin_delete_user'
    ),


    # =========================================================
    # 12. NHẬT KÝ HOẠT ĐỘNG - ADMIN
    # =========================================================

    path(
        'nhat-ky-hoat-dong/',
        views.nhat_ky_hoat_dong_view,
        name='nhat_ky_hoat_dong'
    ),


    # =========================================================
    # 13. CÀI ĐẶT ADMIN
    # =========================================================

    path(
        'admin-settings/',
        views.admin_settings,
        name='admin_settings'
    ),


    # =========================================================
    # 14. ĐƠN VỊ TÍNH
    # =========================================================

    # Danh sách đơn vị tính
    path(
        'don-vi-tinh/',
        views.don_vi_tinh_list_view,
        name='don_vi_tinh_list'
    ),

    # Thêm đơn vị tính
    path(
        'don-vi-tinh/them/',
        views.don_vi_tinh_form_view,
        name='don_vi_tinh_add'
    ),

    # Sửa đơn vị tính
    path(
        'don-vi-tinh/sua/<int:pk>/',
        views.don_vi_tinh_form_view,
        name='don_vi_tinh_edit'
    ),

    # Xóa đơn vị tính
    path(
        'don-vi-tinh/xoa/<int:pk>/',
        views.don_vi_tinh_delete_view,
        name='don_vi_tinh_delete'
    ),

]