from django.utils.module_loading import autodiscover_modules
from .decorators import register
from .sites import AdminReportSite, site
from .reports import Report

__version__ = '0.10.8'
__all__ = ["register", "AdminReportSite", "site", "Report"]


def autodiscover():
    autodiscover_modules('reports', register_to=site)


default_app_config = 'admin_reports.apps.AdminReportConfig'
