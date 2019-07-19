try:
    from .decorators import register
    from .reports import Report
    from .sites import site
except ImportError:
    pass
else:
    __all__ = ["register", "Report", "site"]

__version__ = '0.10.8'
default_app_config = 'admin_reports.apps.AdminReportConfig'
