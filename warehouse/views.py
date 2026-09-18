import csv
import time
from decimal import Decimal, InvalidOperation
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
from django.db import IntegrityError

from .models import (
    DonViTinh,
    NhomHang,
    HangHoa,
    NhaCungCap,
    NguoiDung,
    PhieuKho,
    ChiTietPhieuKho,
    NhatKyHoatDong,
    CauHinhHeThong,
)

from .forms import NhaCungCapForm


# =========================================================
# 1. DECORATORS - PHÂN QUYỀN & KIỂM TRA ĐĂNG NHẬP
# =========================================================

def is_admin(user_or_request):
    """
    Kiểm tra tài khoản có phải ADMIN hay không.
    Hỗ trợ cả request Django và user object.
    """

    # Trường hợp truyền request
    if hasattr(user_or_request, 'session'):

        request = user_or_request

        # Nếu dùng Django authentication
        if hasattr(request, 'user') and request.user.is_authenticated:
            if (
                getattr(request.user, 'is_superuser', False)
                or getattr(request.user, 'is_staff', False)
            ):
                return True

        # Kiểm tra session của hệ thống
        role = str(
            request.session.get('role', '')
        ).upper()

        username = str(
            request.session.get('username', '')
        ).lower()

        return (
            role == 'ADMIN'
            or username == 'admin'
        )

    # Trường hợp truyền user object
    user = user_or_request

    return bool(
        user
        and getattr(user, 'is_authenticated', False)
        and (
            getattr(user, 'is_superuser', False)
            or getattr(user, 'is_staff', False)
        )
    )


def is_staff_member(user_or_request):
    """
    Kiểm tra người dùng đã đăng nhập hay chưa.
    """

    # Trường hợp request
    if hasattr(user_or_request, 'session'):

        request = user_or_request

        # Django authentication
        if (
            hasattr(request, 'user')
            and request.user.is_authenticated
        ):
            return True

        # Hệ thống đăng nhập bằng session
        return bool(
            request.session.get('user_id')
        )

    # Trường hợp user object
    user = user_or_request

    return bool(
        user
        and getattr(
            user,
            'is_authenticated',
            False
        )
    )


def login_required_custom(view_func):
    """
    Yêu cầu người dùng phải đăng nhập.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not is_staff_member(request):
            return redirect('login')

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


def role_required(allowed_roles=None):
    """
    Kiểm tra quyền truy cập.

    ADMIN được phép truy cập tất cả chức năng.
    Các tài khoản khác phải thuộc allowed_roles.
    """

    if allowed_roles is None:
        allowed_roles = []

    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    # Chuẩn hóa role
    allowed_roles = [
        str(role).upper()
        for role in allowed_roles
    ]

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not is_staff_member(request):
                return redirect('login')

            # ADMIN được toàn quyền
            if is_admin(request):
                return view_func(
                    request,
                    *args,
                    **kwargs
                )

            user_role = str(
                request.session.get(
                    'role',
                    ''
                )
            ).upper()

            if user_role in allowed_roles:
                return view_func(
                    request,
                    *args,
                    **kwargs
                )

            messages.error(
                request,
                "Bạn không có quyền truy cập chức năng này!"
            )

            return redirect('dashboard')

        return wrapper

    return decorator


def admin_only(view_func):
    """
    Chỉ ADMIN được truy cập.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not is_staff_member(request):
            return redirect('login')

        if not is_admin(request):
            raise PermissionDenied(
                "Bạn không có quyền quản trị viên (Admin)."
            )

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


def get_current_user_obj(request):
    """
    Lấy đối tượng NguoiDung hiện tại.
    """

    user_id = request.session.get(
        'user_id'
    )

    if user_id:
        user = (
            NguoiDung.objects
            .filter(id=user_id)
            .first()
        )

        if user:
            return user

    # Trường hợp có Django authentication
    if (
        hasattr(request, 'user')
        and request.user.is_authenticated
    ):

        username = getattr(
            request.user,
            'username',
            None
        )

        if username:

            user = (
                NguoiDung.objects
                .filter(
                    ten_dang_nhap=username
                )
                .first()
            )

            if user:
                return user

    # Fallback ADMIN
    return (
        NguoiDung.objects
        .filter(role='ADMIN')
        .first()
    )


# =========================================================
# 2. ĐĂNG NHẬP
# =========================================================

def login_view(request):

    if request.method == 'POST':

        username_input = request.POST.get(
            'ten_dang_nhap',
            ''
        ).strip()

        password_input = request.POST.get(
            'password',
            ''
        ).strip()

        if not username_input:
            messages.error(
                request,
                "Vui lòng nhập tên đăng nhập!"
            )

            return render(
                request,
                'warehouse/login.html'
            )

        if not password_input:
            messages.error(
                request,
                "Vui lòng nhập mật khẩu!"
            )

            return render(
                request,
                'warehouse/login.html'
            )

        try:

            user = NguoiDung.objects.get(
                ten_dang_nhap=username_input,
                is_active=True
            )

            password_correct = False

            # Mật khẩu đã hash
            try:
                password_correct = check_password(
                    password_input,
                    user.password_hash
                )
            except Exception:
                password_correct = False

            # Hỗ trợ dữ liệu mật khẩu cũ dạng text
            if (
                not password_correct
                and user.password_hash == password_input
            ):
                password_correct = True

            if password_correct:

                request.session['user_id'] = user.id
                request.session['username'] = (
                    user.ten_dang_nhap
                )
                request.session['role'] = (
                    user.role
                )

                request.session.modified = True

                return redirect(
                    'dashboard'
                )

            messages.error(
                request,
                "Mật khẩu không chính xác!"
            )

        except NguoiDung.DoesNotExist:

            messages.error(
                request,
                "Tên đăng nhập không tồn tại hoặc đã bị khóa!"
            )

    return render(
        request,
        'warehouse/login.html'
    )


# =========================================================
# 3. ĐĂNG XUẤT
# =========================================================

def logout_view(request):

    request.session.flush()

    return redirect('login')


# =========================================================
# 4. DASHBOARD
# =========================================================

@login_required_custom
def dashboard_view(request):

    tong_san_pham = (
        HangHoa.objects.count()
    )

    hang_sap_het = (
        HangHoa.objects
        .filter(
            so_luong_ton__lt=F(
                'ton_toi_thieu'
            )
        )
        .count()
    )

    tong_tai_khoan = (
        NguoiDung.objects.count()
    )

    tong_gia_tri = (
        HangHoa.objects
        .aggregate(
            total=Sum(
                ExpressionWrapper(
                    F('so_luong_ton')
                    * F('gia_xuat'),
                    output_field=DecimalField()
                )
            )
        )
        .get('total')
        or 0
    )

    top_5_hang = (
        HangHoa.objects
        .order_by('-so_luong_ton')[:5]
    )

    chart_labels = [
        item.ten_hang
        for item in top_5_hang
    ]

    chart_data = [
        item.so_luong_ton
        for item in top_5_hang
    ]

    min_stock_data = [
        item.ton_toi_thieu
        for item in top_5_hang
    ]

    ds_can_nhap = (
        HangHoa.objects
        .filter(
            so_luong_ton__lt=F(
                'ton_toi_thieu'
            )
        )
    )

    context = {
        'username': request.session.get(
            'username'
        ),
        'role': request.session.get(
            'role'
        ),
        'tong_san_pham': tong_san_pham,
        'hang_sap_het': hang_sap_het,
        'tong_tai_khoan': tong_tai_khoan,
        'tong_gia_tri': tong_gia_tri,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'min_stock_data': min_stock_data,
        'ds_can_nhap': ds_can_nhap,
    }

    return render(
        request,
        'warehouse/dashboard.html',
        context
    )


# =========================================================
# 5. DANH SÁCH SẢN PHẨM
# =========================================================

@login_required_custom
def san_pham_list_view(request):

    query = request.GET.get(
        'q',
        ''
    ).strip()

    filter_status = request.GET.get(
        'status',
        'all'
    )

    danh_sach = (
        HangHoa.objects
        .all()
        .order_by('-id')
    )

    if query:

        danh_sach = danh_sach.filter(
            Q(
                ten_hang__icontains=query
            )
            |
            Q(
                ma_hang__icontains=query
            )
        )

    if filter_status == 'low_stock':

        danh_sach = danh_sach.filter(
            so_luong_ton__lt=F(
                'ton_toi_thieu'
            )
        )

    paginator = Paginator(
        danh_sach,
        8
    )

    page_number = request.GET.get(
        'page'
    )

    page_obj = paginator.get_page(
        page_number
    )

    context = {
        'username': request.session.get(
            'username'
        ),
        'role': request.session.get(
            'role'
        ),
        'danh_sach': page_obj,
        'query': query,
        'filter_status': filter_status,
    }

    return render(
        request,
        'warehouse/san_pham_list.html',
        context
    )


