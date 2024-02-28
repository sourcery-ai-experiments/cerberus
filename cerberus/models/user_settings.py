# Standard Library

# Django
from django.contrib.auth.models import User
from django.db import models


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ui_settings = models.JSONField(default=dict)

    def __str__(self) -> str:
        return f"UserSettings for {self.user.username}"
