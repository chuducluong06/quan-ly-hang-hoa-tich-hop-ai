import csv
import time
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Q
from django.core.paginator import Paginator
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models.functions import Coalesce
from .models import DonViTinh, NhomHang, NhaCungCap, NguoiDung, NhatKyHoatDong
from .forms import NhomHangForm, NhaCungCapForm
from .models import NguoiDung

from .models import (
    NguoiDung, NhomHang, HangHoa, PhieuKho, 
    ChiTietPhieuKho, NhaCungCap, NhatKyHoatDong, CauHinhHeThong
)


# --- DECORATORS PHÂN QUYỀN & KIỂM TRA TÀI KHOẢN ---
def is_admin(user_or_request):
    """Kiểm tra quyền Admin (hỗ trợ cả request lẫn Django user object)"""
    if hasattr(user_or_request, 'user') and hasattr(user_or_request, 'session'):
        req = user_or_request
        if req.user.is_authenticated and (req.user.is_superuser or req.user.is_staff):
            return True
        role = req.session.get('role', '')
        username = req.session.get('username', '')
        return str(role).upper() == 'ADMIN' or str(username).lower() == 'admin'
    
    user = user_or_request
    return bool(user and getattr(user, 'is_authenticated', False) and (getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)))


def is_staff_member(user_or_request):
    """Kiểm tra trạng thái đăng nhập (hỗ trợ cả request lẫn user)"""
    if hasattr(user_or_request, 'user') and hasattr(user_or_request, 'session'):
        req = user_or_request
        if req.user.is_authenticated:
            return True
        return bool(req.session.get('user_id'))
    
    user = user_or_request
    return bool(user and getattr(user, 'is_authenticated', False))


def login_required_custom(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_staff_member(request):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(allowed_roles=[]):
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not is_staff_member(request):
                return redirect('login')
            if is_admin(request):
                return view_func(request, *args, **kwargs)
            user_role = request.session.get('role')
            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "Bạn cần đăng nhập với vai trò Quản trị viên (Admin) để truy cập chức năng này.")
            return redirect('dashboard')
        return wrapper
    return decorator


