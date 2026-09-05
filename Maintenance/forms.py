from django import forms

from Proprietes.models import Unit

from .models import MaintenanceRequest


class MaintenanceRequestForm(forms.ModelForm):
    # Voir LeaseForm : le queryset par defaut serait construit a l'import,
    # hors organisation active.
    unit = forms.ModelChoiceField(queryset=Unit.objects.none(), label='Unite locative')

    class Meta:
        model = MaintenanceRequest
        exclude = ('tenant', 'status', 'assigned_to', 'submitted_at', 'completed_at', 'notes', 'cost')

    def __init__(self, owner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Le manager restreint deja a l'organisation active.
        self.fields['unit'].queryset = Unit.objects.all()
        for field in self.fields.values():
            field.widget.attrs['class'] = 'field-input'
        self.fields['description'].widget.attrs['class'] = 'field-input field-textarea'
