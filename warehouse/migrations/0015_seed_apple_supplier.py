from django.db import migrations


APPLE_PRODUCTS = [
    ('APPLE-IPHONE-001', 'Điện thoại Apple iPhone'),
    ('APPLE-IPAD-001', 'Máy tính bảng Apple iPad'),
    ('APPLE-MACBOOK-001', 'Máy tính xách tay Apple MacBook'),
]


def add_apple_supplier(apps, schema_editor):
    supplier_model = apps.get_model('warehouse', 'NhaCungCap')
    product_model = apps.get_model('warehouse', 'HangHoa')
    unit_model = apps.get_model('warehouse', 'DonViTinh')
    database = schema_editor.connection.alias

    suppliers = supplier_model.objects.using(database)
    supplier = suppliers.filter(ma_ncc='NCC-VN-APPLE').first()
    if supplier is None:
        supplier = suppliers.filter(ten_ncc__iexact='Apple').first()
    if supplier is None:
        supplier = suppliers.create(
            ma_ncc='NCC-VN-APPLE',
            ten_ncc='Apple',
        )

    unit = unit_model.objects.using(database).filter(
        ten_dvt='Cái'
    ).first()

    for product_code, product_name in APPLE_PRODUCTS:
        product, _ = product_model.objects.using(database).get_or_create(
            ma_hang=product_code,
            defaults={
                'ten_hang': product_name,
                'don_vi_tinh_id': unit.pk if unit else None,
                'so_luong_ton': 0,
                'ton_toi_thieu': 5,
                'gia_nhap': 0,
                'gia_xuat': 0,
            },
        )
        supplier.hang_hoa.add(product)


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0014_nhacungcap_hang_hoa'),
    ]

    operations = [
        migrations.RunPython(add_apple_supplier, migrations.RunPython.noop),
    ]