def admin_only(view_func):
    """Decorator chỉ cho phép Quản trị viên truy cập"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_staff_member(request):
            return redirect('login')
        if not is_admin(request):
            raise PermissionDenied("Bạn không có quyền quản trị viên (Admin).")
        return view_func(request, *args, **kwargs)
    return wrapper


def get_current_user_obj(request):
    """Hàm tiện ích lấy đối tượng NguoiDung hiện tại an toàn"""
    user_id = request.session.get('user_id')
    if user_id:
        user = NguoiDung.objects.filter(id=user_id).first()
        if user:
            return user
    if request.user.is_authenticated:
        user = NguoiDung.objects.filter(ten_dang_nhap=request.user.username).first()
        if user:
            return user
    return NguoiDung.objects.filter(role='ADMIN').first()


# --- 1. ĐĂNG NHẬP ---
def login_view(request):
    if request.method == 'POST':
        username_input = request.POST.get('ten_dang_nhap', '').strip()
        password_input = request.POST.get('password', '').strip()

        try:
            user = NguoiDung.objects.get(ten_dang_nhap=username_input, is_active=True)
            if check_password(password_input, user.password_hash) or user.password_hash == password_input:
                request.session['user_id'] = user.id
                request.session['username'] = user.ten_dang_nhap
                request.session['role'] = user.role
                return redirect('dashboard')
            else:
                messages.error(request, "Mật khẩu không chính xác!")
        except NguoiDung.DoesNotExist:
            messages.error(request, "Tên đăng nhập không tồn tại hoặc đã bị khóa!")

    return render(request, 'warehouse/login.html')


# --- 2. ĐĂNG XUẤT ---
def logout_view(request):
    request.session.flush()
    return redirect('login')


# --- 3. DASHBOARD ---
@login_required_custom
def dashboard_view(request):
    tong_san_pham = HangHoa.objects.count()
    hang_sap_het = HangHoa.objects.filter(so_luong_ton__lt=F('ton_toi_thieu')).count()
    tong_tai_khoan = NguoiDung.objects.count()

    tong_gia_tri = HangHoa.objects.aggregate(
        total=Sum(ExpressionWrapper(F('so_luong_ton') * F('gia_xuat'), output_field=DecimalField()))
    )['total'] or 0

    top_5_hang = HangHoa.objects.order_by('-so_luong_ton')[:5]
    chart_labels = [item.ten_hang for item in top_5_hang]
    chart_data = [item.so_luong_ton for item in top_5_hang]
    min_stock_data = [item.ton_toi_thieu for item in top_5_hang]

    ds_can_nhap = HangHoa.objects.filter(so_luong_ton__lt=F('ton_toi_thieu'))

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'tong_san_pham': tong_san_pham,
        'hang_sap_het': hang_sap_het,
        'tong_tai_khoan': tong_tai_khoan,
        'tong_gia_tri': tong_gia_tri,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'min_stock_data': min_stock_data,
        'ds_can_nhap': ds_can_nhap,
    }
    return render(request, 'warehouse/dashboard.html', context)


# --- 4. DANH SÁCH SẢN PHẨM ---
@login_required_custom
def san_pham_list_view(request):
    query = request.GET.get('q', '').strip()
    filter_status = request.GET.get('status', 'all')

    danh_sach = HangHoa.objects.all().order_by('-id')

    if query:
        danh_sach = danh_sach.filter(Q(ten_hang__icontains=query) | Q(ma_hang__icontains=query))

    if filter_status == 'low_stock':
        danh_sach = danh_sach.filter(so_luong_ton__lt=F('ton_toi_thieu'))

    paginator = Paginator(danh_sach, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'danh_sach': page_obj,
        'query': query,
        'filter_status': filter_status,
    }
    return render(request, 'warehouse/san_pham_list.html', context)


# --- 5. THÊM / SỬA SẢN PHẨM ---
@login_required_custom
@role_required(['THUKHO'])
def san_pham_form_view(request, pk=None):
    is_edit = pk is not None
    san_pham = get_object_or_404(HangHoa, pk=pk) if is_edit else None
    danh_sach_nhom = NhomHang.objects.all()

    if request.method == 'POST':
        ma_hang = request.POST.get('ma_hang', '').strip()
        ten_hang = request.POST.get('ten_hang', '').strip()
        nhom_hang_id = request.POST.get('nhom_hang_id') or request.POST.get('nhom_hang')
        so_luong_ton = int(request.POST.get('so_luong_ton', 0))
        ton_toi_thieu = int(request.POST.get('ton_toi_thieu', 5))
        gia_nhap = float(request.POST.get('gia_nhap', 0))
        gia_xuat = float(request.POST.get('gia_xuat', 0))

        nhom_hang = NhomHang.objects.filter(id=nhom_hang_id).first() if nhom_hang_id else None

        if is_edit:
            san_pham.ma_hang = ma_hang
            san_pham.ten_hang = ten_hang
            san_pham.nhom_hang = nhom_hang
            san_pham.so_luong_ton = so_luong_ton
            san_pham.ton_toi_thieu = ton_toi_thieu
            san_pham.gia_nhap = gia_nhap
            san_pham.gia_xuat = gia_xuat
            san_pham.save()
            messages.success(request, "Cập nhật sản phẩm thành công!")
        else:
            HangHoa.objects.create(
                ma_hang=ma_hang,
                ten_hang=ten_hang,
                nhom_hang=nhom_hang,
                so_luong_ton=so_luong_ton,
                ton_toi_thieu=ton_toi_thieu,
                gia_nhap=gia_nhap,
                gia_xuat=gia_xuat
            )
            messages.success(request, "Thêm sản phẩm thành công!")

        return redirect('san_pham_list')

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'is_edit': is_edit,
        'san_pham': san_pham,
        'danh_sach_nhom': danh_sach_nhom,
    }
    return render(request, 'warehouse/san_pham_form.html', context)


# --- 6. XÓA SẢN PHẨM ---
@login_required_custom
@role_required(['THUKHO'])
def san_pham_delete_view(request, pk):
    san_pham = get_object_or_404(HangHoa, pk=pk)
    san_pham.delete()
    messages.success(request, "Đã xóa sản phẩm thành công!")
    return redirect('san_pham_list')


# --- 7. CẬP NHẬT KHO NHANH ---
@login_required_custom
@role_required(['THUKHO'])
@transaction.atomic
def cap_nhat_kho_view(request, pk):
    if request.method == 'POST':
        san_pham = get_object_or_404(HangHoa, pk=pk)
        loai_thao_tac = request.POST.get('loai_thao_tac')
        try:
            so_luong = int(request.POST.get('so_luong', 0))
        except ValueError:
            so_luong = 0

        if so_luong <= 0:
            messages.error(request, "Số lượng nhập/xuất phải lớn hơn 0!")
            return redirect('san_pham_list')

        user_id = request.session.get('user_id')
        nguoi_dung = NguoiDung.objects.filter(id=user_id).first()
        ma_phieu_tu_dong = f"P{'N' if loai_thao_tac == 'nhap' else 'X'}-{int(time.time())}"

        if loai_thao_tac == 'nhap':
            phieu = PhieuKho.objects.create(
                ma_phieu=ma_phieu_tu_dong,
                loai_phieu='NHAP',
                nguoi_lap=nguoi_dung,
                ghi_chu="Nhập kho nhanh từ giao diện danh sách"
            )
            ChiTietPhieuKho.objects.create(
                phieu_kho=phieu,
                hang_hoa=san_pham,
                so_luong=so_luong,
                don_gia=san_pham.gia_nhap
            )
            san_pham.so_luong_ton += so_luong
            san_pham.save()
            messages.success(request, f"Đã lập phiếu nhập {ma_phieu_tu_dong} thành công (+{so_luong} {san_pham.ten_hang}).")

        elif loai_thao_tac == 'xuat':
            if so_luong > san_pham.so_luong_ton:
                messages.error(request, f"Số lượng xuất ({so_luong}) lớn hơn tồn kho hiện tại ({san_pham.so_luong_ton})!")
                return redirect('san_pham_list')

            phieu = PhieuKho.objects.create(
                ma_phieu=ma_phieu_tu_dong,
                loai_phieu='XUAT',
                nguoi_lap=nguoi_dung,
                ghi_chu="Xuất kho nhanh từ giao diện danh sách"
            )
            ChiTietPhieuKho.objects.create(
                phieu_kho=phieu,
                hang_hoa=san_pham,
                so_luong=so_luong,
                don_gia=san_pham.gia_xuat
            )
            san_pham.so_luong_ton -= so_luong
            san_pham.save()
            messages.success(request, f"Đã lập phiếu xuất {ma_phieu_tu_dong} thành công (-{so_luong} {san_pham.ten_hang}).")

    return redirect('san_pham_list')


# --- 8. QUẢN LÝ PHIẾU NHẬP ---
@login_required_custom
def phieu_nhap_list_view(request):
    danh_sach_phieu = PhieuKho.objects.filter(loai_phieu='NHAP').order_by('-ngay_lap')
    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'danh_sach_phieu': danh_sach_phieu,
    }
    return render(request, 'warehouse/phieu_nhap_list.html', context)


# --- 9. TẠO PHIẾU NHẬP KHO MỚI ---
# --- 9. TẠO PHIẾU NHẬP KHO MỚI ---
@login_required_custom
@role_required(['THUKHO'])
@transaction.atomic
def phieu_nhap_create_view(request):
    if request.method == 'POST':
        ma_phieu = request.POST.get('ma_phieu', '').strip()
        ncc_id = request.POST.get('nha_cung_cap')
        ghi_chu = request.POST.get('ghi_chu', '').strip()

        hang_hoa_ids = request.POST.getlist('hang_hoa_id[]')
        so_luongs = request.POST.getlist('so_luong[]')
        don_gias = request.POST.getlist('don_gia[]')
        ngay_san_xuats = request.POST.getlist('ngay_san_xuat[]')
        han_su_dungs = request.POST.getlist('han_su_dung[]')

        if not ma_phieu:
            messages.error(request, "Vui lòng nhập mã phiếu nhập!")
            return redirect('phieu_nhap_create')

        if PhieuKho.objects.filter(ma_phieu=ma_phieu).exists():
            messages.error(request, f"Mã phiếu '{ma_phieu}' đã tồn tại! Vui lòng chọn mã khác.")
            return redirect('phieu_nhap_create')

        # Xử lý lấy đối tượng Nhà Cung Cấp an toàn
        nha_cung_cap_obj = None
        if ncc_id:
            try:
                nha_cung_cap_obj = NhaCungCap.objects.get(pk=ncc_id)
            except NhaCungCap.DoesNotExist:
                pass

        items_to_process = []
        for h_id, sl, dg, nsx, hsd in zip(hang_hoa_ids, so_luongs, don_gias, ngay_san_xuats, han_su_dungs):
            if not h_id:
                continue
            try:
                sl_int = int(sl)
                if sl_int <= 0:
                    continue
            except (ValueError, TypeError):
                continue

            hang_hoa = get_object_or_404(HangHoa, id=h_id)
            
            try:
                dg_val = float(dg) if dg != '' and dg is not None else float(hang_hoa.gia_nhap)
            except (ValueError, TypeError):
                dg_val = float(hang_hoa.gia_nhap)

            nsx_val = nsx if nsx else None
            hsd_val = hsd if hsd else None

            items_to_process.append((hang_hoa, sl_int, dg_val, nsx_val, hsd_val))

        if not items_to_process:
            messages.error(request, "Vui lòng chọn ít nhất một sản phẩm cần nhập kho!")
            return redirect('phieu_nhap_create')

        user_id = request.session.get('user_id')
        nguoi_dung = NguoiDung.objects.filter(id=user_id).first() if user_id else None

        # Tạo phiếu kho nhập
        phieu = PhieuKho.objects.create(
            ma_phieu=ma_phieu,
            loai_phieu='NHAP',
            nha_cung_cap=nha_cung_cap_obj, # Truyền đúng đối tượng NhaCungCap
            nguoi_lap=nguoi_dung,
            ghi_chu=ghi_chu
        )

        for hang_hoa, sl_int, dg_val, nsx_val, hsd_val in items_to_process:
            ChiTietPhieuKho.objects.create(
                phieu_kho=phieu,
                hang_hoa=hang_hoa,
                so_luong=sl_int,
                don_gia=dg_val,
                ngay_san_xuat=nsx_val,
                han_su_dung=hsd_val
            )
            hang_hoa.so_luong_ton += sl_int
            hang_hoa.save()

        messages.success(request, f"Lập phiếu nhập {ma_phieu} thành công!")
        return redirect('phieu_nhap_list')

    danh_sach_hang = HangHoa.objects.all().order_by('ten_hang')
    danh_sach_ncc = NhaCungCap.objects.all().order_by('ten') # Thêm dòng này để truyền danh sách nhà cung cấp ra form nếu cần
    ma_phieu_tu_dong = f"PN-{int(time.time())}"
    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'danh_sach_hang': danh_sach_hang,
        'danh_sach_ncc': danh_sach_ncc,
        'ma_phieu_tu_dong': ma_phieu_tu_dong,
    }
    return render(request, 'warehouse/phieu_nhap_form.html', context)


# --- 10. QUẢN LÝ PHIẾU XUẤT ---
@login_required_custom
def phieu_xuat_list_view(request):
    danh_sach_phieu = PhieuKho.objects.filter(loai_phieu='XUAT').order_by('-ngay_lap')
    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'danh_sach_phieu': danh_sach_phieu,
    }
    return render(request, 'warehouse/phieu_xuat_list.html', context)


# --- 11. TẠO PHIẾU XUẤT KHO MỚI ---
@login_required_custom
@role_required(['THUKHO'])
@transaction.atomic
def phieu_xuat_create_view(request):
    if request.method == 'POST':
        ma_phieu = request.POST.get('ma_phieu', '').strip()
        nguoi_nhan = request.POST.get('nguoi_nhan', '').strip()
        ghi_chu = request.POST.get('ghi_chu', '').strip()

        hang_hoa_ids = request.POST.getlist('hang_hoa_id[]')
        so_luongs = request.POST.getlist('so_luong[]')
        don_gias = request.POST.getlist('don_gia[]')

        if not ma_phieu:
            messages.error(request, "Vui lòng nhập mã phiếu xuất!")
            return redirect('phieu_xuat_create')

        if PhieuKho.objects.filter(ma_phieu=ma_phieu).exists():
            messages.error(request, f"Mã phiếu '{ma_phieu}' đã tồn tại! Vui lòng chọn mã khác.")
            return redirect('phieu_xuat_create')

        items_to_process = []
        tong_xuat_theo_hang = {}

        for h_id, sl, dg in zip(hang_hoa_ids, so_luongs, don_gias):
            if not h_id:
                continue
            try:
                sl_int = int(sl)
                if sl_int <= 0:
                    messages.error(request, "Số lượng xuất của các sản phẩm phải lớn hơn 0!")
                    return redirect('phieu_xuat_create')
            except (ValueError, TypeError):
                messages.error(request, "Số lượng xuất không hợp lệ!")
                return redirect('phieu_xuat_create')

            hang_hoa = get_object_or_404(HangHoa, id=h_id)

            try:
                dg_val = float(dg) if dg != '' and dg is not None else float(hang_hoa.gia_xuat)
                if dg_val < 0:
                    dg_val = float(hang_hoa.gia_xuat)
            except (ValueError, TypeError):
                dg_val = float(hang_hoa.gia_xuat)

            tong_xuat_theo_hang[hang_hoa.id] = tong_xuat_theo_hang.get(hang_hoa.id, 0) + sl_int
            items_to_process.append((hang_hoa, sl_int, dg_val))

        if not items_to_process:
            messages.error(request, "Vui lòng chọn ít nhất một sản phẩm cần xuất kho!")
            return redirect('phieu_xuat_create')

        for h_id, tong_sl in tong_xuat_theo_hang.items():
            hang_hoa = HangHoa.objects.get(id=h_id)
            if tong_sl > hang_hoa.so_luong_ton:
                messages.error(
                    request,
                    f"Sản phẩm [{hang_hoa.ma_hang}] {hang_hoa.ten_hang} không đủ tồn kho (Tồn: {hang_hoa.so_luong_ton}, Xuất yêu cầu: {tong_sl})!"
                )
                return redirect('phieu_xuat_create')

        user_id = request.session.get('user_id')
        nguoi_dung = NguoiDung.objects.filter(id=user_id).first() if user_id else None

        # Gộp thông tin người nhận vào ghi chú vì phiếu xuất không dùng đến nhà cung cấp
        ghi_chu_hoan_chinh = f"Người nhận: {nguoi_nhan}. {ghi_chu}".strip()

        phieu = PhieuKho.objects.create(
            ma_phieu=ma_phieu,
            loai_phieu='XUAT',
            nha_cung_cap=None, # Phiếu xuất để trống nhà cung cấp
            nguoi_lap=nguoi_dung,
            ghi_chu=ghi_chu_hoan_chinh
        )

        for hang_hoa, sl_int, dg_val in items_to_process:
            ChiTietPhieuKho.objects.create(
                phieu_kho=phieu,
                hang_hoa=hang_hoa,
                so_luong=sl_int,
                don_gia=dg_val
            )
            hang_hoa.so_luong_ton -= sl_int
            hang_hoa.save()

        messages.success(request, f"Lập phiếu xuất {ma_phieu} thành công!")
        return redirect('phieu_xuat_list')

    danh_sach_hang = HangHoa.objects.all().order_by('ten_hang')
    ma_phieu_tu_dong = f"PX-{int(time.time())}"
    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'danh_sach_hang': danh_sach_hang,
        'ma_phieu_tu_dong': ma_phieu_tu_dong,
    }
    return render(request, 'warehouse/phieu_xuat_form.html', context)


# --- 12. BÁO CÁO NHẬP - XUẤT - TỒN ---
@login_required_custom
@role_required(['KETOANKHO', 'THUKHO'])
def thong_ke_nxt_view(request):
    danh_sach_hang = HangHoa.objects.annotate(
        tong_nhap=Coalesce(Sum('chitietphieukho__so_luong', filter=Q(chitietphieukho__phieu_kho__loai_phieu='NHAP')), 0),
        tong_xuat=Coalesce(Sum('chitietphieukho__so_luong', filter=Q(chitietphieukho__phieu_kho__loai_phieu='XUAT')), 0)
    ).order_by('ma_hang')

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'danh_sach_hang': danh_sach_hang,
    }
    return render(request, 'warehouse/thong_ke_nxt.html', context)


# --- 13. XUẤT CSV ---
@login_required_custom
@role_required(['THUKHO', 'KETOANKHO'])
def export_csv_view(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="danh_sach_hang_hoa.csv"'

    writer = csv.writer(response)
    writer.writerow(['Mã Hàng', 'Tên Hàng', 'Số Lượng Tồn', 'Tồn Tối Thiểu', 'Giá Nhập (VNĐ)', 'Giá Xuất (VNĐ)'])

    danh_sach = HangHoa.objects.all()
    for item in danh_sach:
        writer.writerow([item.ma_hang, item.ten_hang, item.so_luong_ton, item.ton_toi_thieu, item.gia_nhap, item.gia_xuat])

    return response


# --- 14. XEM CHI TIẾT PHIẾU KHO ---
@login_required_custom
def phieu_detail_view(request, pk):
    phieu = get_object_or_404(PhieuKho, pk=pk)
    chi_tiet = phieu.chi_tiet.all()

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'phieu': phieu,
        'chi_tiet': chi_tiet,
    }
    return render(request, 'warehouse/phieu_detail.html', context)


# --- 15. XEM CHI TIẾT LÔ HÀNG ---
@login_required_custom
def chi_tiet_lo_hang_view(request, pk):
    san_pham = get_object_or_404(HangHoa, pk=pk)
    danh_sach_lo = ChiTietPhieuKho.objects.filter(
        hang_hoa=san_pham,
        phieu_kho__loai_phieu='NHAP'
    ).select_related('phieu_kho', 'phieu_kho__nguoi_lap').order_by('-phieu_kho__ngay_lap')

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'san_pham': san_pham,
        'danh_sach_lo': danh_sach_lo,
    }
    return render(request, 'warehouse/chi_tiet_lo_hang.html', context)


# --- 16. QUẢN LÝ NHÓM HÀNG ---
@login_required_custom
def nhom_hang_list_view(request):
    danh_sach = NhomHang.objects.all().order_by('-id')
    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'danh_sach': danh_sach,
    }
    return render(request, 'warehouse/nhom_hang_list.html', context)


@login_required_custom
@role_required(['THUKHO'])
def nhom_hang_form_view(request, pk=None):
    is_edit = pk is not None
    nhom_hang = get_object_or_404(NhomHang, pk=pk) if is_edit else None

    if request.method == 'POST':
        ten_nhom = request.POST.get('ten_nhom', '').strip()
        mo_ta = request.POST.get('mo_ta', '').strip()

        if not ten_nhom:
            messages.error(request, "Vui lòng nhập tên nhóm hàng!")
            return redirect('nhom_hang_edit', pk=pk) if is_edit else redirect('nhom_hang_add')

        check_exist = NhomHang.objects.filter(ten_nhom=ten_nhom)
        if is_edit:
            check_exist = check_exist.exclude(pk=pk)

        if check_exist.exists():
            messages.error(request, f"Nhóm hàng '{ten_nhom}' đã tồn tại!")
            return redirect('nhom_hang_edit', pk=pk) if is_edit else redirect('nhom_hang_add')

        if is_edit:
            nhom_hang.ten_nhom = ten_nhom
            nhom_hang.mo_ta = mo_ta
            nhom_hang.save()
            messages.success(request, "Cập nhật nhóm hàng thành công!")
        else:
            NhomHang.objects.create(ten_nhom=ten_nhom, mo_ta=mo_ta)
            messages.success(request, "Thêm nhóm hàng mới thành công!")

        return redirect('nhom_hang_list')

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'is_edit': is_edit,
        'nhom_hang': nhom_hang,
    }
    return render(request, 'warehouse/nhom_hang_form.html', context)


@login_required_custom
@role_required(['THUKHO'])
def nhom_hang_delete_view(request, pk):
    nhom_hang = get_object_or_404(NhomHang, pk=pk)
    nhom_hang.delete()
    messages.success(request, "Đã xóa nhóm hàng thành công!")
    return redirect('nhom_hang_list')


# --- 17. TRỢ LÝ & DỰ BÁO AI ---
@login_required_custom
def ai_assistant_view(request):
    hang_can_nhap = HangHoa.objects.filter(so_luong_ton__lte=F('ton_toi_thieu'))
    
    goi_y_nhap = []
    for item in hang_can_nhap:
        sl_goi_y = max((item.ton_toi_thieu * 2) - item.so_luong_ton, 10)
        chi_phi_du_kien = sl_goi_y * item.gia_nhap
        goi_y_nhap.append({
            'hang': item,
            'so_luong_goi_y': sl_goi_y,
            'chi_phi': chi_phi_du_kien
        })

    tong_san_pham = HangHoa.objects.count()
    tong_gia_tri = sum(h.so_luong_ton * h.gia_nhap for h in HangHoa.objects.all())
    so_luong_can_canh_bao = hang_can_nhap.count()

    ai_insights = []
    if so_luong_can_canh_bao > 0:
        ai_insights.append(f"⚠️ Phát hiện {so_luong_can_canh_bao} mặt hàng đang chạm/dưới ngưỡng tồn kho tối thiểu. Khuyến nghị lập phiếu nhập ngay.")
    else:
        ai_insights.append("✅ Tất cả các mặt hàng hiện tại đều nằm trong vùng an toàn.")

    if tong_gia_tri > 50000000:
        ai_insights.append(f"💰 Tổng giá trị vốn đọng kho cao ({tong_gia_tri:,.0f} đ). Cần cân đối xuất hàng để tối ưu dòng tiền.")
    else:
        ai_insights.append(f"📊 Tổng giá trị tồn kho ở mức hợp lý ({tong_gia_tri:,.0f} đ).")

    ai_insights.append("📈 Các luồng nhập/xuất kho diễn ra ổn định.")

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'goi_y_nhap': goi_y_nhap,
        'tong_san_pham': tong_san_pham,
        'tong_gia_tri': tong_gia_tri,
        'so_luong_can_canh_bao': so_luong_can_canh_bao,
        'ai_insights': ai_insights,
    }
    return render(request, 'warehouse/ai_assistant.html', context)


# --- 18. QUẢN LÝ NHÀ CUNG CẤP ---
@login_required_custom
def nha_cung_cap_list_view(request):
    danh_sach = NhaCungCap.objects.all().order_by('-id')
    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'danh_sach': danh_sach,
    }
    return render(request, 'warehouse/nha_cung_cap_list.html', context)


@login_required_custom
def nha_cung_cap_form_view(request, pk=None):
    is_edit = pk is not None
    nha_cc = get_object_or_404(NhaCungCap, pk=pk) if is_edit else None

    if request.method == 'POST':
        ma_ncc = request.POST.get('ma_ncc', '').strip()
        ten_ncc = request.POST.get('ten_ncc', '').strip()
        so_dien_thoai = request.POST.get('so_dien_thoai', '').strip()
        email = request.POST.get('email', '').strip()
        dia_chi = request.POST.get('dia_chi', '').strip()

        if not ma_ncc or not ten_ncc:
            messages.error(request, "Vui lòng nhập đầy đủ Mã và Tên nhà cung cấp!")
            return redirect('nha_cung_cap_edit', pk=pk) if is_edit else redirect('nha_cung_cap_add')

        check_exist = NhaCungCap.objects.filter(ma_ncc=ma_ncc)
        if is_edit:
            check_exist = check_exist.exclude(pk=pk)

        if check_exist.exists():
            messages.error(request, f"Mã nhà cung cấp [{ma_ncc}] đã tồn tại!")
            return redirect('nha_cung_cap_edit', pk=pk) if is_edit else redirect('nha_cung_cap_add')

        if is_edit:
            nha_cc.ma_ncc = ma_ncc
            nha_cc.ten_ncc = ten_ncc
            nha_cc.so_dien_thoai = so_dien_thoai
            nha_cc.email = email
            nha_cc.dia_chi = dia_chi
            nha_cc.save()
            messages.success(request, f"Đã cập nhật nhà cung cấp [{ten_ncc}] thành công!")
        else:
            NhaCungCap.objects.create(
                ma_ncc=ma_ncc,
                ten_ncc=ten_ncc,
                so_dien_thoai=so_dien_thoai,
                email=email,
                dia_chi=dia_chi
            )
            messages.success(request, f"Đã thêm nhà cung cấp [{ten_ncc}] thành công!")

        return redirect('nha_cung_cap_list')

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'nha_cc': nha_cc,
        'is_edit': is_edit,
    }
    return render(request, 'warehouse/nha_cung_cap_form.html', context)


@login_required_custom
def nha_cung_cap_delete_view(request, pk):
    nha_cc = get_object_or_404(NhaCungCap, pk=pk)
    ten = nha_cc.ten_ncc
    nha_cc.delete()
    messages.success(request, f"Đã xóa nhà cung cấp [{ten}] thành công!")
    return redirect('nha_cung_cap_list')


# --- 19. QUẢN TỊ QUẢN LÝ NGƯỜI DÙNG & HỆ THỐNG (ADMIN ONLY) ---

@role_required(['ADMIN'])
def admin_user_list(request):
    current_admin = NguoiDung.objects.get(id=request.session['user_id'])

    if request.method == 'POST':
        ten_dang_nhap = request.POST.get('ten_dang_nhap', '').strip()
        mat_khau = request.POST.get('mat_khau', '').strip()
        role = request.POST.get('role', 'THUKHO')

        if NguoiDung.objects.filter(ten_dang_nhap=ten_dang_nhap).exists():
            messages.error(request, f"Tên đăng nhập '{ten_dang_nhap}' đã tồn tại!")
        else:
            NguoiDung.objects.create(
                ten_dang_nhap=ten_dang_nhap,
                password_hash=make_password(mat_khau),
                role=role,
                is_active=True
            )
            NhatKyHoatDong.objects.create(
                nguoi_dung=current_admin,
                hanh_dong="Tạo tài khoản người dùng",
                chi_tiet=f"Tạo tài khoản {ten_dang_nhap} với vai trò {role}"
            )
            messages.success(request, f"Đã thêm người dùng {ten_dang_nhap} thành công!")
            return redirect('quan_ly_tai_khoan')

    users = NguoiDung.objects.all().order_by('-id')
    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'users': users
    }
    return render(request, 'warehouse/admin_user_list.html', context)


@role_required(['ADMIN'])
def admin_toggle_user_status(request, user_id):
    current_admin = NguoiDung.objects.get(id=request.session['user_id'])
    target_user = get_object_or_404(NguoiDung, id=user_id)

    if target_user.id == current_admin.id:
        messages.error(request, "Bạn không thể tự khóa tài khoản của chính mình!")
        return redirect('quan_ly_tai_khoan')

    target_user.is_active = not target_user.is_active
    target_user.save()

    NhatKyHoatDong.objects.create(
        nguoi_dung=current_admin,
        hanh_dong="Thay đổi trạng thái tài khoản",
        chi_tiet=f"{'Khóa' if not target_user.is_active else 'Mở khóa'} tài khoản: {target_user.ten_dang_nhap}"
    )
    messages.success(request, f"Đã cập nhật trạng thái tài khoản {target_user.ten_dang_nhap}.")
    return redirect('admin_user_list')


@role_required(['ADMIN'])
def admin_audit_logs(request):
    logs = NhatKyHoatDong.objects.select_related('nguoi_dung').all().order_by('-thoi_gian')[:100]
    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'logs': logs
    }
    return render(request, 'warehouse/admin_logs.html', context)


@role_required(['ADMIN'])
def admin_settings(request):
    current_admin = NguoiDung.objects.get(id=request.session['user_id'])

    if request.method == 'POST':
        api_key = request.POST.get('gemini_api_key', '').strip()
        default_min_stock = request.POST.get('default_min_stock', '5').strip()

        CauHinhHeThong.objects.update_or_create(
            ten_cau_hinh='GEMINI_API_KEY',
            defaults={'gia_tri': api_key, 'mo_ta': 'API Key kết nối trợ lý AI'}
        )
        CauHinhHeThong.objects.update_or_create(
            ten_cau_hinh='DEFAULT_MIN_STOCK',
            defaults={'gia_tri': default_min_stock, 'mo_ta': 'Ngưỡng tồn kho tối thiểu mặc định'}
        )

        NhatKyHoatDong.objects.create(
            nguoi_dung=current_admin,
            hanh_dong="Cập nhật cấu hình",
            chi_tiet="Thay đổi tham số cấu hình hệ thống"
        )
        messages.success(request, "Lưu cấu hình hệ thống thành công!")
        return redirect('admin_settings')

    config_api = CauHinhHeThong.objects.filter(ten_cau_hinh='GEMINI_API_KEY').first()
    config_stock = CauHinhHeThong.objects.filter(ten_cau_hinh='DEFAULT_MIN_STOCK').first()

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'gemini_api_key': config_api.gia_tri if config_api else '',
        'default_min_stock': config_stock.gia_tri if config_stock else '5'
    }
    return render(request, 'warehouse/admin_settings.html', context)


# --- 19. QUẢN LÝ TÀI KHOẢN & NHẬT KÝ (ADMIN ONLY) ---

@role_required(['ADMIN'])
def quan_ly_tai_khoan_view(request):
    current_admin = get_current_user_obj(request)

    if request.method == 'POST':
        ten_dang_nhap = request.POST.get('ten_dang_nhap', '').strip()
        mat_khau = request.POST.get('mat_khau', '').strip()
        role = request.POST.get('role', 'THUKHO')

        # BẢO MẬT: Không cho phép tạo thêm tài khoản Admin từ form này (chỉ cho THUKHO hoặc KETOANKHO)
        if role == 'ADMIN':
            messages.error(request, "Hệ thống chỉ cho phép duy nhất 1 tài khoản Quản trị viên (Admin) gốc!")
            return redirect('quan_ly_tai_khoan')

        if NguoiDung.objects.filter(ten_dang_nhap=ten_dang_nhap).exists():
            messages.error(request, f"Tên đăng nhập '{ten_dang_nhap}' đã tồn tại!")
        else:
            NguoiDung.objects.create(
                ten_dang_nhap=ten_dang_nhap,
                password_hash=make_password(mat_khau),
                role=role,
                is_active=True
            )
            if current_admin:
                NhatKyHoatDong.objects.create(
                    nguoi_dung=current_admin,
                    hanh_dong="Tạo tài khoản người dùng",
                    chi_tiet=f"Tạo tài khoản {ten_dang_nhap} với vai trò {role}"
                )
            messages.success(request, f"Đã thêm người dùng {ten_dang_nhap} thành công!")
            return redirect('quan_ly_tai_khoan')

    users = NguoiDung.objects.all().order_by('-id')
    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'users': users
    }
    return render(request, 'warehouse/quan_ly_tai_khoan.html', context)


@role_required(['ADMIN'])
def doi_quyen_user_view(request, user_id):
    current_admin = get_current_user_obj(request)
    target_user = get_object_or_404(NguoiDung, id=user_id)

    # Chặn không cho phép đổi quyền của chính tài khoản Admin gốc
    if target_user.role == 'ADMIN' or target_user.ten_dang_nhap.lower() == 'admin':
        messages.error(request, "Không thể thay đổi quyền của tài khoản Quản trị viên tối cao!")
        return redirect('quan_ly_tai_khoan')

    new_role = request.POST.get('role') or request.GET.get('role')

    # Chỉ cho phép chuyển đổi giữa Thủ kho và Kế toán kho
    if new_role not in ['THUKHO', 'KETOANKHO']:
        messages.error(request, "Chỉ được phép phân quyền là Thủ kho hoặc Kế toán kho!")
        return redirect('quan_ly_tai_khoan')

    old_role = target_user.role
    target_user.role = new_role
    target_user.save()

    if current_admin:
        NhatKyHoatDong.objects.create(
            nguoi_dung=current_admin,
            hanh_dong="Đổi quyền tài khoản",
            chi_tiet=f"Đổi quyền tài khoản {target_user.ten_dang_nhap} từ {old_role} sang {new_role}"
        )
    messages.success(request, f"Đã cập nhật quyền tài khoản {target_user.ten_dang_nhap} thành công!")
    return redirect('quan_ly_tai_khoan')


@role_required(['ADMIN'])
def doi_trang_thai_user_view(request, user_id):
    current_admin = get_current_user_obj(request)
    target_user = get_object_or_404(NguoiDung, id=user_id)

    if current_admin and target_user.id == current_admin.id:
        messages.error(request, "Không thể tự khóa tài khoản của chính mình đang đăng nhập!")
        return redirect('quan_ly_tai_khoan')

    target_user.is_active = not target_user.is_active
    target_user.save()

    status_text = "mở khóa" if target_user.is_active else "khóa"
    if current_admin:
        NhatKyHoatDong.objects.create(
            nguoi_dung=current_admin,
            hanh_dong="Thay đổi trạng thái tài khoản",
            chi_tiet=f"Đã {status_text} tài khoản: {target_user.ten_dang_nhap}"
        )
    messages.success(request, f"Đã {status_text} tài khoản {target_user.ten_dang_nhap} thành công!")
    return redirect('quan_ly_tai_khoan')


@role_required(['ADMIN'])
def nhat_ky_hoat_dong_view(request):
    logs_list = NhatKyHoatDong.objects.select_related('nguoi_dung').all().order_by('-thoi_gian')
    paginator = Paginator(logs_list, 15)
    page_number = request.GET.get('page')
    logs = paginator.get_page(page_number)

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'logs': logs
    }
    return render(request, 'warehouse/nhat_ky_hoat_dong.html', context)


# --- ĐƠN VỊ TÍNH (Danh sách, Thêm/Sửa, Xóa) ---
@login_required_custom
def don_vi_tinh_list_view(request):
    danh_sach = DonViTinh.objects.all().order_by('-id')
    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'danh_sach': danh_sach,
    }
    return render(request, 'warehouse/don_vi_tinh_list.html', context)


@login_required_custom
@role_required(['THUKHO', 'ADMIN'])
def don_vi_tinh_form_view(request, pk=None):
    is_edit = pk is not None
    don_vi_tinh = get_object_or_404(DonViTinh, pk=pk) if is_edit else None

    if request.method == 'POST':
        ten_don_vi = request.POST.get('ten_don_vi', '').strip()
        mo_ta = request.POST.get('mo_ta', '').strip()

        if not ten_don_vi:
            messages.error(request, "Vui lòng nhập tên đơn vị tính!")
            return redirect('don_vi_tinh_edit', pk=pk) if is_edit else redirect('don_vi_tinh_add')

        check_exist = DonViTinh.objects.filter(ten_don_vi=ten_don_vi)
        if is_edit:
            check_exist = check_exist.exclude(pk=pk)

        if check_exist.exists():
            messages.error(request, f"Đơn vị tính '{ten_don_vi}' đã tồn tại!")
            return redirect('don_vi_tinh_edit', pk=pk) if is_edit else redirect('don_vi_tinh_add')

        if is_edit:
            don_vi_tinh.ten_don_vi = ten_don_vi
            don_vi_tinh.mo_ta = mo_ta
            don_vi_tinh.save()
            messages.success(request, "Cập nhật đơn vị tính thành công!")
        else:
            DonViTinh.objects.create(ten_don_vi=ten_don_vi, mo_ta=mo_ta)
            messages.success(request, "Thêm đơn vị tính mới thành công!")

        return redirect('don_vi_tinh_list')

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'is_edit': is_edit,
        'don_vi_tinh': don_vi_tinh,
    }
    return render(request, 'warehouse/don_vi_tinh_form.html', context)


@login_required_custom
@role_required(['THUKHO', 'ADMIN'])
def don_vi_tinh_delete_view(request, pk):
    don_vi_tinh = get_object_or_404(DonViTinh, pk=pk)
    don_vi_tinh.delete()
    messages.success(request, "Đã xóa đơn vị tính thành công!")
    return redirect('don_vi_tinh_list')


# --- NHÓM HÀNG (Thêm & Sửa dùng chung form_view) ---
@login_required_custom
@role_required(['THUKHO', 'ADMIN'])
def nhom_hang_form_view(request, pk=None):
    # Kiểm tra xem có phải đang ở chế độ chỉnh sửa (có pk) hay thêm mới (không có pk)
    if pk:
        nhom_hang = get_object_or_404(NhomHang, pk=pk)
        is_edit = True
    else:
        nhom_hang = None
        is_edit = False

    if request.method == 'POST':
        ten_nhom = request.POST.get('ten_nhom')
        mo_ta = request.POST.get('mo_ta')
        
        if is_edit:
            # Cập nhật thông tin nhóm hàng cũ
            nhom_hang.ten_nhom = ten_nhom
            nhom_hang.mo_ta = mo_ta
            nhom_hang.save()
            messages.success(request, "Cập nhật nhóm hàng thành công!")
        else:
            # Tạo mới nhóm hàng
            NhomHang.objects.create(ten_nhom=ten_nhom, mo_ta=mo_ta)
            messages.success(request, "Thêm nhóm hàng mới thành công!")
            
        return redirect('nhom_hang_list')

    context = {
        'nhom_hang': nhom_hang,
        'is_edit': is_edit,  # Biến này giúp template nhận diện là form Sửa hay Thêm
        'username': request.session.get('username'),
        'role': request.session.get('role')
    }
    return render(request, 'warehouse/nhom_hang_form.html', context)

@login_required_custom
@role_required(['THUKHO', 'ADMIN'])
def nhom_hang_delete_view(request, pk):
    item = get_object_or_404(NhomHang, pk=pk)
    item.delete()
    messages.success(request, "Đã xóa nhóm hàng thành công!")
    return redirect('nhom_hang_list')


# --- NHÀ CUNG CẤP (Thêm & Sửa dùng chung form_view) ---
@login_required_custom
@role_required(['THUKHO', 'ADMIN'])
def nha_cung_cap_form_view(request, pk=None):
    instance = get_object_or_404(NhaCungCap, pk=pk) if pk else None
    if request.method == 'POST':
        form = NhaCungCapForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Lưu nhà cung cấp thành công!")
            return redirect('nha_cung_cap_list')
    else:
        form = NhaCungCapForm(instance=instance)
        
    context = {
        'form': form,
        'username': request.session.get('username'),
        'role': request.session.get('role')
    }
    return render(request, 'warehouse/nha_cung_cap_form.html', context)

@login_required_custom
@role_required(['THUKHO', 'ADMIN'])
def nha_cung_cap_delete_view(request, pk):
    item = get_object_or_404(NhaCungCap, pk=pk)
    item.delete()
    messages.success(request, "Đã xóa nhà cung cấp thành công!")
    return redirect('nha_cung_cap_list')

  # Hoặc model User của bạn

def doi_quyen_user(request, user_id):
    if request.method == 'POST':
        user_obj = get_object_or_404(TaiKhoan, id=user_id)
        new_role = request.POST.get('role')
        if new_role in ['THUKHO', 'KETOANKHO']:
            user_obj.role = new_role
            user_obj.save()
            messages.success(request, f"Đã cập nhật quyền cho tài khoản {user_obj.ten_dang_nhap}.")
    return redirect('quan_ly_tai_khoan')

def doi_trang_thai_user(request, user_id):
    if request.method == 'POST':
        user_obj = get_object_or_404(TaiKhoan, id=user_id)
        if user_obj.role != 'ADMIN': # Chặn không cho khóa tài khoản Admin gốc
            user_obj.is_active = not user_obj.is_active
            user_obj.save()
            status_text = "mở khóa" if user_obj.is_active else "khóa"
            messages.success(request, f"Đã {status_text} tài khoản {user_obj.ten_dang_nhap}.")
    return redirect('quan_ly_tai_khoan')