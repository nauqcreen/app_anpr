# Generated by Django 5.0.6 on 2024-05-20 02:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mvp', '0010_checkin'),
    ]

    operations = [
        migrations.AddField(
            model_name='checkin',
            name='check_out_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
