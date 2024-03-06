# Generated by Django 5.0.3 on 2024-03-06 19:59

import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cerberus", "0057_alter_contact_details_alter_invoice_customer_name_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="length",
            field=models.GeneratedField(
                db_persist=True,
                expression=django.db.models.expressions.CombinedExpression(
                    models.F("end"), "-", models.F("start")
                ),
                output_field=models.DurationField(),
            ),
        ),
    ]
