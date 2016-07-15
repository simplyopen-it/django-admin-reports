from django.apps import AppConfig


class AdminReportConfig(AppConfig):
    name = 'admin_reports'

    def ready(self):
        self.module.autodiscover()
