# Generated by Django 5.0.2 on 2024-02-21 19:45

import django.db.models.deletion
import django_fsm
import djmoney.models.fields
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cerberus", "0055_rename_booking_slot_booking__booking_slot"),
    ]

    operations = [
        migrations.AddField(
            model_name="charge",
            name="parent_charge",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="child_charges",
                to="cerberus.charge",
            ),
        ),
        migrations.AlterField(
            model_name="charge",
            name="line",
            field=djmoney.models.fields.MoneyField(decimal_places=2, max_digits=14),
        ),
        migrations.AlterField(
            model_name="charge",
            name="state",
            field=django_fsm.FSMField(
                choices=[("unpaid", "Unpaid"), ("paid", "Paid"), ("void", "Void"), ("refund", "Refund")],
                default="unpaid",
                max_length=50,
                protected=True,
            ),
        ),
        migrations.AlterField(
            model_name="service",
            name="cost",
            field=djmoney.models.fields.MoneyField(decimal_places=2, max_digits=14),
        ),
        migrations.AlterField(
            model_name="service",
            name="cost_per_additional",
            field=djmoney.models.fields.MoneyField(decimal_places=2, default=Decimal("0.0"), max_digits=14),
        ),
    ]
