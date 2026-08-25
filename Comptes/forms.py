from django import forms
from .models import User

class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'field-input'}), label="Mot de passe")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'phone', 'avatar']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'field-input'}),
            'email': forms.EmailInput(attrs={'class': 'field-input'}),
            'first_name': forms.TextInput(attrs={'class': 'field-input'}),
            'last_name': forms.TextInput(attrs={'class': 'field-input'}),
            'role': forms.Select(attrs={'class': 'field-input'}),
            'phone': forms.TextInput(attrs={'class': 'field-input'}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'field-input'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'phone', 'avatar']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'field-input'}),
            'email': forms.EmailInput(attrs={'class': 'field-input'}),
            'first_name': forms.TextInput(attrs={'class': 'field-input'}),
            'last_name': forms.TextInput(attrs={'class': 'field-input'}),
            'role': forms.Select(attrs={'class': 'field-input'}),
            'phone': forms.TextInput(attrs={'class': 'field-input'}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'field-input'}),
        }

from .models import SiteSettings

class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ['app_name', 'logo', 'primary_color']
        widgets = {
            'app_name': forms.TextInput(attrs={'class': 'field-input'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'field-input'}),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'field-input', 'style': 'height: 50px; cursor: pointer;'}),
        }
