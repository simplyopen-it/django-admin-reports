import csv
from django import forms
from django.utils import formats
from django.forms.widgets import SelectMultiple

delimiters = ",;|:"
quotes = "'\"`"
escapechars = " \\"


class ExportForm(forms.Form):
    ''' Let an admin user costomize a CSV export.
    '''
    header = forms.BooleanField(required=False)
    delimiter = forms.ChoiceField(choices=zip(delimiters, delimiters))
    quotechar = forms.ChoiceField(choices=zip(quotes, quotes))
    quoting = forms.ChoiceField(
        choices=((csv.QUOTE_ALL, 'All'),
                 (csv.QUOTE_MINIMAL, 'Minimal'),
                 (csv.QUOTE_NONE, 'None'),
                 (csv.QUOTE_NONNUMERIC, 'Non Numeric')))
    escapechar = forms.ChoiceField(choices=(('', ''), ('\\', '\\')), required=False)
