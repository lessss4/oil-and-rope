# Generated by Django 2.2.2 on 2019-08-15 23:59

from django.db import migrations, models
import registration.models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0002_auto_20190807_1329'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=registration.models.user_directory_path, verbose_name='Avatar'),
        ),
    ]
