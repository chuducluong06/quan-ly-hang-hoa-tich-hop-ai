from django.db import migrations


COMMON_UNITS = [
    ('Cái', 'Đơn vị đếm cho sản phẩm thông dụng.'),
    ('Chiếc', 'Đơn vị đếm cho từng sản phẩm riêng lẻ.'),
    ('Bộ', 'Nhóm sản phẩm được bán hoặc quản lý theo bộ.'),
    ('Đôi', 'Đơn vị đếm cho sản phẩm gồm hai chiếc.'),
    ('Hộp', 'Sản phẩm được đóng gói theo hộp.'),
    ('Thùng', 'Sản phẩm được đóng gói theo thùng.'),
    ('Gói', 'Sản phẩm được đóng gói theo gói.'),
    ('Bao', 'Sản phẩm được đóng gói theo bao.'),
    ('Chai', 'Chất lỏng hoặc sản phẩm được đóng chai.'),
    ('Lọ', 'Sản phẩm được đóng trong lọ.'),
    ('Cuộn', 'Vật liệu được đóng hoặc bán theo cuộn.'),
    ('Tấm', 'Vật liệu được quản lý theo tấm.'),
    ('Thanh', 'Vật liệu dạng thanh.'),
    ('Cây', 'Vật liệu hoặc sản phẩm dạng cây.'),
    ('Mét', 'Đơn vị đo chiều dài.'),
    ('Kilogram (kg)', 'Đơn vị đo khối lượng bằng kilogram.'),
    ('Gram (g)', 'Đơn vị đo khối lượng bằng gram.'),
    ('Tấn', 'Đơn vị đo khối lượng bằng tấn.'),
    ('Lít', 'Đơn vị đo thể tích bằng lít.'),
    ('Mililit (ml)', 'Đơn vị đo thể tích bằng mililit.'),
    ('Pallet', 'Hàng hóa được quản lý theo pallet.'),
]


def add_common_units(apps, schema_editor):
    don_vi_tinh = apps.get_model('warehouse', 'DonViTinh')
    for ten_dvt, mo_ta in COMMON_UNITS:
        don_vi_tinh.objects.using(schema_editor.connection.alias).get_or_create(
            ten_dvt=ten_dvt,
            defaults={'mo_ta': mo_ta},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0011_alter_phieukho_options_alter_phieukho_nguoi_lap_and_more'),
    ]

    operations = [
        migrations.RunPython(add_common_units, migrations.RunPython.noop),
    ]
