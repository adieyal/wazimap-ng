# Generated by Django 2.2.10 on 2020-05-07 03:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('points', '0023_auto_20200509_2036'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profilecategory',
            name='permission_type',
            field=models.CharField(choices=[('private', 'Private'), ('public', 'Public')], default='public', max_length=32),
        ),
    ]
