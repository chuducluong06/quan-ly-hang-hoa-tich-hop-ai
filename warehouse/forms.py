from django import forms
from .models import NhomHang, NhaCungCap

class NhomHangForm(forms.ModelForm):
    class Meta:
        model = NhomHang
        fields = ['ten_nhom', 'mo_ta']
        widgets = {
            'ten_nhom': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm'}),
            'mo_ta': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm', 'rows': 3}),
        }

class NhaCungCapForm(forms.ModelForm):
    class Meta:
        model = NhaCungCap
        # Đã khớp đúng với các trường: ten_ncc, so_dien_thoai, dia_chi trong models.py
        fields = ['ten_ncc', 'so_dien_thoai', 'dia_chi']
        widgets = {
            'ten_ncc': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm'}),
            'so_dien_thoai': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm'}),
            'dia_chi': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm', 'rows': 2}),
        }