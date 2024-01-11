# Standard Library
import contextlib
import os

# Third Party
import dj_database_url

# Locals
from .base import *  # noqa
from .base import DATABASES, MIDDLEWARE

DEBUG = False

env = os.environ.copy()

ALLOWED_HOSTS = env["ALLOWED_HOSTS"]

BASE_URL = env["BASE_URL"]

CSRF_TRUSTED_ORIGINS = [
    BASE_URL,
]

DATABASES["default"] = dict(dj_database_url.config())

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECRET_KEY = env["SECRET_KEY"]

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MIDDLEWARE += [
    "whitenoise.middleware.WhiteNoiseMiddleware",
]


with contextlib.suppress(KeyError):
    EMAIL_HOST = env["SMTP_HOST"]
    EMAIL_HOST_USER = env["SMTP_USER"]
    EMAIL_HOST_PASSWORD = env["SMTP_PASS"]
    EMAIL_PORT = env["SMTP_PORT"]
    EMAIL_USE_TLS = (env["SMTP_TLS"] or "True") != "False"
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "default",
    },
    "renditions": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "renditions",
    },
}
