from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules
from .sites import site


class AdminReportConfig(AppConfig):
    name = "admin_reports"

    def autodiscover(self):
        autodiscover_modules("reports", register_to=site)

    def ready(self):
        self.autodiscover()