# =========================================================
# 6. THÊM / SỬA SẢN PHẨM
# =========================================================

@login_required_custom
@role_required(['THUKHO'])
def san_pham_form_view(
    request,
    pk=None
):

    is_edit = pk is not None

    san_pham = (
        get_object_or_404(
            HangHoa,
            pk=pk
        )
        if is_edit
        else None
    )

    danh_sach_nhom = (
        NhomHang.objects
        .all()
        .order_by('ten_nhom')
    )

    if request.method == 'POST':

        ma_hang = request.POST.get(
            'ma_hang',
            ''
        ).strip()

        ten_hang = request.POST.get(
            'ten_hang',
            ''
        ).strip()

        nhom_hang_id = (
            request.POST.get(
                'nhom_hang_id'
            )
            or request.POST.get(
                'nhom_hang'
            )
        )

        try:
            so_luong_ton = int(
                request.POST.get(
                    'so_luong_ton',
                    0
                )
            )

            ton_toi_thieu = int(
                request.POST.get(
                    'ton_toi_thieu',
                    5
                )
            )

            gia_nhap = Decimal(
                request.POST.get(
                    'gia_nhap',
                    0
                )
            )

            gia_xuat = Decimal(
                request.POST.get(
                    'gia_xuat',
                    0
                )
            )

        except (
            ValueError,
            TypeError,
            InvalidOperation
        ):

            messages.error(
                request,
                "Dữ liệu số lượng hoặc giá không hợp lệ!"
            )

            return redirect(
                'san_pham_edit',
                pk=pk
            ) if is_edit else redirect(
                'san_pham_add'
            )

        if not ma_hang or not ten_hang:

            messages.error(
                request,
                "Vui lòng nhập đầy đủ mã và tên hàng!"
            )

            return redirect(
                'san_pham_edit',
                pk=pk
            ) if is_edit else redirect(
                'san_pham_add'
            )

        if so_luong_ton < 0:

            messages.error(
                request,
                "Số lượng tồn không được âm!"
            )

            return redirect(
                'san_pham_edit',
                pk=pk
            ) if is_edit else redirect(
                'san_pham_add'
            )

        if ton_toi_thieu < 0:

            messages.error(
                request,
                "Tồn tối thiểu không được âm!"
            )

            return redirect(
                'san_pham_edit',
                pk=pk
            ) if is_edit else redirect(
                'san_pham_add'
            )

        if gia_nhap < 0 or gia_xuat < 0:

            messages.error(
                request,
                "Giá nhập và giá xuất không được âm!"
            )

            return redirect(
                'san_pham_edit',
                pk=pk
            ) if is_edit else redirect(
                'san_pham_add'
            )

        # Kiểm tra mã hàng trùng
        check_exist = (
            HangHoa.objects
            .filter(
                ma_hang=ma_hang
            )
        )

        if is_edit:
            check_exist = check_exist.exclude(
                pk=pk
            )

        if check_exist.exists():

            messages.error(
                request,
                f"Mã hàng '{ma_hang}' đã tồn tại!"
            )

            return redirect(
                'san_pham_edit',
                pk=pk
            ) if is_edit else redirect(
                'san_pham_add'
            )

        nhom_hang = None

        if nhom_hang_id:

            try:

                nhom_hang = (
                    NhomHang.objects
                    .filter(
                        id=int(
                            nhom_hang_id
                        )
                    )
                    .first()
                )

            except (
                ValueError,
                TypeError
            ):

                nhom_hang = None

        if is_edit:

            san_pham.ma_hang = ma_hang
            san_pham.ten_hang = ten_hang
            san_pham.nhom_hang = nhom_hang
            san_pham.so_luong_ton = so_luong_ton
            san_pham.ton_toi_thieu = ton_toi_thieu
            san_pham.gia_nhap = gia_nhap
            san_pham.gia_xuat = gia_xuat

            san_pham.save()

            messages.success(
                request,
                "Cập nhật sản phẩm thành công!"
            )

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

            messages.success(
                request,
                "Thêm sản phẩm thành công!"
            )

        return redirect(
            'san_pham_list'
        )

    context = {
        'username': request.session.get(
            'username'
        ),
        'role': request.session.get(
            'role'
        ),
        'is_edit': is_edit,
        'san_pham': san_pham,
        'danh_sach_nhom': danh_sach_nhom,
    }

    return render(
        request,
        'warehouse/san_pham_form.html',
        context
    )


# =========================================================
# 7. XÓA SẢN PHẨM
# =========================================================

@login_required_custom
@role_required(['THUKHO'])
@transaction.atomic
def san_pham_delete_view(request, pk):

    # -----------------------------------------------------
    # KIỂM TRA REQUEST
    # -----------------------------------------------------

    print("========== DELETE ==========")
    print("METHOD =", request.method)
    print("PK =", pk)

    # Chỉ cho phép xóa bằng POST
    if request.method != 'POST':
        messages.error(
            request,
            f"Thao tác không hợp lệ! METHOD = {request.method}"
        )
        return redirect('san_pham_list')

    # -----------------------------------------------------
    # LẤY SẢN PHẨM
    # -----------------------------------------------------

    san_pham = get_object_or_404(
        HangHoa,
        pk=pk
    )

    # -----------------------------------------------------
    # 1. KIỂM TRA ĐÃ CÓ GIAO DỊCH NHẬP / XUẤT CHƯA
    # -----------------------------------------------------

    da_phat_sinh_giao_dich = (
        ChiTietPhieuKho.objects
        .filter(
            hang_hoa=san_pham
        )
        .exists()
    )

    if da_phat_sinh_giao_dich:
        messages.error(
            request,
            (
                f'Không thể xóa sản phẩm "{san_pham.ten_hang}" '
                f'vì sản phẩm đã phát sinh giao dịch nhập/xuất kho.'
            )
        )

        return redirect('san_pham_list')

    # -----------------------------------------------------
    # 2. KIỂM TRA CÒN TỒN KHO
    # -----------------------------------------------------

    if san_pham.so_luong_ton > 0:
        messages.error(
            request,
            (
                f'Không thể xóa sản phẩm "{san_pham.ten_hang}" '
                f'vì sản phẩm đang còn tồn kho '
                f'({san_pham.so_luong_ton}).'
            )
        )

        return redirect('san_pham_list')

    # -----------------------------------------------------
    # 3. XÓA SẢN PHẨM
    # -----------------------------------------------------

    ten_san_pham = san_pham.ten_hang

    try:

        san_pham.delete()

        messages.success(
            request,
            f'Đã xóa sản phẩm "{ten_san_pham}" thành công!'
        )

    except Exception as e:

        messages.error(
            request,
            (
                f'Lỗi khi xóa sản phẩm "{ten_san_pham}": '
                f'{str(e)}'
            )
        )

    return redirect('san_pham_list')

# =========================================================
# 8. CẬP NHẬT KHO NHANH
# =========================================================

