import re
from collections import OrderedDict
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
from django.utils.html import format_html
try:
    from pandas import DataFrame
except ImportError:
    DataFrame = None

admin_view_m = method_decorator(site.admin_view)
ALL_VAR = 'all'
ORDER_VAR = 'o'
PAGE_VAR = 'p'
CONTROL_VARS = [ALL_VAR, ORDER_VAR, PAGE_VAR]
camel_re = re.compile('([a-z0-9])([A-Z])')


class ReportList(object):

    def __init__(self, report_view, results):
        self.report_view = report_view
        self.request = self.report_view.request
        self.params = dict(self.request.GET.items())
        self.list_per_page = self.report_view.get_list_per_page()
        self.list_max_show_all = self.report_view.get_list_max_show_all()
        try:
            self.page_num = int(self.request.GET.get(PAGE_VAR, 0))
        except ValueError:
            self.page_num = 0
        self.show_all = ALL_VAR in self.request.GET
        self.paginator = None
        self.multi_page = False
        self.can_show_all = True
        self._fields = self.report_view.get_fields()
        # Guess fields if not defined
        if self._fields is None:
            if isinstance(results, QuerySet):
                self._fields = [field.name for field in results.query.get_meta().fields]
            elif DataFrame is not None and isinstance(results, DataFrame) and not results.empty:
                self._fields = [name for name in results.index.names if name is not None] + list(results.columns)
            elif isinstance(results, (list, tuple)) and results:
                self._fields = results[0].keys()
            else:
                self._fields = []
        self.fields = []
        for field in self._fields:
            if isinstance(field, (list, tuple)):
                self.fields.append(field)
            else:
                self.fields.append((field, ' '.join([s.title() for s in field.split('_')])))
        self.ordering_field_columns = self._get_ordering_field_columns()
        self.num_sorted_fields = len(self.ordering_field_columns)
        self.full_result_count = self.get_result_count(results)
        self._results = self.get_results(results)

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
        for i, field in enumerate(self.fields):
            name = field[0]
            label = field[1]
            if callable(getattr(self.report_view, name, name)):
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

    def _items(self, record):
        for field_name, _ in self.fields:
            try:
                attr_field = getattr(self.report_view, field_name)
            except AttributeError:
                yield record.get(field_name)
            else:
                if callable(attr_field):
                    yield attr_field(record)

    @property
    def results(self):
        for record in iter(self._results):
            yield self._items(record)

    def get_result_count(self, results):
        if isinstance(results, QuerySet):
            count = results.count()
        elif DataFrame is not None and isinstance(results, DataFrame):
            count = results.index.size
        else:
            count = len(results)
        return count

    def sort_results(self, results):
        if isinstance(results, QuerySet):
            sort_params = []
            for i in self.ordering_field_columns:
                sort = ''
                if self.ordering_field_columns.get(i).lower() == 'desc':
                    sort = '-'
                field_name = self.fields[i][0]
                sort_params.append('%s%s' % (sort, field_name))
            ret = results.order_by(*sort_params)
        elif DataFrame is not None and isinstance(results, DataFrame):
            sort_params = {'columns': None, 'ascending': True}
            columns = []
            ascending = []
            for i in self.ordering_field_columns:
                asc = True
                if self.ordering_field_columns.get(i).lower() == 'desc':
                    asc = False
                columns.append(self.fields[i][0])
                ascending.append(asc)
            if columns:
                sort_params['columns'] = columns
            if ascending:
                sort_params['ascending'] = ascending
            ret = results.reset_index().sort(**sort_params)
        else:
            ret = results
            for i in reversed(self.ordering_field_columns):
                reverse = False
                if self.ordering_field_columns.get(i).lower() == 'desc':
                    reverse = True
                ret = sorted(ret, key=lambda x: x[self.fields[i][0]], reverse=reverse)
        return ret

    def paginate(self, records):
        # paginate
        self.paginator = self.report_view.get_paginator(records)
        result_count = self.paginator.count
        self.multi_page = result_count > self.list_per_page
        self.can_show_all = result_count <= self.list_max_show_all
        if not (self.show_all and self.can_show_all) and self.multi_page:
            try:
                records = self.paginator.page(self.page_num + 1).object_list
            except InvalidPage:
                raise IncorrectLookupParameters
        return records

    def get_results(self, results):
        records = self.sort_results(results)
        if isinstance(records, QuerySet):
            records = records.values(*[field for field, _ in self.fields])
        elif DataFrame is not None and isinstance(records, DataFrame):
            records = records.to_dict(outtype='records')
        records = self.paginate(records)
        return records


class ReportView(TemplateView, FormMixin):
    template_name = 'admin/report.html'
    title = ''
    description = ''
    help_text = ''
    fields = None
    paginator = Paginator # ReportPaginator
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
            'jquery.init.js',
        ]
        return forms.Media(js=[static('admin/js/%s' % url) for url in js])

    def get_form_kwargs(self):
        kwargs = super(ReportView, self).get_form_kwargs()
        if self.request.method == 'GET':
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
                results = self.aggregate(**form.cleaned_data)
            else:
                results = []
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

    def aggregate(self, **kwargs):
        ''' Implement here your data elaboration.
        Must return a list of dict.
        '''
        raise NotImplementedError('Subclasses must implement this method')
