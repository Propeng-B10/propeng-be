from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from user.models import *
from tahunajaran.models import *
from kelas.models import *


class Command(BaseCommand):
    help = 'Creates a superuser account with predefined credentials'

    def handle(self, *args, **options):
        username = 'adminNext'
        email = 'admin@example.com'
        password = 'testpass1234'

        try:
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'User "{username}" already exists'))
                return

            # Create superuser
            admin = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                role='admin'  # Make sure the user has admin role
            )

            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser "{username}"'))
            self.stdout.write(self.style.SUCCESS('Username: adminNext'))
            self.stdout.write(self.style.SUCCESS('Password: testpass1234'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {str(e)}'))