import os
from django.conf import settings
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trend.settings")

app = Celery("trend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(
    # TODO update the packages we used to import
    # packages=["contrib", "notifications",],
    lambda: settings.INSTALLED_APPS,
    related_name="tasks",
)
