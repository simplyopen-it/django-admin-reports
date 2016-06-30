====================
django-admin-reports
====================

Overview
########

"admin_reports" is a Django application to easily create data
aggregation reports to display inside Django admin.

The Django admin is very much centered on models and it provide a
quick and simple way to create a GUI for the CRUD interface, but
often there's the need to display data in an aggregate form, here's
where admin_reports comes handy.

The idea is to have a class similar to ``ModelAdmin`` (from
``django.contrib.admin``) that allow to display derived data
concentrating on implementing the aggregation procedure.

Usage
#####

Basically admin_reports provide you Django site with an abstract view
``Report``. All you need to do is give an implementation to the
abstract method ``aggregate()``. The important thing is that this
method must return a list of dictionaries, a Queryset or a
``pandas.Dataframe`` (https://github.com/pydata/pandas).

A stupid example could be this:
::
   class MyReport(Report):
       def aggregate(self, **kwargs):
           return [
               dict([(k, v) for v, k in enumerate('abcdefgh')]),
               dict([(k, v) for v, k in enumerate('abcdefgh')]),
            ]

At the moment admin-reports does not provide a ``register`` function
like ``django.contrib.admin`` does (but it will), so you'll have to
add the urlpattern yourself to you urls.py.
::
   from admin_reports.views import ReportView

   url(r'^reports/my-report$',
       ReportView.as_view(report_class=reports.MyReport),
       name="my_report")
