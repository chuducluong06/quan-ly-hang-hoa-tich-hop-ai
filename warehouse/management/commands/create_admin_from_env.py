from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError

from warehouse.models import NguoiDung


class Command(BaseCommand):
    help = 'Create or update the application admin using credentials from .env.'

    def handle(self, *args, **options):
        username = settings.ADMIN_USERNAME
        password = settings.ADMIN_PASSWORD

        if not username or not password:
            raise CommandError(
                'Set both ADMIN_USERNAME and ADMIN_PASSWORD in .env before '
                'running this command.'
            )

        user = NguoiDung.objects.filter(ten_dang_nhap=username).first()
        if user and user.role != 'ADMIN':
            raise CommandError(
                f'The account "{username}" already exists and is not an admin.'
            )

        if user is None:
            user = NguoiDung(ten_dang_nhap=username)
            action = 'Created'
        else:
            action = 'Updated'

        user.password_hash = make_password(password)
        user.role = 'ADMIN'
        user.is_active = True
        user.save()

        self.stdout.write(
            self.style.SUCCESS(f'{action} admin account "{username}".')
        )
