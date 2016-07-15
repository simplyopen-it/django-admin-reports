from .decorators import register
from .sites import AdminReportSite, site
from .reports import Report

__all__ = ["register", "AdminReportSite", "site", "Report"]

__version__ = '0.10.0'
