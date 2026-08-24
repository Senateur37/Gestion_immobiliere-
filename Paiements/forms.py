from django import forms

from .models import Payment


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        exclude = ('lease', 'payment_number', 'created_at', 'updated_at')
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'paid_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'field-input')
        self.fields['notes'].widget.attrs['class'] = 'field-input field-textarea'
