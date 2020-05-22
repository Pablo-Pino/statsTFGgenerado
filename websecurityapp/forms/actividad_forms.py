from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

class ActividadCreacionForm(forms.Form):
    titulo = forms.CharField(max_length = 100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    enlace = forms.URLField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    descripcion = forms.CharField(max_length = 1000, widget=forms.Textarea(attrs={'class': 'form-control'}))
    comentable = forms.BooleanField(widget = forms.CheckboxInput(attrs={'class': 'form-control'}), required=False)

class ActividadEdicionForm(forms.Form):
    titulo = forms.CharField(max_length = 100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    enlace = forms.URLField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    descripcion = forms.CharField(max_length = 1000, widget=forms.Textarea(attrs={'class': 'form-control'}))
    comentable = forms.BooleanField(widget = forms.CheckboxInput(attrs={'class': 'form-control'}), required=False)
    borrador = forms.BooleanField(widget = forms.CheckboxInput(attrs={'class': 'form-control'}), required=False)

class ActividadVetoForm(forms.Form):
    motivo_veto = forms.CharField(max_length = 1000, widget=forms.Textarea(attrs={'class': 'form-control'}))
