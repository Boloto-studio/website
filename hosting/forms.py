from django import forms

class ServerCreationForm(forms.Form):
    name = forms.CharField(label="Server Name", max_length=100)
    ram_min = forms.IntegerField(label="Min RAM (GB)")
    ram_max = forms.IntegerField(label="Max RAM (GB)")
    