@login_required_custom
@role_required(['THUKHO'])
@transaction.atomic
def cap_nhat_kho_view(
    request,
    pk
):

    if request.method != 'POST':

        return redirect(
            'san_pham_list'
        )

    san_pham = get_object_or_404(
        HangHoa,
        pk=pk
    )

    loai_thao_tac = request.POST.get(
        'loai_thao_tac'
    )

    try:

        so_luong = int(
            request.POST.get(
                'so_luong',
                0
            )
        )

    except (
        ValueError,
        TypeError
    ):

        so_luong = 0

    if so_luong <= 0:

        messages.error(
            request,
            "Số lượng nhập/xuất phải lớn hơn 0!"
        )

        return redirect(
            'san_pham_list'
        )

    user_id = request.session.get(
        'user_id'
    )

    nguoi_dung = (
        NguoiDung.objects
        .filter(id=user_id)
        .first()
        if user_id
        else None
    )

    ma_phieu_tu_dong = (
        f"P"
        f"{'N' if loai_thao_tac == 'nhap' else 'X'}"
        f"-{int(time.time())}"
    )

    if loai_thao_tac == 'nhap':

        phieu = PhieuKho.objects.create(
            ma_phieu=ma_phieu_tu_dong,
            loai_phieu='NHAP',
            nguoi_lap=nguoi_dung,
            ghi_chu=(
                "Nhập kho nhanh từ giao diện "
                "danh sách"
            )
        )

        ChiTietPhieuKho.objects.create(
            phieu_kho=phieu,
            hang_hoa=san_pham,
            so_luong=so_luong,
            don_gia=san_pham.gia_nhap
        )

        san_pham.so_luong_ton += so_luong

        san_pham.save(
            update_fields=[
                'so_luong_ton'
            ]
        )

        messages.success(
            request,
            (
                f"Đã lập phiếu nhập "
                f"{ma_phieu_tu_dong} thành công "
                f"(+{so_luong} {san_pham.ten_hang})."
            )
        )

    elif loai_thao_tac == 'xuat':

        if so_luong > san_pham.so_luong_ton:

            messages.error(
                request,
                (
                    f"Số lượng xuất ({so_luong}) "
                    f"lớn hơn tồn kho hiện tại "
                    f"({san_pham.so_luong_ton})!"
                )
            )

            return redirect(
                'san_pham_list'
            )

        phieu = PhieuKho.objects.create(
            ma_phieu=ma_phieu_tu_dong,
            loai_phieu='XUAT',
            nguoi_lap=nguoi_dung,
            ghi_chu=(
                "Xuất kho nhanh từ giao diện "
                "danh sách"
            )
        )

        ChiTietPhieuKho.objects.create(
            phieu_kho=phieu,
            hang_hoa=san_pham,
            so_luong=so_luong,
            don_gia=san_pham.gia_xuat
        )

        san_pham.so_luong_ton -= so_luong

        san_pham.save(
            update_fields=[
                'so_luong_ton'
            ]
        )

        messages.success(
            request,
            (
                f"Đã lập phiếu xuất "
                f"{ma_phieu_tu_dong} thành công "
                f"(-{so_luong} {san_pham.ten_hang})."
            )
        )

    else:

        messages.error(
            request,
            "Loại thao tác không hợp lệ!"
        )

    return redirect(
        'san_pham_list'
    )


# =========================================================
# 9. QUẢN LÝ PHIẾU NHẬP
# =========================================================

@login_required_custom
def phieu_nhap_list_view(request):

    danh_sach_phieu = (
        PhieuKho.objects
        .filter(
            loai_phieu='NHAP'
        )
        .select_related(
            'nha_cung_cap',
            'nguoi_lap'
        )
        .order_by(
            '-ngay_lap'
        )
    )

    context = {
        'username': request.session.get(
            'username'
        ),
        'role': request.session.get(
            'role'
        ),
        'danh_sach_phieu': danh_sach_phieu,
    }

    return render(
        request,
        'warehouse/phieu_nhap_list.html',
        context
    )


# =========================================================
# 10. TẠO PHIẾU NHẬP KHO
# =========================================================

@login_required_custom
@role_required(['THUKHO'])
@transaction.atomic
def phieu_nhap_create_view(request):

    if request.method == 'POST':

        ma_phieu = request.POST.get(
            'ma_phieu',
            ''
        ).strip()

        ncc_id = request.POST.get(
            'nha_cung_cap',
            ''
        ).strip()

        ghi_chu = request.POST.get(
            'ghi_chu',
            ''
        ).strip()

        hang_hoa_ids = request.POST.getlist(
            'hang_hoa_id[]'
        )

        so_luongs = request.POST.getlist(
            'so_luong[]'
        )

        don_gias = request.POST.getlist(
            'don_gia[]'
        )

        ngay_san_xuats = request.POST.getlist(
            'ngay_san_xuat[]'
        )

        han_su_dungs = request.POST.getlist(
            'han_su_dung[]'
        )

        # -------------------------------------------------
        # Kiểm tra mã phiếu
        # -------------------------------------------------

        if not ma_phieu:

            messages.error(
                request,
                "Vui lòng nhập mã phiếu nhập!"
            )

            return redirect(
                'phieu_nhap_create'
            )

        if (
            PhieuKho.objects
            .filter(
                ma_phieu=ma_phieu
            )
            .exists()
        ):

            messages.error(
                request,
                (
                    f"Mã phiếu '{ma_phieu}' "
                    f"đã tồn tại! Vui lòng chọn mã khác."
                )
            )

            return redirect(
                'phieu_nhap_create'
            )

        # -------------------------------------------------
        # Nhà cung cấp
        # -------------------------------------------------

        nha_cung_cap_obj = None

        if ncc_id:

            try:

                nha_cung_cap_obj = (
                    NhaCungCap.objects
                    .get(
                        pk=int(ncc_id)
                    )
                )

            except (
                NhaCungCap.DoesNotExist,
                ValueError,
                TypeError
            ):

                messages.error(
                    request,
                    "Nhà cung cấp không hợp lệ!"
                )

                return redirect(
                    'phieu_nhap_create'
                )

        # -------------------------------------------------
        # Kiểm tra sản phẩm
        # -------------------------------------------------

        if not hang_hoa_ids:

            messages.error(
                request,
                "Vui lòng chọn ít nhất một sản phẩm cần nhập kho!"
            )

            return redirect(
                'phieu_nhap_create'
            )

        items_to_process = []

        # -------------------------------------------------
        # Xử lý từng sản phẩm
        # -------------------------------------------------

        for index, h_id in enumerate(
            hang_hoa_ids
        ):

            if not h_id:
                continue

            sl = (
                so_luongs[index]
                if index < len(so_luongs)
                else ''
            )

            try:

                sl_int = int(sl)

            except (
                ValueError,
                TypeError
            ):

                messages.error(
                    request,
                    (
                        f"Số lượng ở dòng "
                        f"{index + 1} không hợp lệ!"
                    )
                )

                return redirect(
                    'phieu_nhap_create'
                )

            if sl_int <= 0:

                messages.error(
                    request,
                    (
                        f"Số lượng ở dòng "
                        f"{index + 1} phải lớn hơn 0!"
                    )
                )

                return redirect(
                    'phieu_nhap_create'
                )

            try:

                hang_hoa = (
                    HangHoa.objects
                    .get(
                        pk=int(h_id)
                    )
                )

            except (
                HangHoa.DoesNotExist,
                ValueError,
                TypeError
            ):

                messages.error(
                    request,
                    (
                        f"Sản phẩm ở dòng "
                        f"{index + 1} không tồn tại!"
                    )
                )

                return redirect(
                    'phieu_nhap_create'
                )

            # -------------------------------------------------
            # Đơn giá
            # -------------------------------------------------

            dg = (
                don_gias[index]
                if index < len(don_gias)
                else ''
            )

            try:

                if dg and dg.strip():

                    dg_val = Decimal(dg)

                else:

                    dg_val = Decimal(
                        str(
                            hang_hoa.gia_nhap or 0
                        )
                    )

            except (
                InvalidOperation,
                ValueError,
                TypeError
            ):

                messages.error(
                    request,
                    (
                        f"Đơn giá của sản phẩm "
                        f"'{hang_hoa.ten_hang}' không hợp lệ!"
                    )
                )

                return redirect(
                    'phieu_nhap_create'
                )

            if dg_val < 0:

                messages.error(
                    request,
                    (
                        f"Đơn giá của sản phẩm "
                        f"'{hang_hoa.ten_hang}' "
                        f"không được âm!"
                    )
                )

                return redirect(
                    'phieu_nhap_create'
                )

            # -------------------------------------------------
            # Ngày sản xuất
            # -------------------------------------------------

            nsx_val = (
                ngay_san_xuats[index]
                if index < len(ngay_san_xuats)
                else ''
            )

            if nsx_val:
                nsx_val = nsx_val.strip()

            if not nsx_val:
                nsx_val = None

            # -------------------------------------------------
            # Hạn sử dụng
            # -------------------------------------------------

            hsd_val = (
                han_su_dungs[index]
                if index < len(han_su_dungs)
                else ''
            )

            if hsd_val:
                hsd_val = hsd_val.strip()

            if not hsd_val:
                hsd_val = None

            items_to_process.append(
                {
                    'hang_hoa': hang_hoa,
                    'so_luong': sl_int,
                    'don_gia': dg_val,
                    'ngay_san_xuat': nsx_val,
                    'han_su_dung': hsd_val,
                }
            )

        if not items_to_process:

            messages.error(
                request,
                "Vui lòng chọn ít nhất một sản phẩm cần nhập kho!"
            )

            return redirect(
                'phieu_nhap_create'
            )

        # -------------------------------------------------
        # Người lập phiếu
        # -------------------------------------------------

        user_id = request.session.get(
            'user_id'
        )

        nguoi_dung = (
            NguoiDung.objects
            .filter(id=user_id)
            .first()
            if user_id
            else None
        )

        # -------------------------------------------------
        # Tạo phiếu
        # -------------------------------------------------

        phieu = PhieuKho.objects.create(
            ma_phieu=ma_phieu,
            loai_phieu='NHAP',
            nha_cung_cap=nha_cung_cap_obj,
            nguoi_lap=nguoi_dung,
            ghi_chu=ghi_chu
        )

        # -------------------------------------------------
        # Chi tiết + cập nhật tồn kho
        # -------------------------------------------------

        for item in items_to_process:

            hang_hoa = item['hang_hoa']
            so_luong = item['so_luong']
            don_gia = item['don_gia']
            ngay_san_xuat = item[
                'ngay_san_xuat'
            ]
            han_su_dung = item[
                'han_su_dung'
            ]

            ChiTietPhieuKho.objects.create(
                phieu_kho=phieu,
                hang_hoa=hang_hoa,
                so_luong=so_luong,
                don_gia=don_gia,
                ngay_san_xuat=ngay_san_xuat,
                han_su_dung=han_su_dung
            )

            hang_hoa.so_luong_ton += (
                so_luong
            )

            hang_hoa.save(
                update_fields=[
                    'so_luong_ton'
                ]
            )

        messages.success(
            request,
            (
                f"Lập phiếu nhập '{ma_phieu}' "
                f"thành công! Đã nhập "
                f"{len(items_to_process)} sản phẩm vào kho."
            )
        )

        return redirect(
            'phieu_nhap_list'
        )

    # -----------------------------------------------------
    # Hiển thị form
    # -----------------------------------------------------

    danh_sach_hang = (
        HangHoa.objects
        .all()
        .order_by('ten_hang')
    )

    danh_sach_ncc = (
        NhaCungCap.objects
        .all()
        .order_by('ten_ncc')
    )

    ma_phieu_tu_dong = (
        f"PN-{int(time.time())}"
    )

    context = {
        'username': request.session.get(
            'username'
        ),
        'role': request.session.get(
            'role'
        ),
        'danh_sach_hang': danh_sach_hang,
        'danh_sach_ncc': danh_sach_ncc,
        'ma_phieu_tu_dong': ma_phieu_tu_dong,
    }

    return render(
        request,
        'warehouse/phieu_nhap_form.html',
        context
    )


