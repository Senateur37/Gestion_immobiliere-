from django import forms

from .models import Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        exclude = ('owner', 'created_at')
        widgets = {'transaction_date': forms.DateInput(attrs={'type': 'date'}), 'notes': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'field-input'
