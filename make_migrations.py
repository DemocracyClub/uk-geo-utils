import django
from django.conf import settings
from django.core.management import call_command

if not settings.configured:
    settings.configure(DEBUG=True, INSTALLED_APPS=("uk_geo_utils",))

django.setup()
call_command("makemigrations", "uk_geo_utils")
