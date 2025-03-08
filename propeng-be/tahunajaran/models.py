from django.db import models

class TahunAjaran(models.Model):
    tahunAjaran = models.IntegerField(unique=True, null=False, blank=False, default=2025)


    def __str__(self):
        return str(self.tahunAjaran)