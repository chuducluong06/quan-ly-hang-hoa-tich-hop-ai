from django.db import migrations


PRODUCT_GROUPS = [
    ('Văn phòng phẩm', 'Giấy, bút và vật tư văn phòng.'),
    ('Đồ điện tử', 'Điện thoại, máy tính và thiết bị điện tử.'),
    ('Thực phẩm', 'Thực phẩm đóng gói, chế biến và hàng tươi.'),
    ('Đồ uống', 'Nước giải khát, trà, sữa và đồ uống đóng chai.'),
    ('Vật liệu xây dựng', 'Thép, ống nhựa và vật liệu công trình.'),
    ('Dược phẩm', 'Thuốc và sản phẩm chăm sóc sức khỏe.'),
    ('Gia dụng', 'Đồ dùng gia đình và sản phẩm nhựa gia dụng.'),
    ('Hóa mỹ phẩm', 'Sản phẩm vệ sinh cá nhân và chất tẩy rửa.'),
    ('May mặc', 'Quần áo, đồng phục và hàng dệt may.'),
]


SUPPLIER_CATALOG = {
    'NCC01': ('Đồ uống', [
        ('COCA-COLA-ZERO-330', 'Nước ngọt Coca-Cola Zero lon 330 ml', 'Chai'),
        ('COCA-COLA-SPRITE-330', 'Nước ngọt Sprite lon 330 ml', 'Chai'),
    ]),
    'NCC-VN-VINAMILK': ('Thực phẩm', [
        ('VINAMILK-SUA-TUOI-180', 'Sữa tươi tiệt trùng Vinamilk 180 ml', 'Hộp'),
        ('VINAMILK-SUA-CHUA-100', 'Sữa chua Vinamilk 100 g', 'Hộp'),
    ]),
    'NCC-VN-TH': ('Thực phẩm', [
        ('TH-SUA-TUOI-180', 'Sữa tươi TH true MILK 180 ml', 'Hộp'),
        ('TH-SUA-CHUA-100', 'Sữa chua TH true MILK 100 g', 'Hộp'),
    ]),
    'NCC-VN-MASAN': ('Thực phẩm', [
        ('MASAN-NM-750', 'Nước mắm Nam Ngư 750 ml', 'Chai'),
        ('MASAN-MI-BO-001', 'Mì ăn liền vị bò', 'Gói'),
    ]),
    'NCC-VN-ACECOOK': ('Thực phẩm', [
        ('ACECOOK-MI-HANH-001', 'Mì ăn liền Hảo Hảo vị hành', 'Gói'),
        ('ACECOOK-MI-LAU-THAI-001', 'Mì ăn liền vị lẩu Thái', 'Gói'),
    ]),
    'NCC-VN-TANHI': ('Đồ uống', [
        ('TANHI-DR-THANH-350', 'Trà thảo mộc Dr Thanh 350 ml', 'Chai'),
        ('TANHI-NUMBER1-330', 'Nước tăng lực Number 1 330 ml', 'Chai'),
    ]),
    'NCC-VN-SABECO': ('Đồ uống', [
        ('SABECO-SAIGON-SPECIAL-330', 'Bia Saigon Special lon 330 ml', 'Chai'),
        ('SABECO-333-330', 'Bia 333 lon 330 ml', 'Chai'),
    ]),
    'NCC-VN-HOAPHAT': ('Vật liệu xây dựng', [
        ('HOAPHAT-THEP-TAM-01', 'Thép tấm xây dựng', 'Tấm'),
        ('HOAPHAT-THEP-THANH-01', 'Thép thanh xây dựng', 'Thanh'),
    ]),
    'NCC-VN-BINHMINH': ('Vật liệu xây dựng', [
        ('BINHMINH-PVC-27', 'Ống PVC đường kính 27 mm', 'Cây'),
        ('BINHMINH-PVC-34', 'Ống PVC đường kính 34 mm', 'Cây'),
    ]),
    'NCC-VN-THIENLONG': ('Văn phòng phẩm', [
        ('THIENLONG-BUT-CHI-001', 'Bút chì Thiên Long', 'Cái'),
        ('THIENLONG-BUT-DA-QUANG-001', 'Bút dạ quang Thiên Long', 'Cái'),
    ]),
    'NCC-VN-DHG': ('Dược phẩm', [
        ('DHG-EFFER-001', 'Viên sủi vitamin C DHG', 'Hộp'),
        ('DHG-OMEGA-001', 'Viên uống dầu cá DHG', 'Hộp'),
    ]),
    'NCC-VN-FPT': ('Đồ điện tử', [
        ('FPT-SSD-001', 'Ổ cứng SSD di động', 'Cái'),
        ('FPT-KEYBOARD-001', 'Bàn phím máy tính', 'Cái'),
    ]),
    'NCC-VN-DUYTAN': ('Gia dụng', [
        ('DUYTAN-HOP-THUC-PHAM-002', 'Hộp nhựa bảo quản thực phẩm', 'Cái'),
        ('DUYTAN-RO-NHUA-001', 'Rổ nhựa gia dụng', 'Cái'),
    ]),
    'NCC-VN-UNILEVER': ('Hóa mỹ phẩm', [
        ('UNILEVER-SHAMPOO-001', 'Dầu gội đầu Clear', 'Chai'),
        ('UNILEVER-SUNLIGHT-001', 'Nước rửa chén Sunlight', 'Chai'),
    ]),
    'NCC-VN-SAMSUNG': ('Đồ điện tử', [
        ('SAMSUNG-TABLET-001', 'Máy tính bảng Samsung Galaxy Tab', 'Cái'),
        ('SAMSUNG-MONITOR-001', 'Màn hình Samsung', 'Cái'),
    ]),
    'NCC-VN-PG': ('Hóa mỹ phẩm', [
        ('PG-HEAD-SHOULDERS-001', 'Dầu gội Head & Shoulders', 'Chai'),
        ('PG-DOWNY-001', 'Nước xả vải Downy', 'Chai'),
    ]),
    'NCC-VN-RANGDONG': ('Đồ điện tử', [
        ('RANGDONG-LED-BULB-12', 'Bóng đèn LED Rạng Đông 12 W', 'Cái'),
        ('RANGDONG-LED-TUBE-12', 'Đèn LED tuýp Rạng Đông 12 W', 'Cái'),
    ]),
    'NCC-VN-VISSAN': ('Thực phẩm', [
        ('VISSAN-XUCXICH-TIETTRUNG-001', 'Xúc xích tiệt trùng VISSAN', 'Gói'),
        ('VISSAN-CHA-LUA-500', 'Chả lụa VISSAN 500 g', 'Hộp'),
    ]),
    'NCC-VN-VIETTIEN': ('May mặc', [
        ('VIETTIEN-AO-THUN-001', 'Áo thun nam Việt Tiến', 'Cái'),
        ('VIETTIEN-AO-KHOAC-001', 'Áo khoác nam Việt Tiến', 'Cái'),
    ]),
    'NCC-VN-CHOLIMEX': ('Thực phẩm', [
        ('CHOLIMEX-TUONG-OT-500', 'Tương ớt Cholimex 500 g', 'Chai'),
        ('CHOLIMEX-SOT-MAYONNAISE-250', 'Xốt mayonnaise Cholimex 250 g', 'Chai'),
    ]),
    'NCC-VN-HOATHO': ('May mặc', [
        ('HOATHO-AO-SO-MI-001', 'Áo sơ mi đồng phục Hòa Thọ', 'Cái'),
        ('HOATHO-VAI-KAKI-001', 'Vải kaki Hòa Thọ', 'Cuộn'),
    ]),
    'NCC-VN-APPLE': ('Đồ điện tử', [
        ('APPLE-IPHONE-18', 'Apple iPhone 18', 'Cái'),
        ('APPLE-MAGIC-KEYBOARD', 'Apple Magic Keyboard', 'Cái'),
    ]),
}


