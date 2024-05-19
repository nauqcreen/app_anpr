# Generated by Django 5.0.6 on 2024-05-17 07:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mvp', '0004_parkingfee'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parkingfee',
            name='fee_per_hour',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
    ]
