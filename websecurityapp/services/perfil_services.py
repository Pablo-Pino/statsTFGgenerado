from django.contrib.auth.models import User
from django.db import transaction
from datetime import date
from random import choice
from django.contrib.auth.hashers import make_password

from websecurityapp.models.perfil_models import Usuario, Anexo
from websecurityapp.forms.perfil_forms import UsuarioForm, AnexoForm
from websecurityapp.exceptions import UnallowedUserException

@transaction.atomic
def registra_usuario(usuario_dict):
    django_user = User.objects.create_user(
        usuario_dict['nombre_usuario'], 
        usuario_dict['email'], 
        usuario_dict['contrasenna'], 
        first_name = usuario_dict['nombre'], 
        last_name = usuario_dict['apellidos']
    )
    usuario = Usuario()
    usuario.django_user = django_user
    usuario.telefono = usuario_dict['telefono']
    usuario.empresa_u_equipo = usuario_dict['empresa_u_equipo']
    usuario.vetado = False
    usuario.es_admin = False
    usuario.full_clean()
    usuario.save()
    usuario.actividades_realizadas.set([])
    usuario.full_clean()
    usuario_registrado = usuario.save()
    return usuario_registrado

def usuario_formulario(usuario):
    data = {
        'nombre_usuario': usuario.django_user.username,
        'nombre': usuario.django_user.first_name,
        'apellidos': usuario.django_user.last_name,
        'email': usuario.django_user.email,
        'telefono': usuario.telefono,
        'empresa_u_equipo': usuario.empresa_u_equipo
    }
    form = UsuarioForm(data)
    return form

@transaction.atomic
def edita_perfil(form_data, usuario):
    django_user = User.objects.get(pk = usuario.django_user.id)
    django_user.username = form_data['nombre_usuario']
    django_user.password = make_password(form_data['contrasenna'])
    django_user.first_name = form_data['nombre']
    django_user.last_name = form_data['apellidos']
    django_user.email = form_data['email']
    django_user.save()
    usuario.telefono = form_data['telefono']
    usuario.empresa_u_equipo = form_data['empresa_u_equipo']
    usuario.save()

def anexo_formulario(anexo):
    data = {
        'anexo': anexo.anexo
    }
    form = AnexoForm(data)
    return form

@transaction.atomic
def crea_anexo(anexo_dict, usuario):
    anexo = Anexo(
        anexo = anexo_dict['anexo'],
        usuario = usuario,
    )
    anexo.save()

@transaction.atomic
def edita_anexo(anexo, anexo_dict, usuario):
    if usuario.id != anexo.usuario.id:
        raise UnallowedUserException()
    anexo.anexo = anexo_dict['anexo']
    anexo.save()

@transaction.atomic
def elimina_anexo(anexo, usuario):
    if usuario.id != anexo.usuario.id:
        raise UnallowedUserException()
    anexo.delete()
