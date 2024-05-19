# Generated by Django 5.0.6 on 2024-05-17 07:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mvp', '0005_alter_parkingfee_fee_per_hour'),
    ]

    operations = [
        migrations.AddField(
            model_name='checkinout',
            name='vehicle_type',
            field=models.CharField(choices=[('Car', 'Car'), ('Motorbike', 'Motorbike'), ('Bicycle', 'Bicycle')], default='Car', max_length=20),
            preserve_default=False,
        ),
    ]
