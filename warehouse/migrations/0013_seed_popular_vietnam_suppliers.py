from django.db import migrations


POPULAR_SUPPLIERS = [
    ('NCC-VN-VINAMILK', 'Vinamilk'),
    ('NCC-VN-TH', 'TH true MILK'),
    ('NCC-VN-MASAN', 'Masan Consumer'),
    ('NCC-VN-ACECOOK', 'Acecook Việt Nam'),
    ('NCC-VN-TANHI', 'Tân Hiệp Phát'),
    ('NCC-VN-SABECO', 'SABECO'),
    ('NCC-VN-HOAPHAT', 'Tập đoàn Hòa Phát'),
    ('NCC-VN-BINHMINH', 'Nhựa Bình Minh'),
    ('NCC-VN-THIENLONG', 'Thiên Long'),
    ('NCC-VN-DHG', 'Dược Hậu Giang (DHG Pharma)'),
    ('NCC-VN-FPT', 'FPT Trading'),
    ('NCC-VN-DUYTAN', 'Nhựa Duy Tân'),
    ('NCC-VN-UNILEVER', 'Unilever Việt Nam'),
    ('NCC-VN-SAMSUNG', 'Samsung Electronics Việt Nam'),
    ('NCC-VN-PG', 'P&G Việt Nam'),
    ('NCC-VN-RANGDONG', 'Bóng đèn phích nước Rạng Đông'),
    ('NCC-VN-VISSAN', 'VISSAN'),
    ('NCC-VN-VIETTIEN', 'May Việt Tiến'),
    ('NCC-VN-CHOLIMEX', 'Thực phẩm Cholimex'),
    ('NCC-VN-HOATHO', 'Dệt may Hòa Thọ'),
]


def add_popular_suppliers(apps, schema_editor):
    supplier_model = apps.get_model('warehouse', 'NhaCungCap')
    database = schema_editor.connection.alias

    for ma_ncc, ten_ncc in POPULAR_SUPPLIERS:
        suppliers = supplier_model.objects.using(database)
        if suppliers.filter(ten_ncc__iexact=ten_ncc).exists():
            continue
        if suppliers.filter(ma_ncc=ma_ncc).exists():
            continue

        suppliers.create(
            ma_ncc=ma_ncc,
            ten_ncc=ten_ncc,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0012_seed_common_units'),
    ]

    operations = [
        migrations.RunPython(add_popular_suppliers, migrations.RunPython.noop),
    ]
