# Generated by Django 2.2.9 on 2019-12-20 13:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='indicators',
        ),
    ]