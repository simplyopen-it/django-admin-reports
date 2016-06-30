import csv
from django import forms

delimiters = ";,|:"
quotes = "\"'`"
escapechars = " \\"


class ExportForm(forms.Form):
    ''' Let an admin user costomize a CSV export.
    '''
    header = forms.BooleanField(required=False, initial=True)
    totals = forms.BooleanField(required=False, initial=True)
    delimiter = forms.ChoiceField(choices=zip(delimiters, delimiters))
    quotechar = forms.ChoiceField(choices=zip(quotes, quotes))
    quoting = forms.ChoiceField(
        choices=(
            (csv.QUOTE_NONNUMERIC, 'Non Numeric'),
            (csv.QUOTE_NONE, 'None'),
            (csv.QUOTE_MINIMAL, 'Minimal'),
            (csv.QUOTE_ALL, 'All'),
        ))
    escapechar = forms.ChoiceField(choices=(('', ''), ('\\', '\\')), required=False)


    def clean_quoting(self):
        quoting = self.cleaned_data.get('quoting')
        if quoting:
            return int(quoting)

    def clean_delimiter(self):
        delimiter = self.cleaned_data.get('delimiter')
        if delimiter:
            return str(delimiter)

    def clean_quotechar(self):
        quotechar = self.cleaned_data.get('quotechar')
        if quotechar:
            return str(quotechar)

    def clean_escapechar(self):
        escapechar = self.cleaned_data.get('escapechar')
        if escapechar:
            return str(escapechar)
        else:
            return ''
