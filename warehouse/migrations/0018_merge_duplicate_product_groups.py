from django.db import migrations


def merge_duplicate_groups(apps, schema_editor):
    group_model = apps.get_model('warehouse', 'NhomHang')
    product_model = apps.get_model('warehouse', 'HangHoa')
    database = schema_editor.connection.alias

    groups_by_name = {}
    for group in group_model.objects.using(database).order_by('pk'):
        normalized_name = group.ten_nhom.casefold()
        primary_group = groups_by_name.get(normalized_name)
        if primary_group is None:
            groups_by_name[normalized_name] = group
            continue

        product_model.objects.using(database).filter(
            nhom_hang_id=group.pk,
        ).update(nhom_hang_id=primary_group.pk)
        group.delete(using=database)


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0017_seed_product_groups_and_catalog'),
    ]

    operations = [
        migrations.RunPython(merge_duplicate_groups, migrations.RunPython.noop),
    ]