# =========================================================
# 11. QUẢN LÝ PHIẾU XUẤT
# =========================================================

@login_required_custom
def phieu_xuat_list_view(request):

    danh_sach_phieu = (
        PhieuKho.objects
        .filter(
            loai_phieu='XUAT'
        )
        .select_related(
            'nguoi_lap'
        )
        .order_by(
            '-ngay_lap'
        )
    )

    context = {
        'username': request.session.get(
            'username'
        ),
        'role': request.session.get(
            'role'
        ),
        'danh_sach_phieu': danh_sach_phieu,
    }

    return render(
        request,
        'warehouse/phieu_xuat_list.html',
        context
    )


# =========================================================
# 12. TẠO PHIẾU XUẤT
# =========================================================

@login_required_custom
@role_required(['THUKHO'])
@transaction.atomic
def phieu_xuat_create_view(request):

    if request.method == 'POST':

        ma_phieu = request.POST.get(
            'ma_phieu',
            ''
        ).strip()

        nguoi_nhan = request.POST.get(
            'nguoi_nhan',
            ''
        ).strip()

        ghi_chu = request.POST.get(
            'ghi_chu',
            ''
        ).strip()

        hang_hoa_ids = request.POST.getlist(
            'hang_hoa_id[]'
        )

        so_luongs = request.POST.getlist(
            'so_luong[]'
        )

        don_gias = request.POST.getlist(
            'don_gia[]'
        )

        if not ma_phieu:

            messages.error(
                request,
                "Vui lòng nhập mã phiếu xuất!"
            )

            return redirect(
                'phieu_xuat_create'
            )

        if (
            PhieuKho.objects
            .filter(
                ma_phieu=ma_phieu
            )
            .exists()
        ):

            messages.error(
                request,
                (
                    f"Mã phiếu '{ma_phieu}' "
                    f"đã tồn tại! Vui lòng chọn mã khác."
                )
            )

            return redirect(
                'phieu_xuat_create'
            )

        items_to_process = []
        tong_xuat_theo_hang = {}

        # -------------------------------------------------
        # Đọc dữ liệu
        # -------------------------------------------------

        for index, h_id in enumerate(
            hang_hoa_ids
        ):

            if not h_id:
                continue

            sl = (
                so_luongs[index]
                if index < len(so_luongs)
                else ''
            )

            dg = (
                don_gias[index]
                if index < len(don_gias)
                else ''
            )

            try:

                sl_int = int(sl)

            except (
                ValueError,
                TypeError
            ):

                messages.error(
                    request,
                    (
                        f"Số lượng xuất "
                        f"ở dòng {index + 1} không hợp lệ!"
                    )
                )

                return redirect(
                    'phieu_xuat_create'
                )

            if sl_int <= 0:

                messages.error(
                    request,
                    (
                        f"Số lượng xuất "
                        f"ở dòng {index + 1} phải lớn hơn 0!"
                    )
                )

                return redirect(
                    'phieu_xuat_create'
                )

            hang_hoa = get_object_or_404(
                HangHoa,
                id=h_id
            )

            # -------------------------------------------------
            # Đơn giá
            # -------------------------------------------------

            try:

                if dg and dg.strip():

                    dg_val = Decimal(
                        dg
                    )

                else:

                    dg_val = Decimal(
                        str(
                            hang_hoa.gia_xuat or 0
                        )
                    )

            except (
                InvalidOperation,
                ValueError,
                TypeError
            ):

                dg_val = Decimal(
                    str(
                        hang_hoa.gia_xuat or 0
                    )
                )

            if dg_val < 0:

                messages.error(
                    request,
                    (
                        f"Đơn giá xuất của "
                        f"'{hang_hoa.ten_hang}' "
                        f"không được âm!"
                    )
                )

                return redirect(
                    'phieu_xuat_create'
                )

            # -------------------------------------------------
            # Gom tổng xuất theo từng sản phẩm
            # -------------------------------------------------

            tong_xuat_theo_hang[
                hang_hoa.id
            ] = (
                tong_xuat_theo_hang.get(
                    hang_hoa.id,
                    0
                )
                + sl_int
            )

            items_to_process.append(
                (
                    hang_hoa,
                    sl_int,
                    dg_val
                )
            )

        if not items_to_process:

            messages.error(
                request,
                "Vui lòng chọn ít nhất một sản phẩm cần xuất kho!"
            )

            return redirect(
                'phieu_xuat_create'
            )

        # -------------------------------------------------
        # KIỂM TRA KHÔNG CHO XUẤT ÂM KHO
        # -------------------------------------------------

        for h_id, tong_sl in (
            tong_xuat_theo_hang.items()
        ):

            hang_hoa = (
                HangHoa.objects
                .get(
                    id=h_id
                )
            )

            if tong_sl > hang_hoa.so_luong_ton:

                messages.error(
                    request,
                    (
                        f"Sản phẩm "
                        f"[{hang_hoa.ma_hang}] "
                        f"{hang_hoa.ten_hang} "
                        f"không đủ tồn kho! "
                        f"(Tồn: "
                        f"{hang_hoa.so_luong_ton}, "
                        f"Xuất yêu cầu: "
                        f"{tong_sl})"
                    )
                )

                return redirect(
                    'phieu_xuat_create'
                )

        # -------------------------------------------------
        # Người lập
        # -------------------------------------------------

        user_id = request.session.get(
            'user_id'
        )

        nguoi_dung = (
            NguoiDung.objects
            .filter(
                id=user_id
            )
            .first()
            if user_id
            else None
        )

        # -------------------------------------------------
        # Người nhận + ghi chú
        # -------------------------------------------------

        if nguoi_nhan:

            ghi_chu_hoan_chinh = (
                f"Người nhận: {nguoi_nhan}. "
                f"{ghi_chu}"
            ).strip()

        else:

            ghi_chu_hoan_chinh = ghi_chu

        # -------------------------------------------------
        # Tạo phiếu xuất
        # -------------------------------------------------

        phieu = PhieuKho.objects.create(
            ma_phieu=ma_phieu,
            loai_phieu='XUAT',
            nha_cung_cap=None,
            nguoi_lap=nguoi_dung,
            ghi_chu=ghi_chu_hoan_chinh
        )

        # -------------------------------------------------
        # Tạo chi tiết + trừ tồn
        # -------------------------------------------------

        for (
            hang_hoa,
            sl_int,
            dg_val
        ) in items_to_process:

            ChiTietPhieuKho.objects.create(
                phieu_kho=phieu,
                hang_hoa=hang_hoa,
                so_luong=sl_int,
                don_gia=dg_val
            )

            hang_hoa.so_luong_ton -= (
                sl_int
            )

            hang_hoa.save(
                update_fields=[
                    'so_luong_ton'
                ]
            )

        messages.success(
            request,
            (
                f"Lập phiếu xuất "
                f"'{ma_phieu}' thành công!"
            )
        )

        return redirect(
            'phieu_xuat_list'
        )

    danh_sach_hang = (
        HangHoa.objects
        .all()
        .order_by('ten_hang')
    )

    ma_phieu_tu_dong = (
        f"PX-{int(time.time())}"
    )

    context = {
        'username': request.session.get(
            'username'
        ),
        'role': request.session.get(
            'role'
        ),
        'danh_sach_hang': danh_sach_hang,
        'ma_phieu_tu_dong': ma_phieu_tu_dong,
    }

    return render(
        request,
        'warehouse/phieu_xuat_form.html',
        context
    )


