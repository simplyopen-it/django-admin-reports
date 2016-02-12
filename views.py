from django.views.generic.edit import FormMixin
from django.views.generic import TemplateView

class ReportView(TemplateView, FormMixin):
    template_name = 'report.html'
    title = ''
    fields = None

    # TODO: Handle function fields (like admin does)
    # TODO: Handle fields labels
    # TODO: sortables columns (?)

    def get_form_kwargs(self):
        kwargs = super(ReportView, self).get_form_kwargs()
        if self.request.method == 'GET':
            kwargs.update({
                'data': self.request.GET,
            })
        return kwargs

    def sort_fields(self, results, fields):
        # TODO: find a way to avoid the need of sort_fields
        return [tuple([result[field] for field in fields]) for result in results]

    def get_context_data(self, **kwargs):
        kwargs = super(ReportView, self).get_context_data(**kwargs)
        form = self.get_form(self.get_form_class())
        if 'form' not in kwargs:
            kwargs['form'] = form
        kwargs.update({
            'title': self.get_title(),
            'has_filters': self.get_form_class() is not None,
        })
        if form.is_valid():
            results = self.aggregate(form)
            fields = self.get_fields(results)
            kwargs.update({
                'results': self.sort_fields(results, fields),
                'fields': fields,
            })
        return kwargs

    def get_title(self):
        return self.title

    def get_fields(self, results):
        fields = self.fields
        if fields is None and results:
            fields = results[0].keys()
        return fields or []

    def aggregate(self, form):
        ''' Implement here your data elaboration.
        Must return a list of dict.
        '''
        raise NotImplementedError('Subclasses must implement this method')
