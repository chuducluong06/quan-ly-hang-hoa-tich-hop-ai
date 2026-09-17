from django.contrib import admin
from .models import (
    NguoiDung, NhomHang, HangHoa,
    PhieuKho, ChiTietPhieuKho, NhaCungCap,
    NhatKyHoatDong, CauHinhHeThong
)

# Tùy biến tiêu đề trang quản trị Backend Django Admin
admin.site.site_header = "Hệ Thống Quản Lý Kho AI - Ban Quản Trị"
admin.site.site_title = "Quản Trị Kho"
admin.site.index_title = "Tổng Quan Dữ Liệu & Nghiệp Vụ Kho"


# Hiển thị chi tiết phiếu kho trực tiếp ngay trong giao diện Phiếu Kho
class ChiTietPhieuKhoInline(admin.TabularInline):
    model = ChiTietPhieuKho
    extra = 1
    raw_id_fields = ['hang_hoa']


@admin.register(NguoiDung)
class NguoiDungAdmin(admin.ModelAdmin):
    list_display = ('id', 'ten_dang_nhap', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('ten_dang_nhap',)
    list_editable = ('role', 'is_active')


@admin.register(NhomHang)
class NhomHangAdmin(admin.ModelAdmin):
    list_display = ('id', 'ten_nhom', 'mo_ta')
    search_fields = ('ten_nhom',)


@admin.register(HangHoa)
class HangHoaAdmin(admin.ModelAdmin):
    list_display = ('ma_hang', 'ten_hang', 'nhom_hang', 'so_luong_ton', 'ton_toi_thieu', 'gia_nhap', 'gia_xuat')
    list_filter = ('nhom_hang',)
    search_fields = ('ma_hang', 'ten_hang')
    list_editable = ('ton_toi_thieu', 'gia_nhap', 'gia_xuat')


@admin.register(PhieuKho)
class PhieuKhoAdmin(admin.ModelAdmin):
    list_display = ('ma_phieu', 'loai_phieu', 'nha_cung_cap', 'nguoi_lap', 'ngay_lap')
    list_filter = ('loai_phieu', 'ngay_lap')
    search_fields = ('ma_phieu', 'nha_cung_cap')
    inlines = [ChiTietPhieuKhoInline]


@admin.register(NhaCungCap)
class NhaCungCapAdmin(admin.ModelAdmin):
    list_display = ('ma_ncc', 'ten_ncc', 'so_dien_thoai', 'email')
    search_fields = ('ma_ncc', 'ten_ncc', 'so_dien_thoai')


@admin.register(NhatKyHoatDong)
class NhatKyHoatDongAdmin(admin.ModelAdmin):
    list_display = ('nguoi_dung', 'hanh_dong', 'ip_address', 'thoi_gian')
    list_filter = ('hanh_dong', 'thoi_gian')
    readonly_fields = ('nguoi_dung', 'hanh_dong', 'chi_tiet', 'ip_address', 'thoi_gian')


@admin.register(CauHinhHeThong)
class CauHinhHeThongAdmin(admin.ModelAdmin):
    list_display = ('ten_cau_hinh', 'gia_tri', 'mo_ta')
    list_editable = ('gia_tri',)