# =========================================================
# 13. BÁO CÁO NHẬP - XUẤT - TỒN
# =========================================================

@login_required_custom
@role_required([
    'KETOANKHO',
    'THUKHO'
])
def thong_ke_nxt_view(request):

    danh_sach_hang = (
        HangHoa.objects
        .annotate(
            tong_nhap=Coalesce(
                Sum(
                    'chitietphieukho__so_luong',
                    filter=Q(
                        chitietphieukho__phieu_kho__loai_phieu='NHAP'
                    )
                ),
                0
            ),
            tong_xuat=Coalesce(
                Sum(
                    'chitietphieukho__so_luong',
                    filter=Q(
                        chitietphieukho__phieu_kho__loai_phieu='XUAT'
                    )
                ),
                0
            )
        )
        .order_by(
            'ma_hang'
        )
    )

    context = {
        'username': request.session.get(
            'username'
        ),
        'role': request.session.get(
            'role'
        ),
        'danh_sach_hang': danh_sach_hang,
    }

    return render(
        request,
        'warehouse/thong_ke_nxt.html',
        context
    )


# =========================================================
# 14. XUẤT CSV
# =========================================================

@login_required_custom
@role_required([
    'THUKHO',
    'KETOANKHO'
])
def export_csv_view(request):

    response = HttpResponse(
        content_type='text/csv; charset=utf-8-sig'
    )

    response[
        'Content-Disposition'
    ] = (
        'attachment; '
        'filename="danh_sach_hang_hoa.csv"'
    )

    writer = csv.writer(
        response
    )

    writer.writerow([
        'Mã Hàng',
        'Tên Hàng',
        'Số Lượng Tồn',
        'Tồn Tối Thiểu',
        'Giá Nhập (VNĐ)',
        'Giá Xuất (VNĐ)'
    ])

    danh_sach = (
        HangHoa.objects
        .all()
        .order_by('ma_hang')
    )

    for item in danh_sach:

        writer.writerow([
            item.ma_hang,
            item.ten_hang,
            item.so_luong_ton,
            item.ton_toi_thieu,
            item.gia_nhap,
            item.gia_xuat
        ])

    return response


# =========================================================
# 15. CHI TIẾT PHIẾU KHO
# =========================================================

@login_required_custom
def phieu_detail_view(
    request,
    pk
):

    phieu = get_object_or_404(
        PhieuKho,
        pk=pk
    )

    chi_tiet = (
        phieu.chi_tiet
        .select_related(
            'hang_hoa'
        )
        .all()
    )

    context = {
        'username': request.session.get(
            'username'
        ),
        'role': request.session.get(
            'role'
        ),
        'phieu': phieu,
        'chi_tiet': chi_tiet,
    }

    return render(
        request,
        'warehouse/phieu_detail.html',
        context
    )


# =========================================================
# 16. CHI TIẾT LÔ HÀNG
# =========================================================

@login_required_custom
def chi_tiet_lo_hang_view(
    request,
    pk
):

    san_pham = get_object_or_404(
        HangHoa,
        pk=pk
    )

    danh_sach_lo = (
        ChiTietPhieuKho.objects
        .filter(
            hang_hoa=san_pham,
            phieu_kho__loai_phieu='NHAP'
        )
        .select_related(
            'phieu_kho',
            'phieu_kho__nguoi_lap'
        )
        .order_by(
            '-phieu_kho__ngay_lap'
        )
    )

    context = {
        'username': request.session.get(
            'username'
        ),
        'role': request.session.get(
            'role'
        ),
        'san_pham': san_pham,
        'danh_sach_lo': danh_sach_lo,
    }

    return render(
        request,
        'warehouse/chi_tiet_lo_hang.html',
        context
    )


# =========================================================
# 17. QUẢN LÝ NHÓM HÀNG
# =========================================================

@login_required_custom
def nhom_hang_list_view(request):

    danh_sach = (
        NhomHang.objects
        .all()
        .order_by('-id')
    )

    context = {
        'username': request.session.get(
            'username'
        ),
        'role': request.session.get(
            'role'
        ),
        'danh_sach': danh_sach,
    }

    return render(
        request,
        'warehouse/nhom_hang_list.html',
        context
    )


@login_required_custom
@role_required([
    'THUKHO',
    'ADMIN'
])
def nhom_hang_form_view(
    request,
    pk=None
):

    is_edit = pk is not None

    nhom_hang = (
        get_object_or_404(
            NhomHang,
            pk=pk
        )
        if is_edit
        else None
    )

    if request.method == 'POST':

        ten_nhom = request.POST.get(
            'ten_nhom',
            ''
        ).strip()

        mo_ta = request.POST.get(
            'mo_ta',
            ''
        ).strip()

        if not ten_nhom:

            messages.error(
                request,
                "Vui lòng nhập tên nhóm hàng!"
            )

            return redirect(
                'nhom_hang_edit',
                pk=pk
            ) if is_edit else redirect(
                'nhom_hang_add'
            )

        check_exist = (
            NhomHang.objects
            .filter(
                ten_nhom=ten_nhom
            )
        )

        if is_edit:

            check_exist = (
                check_exist
                .exclude(pk=pk)
            )

        if check_exist.exists():

            messages.error(
                request,
                (
                    f"Nhóm hàng "
                    f"'{ten_nhom}' đã tồn tại!"
                )
            )

            return redirect(
                'nhom_hang_edit',
                pk=pk
            ) if is_edit else redirect(
                'nhom_hang_add'
            )

        if is_edit:

            nhom_hang.ten_nhom = ten_nhom
            nhom_hang.mo_ta = mo_ta

            nhom_hang.save()

            messages.success(
                request,
                "Cập nhật nhóm hàng thành công!"
            )

        else:

            NhomHang.objects.create(
                ten_nhom=ten_nhom,
                mo_ta=mo_ta
            )

            messages.success(
                request,
                "Thêm nhóm hàng mới thành công!"
            )

        return redirect(
            'nhom_hang_list'
        )

    context = {
        'username': request.session.get(
            'username'
        ),
        'role': request.session.get(
            'role'
        ),
        'is_edit': is_edit,
        'nhom_hang': nhom_hang,
    }

    return render(
        request,
        'warehouse/nhom_hang_form.html',
        context
    )


@login_required_custom
@role_required([
    'THUKHO',
    'ADMIN'
])
def nhom_hang_delete_view(
    request,
    pk
):

    if request.method != 'POST':

        messages.error(
            request,
            "Thao tác không hợp lệ!"
        )

        return redirect(
            'nhom_hang_list'
        )

    item = get_object_or_404(
        NhomHang,
        pk=pk
    )

    item.delete()

    messages.success(
        request,
        "Đã xóa nhóm hàng thành công!"
    )

    return redirect(
        'nhom_hang_list'
    )


