# Generated by Django 5.1.6 on 2025-03-08 00:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_student_tahun_ajaran'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='name',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='student',
            name='username',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='teacher',
            name='name',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='teacher',
            name='username',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
    ]
