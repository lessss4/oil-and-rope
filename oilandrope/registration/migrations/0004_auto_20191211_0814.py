# Generated by Django 2.2.2 on 2019-12-11 08:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0003_auto_20190815_2359'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profile',
            options={'ordering': ['user__username', 'user__first_name'], 'verbose_name': 'Profile', 'verbose_name_plural': 'Profiles'},
        ),
    ]