SUPPLIER_GROUPS = {
    supplier_code: group_name
    for supplier_code, (group_name, _products) in SUPPLIER_CATALOG.items()
}


def seed_product_groups_and_catalog(apps, schema_editor):
    group_model = apps.get_model('warehouse', 'NhomHang')
    supplier_model = apps.get_model('warehouse', 'NhaCungCap')
    product_model = apps.get_model('warehouse', 'HangHoa')
    unit_model = apps.get_model('warehouse', 'DonViTinh')
    database = schema_editor.connection.alias

    groups = {
        group.ten_nhom.casefold(): group
        for group in group_model.objects.using(database).all()
    }
    for group_name, description in PRODUCT_GROUPS:
        group = groups.get(group_name.casefold())
        if group is None:
            group = group_model.objects.using(database).create(
                ten_nhom=group_name,
                mo_ta=description,
            )
            groups[group_name.casefold()] = group
        groups[group_name] = group

    units = {
        unit.ten_dvt: unit.pk
        for unit in unit_model.objects.using(database).all()
    }
    suppliers = supplier_model.objects.using(database)
    products = product_model.objects.using(database)

    for supplier_code, (group_name, catalog) in SUPPLIER_CATALOG.items():
        supplier = suppliers.filter(ma_ncc=supplier_code).first()
        if supplier is None:
            continue
        group = groups[group_name]

        for product_code, product_name, unit_name in catalog:
            product, _ = products.get_or_create(
                ma_hang=product_code,
                defaults={
                    'ten_hang': product_name,
                    'nhom_hang_id': group.pk,
                    'don_vi_tinh_id': units.get(unit_name),
                    'so_luong_ton': 0,
                    'ton_toi_thieu': 5,
                    'gia_nhap': 0,
                    'gia_xuat': 0,
                },
            )
            if product.nhom_hang_id is None:
                product.nhom_hang_id = group.pk
                product.save(using=database, update_fields=['nhom_hang'])
            supplier.hang_hoa.add(product)

    for supplier_code, group_name in SUPPLIER_GROUPS.items():
        supplier = suppliers.filter(ma_ncc=supplier_code).first()
        if supplier is None:
            continue
        products.filter(
            nha_cung_caps=supplier,
            nhom_hang__isnull=True,
        ).update(nhom_hang=groups[group_name])

    unassigned_products = products.filter(nhom_hang__isnull=True)
    keyword_groups = (
        ('Văn phòng phẩm', ('bút', 'vở', 'giấy')),
        ('Đồ điện tử', ('iphone', 'điện thoại', 'máy tính', 'màn hình', 'tivi')),
        ('Đồ uống', ('coca', 'nước ngọt', 'bia', 'trà xanh')),
        ('May mặc', ('áo ', 'quần ', 'vải')),
        ('Dược phẩm', ('thuốc', 'viên nén', 'vitamin')),
        ('Vật liệu xây dựng', ('thép', 'ống pvc', 'ống ppr')),
        ('Gia dụng', ('nhựa', 'bình nước')),
        ('Thực phẩm', ('sữa', 'mì ', 'phở', 'nước mắm', 'xúc xích')),
    )
    for group_name, keywords in keyword_groups:
        for keyword in keywords:
            unassigned_products.filter(
                ten_hang__icontains=keyword,
            ).update(nhom_hang=groups[group_name])


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0016_seed_latest_apple_models'),
    ]

    operations = [
        migrations.RunPython(
            seed_product_groups_and_catalog,
            migrations.RunPython.noop,
        ),
    ]
