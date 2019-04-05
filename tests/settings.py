# -*- coding: utf-8
from __future__ import unicode_literals, absolute_import

import django

DEBUG = True
USE_TZ = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "o(-0r0xm6uklh0%+yl2te#+=dhqmq1st5yx)u!)$zo2=!1j(sc"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ROOT_URLCONF = "tests.urls"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "django_grpc",
]

SITE_ID = 1

if django.VERSION >= (1, 10):
    MIDDLEWARE = ()
else:
    MIDDLEWARE_CLASSES = ()


INSTALLED_APPS = [
    'django_grpc',
    'tests.sampleapp',
]

GRPCSERVER = {
    'servicers': ('tests.sampleapp.utils.register_servicer',),
}
