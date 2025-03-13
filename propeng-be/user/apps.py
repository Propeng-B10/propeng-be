from django.apps import AppConfig
from django.db.models.signals import post_migrate

def ensure_admin_exists(sender, **kwargs):
    from django.contrib.auth.hashers import make_password
    from user.models import User
    
    if not User.objects.filter(username='adminNext').exists():
        User.objects.create(
            username='adminNext',
            email='admin@example.com',
            password=make_password('testpass1234'),
            role='admin',
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        print("Admin user 'adminNext' created successfully!")

class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user'

    def ready(self):
        post_migrate.connect(ensure_admin_exists, sender=self)
