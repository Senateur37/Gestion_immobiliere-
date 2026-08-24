from django import forms

from Comptes.models import User
from Proprietes.models import Unit

from .models import Lease


class LeaseForm(forms.ModelForm):
    class Meta:
        model = Lease
        exclude = ('document', 'signed_at')
        widgets = {'start_date': forms.DateInput(attrs={'type': 'date'}), 'end_date': forms.DateInput(attrs={'type': 'date'}), 'notes': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, owner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit'].queryset = Unit.objects.filter(property__owner=owner)
        self.fields['tenant'].queryset = User.objects.filter(role='tenant', is_active=True)