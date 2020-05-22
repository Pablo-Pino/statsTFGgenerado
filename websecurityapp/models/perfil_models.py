from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.core.validators import RegexValidator



class Usuario(models.Model):
    django_user = models.ForeignKey(User, on_delete = models.CASCADE)
    telefono = models.CharField(max_length = 30, null = True, blank = True, validators=[RegexValidator(regex = '^(\+\d{1,3}\(\d{1,3}\)*)*\d{4,}$', message = 'No sigue el patron')])
    empresa_u_equipo = models.CharField(max_length = 100, null = True, blank = True)
    vetado = models.BooleanField()
    es_admin = models.BooleanField()
    # Para evitar errores de importación circular de clases, se referencia la clase usando <nombre_app>.<clase_entidad>
    actividades_realizadas = models.ManyToManyField('websecurityapp.Actividad')

class Anexo(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete = models.CASCADE)
    anexo = models.URLField()