# =========================================================
# 18. TRỢ LÝ & DỰ BÁO AI
# =========================================================

@login_required_custom
def ai_assistant_view(request):

    hang_can_nhap = (
        HangHoa.objects
        .filter(
            so_luong_ton__lte=F(
                'ton_toi_thieu'
            )
        )
    )

    goi_y_nhap = []

    for item in hang_can_nhap:

        sl_goi_y = max(
            (
                item.ton_toi_thieu * 2
            )
            - item.so_luong_ton,
            10
        )

        chi_phi_du_kien = (
            sl_goi_y
            * item.gia_nhap
        )

        goi_y_nhap.append(
            {
                'hang': item,
                'so_luong_goi_y': sl_goi_y,
                'chi_phi': chi_phi_du_kien,
            }
        )

    tong_san_pham = (
        HangHoa.objects.count()
    )

    tong_gia_tri = sum(
        (
            h.so_luong_ton
            * h.gia_nhap
        )
        for h in HangHoa.objects.all()
    )

    so_luong_can_canh_bao = (
        hang_can_nhap.count()
    )

    ai_insights = []

    if so_luong_can_canh_bao > 0:

        ai_insights.append(
            (
                f"⚠️ Phát hiện "
                f"{so_luong_can_canh_bao} mặt hàng "
                f"đang chạm/dưới ngưỡng tồn kho tối thiểu. "
                f"Khuyến nghị lập phiếu nhập."
            )
        )

    else:

        ai_insights.append(
            "✅ Tất cả các mặt hàng hiện tại đều nằm trong vùng an toàn."
        )

    if tong_gia_tri > 50000000:

        ai_insights.append(
            (
                f"💰 Tổng giá trị vốn đọng kho cao "
                f"({tong_gia_tri:,.0f} đ). "
                f"Cần cân đối xuất hàng để tối ưu dòng tiền."
            )
        )

    else:

        ai_insights.append(
            (
                f"📊 Tổng giá trị tồn kho "
                f"({tong_gia_tri:,.0f} đ)."
            )
        )

    ai_insights.append(
        "📈 Các luồng nhập/xuất kho được hệ thống theo dõi ổn định."
    )

    context = {
        'username': request.session.get(
            'username'
        ),
        'role': request.session.get(
            'role'
        ),
        'goi_y_nhap': goi_y_nhap,
        'tong_san_pham': tong_san_pham,
        'tong_gia_tri': tong_gia_tri,
        'so_luong_can_canh_bao': so_luong_can_canh_bao,
        'ai_insights': ai_insights,
    }

    return render(
        request,
        'warehouse/ai_assistant.html',
        context
    )


# =========================================================
# 19. QUẢN LÝ NHÀ CUNG CẤP
# =========================================================

@login_required_custom
def nha_cung_cap_list_view(request):

    danh_sach = (
        NhaCungCap.objects
        .all()
        .order_by('-id')
    )

    keyword = request.GET.get(
        'keyword',
        ''
    ).strip()

    if keyword:
        danh_sach = danh_sach.filter(
            Q(ma_ncc__icontains=keyword)
            | Q(ten_ncc__icontains=keyword)
            | Q(so_dien_thoai__icontains=keyword)
        )

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'nha_cung_caps': danh_sach,
        'keyword': keyword,
    }

    return render(
        request,
        'warehouse/nha_cung_cap_list.html',
        context
    )

@login_required_custom
@role_required(['THUKHO', 'ADMIN'])
def nha_cung_cap_form_view(request, pk=None):

    instance = get_object_or_404(
        NhaCungCap,
        pk=pk
    ) if pk else None

    if request.method == 'POST':

        ma_ncc = request.POST.get('ma_ncc', '').strip()
        ten_ncc = request.POST.get('ten_ncc', '').strip()
        so_dien_thoai = request.POST.get('so_dien_thoai', '').strip()
        email = request.POST.get('email', '').strip()
        dia_chi = request.POST.get('dia_chi', '').strip()

        if not ma_ncc:
            messages.error(
                request,
                'Vui lòng nhập mã nhà cung cấp!'
            )

        elif not ten_ncc:
            messages.error(
                request,
                'Vui lòng nhập tên nhà cung cấp!'
            )

        else:

            # Kiểm tra trùng mã NCC
            trung_ma = NhaCungCap.objects.filter(
                ma_ncc=ma_ncc
            )

            if instance:
                trung_ma = trung_ma.exclude(
                    pk=instance.pk
                )

            if trung_ma.exists():

                messages.error(
                    request,
                    f'Mã nhà cung cấp "{ma_ncc}" đã tồn tại!'
                )

            else:

                try:

                    if instance is None:

                        # THÊM
                        NhaCungCap.objects.create(
                            ma_ncc=ma_ncc,
                            ten_ncc=ten_ncc,
                            so_dien_thoai=so_dien_thoai or None,
                            email=email or None,
                            dia_chi=dia_chi or None
                        )

                        messages.success(
                            request,
                            f'Đã thêm nhà cung cấp "{ten_ncc}" thành công!'
                        )

                    else:

                        # SỬA
                        instance.ma_ncc = ma_ncc
                        instance.ten_ncc = ten_ncc
                        instance.so_dien_thoai = (
                            so_dien_thoai or None
                        )
                        instance.email = email or None
                        instance.dia_chi = dia_chi or None

                        instance.save()

                        messages.success(
                            request,
                            f'Đã cập nhật nhà cung cấp "{ten_ncc}" thành công!'
                        )

                    return redirect('nha_cung_cap_list')

                except IntegrityError:

                    messages.error(
                        request,
                        'Không thể lưu nhà cung cấp. '
                        'Mã nhà cung cấp có thể đã tồn tại!'
                    )

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),

        'is_edit': instance is not None,

        'nha_cc': instance,

        'form_data': {
            'ma_ncc': request.POST.get(
                'ma_ncc',
                instance.ma_ncc if instance else ''
            ),

            'ten_ncc': request.POST.get(
                'ten_ncc',
                instance.ten_ncc if instance else ''
            ),

            'so_dien_thoai': request.POST.get(
                'so_dien_thoai',
                instance.so_dien_thoai if instance else ''
            ),

            'email': request.POST.get(
                'email',
                instance.email if instance else ''
            ),

            'dia_chi': request.POST.get(
                'dia_chi',
                instance.dia_chi if instance else ''
            ),
        }
    }

    return render(
        request,
        'warehouse/nha_cung_cap_form.html',
        context
    )

@login_required_custom
@role_required([
    'THUKHO',
    'ADMIN'
])
def nha_cung_cap_delete_view(request, pk):

    if request.method != 'POST':
        messages.error(
            request,
            'Phương thức không hợp lệ!'
        )
        return redirect('nha_cung_cap_list')

    nha_cung_cap = get_object_or_404(
        NhaCungCap,
        pk=pk
    )

    try:
        ten_ncc = nha_cung_cap.ten_ncc

        nha_cung_cap.delete()

        messages.success(
            request,
            f'Đã xóa nhà cung cấp "{ten_ncc}" thành công!'
        )

    except IntegrityError:
        messages.error(
            request,
            'Không thể xóa nhà cung cấp này vì '
            'dữ liệu đang được sử dụng!'
        )

    return redirect('nha_cung_cap_list')

# =========================================================
# 20. QUẢN LÝ TÀI KHOẢN ADMIN
# =========================================================

