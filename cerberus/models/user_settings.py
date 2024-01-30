# Standard Library

# Django
from django.contrib.auth.models import User
from django.db import models


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ui_settings = models.JSONField(default=dict)
