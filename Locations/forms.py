from django import forms
from django.db.models import Q

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
        # Ne jamais exposer les locataires des autres proprietaires. On limite
        # aux locataires deja lies a un bail de ce proprietaire, plus ceux qui
        # ne sont encore rattaches a aucun bail (sinon aucun premier bail ne
        # serait creable). Ce compromis disparait avec organizations.Organization,
        # qui donnera un vrai perimetre au lieu de cette heuristique.
        self.fields['tenant'].queryset = User.objects.filter(
            role='tenant', is_active=True
        ).filter(
            Q(leases__unit__property__owner=owner) | Q(leases__isnull=True)
        ).distinct()