@role_required(['ADMIN'])
def quan_ly_tai_khoan_view(request):

    current_admin = get_current_user_obj(request)

    # -----------------------------------------------------
    # TẠO TÀI KHOẢN MỚI
    # -----------------------------------------------------

    if request.method == 'POST':

        ten_dang_nhap = request.POST.get(
            'ten_dang_nhap',
            ''
        ).strip()

        mat_khau = request.POST.get(
            'mat_khau',
            ''
        ).strip()

        role = request.POST.get(
            'role',
            'THUKHO'
        ).strip().upper()

        # Kiểm tra tên đăng nhập
        if not ten_dang_nhap:

            messages.error(
                request,
                "Vui lòng nhập tên đăng nhập!"
            )

            return redirect(
                'quan_ly_tai_khoan'
            )

        # Không cho tạo username admin
        if ten_dang_nhap.lower() == 'admin':

            messages.error(
                request,
                "Tên đăng nhập 'admin' được dành cho tài khoản quản trị viên tối cao!"
            )

            return redirect(
                'quan_ly_tai_khoan'
            )

        # Kiểm tra mật khẩu
        if not mat_khau:

            messages.error(
                request,
                "Vui lòng nhập mật khẩu!"
            )

            return redirect(
                'quan_ly_tai_khoan'
            )

        if len(mat_khau) < 6:

            messages.error(
                request,
                "Mật khẩu phải có ít nhất 6 ký tự!"
            )

            return redirect(
                'quan_ly_tai_khoan'
            )

        # Kiểm tra quyền
        if role not in [
            'THUKHO',
            'KETOANKHO'
        ]:

            messages.error(
                request,
                "Chỉ được phép tạo tài khoản Thủ kho hoặc Kế toán kho!"
            )

            return redirect(
                'quan_ly_tai_khoan'
            )

        # Kiểm tra username trùng
        if (
            NguoiDung.objects
            .filter(
                ten_dang_nhap__iexact=ten_dang_nhap
            )
            .exists()
        ):

            messages.error(
                request,
                (
                    f"Tên đăng nhập "
                    f"'{ten_dang_nhap}' đã tồn tại!"
                )
            )

            return redirect(
                'quan_ly_tai_khoan'
            )

        # -------------------------------------------------
        # Tạo tài khoản
        # -------------------------------------------------

        new_user = NguoiDung.objects.create(
            ten_dang_nhap=ten_dang_nhap,
            password_hash=make_password(
                mat_khau
            ),
            role=role,
            is_active=True
        )

        # -------------------------------------------------
        # Ghi nhật ký
        # -------------------------------------------------

        if current_admin:

            NhatKyHoatDong.objects.create(
                nguoi_dung=current_admin,
                hanh_dong="Tạo tài khoản người dùng",
                chi_tiet=(
                    f"Tạo tài khoản "
                    f"{new_user.ten_dang_nhap} "
                    f"với vai trò {role}"
                )
            )

        messages.success(
            request,
            (
                f"Đã tạo tài khoản "
                f"'{ten_dang_nhap}' thành công!"
            )
        )

        return redirect(
            'quan_ly_tai_khoan'
        )

    # -----------------------------------------------------
    # DANH SÁCH TÀI KHOẢN
    # -----------------------------------------------------

    users = (
        NguoiDung.objects
        .all()
        .order_by('-id')
    )

    context = {
        'username': request.session.get(
            'username'
        ),
        'role': request.session.get(
            'role'
        ),
        'users': users,
    }

    return render(
        request,
        'warehouse/quan_ly_tai_khoan.html',
        context
    )


# =========================================================
# 21. ĐỔI QUYỀN TÀI KHOẢN
# =========================================================

@role_required(['ADMIN'])
def doi_quyen_user_view(
    request,
    user_id
):

    # Chỉ cho phép POST
    if request.method != 'POST':

        messages.error(
            request,
            "Thao tác không hợp lệ!"
        )

        return redirect(
            'quan_ly_tai_khoan'
        )

    current_admin = get_current_user_obj(
        request
    )

    target_user = get_object_or_404(
        NguoiDung,
        id=user_id
    )

    # -----------------------------------------------------
    # Không cho thay đổi ADMIN tối cao
    # -----------------------------------------------------

    if (
        str(target_user.role).upper() == 'ADMIN'
        or target_user.ten_dang_nhap.lower() == 'admin'
    ):

        messages.error(
            request,
            "Không thể thay đổi quyền của tài khoản Quản trị viên tối cao!"
        )

        return redirect(
            'quan_ly_tai_khoan'
        )

    new_role = request.POST.get(
        'role',
        ''
    ).strip().upper()

    # -----------------------------------------------------
    # Kiểm tra quyền mới
    # -----------------------------------------------------

    if new_role not in [
        'THUKHO',
        'KETOANKHO'
    ]:

        messages.error(
            request,
            "Chỉ được phép phân quyền Thủ kho hoặc Kế toán kho!"
        )

        return redirect(
            'quan_ly_tai_khoan'
        )

    old_role = target_user.role

    # Nếu không thay đổi
    if old_role == new_role:

        messages.info(
            request,
            "Quyền tài khoản không thay đổi."
        )

        return redirect(
            'quan_ly_tai_khoan'
        )

    # -----------------------------------------------------
    # Cập nhật quyền
    # -----------------------------------------------------

    target_user.role = new_role

    target_user.save(
        update_fields=[
            'role'
        ]
    )

    # -----------------------------------------------------
    # Ghi nhật ký
    # -----------------------------------------------------

    if current_admin:

        NhatKyHoatDong.objects.create(
            nguoi_dung=current_admin,
            hanh_dong="Đổi quyền tài khoản",
            chi_tiet=(
                f"Đổi quyền tài khoản "
                f"{target_user.ten_dang_nhap} "
                f"từ {old_role} "
                f"sang {new_role}"
            )
        )

    messages.success(
        request,
        (
            f"Đã cập nhật quyền tài khoản "
            f"'{target_user.ten_dang_nhap}' thành công!"
        )
    )

    return redirect(
        'quan_ly_tai_khoan'
    )


# =========================================================
# 22. KHÓA / MỞ KHÓA TÀI KHOẢN
# =========================================================

@role_required(['ADMIN'])
def doi_trang_thai_user_view(
    request,
    user_id
):

    # Chỉ cho phép POST
    if request.method != 'POST':

        messages.error(
            request,
            "Thao tác không hợp lệ!"
        )

        return redirect(
            'quan_ly_tai_khoan'
        )

    current_admin = get_current_user_obj(
        request
    )

    target_user = get_object_or_404(
        NguoiDung,
        id=user_id
    )

    # -----------------------------------------------------
    # Không cho tự khóa tài khoản
    # -----------------------------------------------------

    if (
        current_admin
        and target_user.id == current_admin.id
    ):

        messages.error(
            request,
            "Bạn không thể tự khóa tài khoản đang đăng nhập!"
        )

        return redirect(
            'quan_ly_tai_khoan'
        )

    # -----------------------------------------------------
    # Không cho khóa ADMIN tối cao
    # -----------------------------------------------------

    if (
        str(target_user.role).upper() == 'ADMIN'
        or target_user.ten_dang_nhap.lower() == 'admin'
    ):

        messages.error(
            request,
            "Không thể khóa tài khoản Quản trị viên tối cao!"
        )

        return redirect(
            'quan_ly_tai_khoan'
        )

    # -----------------------------------------------------
    # Đổi trạng thái
    # -----------------------------------------------------

    target_user.is_active = (
        not target_user.is_active
    )

    target_user.save(
        update_fields=[
            'is_active'
        ]
    )

    status_text = (
        "mở khóa"
        if target_user.is_active
        else "khóa"
    )

    # -----------------------------------------------------
    # Ghi nhật ký
    # -----------------------------------------------------

    if current_admin:

        NhatKyHoatDong.objects.create(
            nguoi_dung=current_admin,
            hanh_dong="Thay đổi trạng thái tài khoản",
            chi_tiet=(
                f"Đã {status_text} tài khoản: "
                f"{target_user.ten_dang_nhap}"
            )
        )

    messages.success(
        request,
        (
            f"Đã {status_text} tài khoản "
            f"'{target_user.ten_dang_nhap}' thành công!"
        )
    )

    return redirect(
        'quan_ly_tai_khoan'
    )


# =========================================================
# 23. XÓA TÀI KHOẢN
# =========================================================

@role_required(['ADMIN'])
def admin_delete_user(
    request,
    user_id
):

    # Chỉ cho phép POST
    if request.method != 'POST':

        messages.error(
            request,
            "Thao tác không hợp lệ!"
        )

        return redirect(
            'quan_ly_tai_khoan'
        )

    current_admin = get_current_user_obj(
        request
    )

    target_user = get_object_or_404(
        NguoiDung,
        id=user_id
    )

    # -----------------------------------------------------
    # Không cho tự xóa
    # -----------------------------------------------------

    if (
        current_admin
        and target_user.id == current_admin.id
    ):

        messages.error(
            request,
            "Bạn không thể tự xóa tài khoản của chính mình!"
        )

        return redirect(
            'quan_ly_tai_khoan'
        )

    # -----------------------------------------------------
    # Không cho xóa ADMIN tối cao
    # -----------------------------------------------------

    if (
        str(target_user.role).upper() == 'ADMIN'
        or target_user.ten_dang_nhap.lower() == 'admin'
    ):

        messages.error(
            request,
            "Không thể xóa tài khoản Quản trị viên tối cao!"
        )

        return redirect(
            'quan_ly_tai_khoan'
        )

    ten_dang_nhap = target_user.ten_dang_nhap

    # -----------------------------------------------------
    # Ghi nhật ký trước khi xóa
    # -----------------------------------------------------

    if current_admin:

        NhatKyHoatDong.objects.create(
            nguoi_dung=current_admin,
            hanh_dong="Xóa tài khoản",
            chi_tiet=(
                f"Đã xóa tài khoản: "
                f"{ten_dang_nhap}"
            )
        )

    # -----------------------------------------------------
    # Xóa tài khoản
    # -----------------------------------------------------

    target_user.delete()

    messages.success(
        request,
        (
            f"Đã xóa tài khoản "
            f"'{ten_dang_nhap}' thành công!"
        )
    )

    return redirect(
        'quan_ly_tai_khoan'
    )


