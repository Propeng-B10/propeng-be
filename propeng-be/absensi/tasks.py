from celery import shared_task
from django.utils import timezone
from .models import AbsenHarian

@shared_task
def delete_expired_kodes():
    AbsenHarian.objects.filter(expiry_time__lt=timezone.now()).update(kode=None)