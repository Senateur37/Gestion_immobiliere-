from django import forms
from django.db.models import Q

from Comptes.models import User
from Proprietes.models import Unit

from .models import Lease


class LeaseForm(forms.ModelForm):
    # Declare explicitement : sans cela, Django construit le queryset a
    # l'import du module, hors de toute organisation active. Le vrai
    # queryset est pose dans __init__.
    unit = forms.ModelChoiceField(queryset=Unit.objects.none(), label='Unite locative')

    class Meta:
        model = Lease
        exclude = ('document', 'signed_at')
        widgets = {'start_date': forms.DateInput(attrs={'type': 'date'}), 'end_date': forms.DateInput(attrs={'type': 'date'}), 'notes': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, owner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Le manager restreint deja a l'organisation active.
        self.fields['unit'].queryset = Unit.objects.all()
        # Les locataires visibles sont ceux deja lies a un bail de
        # l'organisation, plus ceux qui ne sont rattaches a aucun bail
        # (sans quoi aucun premier bail ne serait creable). Le perimetre
        # vient des unites, qui portent l'organisation.
        self.fields['tenant'].queryset = User.objects.filter(
            role='tenant', is_active=True
        ).filter(
            Q(leases__unit__in=Unit.objects.all()) | Q(leases__isnull=True)
        ).distinct()