# =========================================================
# 24. NHẬT KÝ HOẠT ĐỘNG
# =========================================================

@role_required(['ADMIN'])
def nhat_ky_hoat_dong_view(request):

    logs_list = (
        NhatKyHoatDong.objects
        .select_related(
            'nguoi_dung'
        )
        .all()
        .order_by(
            '-thoi_gian'
        )
    )

    paginator = Paginator(
        logs_list,
        15
    )

    page_number = request.GET.get(
        'page',
        1
    )

    logs = paginator.get_page(
        page_number
    )

    context = {
        'username': request.session.get(
            'username'
        ),
        'role': request.session.get(
            'role'
        ),
        'logs': logs,
    }

    return render(
        request,
        'warehouse/nhat_ky_hoat_dong.html',
        context
    )


# =========================================================
# 25. CÀI ĐẶT HỆ THỐNG
# =========================================================

@role_required(['ADMIN'])
def admin_settings(request):

    current_admin = get_current_user_obj(
        request
    )

    # -----------------------------------------------------
    # LƯU CẤU HÌNH
    # -----------------------------------------------------

    if request.method == 'POST':

        api_key = request.POST.get(
            'gemini_api_key',
            ''
        ).strip()

        default_min_stock = request.POST.get(
            'default_min_stock',
            '5'
        ).strip()

        # -------------------------------------------------
        # Kiểm tra ngưỡng tồn kho
        # -------------------------------------------------

        try:

            min_stock_value = int(
                default_min_stock
            )

            if min_stock_value < 0:
                raise ValueError

        except (
            ValueError,
            TypeError
        ):

            messages.error(
                request,
                (
                    "Ngưỡng tồn kho tối thiểu "
                    "phải là số nguyên "
                    "lớn hơn hoặc bằng 0!"
                )
            )

            return redirect(
                'admin_settings'
            )

        # -------------------------------------------------
        # Lưu API Key
        # -------------------------------------------------

        CauHinhHeThong.objects.update_or_create(
            ten_cau_hinh='GEMINI_API_KEY',
            defaults={
                'gia_tri': api_key,
                'mo_ta': 'API Key kết nối trợ lý AI'
            }
        )

        # -------------------------------------------------
        # Lưu ngưỡng tồn kho mặc định
        # -------------------------------------------------

        CauHinhHeThong.objects.update_or_create(
            ten_cau_hinh='DEFAULT_MIN_STOCK',
            defaults={
                'gia_tri': str(
                    min_stock_value
                ),
                'mo_ta': (
                    'Ngưỡng tồn kho tối thiểu '
                    'mặc định'
                )
            }
        )

        # -------------------------------------------------
        # Ghi nhật ký
        # -------------------------------------------------

        if current_admin:

            NhatKyHoatDong.objects.create(
                nguoi_dung=current_admin,
                hanh_dong="Cập nhật cấu hình",
                chi_tiet=(
                    "Thay đổi tham số "
                    "cấu hình hệ thống"
                )
            )

        messages.success(
            request,
            "Lưu cấu hình hệ thống thành công!"
        )

        return redirect(
            'admin_settings'
        )

    # -----------------------------------------------------
    # LẤY CẤU HÌNH API KEY
    # -----------------------------------------------------

    config_api = (
        CauHinhHeThong.objects
        .filter(
            ten_cau_hinh='GEMINI_API_KEY'
        )
        .first()
    )

    # -----------------------------------------------------
    # LẤY CẤU HÌNH TỒN KHO
    # -----------------------------------------------------

    config_stock = (
        CauHinhHeThong.objects
        .filter(
            ten_cau_hinh='DEFAULT_MIN_STOCK'
        )
        .first()
    )

    context = {
        'username': request.session.get(
            'username'
        ),
        'role': request.session.get(
            'role'
        ),
        'gemini_api_key': (
            config_api.gia_tri
            if config_api
            else ''
        ),
        'default_min_stock': (
            config_stock.gia_tri
            if config_stock
            else '5'
        ),
    }

    return render(
        request,
        'warehouse/admin_settings.html',
        context
    )


# =========================================================
# 26. ĐƠN VỊ TÍNH
# =========================================================

@login_required_custom
def don_vi_tinh_list_view(request):

    danh_sach = (
        DonViTinh.objects
        .all()
        .order_by('-id')
    )

    context = {
        'username': request.session.get(
            'username'
        ),
        'role': request.session.get(
            'role'
        ),
        'danh_sach': danh_sach,
    }

    return render(
        request,
        'warehouse/don_vi_tinh_list.html',
        context
    )


@login_required_custom
@role_required(['THUKHO', 'ADMIN'])
def don_vi_tinh_form_view(request, pk=None):
    """
    Thêm / sửa đơn vị tính
    """

    instance = get_object_or_404(DonViTinh, pk=pk) if pk else None

    if request.method == 'POST':

        ten_dvt = request.POST.get('ten_dvt', '').strip()
        mo_ta = request.POST.get('mo_ta', '').strip()

        # =========================
        # KIỂM TRA DỮ LIỆU
        # =========================

        if not ten_dvt:
            messages.error(
                request,
                'Vui lòng nhập tên đơn vị tính!'
            )

        else:

            # Kiểm tra trùng tên
            trung_ten = DonViTinh.objects.filter(
                ten_dvt=ten_dvt
            )

            # Nếu đang sửa thì loại chính bản ghi đang sửa
            if instance:
                trung_ten = trung_ten.exclude(
                    pk=instance.pk
                )

            if trung_ten.exists():

                messages.error(
                    request,
                    f'Tên đơn vị tính "{ten_dvt}" đã tồn tại!'
                )

            else:

                try:

                    # =========================
                    # THÊM MỚI
                    # =========================

                    if instance is None:

                        DonViTinh.objects.create(
                            ten_dvt=ten_dvt,
                            mo_ta=mo_ta or None
                        )

                        messages.success(
                            request,
                            f'Đã thêm đơn vị tính "{ten_dvt}" thành công!'
                        )

                    # =========================
                    # CẬP NHẬT
                    # =========================

                    else:

                        instance.ten_dvt = ten_dvt
                        instance.mo_ta = mo_ta or None

                        instance.save()

                        messages.success(
                            request,
                            f'Đã cập nhật đơn vị tính "{ten_dvt}" thành công!'
                        )

                    return redirect('don_vi_tinh_list')

                except IntegrityError:

                    messages.error(
                        request,
                        'Không thể lưu đơn vị tính. Tên đơn vị tính có thể đã tồn tại!'
                    )

    # =========================
    # DỮ LIỆU HIỂN THỊ FORM
    # =========================

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),

        'is_edit': instance is not None,

        'don_vi_tinh': instance,

        'form_data': {
            'ten_dvt': request.POST.get(
                'ten_dvt',
                instance.ten_dvt if instance else ''
            ),

            'mo_ta': request.POST.get(
                'mo_ta',
                instance.mo_ta if instance else ''
            ),
        }
    }

    return render(
        request,
        'warehouse/don_vi_tinh_form.html',
        context
    )


@login_required_custom
@role_required([
    'THUKHO',
    'ADMIN'
])
def don_vi_tinh_delete_view(
    request,
    pk
):

    if request.method != 'POST':

        messages.error(
            request,
            "Thao tác không hợp lệ!"
        )

        return redirect(
            'don_vi_tinh_list'
        )

    don_vi_tinh = get_object_or_404(
        DonViTinh,
        pk=pk
    )

    don_vi_tinh.delete()

    messages.success(
        request,
        "Đã xóa đơn vị tính thành công!"
    )

    return redirect(
        'don_vi_tinh_list'
    )