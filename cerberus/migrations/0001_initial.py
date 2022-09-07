# Generated by Django 4.0.5 on 2022-06-03 20:50

import cerberus.models
from django.db import migrations, models
import django.db.models.deletion
import django_fsm


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Booking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                ("cost", models.IntegerField()),
                ("start", models.DateTimeField()),
                ("end", models.DateTimeField()),
                (
                    "state",
                    django_fsm.FSMField(
                        choices=[
                            ("enquiry", "enquiry"),
                            ("preliminary", "preliminary"),
                            ("confirmed", "confirmed"),
                            ("canceled", "canceled"),
                            ("completed", "completed"),
                        ],
                        default="preliminary",
                        max_length=50,
                        protected=True,
                    ),
                ),
            ],
            options={
                "ordering": ("-created",),
            },
        ),
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("active", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ("-created",),
            },
        ),
        migrations.CreateModel(
            name="Service",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("length", models.DurationField(blank=True, null=True)),
                ("booked_length", models.DurationField(blank=True, null=True)),
                ("cost", models.IntegerField(blank=True, null=True)),
                ("cost_per_additional", models.IntegerField(blank=True, null=True)),
                ("max_pet", models.IntegerField(blank=True, null=True)),
                ("max_customer", models.IntegerField(blank=True, null=True)),
                ("display_colour", models.CharField(max_length=255)),
            ],
            options={
                "ordering": ("-created",),
            },
        ),
        migrations.CreateModel(
            name="Vet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("phone", models.CharField(blank=True, max_length=128, null=True)),
                ("details", models.TextField(blank=True, default="")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="Pet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("dob", models.DateField(blank=True, null=True)),
                ("active", models.BooleanField(default=True)),
                (
                    "social_media_concent",
                    models.CharField(
                        choices=[("yes", "Yes"), ("no", "No"), ("annon", "Anonymous")], default="yes", max_length=5
                    ),
                ),
                (
                    "sex",
                    models.CharField(
                        choices=[(None, "(Unknown)"), ("male", "Male"), ("female", "Female")],
                        default="(Unknown)",
                        max_length=10,
                    ),
                ),
                ("description", models.TextField(blank=True, default="")),
                (
                    "neutered",
                    models.CharField(
                        choices=[(None, "(Unknown)"), ("yes", "Yes"), ("no", "No"), ("implant", "Implant")],
                        default="(Unknown)",
                        max_length=10,
                    ),
                ),
                ("medical_conditions", models.TextField(blank=True, default="")),
                ("treatment_limit", models.IntegerField(default=0)),
                ("allergies", models.TextField(blank=True, default="")),
                ("microchipped", models.BooleanField(default=True)),
                ("off_lead_consent", models.BooleanField(default=False)),
                ("vaccinated", models.BooleanField(default=True)),
                ("flead_wormed", models.BooleanField(default=False)),
                ("insured", models.BooleanField(default=False)),
                ("leucillin", models.BooleanField(default=True)),
                ("noise_sensitive", models.BooleanField(default=False)),
                (
                    "customer",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pets", to="cerberus.customer"),
                ),
                (
                    "vet",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="pets", to="cerberus.vet"
                    ),
                ),
            ],
            options={
                "ordering": ("name",),
            },
        ),
        migrations.AddField(
            model_name="customer",
            name="vet",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="customers", to="cerberus.vet"
            ),
        ),
        migrations.CreateModel(
            name="Contact",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("details", models.CharField(blank=True, max_length=255, null=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                (
                    "customer",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="contacts", to="cerberus.customer"),
                ),
            ],
            options={
                "ordering": ("-created",),
            },
        ),
        migrations.CreateModel(
            name="Charge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                ("cost", models.IntegerField()),
                ("due", models.DateTimeField(default=cerberus.models.get_default_due_date)),
                (
                    "state",
                    django_fsm.FSMField(
                        choices=[
                            ("unconfirmed", "unconfirmed"),
                            ("unpaid", "unpaid"),
                            ("overdue", "overdue"),
                            ("paid", "paid"),
                            ("void", "void"),
                        ],
                        default="unpaid",
                        max_length=50,
                        protected=True,
                    ),
                ),
                (
                    "booking",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="cerberus.booking"),
                ),
                ("customer", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="cerberus.customer")),
            ],
            options={
                "ordering": ("-created",),
            },
        ),
        migrations.CreateModel(
            name="BookingSlot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("start", models.DateTimeField()),
                ("end", models.DateTimeField()),
            ],
            options={
                "unique_together": {("start", "end")},
            },
        ),
        migrations.AddField(
            model_name="booking",
            name="booking_slot",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="bookings",
                to="cerberus.bookingslot",
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="pet",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="bookings", to="cerberus.pet"
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="service",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="bookings", to="cerberus.service"
            ),
        ),
        migrations.CreateModel(
            name="Address",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("address_line_1", models.CharField(blank=True, default="", max_length=100)),
                ("address_line_2", models.CharField(blank=True, default="", max_length=100)),
                ("address_line_3", models.CharField(blank=True, default="", max_length=100)),
                ("town", models.CharField(blank=True, default="", max_length=100)),
                ("county", models.CharField(blank=True, default="", max_length=100)),
                ("postcode", models.CharField(blank=True, default="", max_length=100)),
                (
                    "customer",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="addresss", to="cerberus.customer"),
                ),
            ],
            options={
                "ordering": ("-created",),
            },
        ),
    ]