from django.urls import path
from . import views

urlpatterns = [
    # --- Xác thực & Tổng quan ---
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login_alt'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # --- Quản lý Hàng Hóa & Tồn Kho ---
    path('san-pham/', views.san_pham_list_view, name='san_pham_list'),
    path('san-pham/them/', views.san_pham_form_view, name='san_pham_add'),
    path('san-pham/sua/<int:pk>/', views.san_pham_form_view, name='san_pham_edit'),
    path('san-pham/xoa/<int:pk>/', views.san_pham_delete_view, name='san_pham_delete'),
    path('san-pham/cap-nhat-kho/<int:pk>/', views.cap_nhat_kho_view, name='cap_nhat_kho'),
    path('san-pham/<int:pk>/lo-hang/', views.chi_tiet_lo_hang_view, name='chi_tiet_lo_hang'),

    # --- Nghiệp vụ Nhập - Xuất Kho ---
    path('phieu-nhap/', views.phieu_nhap_list_view, name='phieu_nhap_list'),
    path('phieu-nhap/them/', views.phieu_nhap_create_view, name='phieu_nhap_create'),
    
    path('phieu-xuat/', views.phieu_xuat_list_view, name='phieu_xuat_list'),
    path('phieu-xuat/them/', views.phieu_xuat_create_view, name='phieu_xuat_create'),
    
    path('phieu/<int:pk>/', views.phieu_detail_view, name='phieu_detail'),

    # --- Báo cáo & Thống kê ---
    path('thong-ke-nxt/', views.thong_ke_nxt_view, name='thong_ke_nxt'),
    path('export-csv/', views.export_csv_view, name='export_csv'),

    # --- Quản lý Nhóm Hàng ---
    path('nhom-hang/', views.nhom_hang_list_view, name='nhom_hang_list'),
    path('nhom-hang/them/', views.nhom_hang_form_view, name='nhom_hang_add'),
    path('nhom-hang/sua/<int:pk>/', views.nhom_hang_form_view, name='nhom_hang_edit'),
    path('nhom-hang/xoa/<int:pk>/', views.nhom_hang_delete_view, name='nhom_hang_delete'),

    # --- Quản lý Đơn vị tính ---
    path('don-vi-tinh/', views.don_vi_tinh_list_view, name='don_vi_tinh_list'),
    path('don-vi-tinh/them/', views.don_vi_tinh_form_view, name='don_vi_tinh_add'),
    path('don-vi-tinh/sua/<int:pk>/', views.don_vi_tinh_form_view, name='don_vi_tinh_edit'),
    path('don-vi-tinh/xoa/<int:pk>/', views.don_vi_tinh_delete_view, name='don_vi_tinh_delete'),

    # --- Quản lý Nhà cung cấp ---
    path('nha-cung-cap/', views.nha_cung_cap_list_view, name='nha_cung_cap_list'),
    path('nha-cung-cap/them/', views.nha_cung_cap_form_view, name='nha_cung_cap_add'),
    path('nha-cung-cap/sua/<int:pk>/', views.nha_cung_cap_form_view, name='nha_cung_cap_edit'),
    path('nha-cung-cap/xoa/<int:pk>/', views.nha_cung_cap_delete_view, name='nha_cung_cap_delete'),

    # --- Trí tuệ nhân tạo (AI) ---
    path('ai-assistant/', views.ai_assistant_view, name='ai_assistant'),

    # --- Quản trị Admin & Tài khoản ---
    path('quan-ly-tai-khoan/', views.admin_user_list, name='quan_ly_tai_khoan'),
    path('quan-ly-tai-khoan/doi-quyen/<int:user_id>/', views.doi_quyen_user, name='doi_quyen_user'),
    path('quan-ly-tai-khoan/doi-trang-thai/<int:user_id>/', views.admin_toggle_user_status, name='doi_trang_thai_user'),
    path('quan-ly-tai-khoan/<int:user_id>/toggle-status/', views.admin_toggle_user_status, name='admin_toggle_user_status'),
    path('nhat-ky-hoat-dong/', views.admin_audit_logs, name='nhat_ky_hoat_dong'),
    path('admin-settings/', views.admin_settings, name='admin_settings'),
]