# Generated by Django 5.1.6 on 2025-05-21 11:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('evalguru', '0001_initial'),
        ('matapelajaran', '0001_initial'),
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='evalguru',
            name='guru',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evalguru_guru', to='user.teacher'),
        ),
        migrations.AddField(
            model_name='evalguru',
            name='matapelajaran',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evalguru_matapelajaran', to='matapelajaran.matapelajaran'),
        ),
        migrations.AddField(
            model_name='evalguru',
            name='siswa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evalguru_siswa', to='user.student'),
        ),
        migrations.AddField(
            model_name='isianevalguru',
            name='guru',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='isianEvalGuru_guru', to='user.teacher'),
        ),
        migrations.AddField(
            model_name='isianevalguru',
            name='matapelajaran',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='isianEvalGuru_matapelajaran', to='matapelajaran.matapelajaran'),
        ),
        migrations.AddField(
            model_name='isianevalguru',
            name='siswa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='isianEvalGuru_siswa', to='user.student'),
        ),
    ]
