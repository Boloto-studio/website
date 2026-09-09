from django import forms

from .models import ContactRequest


class ContactRequestForm(forms.ModelForm):
    class Meta:
        model = ContactRequest
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter designation'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter return address'}),
            'message': forms.Textarea(attrs={'placeholder': 'Begin transmission...', 'rows': 6}),
        }