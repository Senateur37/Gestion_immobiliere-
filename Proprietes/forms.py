from django import forms

from .models import Property, Unit


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        exclude = ('owner',)
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ex. Residence Le Parc'}),
            'address': forms.TextInput(attrs={'placeholder': 'Adresse complete'}),
            'city': forms.TextInput(attrs={'placeholder': 'Ville'}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'Code postal'}),
            'total_area': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'year_built': forms.NumberInput(attrs={'min': '1800', 'max': '2100'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Ajoutez les informations utiles sur ce bien...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Nom du bien'
        self.fields['property_type'].label = 'Type de bien'
        self.fields['total_area'].label = 'Surface totale (m²)'
        self.fields['year_built'].label = 'Annee de construction'
        self.fields['is_active'].label = 'Bien actif'
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'field-input')
        self.fields['description'].widget.attrs['class'] = 'field-input field-textarea'
        self.fields['is_active'].widget.attrs['class'] = 'field-checkbox'


class UnitForm(forms.ModelForm):
    property = forms.ModelChoiceField(queryset=Property.objects.none(), label='Bien immobilier')

    class Meta:
        model = Unit
        exclude = ('property',)
        widgets = {
            'available_from': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        if owner is not None:
            self.fields['property'].queryset = Property.objects.filter(owner=owner)
        if self.instance and self.instance.pk:
            self.fields['property'].initial = self.instance.property_id
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'field-input')
        self.fields['description'].widget.attrs['class'] = 'field-input field-textarea'
