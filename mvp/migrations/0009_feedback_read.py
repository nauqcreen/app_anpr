# Generated by Django 5.0.6 on 2024-05-18 11:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mvp', '0008_adminreply'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedback',
            name='read',
            field=models.BooleanField(default=False),
        ),
    ]
