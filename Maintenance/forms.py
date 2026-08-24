from django import forms

from Proprietes.models import Unit

from .models import MaintenanceRequest


class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        exclude = ('tenant', 'status', 'assigned_to', 'submitted_at', 'completed_at', 'notes', 'cost')

    def __init__(self, owner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit'].queryset = Unit.objects.filter(property__owner=owner)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'field-input'
        self.fields['description'].widget.attrs['class'] = 'field-input field-textarea'
