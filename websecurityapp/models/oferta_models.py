from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from websecurityapp.models.perfil_models import Usuario
from websecurityapp.models.actividad_models import Actividad
from websecurityapp.validators import past_validator

class Oferta(models.Model):
    titulo = models.CharField(max_length = 100)
    descripcion = models.CharField(max_length = 1000)
    borrador = models.BooleanField()
    cerrada = models.BooleanField()
    vetada = models.BooleanField()
    motivo_veto = models.CharField(max_length = 1000, null = True, blank = True)
    fecha_creacion = models.DateField(validators = [past_validator])
    identificador = models.CharField(max_length = 30, unique = True)
    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    actividades = models.ManyToManyField(Actividad)

    def clean(self):
        super().clean()
        # No puede haber una oferta vetada sin motivo de veto
        if self.vetada and not self.motivo_veto:
            raise ValidationError('No puede haber una oferta vetada sin motivo de veto')



class Solicitud(models.Model):
    usuario = models.ForeignKey(Usuario, related_name='solicitudes', on_delete=models.CASCADE)
    oferta = models.ForeignKey(Oferta, related_name='solicitudes', on_delete=models.CASCADE)

    class Meta:
       unique_together = ['usuario', 'oferta']

    def clean(self):
        super().clean()
        # No puede haber una oferta en modo borrador en una solicitud
        if self.oferta.borrador:
            raise ValidationError('No puede haber una oferta en modo borrador en una solicitud')
        actividades_requeridas = self.oferta.actividades.all()
        actividades_realizadas = self.usuario.actividades_realizadas.all()
        for actividad in actividades_requeridas:
            if not actividad in actividades_realizadas:
                raise ValidationError("El usuario debe haber resuelto todas las actividades para poder solicitar la oferta")
        if self.usuario == self.oferta.autor:
            raise ValidationError("El autor de la oferta no puede ser un solicitante de la misma")

