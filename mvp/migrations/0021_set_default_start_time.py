# Generated by Django 5.0.6 on 2024-05-20 06:08
from django.db import migrations, models
def set_default_start_time(apps, schema_editor):
    InOut = apps.get_model('mvp', 'InOut')
    for inout in InOut.objects.filter(start_time__isnull=True):
        inout.start_time = '00:00:00'  # Set your desired default time here
        inout.save()

class Migration(migrations.Migration):

    dependencies = [
        ('mvp', '0015_rename_time_inout_start_time_inout_end_time'),  # Replace with the actual previous migration file
    ]

    operations = [
        migrations.RunPython(set_default_start_time),
    ]