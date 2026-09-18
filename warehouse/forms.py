from django import forms

from .models import (
    NhomHang,
    NhaCungCap,
    DonViTinh,
)


# =========================================================
# FORM QUẢN LÝ NHÓM HÀNG
# =========================================================

class NhomHangForm(forms.ModelForm):

    class Meta:
        model = NhomHang

        fields = [
            'ten_nhom',
            'mo_ta',
        ]

        widgets = {

            'ten_nhom': forms.TextInput(
                attrs={
                    'class': (
                        'w-full px-3 py-2 border '
                        'border-gray-300 rounded-lg '
                        'shadow-sm focus:ring-blue-500 '
                        'focus:border-blue-500 text-sm'
                    ),
                    'placeholder': 'Nhập tên nhóm hàng',
                }
            ),

            'mo_ta': forms.Textarea(
                attrs={
                    'class': (
                        'w-full px-3 py-2 border '
                        'border-gray-300 rounded-lg '
                        'shadow-sm focus:ring-blue-500 '
                        'focus:border-blue-500 text-sm'
                    ),
                    'rows': 3,
                    'placeholder': 'Nhập mô tả nhóm hàng',
                }
            ),
        }


# =========================================================
# FORM QUẢN LÝ NHÀ CUNG CẤP
# =========================================================

class NhaCungCapForm(forms.ModelForm):

    class Meta:
        model = NhaCungCap

        fields = [
            'ma_ncc',
            'ten_ncc',
            'so_dien_thoai',
            'email',
            'dia_chi',
        ]

        widgets = {

            'ma_ncc': forms.TextInput(
                attrs={
                    'class': (
                        'w-full px-3 py-2 border '
                        'border-gray-300 rounded-lg '
                        'shadow-sm focus:ring-blue-500 '
                        'focus:border-blue-500 text-sm'
                    ),
                    'placeholder': 'Nhập mã nhà cung cấp',
                }
            ),

            'ten_ncc': forms.TextInput(
                attrs={
                    'class': (
                        'w-full px-3 py-2 border '
                        'border-gray-300 rounded-lg '
                        'shadow-sm focus:ring-blue-500 '
                        'focus:border-blue-500 text-sm'
                    ),
                    'placeholder': 'Nhập tên nhà cung cấp',
                }
            ),

            'so_dien_thoai': forms.TextInput(
                attrs={
                    'class': (
                        'w-full px-3 py-2 border '
                        'border-gray-300 rounded-lg '
                        'shadow-sm focus:ring-blue-500 '
                        'focus:border-blue-500 text-sm'
                    ),
                    'placeholder': 'Nhập số điện thoại',
                }
            ),

            'email': forms.EmailInput(
                attrs={
                    'class': (
                        'w-full px-3 py-2 border '
                        'border-gray-300 rounded-lg '
                        'shadow-sm focus:ring-blue-500 '
                        'focus:border-blue-500 text-sm'
                    ),
                    'placeholder': 'Nhập địa chỉ email',
                }
            ),

            'dia_chi': forms.Textarea(
                attrs={
                    'class': (
                        'w-full px-3 py-2 border '
                        'border-gray-300 rounded-lg '
                        'shadow-sm focus:ring-blue-500 '
                        'focus:border-blue-500 text-sm'
                    ),
                    'rows': 2,
                    'placeholder': 'Nhập địa chỉ nhà cung cấp',
                }
            ),
        }


# =========================================================
# FORM QUẢN LÝ ĐƠN VỊ TÍNH
# =========================================================

class DonViTinhForm(forms.ModelForm):

    class Meta:
        model = DonViTinh

        fields = [
            'ten_dvt',
            'mo_ta',
        ]

        widgets = {

            # -----------------------------
            # Tên đơn vị tính
            # -----------------------------
            'ten_dvt': forms.TextInput(
                attrs={
                    'class': (
                        'w-full px-3 py-2 border '
                        'border-gray-300 rounded-lg '
                        'shadow-sm focus:ring-blue-500 '
                        'focus:border-blue-500 text-sm'
                    ),
                    'placeholder': 'Nhập tên đơn vị tính',
                }
            ),

            # -----------------------------
            # Mô tả
            # -----------------------------
            'mo_ta': forms.Textarea(
                attrs={
                    'class': (
                        'w-full px-3 py-2 border '
                        'border-gray-300 rounded-lg '
                        'shadow-sm focus:ring-blue-500 '
                        'focus:border-blue-500 text-sm'
                    ),
                    'rows': 3,
                    'placeholder': 'Nhập mô tả đơn vị tính',
                }
            ),
        }