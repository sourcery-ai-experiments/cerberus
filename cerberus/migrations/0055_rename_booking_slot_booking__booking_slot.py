# Generated by Django 5.0.1 on 2024-02-11 19:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("cerberus", "0054_alter_customer_options_alter_customer_vet_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="booking",
            old_name="booking_slot",
            new_name="_booking_slot",
        ),
    ]
