# Generated by Django 5.0.6 on 2024-05-20 05:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mvp', '0016_alter_inout_start_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inout',
            name='start_time',
            field=models.TimeField(),
        ),
    ]