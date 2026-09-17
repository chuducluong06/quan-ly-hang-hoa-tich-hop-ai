from django.db import models
from django.utils import timezone


class NguoiDung(models.Model):
    ROLES = (
        ('ADMIN', 'Quản trị viên (Admin)'),
        ('THUKHO', 'Thủ kho'),
        ('KETOANKHO', 'Kế toán kho'),
    )
    
    ten_dang_nhap = models.CharField(max_length=100, unique=True, verbose_name="Tên đăng nhập")
    password_hash = models.CharField(max_length=255, verbose_name="Mật khẩu mã hóa")
    role = models.CharField(max_length=50, choices=ROLES, default='THUKHO', verbose_name="Vai trò")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")

    class Meta:
        db_table = "NguoiDung"
        verbose_name = "Người Dùng"
        verbose_name_plural = "Danh sách người dùng"

    def __str__(self):
        return f"{self.ten_dang_nhap} ({self.get_role_display()})"


class NhomHang(models.Model):
    ten_nhom = models.CharField(max_length=255, unique=True, verbose_name="Tên nhóm hàng")
    mo_ta = models.TextField(blank=True, null=True, verbose_name="Mô tả")

    class Meta:
        db_table = "NhomHang"
        verbose_name = "Nhóm hàng"
        verbose_name_plural = "Các nhóm hàng"

    def __str__(self):
        return self.ten_nhom


class DonViTinh(models.Model):
    ten_dvt = models.CharField(max_length=100, unique=True, verbose_name="Tên đơn vị tính")
    mo_ta = models.TextField(blank=True, null=True, verbose_name="Mô tả")

    class Meta:
        db_table = "DonViTinh"
        verbose_name = "Đơn vị tính"
        verbose_name_plural = "Các đơn vị tính"

    def __str__(self):
        return self.ten_dvt


class NhaCungCap(models.Model):
    ma_ncc = models.CharField(max_length=50, unique=True, verbose_name="Mã nhà cung cấp")
    ten_ncc = models.CharField(max_length=255, verbose_name="Tên nhà cung cấp")
    so_dien_thoai = models.CharField(max_length=20, blank=True, null=True, verbose_name="Số điện thoại")
    dia_chi = models.TextField(blank=True, null=True, verbose_name="Địa chỉ")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    ngay_tao = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        db_table = "NhaCungCap"
        verbose_name = "Nhà Cung Cấp"
        verbose_name_plural = "Danh sách nhà cung cấp"

    def __str__(self):
        return f"{self.ten_ncc} ({self.ma_ncc})"


class HangHoa(models.Model):
    ma_hang = models.CharField(max_length=50, unique=True, verbose_name="Mã hàng")
    ten_hang = models.CharField(max_length=255, verbose_name="Tên hàng")
    nhom_hang = models.ForeignKey(NhomHang, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Nhóm hàng")
    don_vi_tinh = models.ForeignKey(DonViTinh, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Đơn vị tính")
    so_luong_ton = models.IntegerField(default=0, verbose_name="Số lượng tồn")
    ton_toi_thieu = models.IntegerField(default=5, verbose_name="Tồn tối thiểu")
    gia_nhap = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Giá nhập")
    gia_xuat = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Giá xuất")

    @property
    def is_can_nhap_them(self):
        """Kiểm tra xem hàng hóa có đang dưới mức tồn tối thiểu hay không"""
        return self.so_luong_ton <= self.ton_toi_thieu

    class Meta:
        db_table = "HangHoa"
        verbose_name = "Hàng hóa"
        verbose_name_plural = "Danh mục hàng hóa"

    def __str__(self):
        return f"[{self.ma_hang}] {self.ten_hang}"


class PhieuKho(models.Model):
    LOAI_PHIEU = (
        ('NHAP', 'Phiếu Nhập Kho'),
        ('XUAT', 'Phiếu Xuất Kho'),
    )
    
    ma_phieu = models.CharField(max_length=50, unique=True, verbose_name="Mã phiếu")
    loai_phieu = models.CharField(max_length=10, choices=LOAI_PHIEU, verbose_name="Loại phiếu")
    nha_cung_cap = models.ForeignKey(NhaCungCap, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Nhà cung cấp")
    ngay_lap = models.DateTimeField(auto_now_add=True, verbose_name="Ngày lập")
    nguoi_lap = models.ForeignKey(NguoiDung, on_delete=models.SET_NULL, null=True, verbose_name="Người lập phiếu")
    ghi_chu = models.TextField(blank=True, null=True, verbose_name="Ghi chú")

    def tinh_tong_tien(self):
        """Tính tổng giá trị của phiếu kho dựa vào chi tiết"""
        return sum(item.thanh_tien for item in self.chi_tiet.all())

    @property
    def chitietphieukho_set(self):
        """Alias tương thích ngược nếu view cũ gọi tới set này"""
        return self.chi_tiet

    class Meta:
        db_table = "PhieuKho"
        verbose_name = "Phiếu Kho"
        verbose_name_plural = "Quản lý Phiếu Kho"

    def __str__(self):
        return f"[{self.get_loai_phieu_display()}] {self.ma_phieu}"


class ChiTietPhieuKho(models.Model):
    phieu_kho = models.ForeignKey(PhieuKho, on_delete=models.CASCADE, related_name='chi_tiet', verbose_name="Phiếu kho")
    hang_hoa = models.ForeignKey(HangHoa, on_delete=models.CASCADE, verbose_name="Hàng hóa")
    so_luong = models.IntegerField(verbose_name="Số lượng giao dịch")
    don_gia = models.DecimalField(max_digits=18, decimal_places=2, verbose_name="Đơn giá tại thời điểm lập")
    
    ngay_san_xuat = models.DateField(null=True, blank=True, verbose_name="Ngày sản xuất")
    han_su_dung = models.DateField(null=True, blank=True, verbose_name="Hạn sử dụng")

    class Meta:
        db_table = "ChiTietPhieuKho"
        verbose_name = "Chi tiết phiếu kho"
        verbose_name_plural = "Chi tiết các phiếu kho"

    def __str__(self):
        return f"{self.phieu_kho.ma_phieu} - {self.hang_hoa.ten_hang} (SL: {self.so_luong})"

    @property
    def thanh_tien(self):
        return self.so_luong * self.don_gia


class NhatKyHoatDong(models.Model):
    nguoi_dung = models.ForeignKey(NguoiDung, on_delete=models.CASCADE, verbose_name="Người thực hiện")
    hanh_dong = models.CharField(max_length=255, verbose_name="Hành động")
    chi_tiet = models.TextField(blank=True, null=True, verbose_name="Chi tiết")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="Địa chỉ IP")
    thoi_gian = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian")

    class Meta:
        db_table = "NhatKyHoatDong"
        verbose_name = "Nhật Ký Hoạt Động"
        verbose_name_plural = "Nhật ký hoạt động"
        ordering = ['-thoi_gian']

    def __str__(self):
        return f"{self.nguoi_dung.ten_dang_nhap} - {self.hanh_dong} - {self.thoi_gian}"


class CauHinhHeThong(models.Model):
    ten_cau_hinh = models.CharField(max_length=100, unique=True, verbose_name="Tên cấu hình")
    gia_tri = models.CharField(max_length=255, verbose_name="Giá trị")
    mo_ta = models.TextField(blank=True, null=True, verbose_name="Mô tả")

    class Meta:
        db_table = "CauHinhHeThong"
        verbose_name = "Cấu Hình Hệ Thống"
        verbose_name_plural = "Cấu hình hệ thống"

    def __str__(self):
        return self.ten_cau_hinh