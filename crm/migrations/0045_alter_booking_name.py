# Generated by Django 4.0.5 on 2022-08-14 20:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0044_alter_customer_first_name_alter_customer_last_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='name',
            field=models.CharField(max_length=520),
        ),
    ]
