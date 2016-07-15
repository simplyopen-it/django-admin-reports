# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict
from django import forms
from django.conf import settings
from django.core.paginator import InvalidPage
from django.core.exceptions import PermissionDenied
from django.views.generic.edit import FormMixin
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.template.context import RequestContext
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.utils.html import format_html
from django.shortcuts import render_to_response
from django.contrib.admin.templatetags.admin_static import static
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin import site

admin_view_m = method_decorator(site.admin_view)
ALL_VAR = 'all'
ORDER_VAR = 'o'
PAGE_VAR = 'p'
EXPORT_VAR = 'e'
CONTROL_VARS = [ALL_VAR, ORDER_VAR, PAGE_VAR, EXPORT_VAR]


class ReportList(object):

    def __init__(self, request, report):
        self.request = request
        self.report = report
        self.params = dict(self.request.GET.items())
        self.ordering_field_columns = self._get_ordering_field_columns()
        self.report.set_sort_params(*self._get_ordering())
        self.multi_page = False
        self.can_show_all = True
        self.paginator = self.report.get_paginator()
        try:
            self.page_num = int(self.request.GET.get(PAGE_VAR, 0))
        except ValueError:
            self.page_num = 0
        self.show_all = ALL_VAR in self.request.GET

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

    def _get_ordering(self):
        ordering = []
        if ORDER_VAR in self.params:
            sort_values = self.params.get(ORDER_VAR).split('.')
            fields = self.report.get_fields()
            for o in sort_values:
                if o.startswith('-'):
                    field = '-%s' % fields[int(o.replace('-', ''))][0]
                else:
                    field = fields[int(o)][0]
                ordering.append(field)
        return ordering

    def _get_ordering_field_columns(self):
        """
        Returns an OrderedDict of ordering field column numbers and asc/desc
        """
        # We must cope with more than one column having the same underlying sort
        # field, so we base things on column numbers.
        ordering = []
        ordering_fields = OrderedDict()
        if ORDER_VAR not in self.params:
            # for ordering specified on ModelAdmin or model Meta, we don't know
            # the right column numbers absolutely, because there might be more
            # than one column associated with that ordering, so we guess.
            for field in ordering:
                if field.startswith('-'):
                    field = field[1:]
                    order_type = 'desc'
                else:
                    order_type = 'asc'
                for index, attr in enumerate(self.list_display):
                    if self.get_ordering_field(attr) == field:
                        ordering_fields[index] = order_type
                        break
        else:
            for p in self.params[ORDER_VAR].split('.'):
                _, pfx, idx = p.rpartition('-')
                try:
                    idx = int(idx)
                except ValueError:
                    continue  # skip it
                ordering_fields[idx] = 'desc' if pfx == '-' else 'asc'
        return ordering_fields

    def headers(self):
        fields = self.report.get_fields()
        for i, field in enumerate(fields):
            name = field[0]
            label = field[1]
            if callable(getattr(self.report, name, name)):
                yield {
                    'label': label,
                    'class_attrib': format_html(' class="column-{0}"', name),
                    'sortable': False,
                }
                continue
            th_classes = ['sortable', 'column-{0}'.format(name)]
            order_type = ''
            new_order_type = 'asc'
            sort_priority = 0
            sorted_ = False
            # Is it currently being sorted on?
            if i in self.ordering_field_columns:
                sorted_ = True
                order_type = self.ordering_field_columns.get(i).lower()
                sort_priority = list(self.ordering_field_columns).index(i) + 1
                th_classes.append('sorted %sending' % order_type)
                new_order_type = {'asc': 'desc', 'desc': 'asc'}[order_type]
            # build new ordering param
            o_list_primary = []  # URL for making this field the primary sort
            o_list_remove = []  # URL for removing this field from sort
            o_list_toggle = []  # URL for toggling order type for this field
            make_qs_param = lambda t, n: ('-' if t == 'desc' else '') + str(n)
            for j, ot in self.ordering_field_columns.items():
                if j == i:  # Same column
                    param = make_qs_param(new_order_type, j)
                    # We want clicking on this header to bring the ordering to the
                    # front
                    o_list_primary.insert(0, param)
                    o_list_toggle.append(param)
                    # o_list_remove - omit
                else:
                    param = make_qs_param(ot, j)
                    o_list_primary.append(param)
                    o_list_toggle.append(param)
                    o_list_remove.append(param)
            if i not in self.ordering_field_columns:
                o_list_primary.insert(0, make_qs_param(new_order_type, i))
            yield {
                "label": label,
                "sortable": True,
                "sorted": sorted_,
                "ascending": order_type == "asc",
                "sort_priority": sort_priority,
                "url_primary": self.get_query_string({ORDER_VAR: '.'.join(o_list_primary)}),
                "url_remove": self.get_query_string({ORDER_VAR: '.'.join(o_list_remove)}),
                "url_toggle": self.get_query_string({ORDER_VAR: '.'.join(o_list_toggle)}),
                "class_attrib": format_html(' class="{0}"', ' '.join(th_classes)) if th_classes else '',
            }

    @property
    def totals(self):
        fields = self.report.get_fields()
        for idx, value in enumerate(self.report.iter_totals()):
            yield (self.report.get_alignment(fields[idx][0]), value)

    @property
    def results(self):
        fields = self.report.get_fields()
        for record in self.paginate():
            yield [(self.report.get_alignment(fields[idx][0]), value) for idx, value in enumerate(record)]

    def get_result_count(self):
        return len(self.report)

    def paginate(self):
        records = self.report.results
        self.paginator = self.report.get_paginator()
        result_count = self.paginator.count
        self.multi_page = result_count > self.report.get_list_per_page()
        self.can_show_all = result_count <= self.report.get_list_max_show_all()
        if not (self.show_all and self.can_show_all) and self.multi_page:
            try:
                records = self.paginator.page(self.page_num + 1).object_list
            except InvalidPage:
                raise IncorrectLookupParameters
        return records


