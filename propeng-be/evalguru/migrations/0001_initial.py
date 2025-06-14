# Generated by Django 5.1.6 on 2025-05-21 11:38

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EvalGuru',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('variabel', models.PositiveIntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4)])),
                ('indikator', models.PositiveIntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8)])),
                ('skorlikert', models.PositiveIntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])),
                ('createdAt', models.DateTimeField(auto_now_add=True)),
                ('updatedAt', models.DateTimeField(auto_now=True)),
                ('kritik_saran', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='isianEvalGuru',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('isian', models.JSONField(default=dict)),
                ('createdAt', models.DateTimeField(auto_now_add=True)),
                ('updatedAt', models.DateTimeField(auto_now=True)),
                ('kritik_saran', models.TextField(blank=True, null=True)),
            ],
        ),
    ]
