# Generated by Django 5.0.3 on 2024-03-27 08:31

from django.db import migrations, models

def set_pets_from_pet(apps, schema_editor):
    Booking = apps.get_model('cerberus', 'Booking')
    for booking in Booking.objects.only('pet', 'pets').all():
        booking.pets.set([booking.pet])
        booking.save()

class Migration(migrations.Migration):

    dependencies = [
        ("cerberus", "0067_booking_customer"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="pets",
            field=models.ManyToManyField(to="cerberus.pet"),
        ),
        migrations.RunPython(set_pets_from_pet),
    ]