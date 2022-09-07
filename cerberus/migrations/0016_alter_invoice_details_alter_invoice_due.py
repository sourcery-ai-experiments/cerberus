# Generated by Django 4.0.5 on 2022-06-26 20:17

import cerberus.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cerberus', '0015_alter_charge_content_type_alter_charge_object_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='details',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='due',
            field=models.DateField(default=cerberus.models.get_default_due_date),
        ),
    ]