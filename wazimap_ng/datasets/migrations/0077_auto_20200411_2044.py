# Generated by Django 2.2.10 on 2020-04-11 20:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0076_auto_20200411_2035'),
    ]

    database_operations = [
        migrations.AlterModelTable('IndicatorCategory', 'profile_indicatorcategory'),  
    ]

    state_operations = [

    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=database_operations,
            state_operations=state_operations)
    ]
