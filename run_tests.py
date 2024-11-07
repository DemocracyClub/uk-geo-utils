#!/usr/bin/env python
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def root(*x):
    return os.path.join(BASE_DIR, *x)


if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            "default": {
                "ENGINE": "django.contrib.gis.db.backends.postgis",
                "NAME": "test",
                "USER": "postgres",
                "PASSWORD": "",
                "HOST": "localhost",
                "PORT": "",
            },
            "other": {
                "ENGINE": "django.contrib.gis.db.backends.postgis",
                "NAME": "test_other",
                "USER": "postgres",
                "PASSWORD": "",
                "HOST": "localhost",
                "PORT": "",
            },
        },
        INSTALLED_APPS=("uk_geo_utils",),
    )

django.setup()
TestRunner = get_runner(settings)
test_runner = TestRunner(verbosity=1, interactive=True, failfast=False)
failures = test_runner.run_tests(["uk_geo_utils"])
sys.exit(failures)
