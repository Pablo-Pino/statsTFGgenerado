from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from websecurityapp.models.perfil_models import Usuario
from websecurityapp.validators import past_validator

class Actividad(models.Model):
    titulo = models.CharField(max_length = 100)
    autor = models.ForeignKey(Usuario, on_delete = models.CASCADE)
    enlace = models.URLField()
    descripcion = models.CharField(max_length = 1000)
    borrador = models.BooleanField()
    vetada = models.BooleanField()
    motivo_veto = models.CharField(max_length = 1000, null = True, blank = True)
    fecha_creacion = models.DateField(validators = [past_validator])
    comentable = models.BooleanField()
    identificador = models.CharField(max_length = 30, unique = True)

    def clean(self):
        super().clean()
        # No puede haber una actividad vetada sin motivo de veto
        if self.vetada and not self.motivo_veto:
            raise ValidationError('No puede haber una actividad vetada sin motivo de veto')

class SesionActividad(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete = models.CASCADE)
    actividad = models.ForeignKey(Actividad, on_delete = models.CASCADE)
    token = models.CharField(max_length = 100)
    