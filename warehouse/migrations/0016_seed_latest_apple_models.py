from django.db import migrations


LATEST_APPLE_PRODUCTS = [
    ('APPLE-IPHONE-18-PRO', 'Apple iPhone 18 Pro'),
    ('APPLE-IPHONE-18-PRO-MAX', 'Apple iPhone 18 Pro Max'),
    ('APPLE-IPHONE-DUO', 'Apple iPhone Duo'),
    ('APPLE-IPAD-PRO-M5-11', 'Apple iPad Pro 11 inch M5'),
    ('APPLE-IPAD-PRO-M5-13', 'Apple iPad Pro 13 inch M5'),
    ('APPLE-IPAD-AIR-M4-11', 'Apple iPad Air 11 inch M4'),
    ('APPLE-IPAD-AIR-M4-13', 'Apple iPad Air 13 inch M4'),
    ('APPLE-MACBOOK-AIR-M5-13', 'Apple MacBook Air 13 inch M5'),
    ('APPLE-MACBOOK-AIR-M5-15', 'Apple MacBook Air 15 inch M5'),
    ('APPLE-MACBOOK-PRO-M5-14', 'Apple MacBook Pro 14 inch M5'),
    ('APPLE-MACBOOK-PRO-M5-16', 'Apple MacBook Pro 16 inch M5'),
    ('APPLE-WATCH-SERIES-12', 'Apple Watch Series 12'),
    ('APPLE-WATCH-ULTRA-4', 'Apple Watch Ultra 4'),
    ('APPLE-WATCH-SE-3', 'Apple Watch SE 3'),
    ('APPLE-AIRPODS-5', 'Apple AirPods 5'),
    ('APPLE-AIRPODS-PRO-3', 'Apple AirPods Pro 3'),
    ('APPLE-AIRPODS-MAX-2', 'Apple AirPods Max 2'),
]


def add_latest_apple_models(apps, schema_editor):
    supplier_model = apps.get_model('warehouse', 'NhaCungCap')
    product_model = apps.get_model('warehouse', 'HangHoa')
    unit_model = apps.get_model('warehouse', 'DonViTinh')
    database = schema_editor.connection.alias

    supplier = supplier_model.objects.using(database).filter(
        ma_ncc='NCC-VN-APPLE',
    ).first()
    if supplier is None:
        supplier = supplier_model.objects.using(database).filter(
            ten_ncc__iexact='Apple',
        ).first()
    if supplier is None:
        return

    unit = unit_model.objects.using(database).filter(ten_dvt='Cái').first()

    for product_code, product_name in LATEST_APPLE_PRODUCTS:
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
        ('warehouse', '0015_seed_apple_supplier'),
    ]

    operations = [
        migrations.RunPython(add_latest_apple_models, migrations.RunPython.noop),
    ]
