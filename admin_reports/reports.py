# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db.models.query import QuerySet
from django.utils.safestring import mark_safe
from django.core.paginator import Paginator
import csv
import re
try:
    pnd = True
    from pandas import DataFrame
except ImportError:
    pnd = False
from .forms import ExportForm

camel_re = re.compile('([a-z0-9])([A-Z])')


class Report(object):
    fields = None
    formatting = None
    has_totals = False
    totals_on_top = False
    title = None
    description = ''
    help_text = ''
    template_name = 'admin/report.html'
    paginator = Paginator # ReportPaginator
    list_per_page = 100
    list_max_show_all = 200
    alignment = None
    form_class = None
    export_form_class = ExportForm
    initial = {}

    def __init__(self, sort_params=None, **kwargs):
        self._sort_params = sort_params if sort_params is not None else tuple()
        self._params = kwargs if kwargs else self.get_initial()
        self._data_type = 'list'
        self._results = []
        self._totals = {}
        self._evaluated = False
        self._sorted = False

    def __len__(self):
        if not self._evaluated:
            self._eval()
        if self._data_type == 'qs':
            return self._results.count()
        elif self._data_type == 'df':
            return self._results.index.size
        return len(self._results)

    def _split_totals(self, results):
        if self.has_totals and (len(results) > 0):
            if pnd and isinstance(results, DataFrame):
                self._results = results.iloc[:-1]
                self._totals = results.iloc[-1]
            else:
                self._results = results[:-1]
                self._totals = results[-1]
        else:
            self._results = results
            self._totals = {}

    def _sort_results(self):
        if self._data_type == 'qs':
            return self._results.order_by(*self._sort_params)
        elif self._data_type == 'df':
            columns = []
            ascending = []
            for param in self._sort_params:
                if param.startswith('-'):
                    ascending.append(0)
                    columns.append(param.replace('-', '', 1))
                else:
                    ascending.append(1)
                    columns.append(param)
            if columns:
                self._results = self._results.reset_index().sort(columns, ascending=ascending)
        else:
            for param in reversed(self._sort_params):
                reverse = False
                if param.startswith('-'):
                    reverse = True
                    param = param.replace('-', '', 1)
                self._results = sorted(self._results, key=lambda x: x[param], reverse=reverse)
        self._sorted = True

    def _eval(self):
        results = self.aggregate(**self._params)
        if isinstance(results, QuerySet):
            self._data_type = 'qs'
        elif pnd and isinstance(results, DataFrame):
            self._data_type = 'df'
        self._split_totals(results)
        self._evaluated = True

    def _items(self, record):
        for field_name, _ in self.get_fields():
            # Does the field_name refer to an aggregation column or is
            # it an attribute of this instance?
            try:
                attr_field = getattr(self, field_name)
            except AttributeError:
                # The field is a record element
                ret = record.get(field_name)
                formatting_func = self.get_formatting().get(field_name)
                if formatting_func is not None:
                    try:
                        ret = formatting_func(ret)
                    except (TypeError, ValueError):
                        pass
            else:
                # The view class has an attribute with this field_name
                if callable(attr_field):
                    ret = attr_field(record)
                    if getattr(attr_field, 'allow_tags', False):
                        ret = mark_safe(ret)
            yield ret

    def reset(self):
        self._sorted = False
        self._evaluated = False

    def get_results(self):
        if not self._evaluated:
            self._eval()
        if not self._sorted:
            self._sort_results()
        if self._data_type == 'qs':
            self._results.values()
        elif self._data_type == 'df':
            return self._results.to_dict(outtype='records')
        return self._results

    def get_totals(self):
        if self.has_totals and not self._evaluated:
            self._eval()
        if self._data_type == 'qs':
            return dict(self._totals)
        elif self._data_type == 'df':
            return self._totals.to_dict()
        return self._totals

    def get_formatting(self):
        if self.formatting is not None:
            return self.formatting
        return {}

    def get_alignment(self, field):
        if self.alignment is None:
            return 'align-left'
        else:
            try:
                return self.alignment[field]
            except KeyError:
                return 'align-left'

    def get_fields(self):
        if self.fields is not None:
            fields = self.fields
        elif self._data_type == 'df':
            fields = self._results.columns
        elif self._data_type == 'qs':
            fields = self._results.values().field_names
        else:
            try:
                fields = self.get_results()[0].keys()
            except IndexError:
                fields = []
        return [field if isinstance(field, (list, tuple)) else
                (field, ' '.join([s.title() for s in field.split('_')]))
                for field in fields]

    def set_params(self, **kwargs):
        self._params = kwargs
        self._evaluated = False

    def set_sort_params(self, *sort_params):
        self._sort_params = tuple(sort_params)
        self._sorted = False

    def get_sort_params(self):
        return tuple(self._sort_params)

    sort_params = property(set_sort_params, get_sort_params)

    def get_initial(self):
        return self.initial

    def get_form_class(self):
        return self.form_class

    def get_title(self):
        if self.title is None:
            return camel_re.sub(r'\1 \2', self.__class__.__name__).capitalize()
        return self.title

    def get_help_text(self):
        return mark_safe(self.help_text)

    def get_description(self):
        return mark_safe(self.description)

    def get_has_totals(self):
        return self.has_totals

    def get_paginator(self):
        return self.paginator(self.results, self.get_list_per_page())

    def get_list_max_show_all(self):
        return self.get_list_max_show_all

    def get_list_per_page(self):
        return self.list_per_page

    def get_export_form_class(self):
        return self.export_form_class

    def iter_results(self):
        for record in self.get_results():
            yield self._items(record)

    @property
    def results(self):
        return [tuple([elem for elem in record])
                for record in self.iter_results()]

    def iter_totals(self):
        return self._items(self.get_totals())

    @property
    def totals(self):
        return tuple([elem for elem in self.iter_totals()])

    def sort(self, *sort_params):
        self._sort_params = sort_params
        return self.results

    def aggregate(self, **kwargs):
        ''' Implement here your data elaboration.
        Must return a list of dict.
        '''
        raise NotImplementedError('Subclasses must implement this method')

    def to_csv(self, fileobj, header=False, totals=False, delimiter=';',
               quotechar='"', quoting=csv.QUOTE_NONNUMERIC,
               escapechar='', extra_rows=None, **kwargs):
        writer = csv.writer(fileobj, delimiter=str(delimiter),
                            quotechar=str(quotechar), quoting=quoting,
                            escapechar=str(escapechar), **kwargs)
        if extra_rows is not None:
            writer.writerows(extra_rows)
        if header:
            writer.writerow([name.encode(settings.DEFAULT_CHARSET) for name, _ in self.get_fields()])
        for record in self.iter_results():
            writer.writerow([elem.encode(settings.DEFAULT_CHARSET) if isinstance(elem, unicode) else elem
                             for elem in record])
        if totals and self.get_has_totals():
            writer.writerow(self.totals)

    def has_permission(self, request):
        return request.user.is_active and request.user.is_staff
