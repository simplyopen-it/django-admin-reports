.. image:: https://img.shields.io/pypi/v/admin_reports.svg
   :target: https://pypi.python.org/pypi/admin_reports

====================
django-admin-reports
====================

Overview
********

"admin_reports" is a Django application to easily create data
aggregation reports to display inside Django admin.

The Django admin is very much centered on models and it provide a
quick and simple way to create a GUI for the CRUD interface, but
often there's the need to display data in an aggregate form, here's
where admin_reports comes handy.

The idea is to have a class similar to ``ModelAdmin`` (from
``django.contrib.admin``) that allow to display derived data
concentrating on implementing the aggregation procedure.

Basic Usage
***********

Basically admin_reports provide your Django site with an abstract view
``Report``. All you need to do is give an implementation to the
abstract method ``aggregate()``. The important thing is that this
method must return a list of dictionaries, a Queryset or a
``pandas.Dataframe`` (https://github.com/pydata/pandas).

A stupid example could be this: ::

  from admin_reports import Report, register

  @register()
  class MyReport(Report):
      def aggregate(self, **kwargs):
          return [
              dict([(k, v) for v, k in enumerate('abcdefgh')]),
              dict([(k, v) for v, k in enumerate('abcdefgh')]),
          ]


Then in your django site ``urls.py`` add the following: ::

  from django.contrib import admin
  import admin_reports

  urlpatterns = patterns(
      ...
      url(r^admin/', include(admin.site.urls)),
      url(r'^admin/', include(admin_reports.site.urls)),
      ...
  )

The auto generate urls will be a lowercase version of
your class name.

So for the example above::

  /admin/myapp/myreport

The urlname to be passed to ``reverse`` will be the underscored
version of your class name, so with the above example::

  'admin_reports:my_report'


Passing parameters to ``aggregate``
===================================

Most of the times you'll need to pass parameters to ``aggregate``, you
can do so by the association of a Form class to your Report: all the
form fields will be passed to ``aggregate`` as keyword arguments, then
it's up to you what do with them.::

  from django import forms
  from admin_reports import Report


  class MyReportForm(forms.Form):
      from_date = forms.DateField(label="From")
      to_date = forms.DateField(label="To")


  class MyReport(Report):
      form_class = MyReportForm

      def aggregate(self, from_date=None, to_date=None, **kwargs):
          # Write yout aggregation here
          return ret


The Report class
****************

The ``Report`` class is projected to be flexible and let you modify
various aspect of the final report.

Attributes
==========

As for the ``ModelAdmin`` the most straightforward way of changing the
behavior of your subclasses is to override the public class
attributes; anyway for each of these attributes there is a
``get_<attr>`` method hook to override in order to alter behaviors at
run-time.

Report.fields
-------------

This is a list of field names that you want to be used as columns in
your report, the default is ``None`` and means that the ``get_fields``
method will try to guess them from the results of your ``aggregate``
implementation.

The ``fields`` attribute can contain names of callables. This
methods are supposed to receive a record of the report as a
parameter.::

  class MyReport(Report):

      fields = [
          ...,
          'pretty_value',
          ...
      ]

      def pretty_value(self, record):
          return do_something_fancy_with(record['my_column'])

For this callables the ``allow_tags`` attribute can be set to ``True``
if they are supposed to return an HTML string.

Fields labels
^^^^^^^^^^^^^

When a field name is provided alone in the ``fields`` attribute
``admin_reports`` will generate a label for you in the rendered
table. If you want to provide a custom label just enter a tuple of two
elements instead of just the field name, ``(field_name, label)``.

Report.formatting
-----------------

The ``formatting`` attribute is a dictionary that lets you specify the
formatting function to use for each field.::

  class MyReport(Report):

      formatting = {
          'amount': lambda x: format(x, ',.2f'),
      }

Report.has_totals
-----------------

This attribute is a boolean to tell whether the last record of your
aggregation is to be considered as a row of totals, in this case it
will be displayed highlighted on every page.

Report.totals_on_top
--------------------

Whether to display an eventual record of totals in on top of the
table, if ``False`` it will be displayed on bottom.

This attribute has no effect if ``Report.has_totals`` is ``False``.

Report.title
------------

A string to use as the page title.

Report.description
------------------

A short description to explain the meaning of the report.

Report.help_text
----------------

A longer description of the report, meant to explain the meaning of
each single field.

Report.template_name
--------------------

The template to use to render the report as an html page (default:
``admin/report.html``).

Report.paginator
----------------

The class to use a ``Paginator``.

Report.list_per_page
--------------------

``list_per_page`` parameter passed to the ``Paginator`` class.

Report.list_max_show_all
------------------------

``list_max_show_all`` parameter passed to the ``Paginator`` class.

Report.alignment
----------------

How to align values in columns when rendering the html table, a
dictionary that associates to each field one of the following values
(``aling-left``, ``align-center``, ``align-right``).

Report.form_class
-----------------

The ``Form`` class to use to pass parameter to the ``aggregate`` method.

Report.export_form_class
------------------------

The ``Form`` class to use to pass parameter to the ``to_csv`` method.

Report.initial
--------------

Initial values for the ``form_class``.
