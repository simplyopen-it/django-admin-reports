import re
from django import forms
from django.conf import settings
from django.db.models import QuerySet
from django.core.paginator import Paginator, InvalidPage
from django.views.generic.edit import FormMixin
from django.views.generic import TemplateView
from django.contrib.admin.templatetags.admin_static import static
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin import site
from django.utils.safestring import mark_safe
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
try:
    from pandas import DataFrame
except ImportError:
    DataFrame = None

admin_view_m = method_decorator(site.admin_view)
ALL_VAR = 'all'
ORDER_VAR = 'o'
PAGE_VAR = 'p'
camel_re = re.compile('([a-z0-9])([A-Z])')


class ReportPaginator(Paginator):

    def _get_count(self):
        if DataFrame and isinstance(self.object_list, DataFrame):
            self._count = len(self.object_list)
        else:
            self._count = super(ReportPaginator, self)._get_count()
        return self._count
    count = property(_get_count)


class ReportList(object):

    def __init__(self, report_view, results):
        self.report_view = report_view
        self._results = results
        self.request = self.report_view.request
        self.params = dict(self.request.GET.items())
        self.paginator = self.report_view.get_paginator(self._results)
        self.list_per_page = self.report_view.get_list_per_page()
        self.list_max_show_all = self.report_view.get_list_max_show_all()
        try:
            self.page_num = int(self.request.GET.get(PAGE_VAR, 0))
        except ValueError:
            self.page_num = 0
        self.show_all = ALL_VAR in self.request.GET
        result_count = self.paginator.count
        self.multi_page = result_count > self.list_per_page
        self.can_show_all = result_count <= self.list_max_show_all
        self._fields = self.report_view.get_fields()
        if self._fields is None:
            if self._results:
                self._fields = self._results[0].keys()
            else:
                self._fields = []

    def get_query_string(self, new_params=None, remove=None):
        if new_params is None:
            new_params = {}
        if remove is None:
            remove = []
        p = self.params.copy()
        for r in remove:
            for k in list(p):
                if k.startswith(r):
                    del p[k]
        for k, v in new_params.items():
            if v is None:
                if k in p:
                    del p[k]
            else:
                p[k] = v
        return '?%s' % urlencode(sorted(p.items()))

    @property
    def fields(self):
        for field in self._fields:
            if isinstance(field, (list, tuple)):
                yield field
            else: # str, unicode
                yield (field, ' '.join([s.title() for s in field.split('_')]))

    def _items(self, record):
        for field, _ in self.fields:
            try:
                attr_field = getattr(self.report_view, field)
            except AttributeError:
                yield record.get(field)
            else:
                if callable(attr_field):
                    yield attr_field(record)

    @property
    def results(self):
        if (self.show_all and self.can_show_all) or not self.multi_page:
            results = self._results
        else:
            try:
                results = self.paginator.page(self.page_num + 1).object_list
            except InvalidPage:
                raise IncorrectLookupParameters
        if isinstance(results, QuerySet):
            records = results.values(*[field for field, _ in self.fields])
        elif DataFrame is not None and isinstance(self._results, DataFrame):
            records = results.reset_index().T.to_dict().values()
        else:
            records = results
        for record in iter(records):
            yield self._items(record)


class ReportView(TemplateView, FormMixin):
    template_name = 'admin/report.html'
    title = ''
    description = ''
    help_text = ''
    fields = None
    paginator = ReportPaginator
    list_per_page = 100
    list_max_show_all = 200

    @admin_view_m
    def dispatch(self, request, *args, **kwargs):
        return super(ReportView, self).dispatch(request, *args, **kwargs)

    @property
    def media(self):
        # taken from django.contrib.admin.options ModelAdmin
        extra = '' if settings.DEBUG else '.min'
        js = [
            'core.js',
            'admin/RelatedObjectLookups.js',
            'jquery%s.js' % extra,
            'jquery.init.js'
        ]
        return forms.Media(js=[static('admin/js/%s' % url) for url in js])

    def get_form_kwargs(self):
        kwargs = super(ReportView, self).get_form_kwargs()
        if self.request.method == 'GET':
            if self.request.GET:
                kwargs.update({
                    'data': self.request.GET,
                })
            else:
                kwargs.update({
                    'data': kwargs['initial']
                })
        return kwargs

    def get_form(self, form_class=None):
        if form_class is None:
            return None
        return super(ReportView, self).get_form(form_class)

    def get_context_data(self, **kwargs):
        kwargs = super(ReportView, self).get_context_data(**kwargs)
        kwargs['media'] = self.media
        kwargs.update({
            'title': self.get_title(),
            'has_filters': self.get_form_class() is not None,
            'help_text': self.get_help_text(),
            'description': self.get_description(),
        })
        form = self.get_form(self.get_form_class())
        if form is not None:
            if 'form' not in kwargs:
                kwargs['form'] = form
            if form.is_valid():
                results = self.aggregate(form)
        else:
            results = self.aggregate()
        kwargs.update({
            'rl': ReportList(self, results),
        })
        return kwargs

    def get_title(self):

        if not self.title:
            return camel_re.sub(r'\1 \2', self.__class__.__name__).capitalize()
        return self.title

    def get_fields(self):
        return self.fields

    def get_help_text(self):
        return mark_safe(self.help_text)

    def get_description(self):
        return mark_safe(self.description)

    def get_paginator(self, results):
        return self.paginator(results, self.get_list_per_page())

    def get_list_per_page(self):
        return self.list_per_page

    def get_list_max_show_all(self):
        return self.get_list_max_show_all

    def aggregate(self, form=None):
        ''' Implement here your data elaboration.
        Must return a list of dict.
        '''
        raise NotImplementedError('Subclasses must implement this method')
