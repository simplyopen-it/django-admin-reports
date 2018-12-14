from django.utils.module_loading import autodiscover_modules

__version__ = "0.11.0"
__all__ = ["register", "AdminReportSite", "site", "Report", "sites", "decorators"]


def autodiscover():
    from .decorators import register
    from .sites import AdminReportSite, site
    from .reports import Report

    autodiscover_modules("reports", register_to=site)


default_app_config = "admin_reports.apps.AdminReportConfig"
