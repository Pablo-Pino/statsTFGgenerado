from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime

from websecurityapp.models.actividad_models import SesionActividad, Actividad
from websecurityapp.models.perfil_models import Usuario

@transaction.atomic
def crea_sesionactividad(request, actividad):
    usuario = Usuario.objects.get(django_user_id = request.user.id)
    try:
        sesionactividad = SesionActividad.objects.get(usuario = usuario, actividad = actividad)
        sesionactividad.token = usuario.django_user.username + str(datetime.now())
    except ObjectDoesNotExist as e:
        sesionactividad = SesionActividad(
            usuario = usuario,
            actividad = actividad,
            token = usuario.django_user.username + str(datetime.now())
        )
    sesionactividad.save()
    return sesionactividad

@transaction.atomic
def elimina_sesionactividad(request, actividad):
    token = request.data['token']
    sesionactividad = SesionActividad.objects.get(token = token, actividad = actividad)
    sesionactividad.delete()

@transaction.atomic
def añade_actividad_realizada(request, actividad):
    if not request.user.is_authenticated:
        raise Exception('Se debe estar autenticado para realizar una actividad')
    # No se puede considerar realizada una actividad si no está en modo borrador
    if not actividad.borrador:
        usuario = Usuario.objects.get(django_user = request.user)
        actividades_realizadas = list(usuario.actividades_realizadas.all())
        actividades_realizadas.append(actividad)
        usuario.actividades_realizadas.set(actividades_realizadas)
        usuario.save()

