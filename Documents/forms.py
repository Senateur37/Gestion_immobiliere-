from django import forms

from .models import Document


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        exclude = ('owner', 'file_size', 'mime_type', 'created_at')
        widgets = {'expires_at': forms.DateInput(attrs={'type': 'date'}), 'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'field-input'
