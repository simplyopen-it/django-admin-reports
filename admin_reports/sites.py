from django.apps import apps
from django.conf.urls import url
from .views import ReportView
from .reports import Report, camel_re


class AlreadyRegistered(Exception):
    pass


class NotRegistered(Exception):
    pass


class AdminReportSite(object):

    def __init__(self, name='admin_reports'):
        self.name = name
        self._registry = []

    def register(self, report):
        if issubclass(report, Report):
            if report in self._registry:
                raise AlreadyRegistered('The report %s is already registered' % report.__name__)
            self._registry.append(report)

    def unregister(self, report):
        if issubclass(report, Report):
            if report not in self._registry:
                raise NotRegistered('The report %s is not registered' % report.__name__)
            self._registry.remove(report)

    def get_urls(self):
        urlpatterns = []

        for report in self._registry:
            app_name = apps.get_containing_app_config(report.__module__).name
            urlpatterns.append(
                url(r"^{0}/{1}/$".format(app_name.replace(".", "_"), report.__name__.lower()),
                    ReportView.as_view(report_class=report),
                    name=camel_re.sub(r'\1_\2', report.__name__).lower()
                ))
        return urlpatterns

    @property
    def urls(self):
        return self.get_urls(), 'admin_reports', self.name


site = AdminReportSite()
