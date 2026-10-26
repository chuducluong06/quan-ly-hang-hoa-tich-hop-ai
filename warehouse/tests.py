from django.contrib.auth.hashers import check_password, make_password
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse

from .models import (
    ChiTietPhieuKho,
    DonViTinh,
    HangHoa,
    NhomHang,
    NguoiDung,
    NhaCungCap,
    PhieuKho,
)


class AdminUserManagementTests(TestCase):
    def setUp(self):
        self.admin = NguoiDung.objects.create(
            ten_dang_nhap='admin',
            password_hash=make_password('admin-pass'),
            role='ADMIN',
            is_active=True,
        )
        self.staff = NguoiDung.objects.create(
            ten_dang_nhap='staff',
            password_hash=make_password('old-pass'),
            role='THUKHO',
            is_active=True,
        )
        session = self.client.session
        session['user_id'] = self.admin.id
        session['username'] = self.admin.ten_dang_nhap
        session['role'] = self.admin.role
        session.save()

    def test_admin_can_reset_other_users_password(self):
        response = self.client.post(
            reverse('admin_reset_user_password', args=[self.staff.id]),
            {
                'mat_khau_moi': 'new-password',
                'xac_nhan_mat_khau': 'new-password',
            },
        )

        self.staff.refresh_from_db()
        self.assertRedirects(response, reverse('quan_ly_tai_khoan'))
        self.assertTrue(check_password('new-password', self.staff.password_hash))

    def test_password_reset_rejects_mismatched_confirmation(self):
        response = self.client.post(
            reverse('admin_reset_user_password', args=[self.staff.id]),
            {
                'mat_khau_moi': 'new-password',
                'xac_nhan_mat_khau': 'different-password',
            },
        )

        self.staff.refresh_from_db()
        self.assertRedirects(response, reverse('quan_ly_tai_khoan'))
        self.assertTrue(check_password('old-pass', self.staff.password_hash))

    def test_admin_cannot_reset_own_password_from_user_management(self):
        response = self.client.post(
            reverse('admin_reset_user_password', args=[self.admin.id]),
            {
                'mat_khau_moi': 'new-password',
                'xac_nhan_mat_khau': 'new-password',
            },
        )

        self.admin.refresh_from_db()
        self.assertRedirects(response, reverse('quan_ly_tai_khoan'))
        self.assertTrue(check_password('admin-pass', self.admin.password_hash))

    def test_admin_can_delete_other_users(self):
        response = self.client.post(
            reverse('admin_delete_user', args=[self.staff.id])
        )

        self.assertRedirects(response, reverse('quan_ly_tai_khoan'))
        self.assertFalse(NguoiDung.objects.filter(id=self.staff.id).exists())

    def test_admin_account_cannot_be_deleted_or_reset(self):
        delete_response = self.client.post(
            reverse('admin_delete_user', args=[self.admin.id])
        )
        reset_response = self.client.post(
            reverse('admin_reset_user_password', args=[self.admin.id]),
            {
                'mat_khau_moi': 'new-password',
                'xac_nhan_mat_khau': 'new-password',
            },
        )

        self.assertRedirects(delete_response, reverse('quan_ly_tai_khoan'))
        self.assertRedirects(reset_response, reverse('quan_ly_tai_khoan'))
        self.assertTrue(NguoiDung.objects.filter(id=self.admin.id).exists())

    def test_admin_settings_page_keeps_configuration_fields_in_responsive_layout(self):
        response = self.client.get(reverse('admin_settings'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="admin-page admin-settings-page"')
        self.assertContains(response, 'name="gemini_api_key"')
        self.assertContains(response, 'name="default_min_stock"')
        self.assertContains(response, 'admin-page-actions')

    def test_admin_pages_share_the_same_layout_styles(self):
        for route_name, heading in (
            ('quan_ly_tai_khoan', 'admin-page-title'),
            ('nhat_ky_hoat_dong', 'admin-page-title'),
            ('admin_settings', 'admin-page-title'),
        ):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'warehouse/admin-pages.css')
                self.assertContains(response, heading)
                self.assertContains(response, 'admin-page-header')

    def test_admin_pages_use_the_shared_task_sidebar(self):
        for route_name in (
            'quan_ly_tai_khoan',
            'nhat_ky_hoat_dong',
            'admin_settings',
        ):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'id="taskMenuTemplate"')
                self.assertContains(response, 'id="taskMenuConfig"')
                self.assertContains(response, 'warehouse/task-menu.js')
                self.assertNotContains(response, 'id="sidebarNav"')
                self.assertNotContains(response, 'id="currentDate"')

    def test_user_management_actions_are_grouped_for_clear_scanning(self):
        response = self.client.get(reverse('quan_ly_tai_khoan'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'admin-user-table')
        self.assertContains(response, 'admin-user-action-stack')
        self.assertContains(response, 'admin-password-reset-form')
        self.assertContains(response, 'admin-account-actions')

    def test_account_list_search_filters_by_username(self):
        NguoiDung.objects.create(
            ten_dang_nhap='warehouse-operator',
            password_hash=make_password('staff-pass'),
            role='THUKHO',
            is_active=True,
        )

        response = self.client.get(
            reverse('quan_ly_tai_khoan'),
            {'q': 'warehouse'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'warehouse-operator')
        self.assertNotContains(response, 'staff')
        self.assertContains(response, 'name="q"')
        self.assertContains(response, 'value="warehouse"')

    def test_global_search_finds_products_suppliers_and_vouchers(self):
        supplier = NhaCungCap.objects.create(
            ma_ncc='SEARCH-TEST',
            ten_ncc='Northstar Search Supplier',
            so_dien_thoai='0900000000',
            email='search@example.com',
        )
        product = HangHoa.objects.create(
            ma_hang='SEARCH-ITEM',
            ten_hang='Northstar Search Product',
            so_luong_ton=12,
            gia_nhap=1000,
            gia_xuat=1500,
        )
        supplier.hang_hoa.add(product)
        voucher = PhieuKho.objects.create(
            ma_phieu='SEARCH-VOUCHER',
            loai_phieu='NHAP',
            nha_cung_cap=supplier,
            ghi_chu='Northstar reference',
        )

        response = self.client.get(
            reverse('global_search'),
            {'q': 'Northstar'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.ten_hang)
        self.assertContains(response, supplier.ten_ncc)
        self.assertContains(response, voucher.ma_phieu)
        self.assertContains(response, reverse('phieu_detail', args=[voucher.pk]))

    def test_global_search_toolbar_has_working_get_forms(self):
        response = self.client.get(reverse('global_search'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-global-search-url="/tim-kiem/"')
        self.assertContains(response, 'warehouse/task-menu.js')
        script_path = finders.find('warehouse/task-menu.js')
        self.assertIsNotNone(script_path)
        with open(script_path, encoding='utf-8') as script_file:
            script = script_file.read()
        self.assertIn('name="q"', script)
        self.assertIn('action="${globalSearchUrl}"', script)


class TaskMenuNavigationTests(TestCase):
    def setUp(self):
        session = self.client.session
        session['user_id'] = 1
        session['username'] = 'admin'
        session['role'] = 'ADMIN'
        session.save()

    def test_unit_and_supplier_pages_use_the_shared_task_menu(self):
        for route_name in (
            'don_vi_tinh_list',
            'don_vi_tinh_add',
            'nha_cung_cap_list',
            'nha_cung_cap_add',
        ):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'id="taskMenuTemplate"')
                self.assertContains(response, 'id="taskMenuConfig"')
                self.assertContains(response, 'warehouse/task-menu.js')
                self.assertNotContains(response, 'id="sidebarNav"')
                self.assertNotContains(response, 'id="currentDate"')

    def test_task_menu_only_hides_legacy_headers(self):
        script_path = finders.find('warehouse/task-menu.js')
        self.assertIsNotNone(script_path)

        with open(script_path, encoding='utf-8') as script_file:
            script = script_file.read()

        self.assertIn('header.h-16, body > nav.navbar', script)
        self.assertNotIn('querySelectorAll("header,', script)

    def test_product_list_keeps_stock_and_product_actions_on_one_row(self):
        product = HangHoa.objects.create(
            ma_hang='ACTION-BUTTONS-TEST',
            ten_hang='Sản phẩm kiểm thử các nút',
            so_luong_ton=5,
            gia_nhap=1000,
            gia_xuat=1500,
        )
        response = self.client.get(reverse('san_pham_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'product-inventory-table')
        self.assertContains(response, 'product-flow-actions')
        self.assertContains(response, 'product-actions-cell')
        self.assertContains(response, 'min-width: 980px')
        self.assertContains(
            response,
            f'href="{reverse("phieu_nhap_create")}?san_pham_id={product.pk}"',
        )
        self.assertContains(
            response,
            f'href="{reverse("phieu_xuat_create")}?san_pham_id={product.pk}"',
        )
        self.assertContains(
            response,
            f'href="{reverse("chi_tiet_lo_hang", args=[product.pk])}"',
        )
        self.assertContains(
            response,
            f'href="{reverse("san_pham_edit", args=[product.pk])}"',
        )
        self.assertContains(
            response,
            f'action="{reverse("san_pham_delete", args=[product.pk])}"',
        )

    def test_common_warehouse_units_are_available(self):
        self.assertGreaterEqual(DonViTinh.objects.count(), 20)
        for unit_name in ('Cái', 'Thùng', 'Kilogram (kg)', 'Lít', 'Pallet'):
            self.assertTrue(DonViTinh.objects.filter(ten_dvt=unit_name).exists())

        response = self.client.get(reverse('don_vi_tinh_list'))
        self.assertContains(response, 'Kilogram (kg)')
        self.assertContains(response, 'Thùng')

    def test_popular_vietnamese_suppliers_are_available(self):
        self.assertGreaterEqual(NhaCungCap.objects.count(), 20)
        for supplier_name in (
            'Vinamilk',
            'TH true MILK',
            'Masan Consumer',
            'Acecook Việt Nam',
            'Tập đoàn Hòa Phát',
            'Apple',
        ):
            self.assertTrue(
                NhaCungCap.objects.filter(ten_ncc=supplier_name).exists()
            )

        response = self.client.get(reverse('nha_cung_cap_list'))
        self.assertContains(response, 'Vinamilk')
        self.assertContains(response, 'Masan Consumer')
        self.assertContains(response, 'Apple')

    def test_apple_supplier_has_linked_products(self):
        supplier = NhaCungCap.objects.get(ma_ncc='NCC-VN-APPLE')

        self.assertGreaterEqual(supplier.hang_hoa.count(), 20)
        self.assertTrue(
            supplier.hang_hoa.filter(
                ma_hang='APPLE-IPHONE-18-PRO',
            ).exists()
        )
        self.assertTrue(
            supplier.hang_hoa.filter(
                ma_hang='APPLE-IPHONE-DUO',
            ).exists()
        )
        self.assertTrue(
            supplier.hang_hoa.filter(
                ma_hang='APPLE-MACBOOK-PRO-M5-14',
            ).exists()
        )

    def test_product_groups_and_expanded_supplier_catalog_are_seeded(self):
        for group_name in (
            'Văn phòng phẩm',
            'Đồ điện tử',
            'Thực phẩm',
            'Đồ uống',
            'Vật liệu xây dựng',
            'Dược phẩm',
            'Gia dụng',
            'Hóa mỹ phẩm',
            'May mặc',
        ):
            self.assertTrue(
                NhomHang.objects.filter(ten_nhom__iexact=group_name).exists()
            )

        electronic_group_names = [
            group.ten_nhom.casefold()
            for group in NhomHang.objects.all()
            if group.ten_nhom.casefold() == 'đồ điện tử'.casefold()
        ]
        self.assertEqual(len(electronic_group_names), 1)

        self.assertGreaterEqual(HangHoa.objects.count(), 100)

        vinamilk_product = HangHoa.objects.get(
            ma_hang='VINAMILK-SUA-TUOI-180'
        )
        self.assertEqual(
            vinamilk_product.nhom_hang.ten_nhom.casefold(),
            'thực phẩm'.casefold(),
        )
        self.assertEqual(vinamilk_product.so_luong_ton, 0)
        self.assertEqual(vinamilk_product.gia_nhap, 0)

        apple_product = HangHoa.objects.get(ma_hang='APPLE-MAGIC-KEYBOARD')
        self.assertEqual(
            apple_product.nhom_hang.ten_nhom.casefold(),
            'đồ điện tử'.casefold(),
        )
        self.assertTrue(
            apple_product.nha_cung_caps.filter(ma_ncc='NCC-VN-APPLE').exists()
        )

    def test_group_edit_can_assign_and_move_products(self):
        target_group = NhomHang.objects.create(ten_nhom='Nhóm đích kiểm thử')
        previous_group = NhomHang.objects.create(ten_nhom='Nhóm cũ kiểm thử')
        old_product = HangHoa.objects.create(
            ma_hang='GROUP-OLD-TEST',
            ten_hang='Sản phẩm cũ',
            nhom_hang=target_group,
            so_luong_ton=0,
            gia_nhap=0,
            gia_xuat=0,
        )
        moved_product = HangHoa.objects.create(
            ma_hang='GROUP-MOVE-TEST',
            ten_hang='Sản phẩm chuyển nhóm',
            nhom_hang=previous_group,
            so_luong_ton=0,
            gia_nhap=0,
            gia_xuat=0,
        )

        form_response = self.client.get(
            reverse('nhom_hang_edit', args=[target_group.pk])
        )
        self.assertContains(form_response, 'name="hang_hoa_ids"')
        self.assertContains(form_response, 'GROUP-OLD-TEST')
        self.assertContains(form_response, 'GROUP-MOVE-TEST')
        self.assertContains(
            form_response,
            f'value="{old_product.pk}"',
        )

        response = self.client.post(
            reverse('nhom_hang_edit', args=[target_group.pk]),
            {
                'ten_nhom': target_group.ten_nhom,
                'mo_ta': '',
                'hang_hoa_ids': [str(moved_product.pk)],
            },
        )

        self.assertRedirects(response, reverse('nhom_hang_list'))
        old_product.refresh_from_db()
        moved_product.refresh_from_db()
        self.assertIsNone(old_product.nhom_hang)
        self.assertEqual(moved_product.nhom_hang, target_group)

    def test_sample_product_codes_are_linked_to_suppliers(self):
        supplier = NhaCungCap.objects.get(ma_ncc='NCC-VN-VINAMILK')
        products = supplier.hang_hoa.all()

        self.assertGreaterEqual(products.count(), 2)
        self.assertTrue(
            products.filter(ma_hang='VINAMILK-SUA-001').exists()
        )
        sample_product = products.get(ma_hang='VINAMILK-SUA-001')
        self.assertEqual(sample_product.so_luong_ton, 0)
        self.assertEqual(sample_product.gia_nhap, 0)

        response = self.client.get(reverse('nha_cung_cap_list'))
        self.assertContains(response, 'VINAMILK-SUA-001')

    def test_supplier_edit_updates_product_code_assignments(self):
        supplier = NhaCungCap.objects.get(ma_ncc='NCC-VN-VINAMILK')
        product = HangHoa.objects.get(ma_hang='VINAMILK-SUA-001')

        response = self.client.post(
            reverse('nha_cung_cap_edit', args=[supplier.pk]),
            {
                'ma_ncc': supplier.ma_ncc,
                'ten_ncc': supplier.ten_ncc,
                'so_dien_thoai': '',
                'email': '',
                'dia_chi': '',
                'hang_hoa_ids': [str(product.pk)],
            },
        )

        self.assertRedirects(response, reverse('nha_cung_cap_list'))
        self.assertQuerySetEqual(
            supplier.hang_hoa.order_by('pk'),
            [product],
        )

    def test_purchase_and_sales_forms_load_searchable_select_assets(self):
        for route_name in ('phieu_nhap_create', 'phieu_xuat_create'):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'warehouse/searchable-select.css')
                self.assertContains(response, 'warehouse/searchable-select.js')
                self.assertContains(response, 'class="select-hang')

        self.assertContains(
            self.client.get(reverse('phieu_nhap_create')),
            'name="nha_cung_cap"',
        )

    def test_purchase_form_products_include_their_supplier_ids(self):
        supplier = NhaCungCap.objects.get(ma_ncc='NCC-VN-VINAMILK')
        product = supplier.hang_hoa.get(ma_hang='VINAMILK-SUA-001')

        response = self.client.get(reverse('phieu_nhap_create'))

        self.assertContains(
            response,
            f'data-suppliers="{supplier.pk}"',
        )
        self.assertContains(response, product.ma_hang)

    def test_purchase_and_sales_lists_have_detail_buttons(self):
        product = HangHoa.objects.create(
            ma_hang='TEST-DETAIL',
            ten_hang='Sản phẩm kiểm thử',
            so_luong_ton=5,
            gia_nhap=1000,
            gia_xuat=1500,
        )
        supplier = NhaCungCap.objects.create(
            ma_ncc='TEST-NCC',
            ten_ncc='Nhà cung cấp kiểm thử',
        )

        for kind, route_name, code in (
            ('NHAP', 'phieu_nhap_list', 'PN-DETAIL'),
            ('XUAT', 'phieu_xuat_list', 'PX-DETAIL'),
        ):
            with self.subTest(kind=kind):
                receipt = PhieuKho.objects.create(
                    ma_phieu=code,
                    loai_phieu=kind,
                    nha_cung_cap=supplier if kind == 'NHAP' else None,
                )
                ChiTietPhieuKho.objects.create(
                    phieu_kho=receipt,
                    hang_hoa=product,
                    so_luong=2,
                    don_gia=1000,
                )

                response = self.client.get(reverse(route_name))
                detail_url = reverse('phieu_detail', args=[receipt.id])
                self.assertContains(response, 'Chi tiết')
                self.assertContains(response, f'href="{detail_url}"')

                detail_response = self.client.get(detail_url)
                self.assertEqual(detail_response.status_code, 200)
                self.assertContains(detail_response, code)
                self.assertContains(detail_response, 'Sản phẩm kiểm thử')
