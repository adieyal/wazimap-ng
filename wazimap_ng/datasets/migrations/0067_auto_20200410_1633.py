# Generated by Django 2.2.10 on 2020-04-10 16:33

import django.contrib.postgres.fields.jsonb
import django.core.validators
from django.db import migrations, models
import wazimap_ng.datasets.models.upload


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0066_auto_20200409_0418'),
    ]

    operations = [
        migrations.AlterField(
            model_name='indicator',
            name='subindicators',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=list, null=True),
        ),
        migrations.AlterField(
            model_name='profilehighlight',
            name='subindicator',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profileindicator',
            name='subindicators',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=list),
        ),
    ]
