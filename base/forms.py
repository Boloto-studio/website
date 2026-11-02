from django import forms

from .models import ContactRequest


class ContactRequestForm(forms.ModelForm):
    class Meta:
        model = ContactRequest
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'terminal-input', 'placeholder': 'Enter designation'}),
            'email': forms.EmailInput(attrs={'class': 'terminal-input', 'placeholder': 'Enter return address'}),
            'message': forms.Textarea(attrs={'class': 'terminal-textarea', 'placeholder': 'Begin transmission...', 'rows': 6}),
        }