====================
django-admin-reports
====================

Overview
########

"admin_reports" is a Django application to easily create data
aggregation reports to display inside Django admin.

The Django admin is very much centered on models and it provide a
quick and simple way to create a GUI for the CRUD interface, but
ofthen there's the need to display data in an aggregate form, here's
where admin_reports comes handy.

Usage
#####

Basically admin_reports provide you Django site with an abstract view
``ReportView``. All you need to do is give an implementation to the
abstract method ``aggregate()``. The important thing is that this
method must return a list of dictionaries, a Queryset or a
``pandas.Dataframe`` (https://github.com/pydata/pandas).

A stupid example could be this:
::
   class MyReport(ReportView):
       def aggregate(self, **kwargs):
           return [
               dict([(k, v) for v, k in enumerate('abcdefgh')]),
               dict([(k, v) for v, k in enumerate('abcdefgh')]),
            ]