class ReportView(TemplateView, FormMixin):

    report_class = None

    @admin_view_m
    def dispatch(self, request, *args, **kwargs):
        return super(ReportView, self).dispatch(request, *args, **kwargs)

    def __init__(self, report_class, *args, **kwargs):
        super(ReportView, self).__init__(*args, **kwargs)
        self.report_class = report_class
        self.report = None

    def get_initial(self):
        initial = super(ReportView, self).get_initial()
        initial.update(self.report.get_initial())
        return initial

    @property
    def media(self):
        # taken from django.contrib.admin.options ModelAdmin
        extra = '' if settings.DEBUG else '.min'
        js = [
            'core.js',
            'admin/RelatedObjectLookups.js',
            'jquery%s.js' % extra,
            'jquery.init.js',
        ]
        return forms.Media(js=[static('admin/js/%s' % url) for url in js])

    def _export(self, form=None):
        if form is None:
            form = self.get_export_form()
        ctx = {
            'form': form,
            'back': '?%s' % '&'.join(['%s=%s' % param for param in self.request.GET.items()
                                      if param[0] != EXPORT_VAR]),
        }
        return render_to_response('admin/export.html', RequestContext(self.request, ctx))

    def post(self, *args, **kwargs):
        self.report = self.report_class()
        if not self.report.has_permission(self.request):
            raise PermissionDenied()
        form = self.get_export_form(data=self.request.POST)
        if form.is_valid():
            context = self.get_context_data(**kwargs)
            filename = context['title'].lower().replace(' ', '_')
            response =  HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment;filename="%s.csv"' % filename
            self.report.to_csv(response, **form.cleaned_data)
            return response
        return self._export(form=form)

    def get(self, request, *args, **kwargs):
        self.report = self.report_class()
        if not self.report.has_permission(request):
            raise PermissionDenied()
        if EXPORT_VAR in request.GET:
            return self._export()
        return super(ReportView, self).get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ReportView, self).get_form_kwargs()
        if self.request.method in ('GET', 'POST'):
            form_data = dict([(key, val) for key, val in self.request.GET.iteritems()
                              if key not in CONTROL_VARS])
            if form_data:
                kwargs.update({
                    'data': form_data,
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

    def get_form_class(self):
        return self.report_class.form_class

    def get_context_data(self, **kwargs):
        kwargs = super(ReportView, self).get_context_data(**kwargs)
        kwargs['media'] = self.media
        export_path = '?%s' % '&'.join(['%s=%s' % item for item in self.request.GET.iteritems()] + [EXPORT_VAR])
        form = self.get_form(self.get_form_class())
        if form is not None:
            if 'form' not in kwargs:
                kwargs['form'] = form
            if form.is_valid():
                self.report.set_params(**form.cleaned_data)
        kwargs.update({
            'rl': ReportList(self.request, self.report),
            'title': self.report.get_title(),
            'has_filters': self.get_form_class() is not None,
            'help_text': self.report.get_help_text(),
            'description': self.report.get_description(),
            'export_path': export_path,
            'totals': self.report.get_has_totals(),
            'totals_on_top': self.report.totals_on_top,
            'suit': 'suit' in settings.INSTALLED_APPS,
        })
        return kwargs

    def get_template_names(self):
        return self.report.template_name

    def get_export_form(self, form_class=None, **kwargs):
        if form_class is None:
            form_class = self.report.get_export_form_class()
        return form_class(**kwargs)
