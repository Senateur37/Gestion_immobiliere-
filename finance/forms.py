"""Formulaires du domaine financier."""
from django import forms

from core.forms import TenantModelForm
from Locations.models import Lease

from .models import Payment


class PaymentForm(TenantModelForm):
    """Saisie d'un encaissement.

    Le formulaire ne demande pas ce que le versement solde : l'imputation
    est calculee par le service, qui commence par les echeances les plus
    anciennes. L'agent saisit ce qu'il a recu, pas ce qu'il en deduit.
    """

    lease = forms.ModelChoiceField(queryset=Lease.objects.none(), label='Bail')

    class Meta:
        model = Payment
        fields = ('lease', 'compte', 'amount', 'payment_date', 'method', 'external_reference', 'notes')
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'external_reference': forms.TextInput(
                attrs={'placeholder': 'Numero de transaction, avis de virement...'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Le manager restreint deja aux baux de l'organisation active.
        self.fields['lease'].queryset = Lease.objects.select_related(
            'unit', 'unit__property', 'tenant'
        ).exclude(status='draft')
        self.fields['amount'].label = 'Montant recu'
        self.fields['compte'].label = 'Compte encaisseur'
        self.fields['compte'].required = True
        self.fields['compte'].help_text = (
            "Caisse, banque ou compte mobile. C'est ce choix qui produit "
            "l'ecriture comptable."
        )
        try:
            from comptes.models import Compte
            self.fields['compte'].queryset = Compte.objects.filter(actif=True)
        except Exception:
            pass
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'field-input')
        self.fields['notes'].widget.attrs['class'] = 'field-input field-textarea'

    def clean_amount(self):
        montant = self.cleaned_data['amount']
        if montant <= 0:
            raise forms.ValidationError('Le montant recu doit etre positif.')
        return montant
