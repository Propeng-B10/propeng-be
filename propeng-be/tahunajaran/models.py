from django.db import models

class TahunAjaran(models.Model):
    tahunAjaran = models.IntegerField(unique=True, null=True)