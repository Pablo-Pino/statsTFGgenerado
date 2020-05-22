from django.contrib.auth.models import User
from django.db import transaction
from datetime import date
from random import choice
from django.contrib.auth.hashers import make_password
from django.db.models import Q

from websecurityapp.models.actividad_models import Actividad
from websecurityapp.models.perfil_models import Usuario
from websecurityapp.forms.actividad_forms import ActividadEdicionForm
from websecurityapp.exceptions import UnallowedUserException
from websecurityapp.services.util_services import genera_identificador

@transaction.atomic
def listado_actividades(request):
    if not request.user.is_authenticated:
        raise Exception('Se debe estar autenticado para listar las actividades')
    usuario = Usuario.objects.get(django_user__id=request.user.id)
    if usuario.es_admin:
        return Actividad.objects.exclude(Q(borrador=True) & ~Q(autor=usuario)).order_by('id')
    else:
        return Actividad.objects.exclude((Q(borrador=True) | Q(vetada=True)) & ~Q(autor=usuario)).order_by('id')

@transaction.atomic
def listado_actividades_propias(request):
    if not request.user.is_authenticated:
        raise Exception('Se debe estar autenticado para listar las actividades')
    usuario = Usuario.objects.get(django_user__id=request.user.id)
    return Actividad.objects.filter(autor=usuario).order_by('id')

@transaction.atomic
def crea_actividad(actividad_dict, request):
    if not request.user.is_authenticated:
        raise Exception('Se debe estar autenticado para crear una actividad')
    actividad = Actividad(
        titulo = actividad_dict['titulo'],
        enlace = actividad_dict['enlace'],
        descripcion = actividad_dict['descripcion'],
        comentable = actividad_dict['comentable'],
        autor = actividad_dict['autor'],
        borrador = True,
        vetada = False,
        fecha_creacion = date.today(),
        identificador = 'ACT-' + genera_identificador(),
    )
    actividad.full_clean()
    actividad.save()
    return actividad

def actividad_formulario(actividad):
    data = {
        'titulo': actividad.titulo,
        'enlace': actividad.enlace,
        'descripcion': actividad.descripcion,
        'comentable': actividad.comentable,
        'borrador': actividad.borrador,
    }
    form = ActividadEdicionForm(data)
    return form

@transaction.atomic
def edita_actividad(request, form_data, actividad):
    if not actividad.autor.django_user.id == request.user.id:
        raise UnallowedUserException()
    if not actividad.borrador:
        raise Exception('No se puede editar una actividad que no está en modo borrador')
    actividad.titulo = form_data['titulo']
    actividad.enlace = form_data['enlace']
    actividad.descripcion = form_data['descripcion']
    actividad.comentable = form_data['comentable']
    actividad.borrador = form_data['borrador']
    actividad.full_clean()
    actividad.save(update_fields = ['titulo', 'enlace', 'descripcion', 'comentable', 'borrador'])
    return actividad

@transaction.atomic
def elimina_actividad(request, actividad):
    if not actividad.autor.django_user.id == request.user.id:
        raise UnallowedUserException()
    if not actividad.borrador:
        raise Exception(['No se puede eliminar una actividad que no está en modo borrador'])
    actividad.delete()

@transaction.atomic
def veta_actividad(request, form_data, actividad):
    usuario = Usuario.objects.get(django_user_id = request.user.id)
    if not usuario.es_admin:
        raise Exception('Se requieren permisos de administrador para realizar esta accion')
    if actividad.vetada:
        raise Exception('No se puede volver a vetar una actividad vetada')
    actividad.motivo_veto = form_data['motivo_veto']
    actividad.vetada = True
    actividad.full_clean()
    actividad.save(update_fields = ['motivo_veto', 'vetada'])

@transaction.atomic
def levanta_veto_actividad(request, actividad):
    usuario = Usuario.objects.get(django_user_id = request.user.id)
    if not usuario.es_admin:
        raise Exception('Se requieren permisos de administrador para realizar esta accion')
    if not actividad.vetada:
        raise Exception('No se puede levantar el veto sobre una actividad no vetada')
    actividad.motivo_veto = None
    actividad.vetada = False
    actividad.full_clean()
    actividad.save(update_fields = ['motivo_veto', 'vetada'])
