from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

class UsuarioForm(forms.Form):
    nombre_usuario = forms.CharField(max_length = 30)
    contrasenna = forms.CharField(max_length = 30, widget = forms.PasswordInput)
    nombre = forms.CharField(max_length = 30)
    apellidos = forms.CharField(max_length = 30)
    email = forms.EmailField(max_length = 50)
    telefono = forms.CharField(max_length = 30, required = False, validators=[RegexValidator(regex = '^(\+\d{1,3}\(\d{1,3}\)*)*\d{4,}$', message = 'No sigue el patron')])
    empresa_u_equipo = forms.CharField(max_length = 100, required = False)

class AnexoForm(forms.Form):
    anexo = forms.URLField(widget=forms.TextInput(attrs={'class': 'form-control'}))