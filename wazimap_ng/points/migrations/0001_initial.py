# Generated by Django 2.2.8 on 2020-01-10 18:05

import django.contrib.gis.db.models.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('coordinates', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField()),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='locations', to='points.Category')),
            ],
        ),
    ]