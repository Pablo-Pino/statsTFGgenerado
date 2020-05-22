from django.core.paginator import Paginator
from django.shortcuts import render
from django.http import HttpResponse, QueryDict, HttpResponseRedirect
from django.views import View
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin

from websecurityapp.exceptions import UnallowedUserException
from websecurityapp.forms.perfil_forms import UsuarioForm,  AnexoForm
from websecurityapp.models.perfil_models import Usuario, Anexo
from websecurityapp.services.perfil_services import registra_usuario, usuario_formulario, edita_perfil, anexo_formulario, crea_anexo, edita_anexo, elimina_anexo
from websecurityserver.settings import numero_objetos_por_pagina


class RegistroUsuarioView(View):
    template_name = 'perfil/registro_usuario.html'
    
    def get(self, request):
        context = {}
        usuario_form = UsuarioForm()
        context.update({'usuario_form': usuario_form})
        return render(request, self.template_name, context)

    def post(self, request):
        context = {}
        usuario_form = UsuarioForm(request.POST)
        if usuario_form.is_valid():
            usuario_form.clean()
            usuario_form_data = usuario_form.cleaned_data
            registra_usuario(usuario_form_data)
            usuario_form = UsuarioForm()
            context.update({'usuario_form': usuario_form, 'registro_exito': True})
            return render(request, self.template_name, context)
        else:
            usuario_form.clean()
            context.update({'usuario_form': usuario_form, 'registro_exito': False})
            return render(request, self.template_name, context)

class DetallesPerfilView(LoginRequiredMixin, View):
    template_name = 'perfil/detalles_perfil.html'

    def get(self, request):
        context = {}
        # Se busca el usuario
        usuario = Usuario.objects.get(django_user_id = request.user.id)
        # Si se encuentra el usuario, se buscan sus anexos y se le muestra su perfil
        anexos = Anexo.objects.filter(usuario_id = usuario.id).order_by('id')
        # Se obtienen las actividades_realizadas por el usuario y se paginan
        actividades_realizadas = usuario.actividades_realizadas.all().order_by('id')
        paginator = Paginator(actividades_realizadas, numero_objetos_por_pagina)
        page_number = request.GET.get('page')
        page_obj_actividades_realizadas = paginator.get_page(page_number)
        # Se añade al usuario, sus anexos y las actividades al contexto
        context.update({
            'usuario': usuario,
            'usuario_perfil': usuario,
            'anexos': anexos,
            'page_obj_actividades_realizadas': page_obj_actividades_realizadas,
        })
        return render(request, self.template_name, context)

class DetallesPerfilAjenoView(LoginRequiredMixin, View):
    template_name = 'perfil/detalles_perfil.html'

    def get(self, request, usuario_id):
        context = {}
        # Se busca el usuario
        usuario = Usuario.objects.get(django_user_id = request.user.id)
        try:
            usuario_perfil = Usuario.objects.get(pk=usuario_id)
        # Si no se enecuentra el usuario cuyo perfil se quiere ver, se redirige a la pagina principal
        except ObjectDoesNotExist as e:
            messages.error(request, 'No se ha encontrado el usuario')
            return HttpResponseRedirect(reverse('home'))
        # Si se encuentra el usuario, se buscan sus anexos y se le muestra su perfil
        anexos = Anexo.objects.filter(usuario_id = usuario_id).order_by('id')
        # Se obtienen las actividades_realizadas por el usuario que no estan vetadas y se paginan
        actividades_realizadas = usuario_perfil.actividades_realizadas.filter(vetada=False).order_by('id')
        paginator = Paginator(actividades_realizadas, numero_objetos_por_pagina)
        page_number = request.GET.get('page')
        page_obj_actividades_realizadas = paginator.get_page(page_number)
        # Se añaden al usuario registraado, el usuario cuyo perfil se visita, sus anexos y las actividades resueltas por
        # dicho usuario al contexto
        context.update({
            'usuario': usuario,
            'usuario_perfil': usuario_perfil,
            'anexos': anexos,
            'page_obj_actividades_realizadas': page_obj_actividades_realizadas,
        })
        return render(request, self.template_name, context)

class EdicionPerfilView(LoginRequiredMixin, View):
    template_name = 'perfil/edicion_perfil.html'

    def get(self, request):
        context = {}
        # Se busca el usuario
        usuario = Usuario.objects.get(django_user_id = request.user.id)
        # Si se encuentra el usuario, se crea el formulario en base a sus datos
        form = usuario_formulario(usuario)
        # Se dan los datos necesarios para crear el formulario y darle estilo
        context.update({
            'form': form,
            'validated': False, 
            'form_class': 'needs-validation'
        })
        # Se renderiza el formulario
        return render(request, self.template_name, context)

    def post(self, request):
        context = {}
        form = UsuarioForm(request.POST)
        # Si el formulario es válido
        if form.is_valid():
            # Se trratan los datos del formulario
            form.clean()
            form_data = form.cleaned_data
            # Se busca el usuario
            usuario = Usuario.objects.get(django_user_id = request.user.id)
            # Se trata de edita el usuario
            try:
                edita_perfil(form_data, usuario)
            except Exception as e:
                # Si se produce un error en la edición, entonces se redirige al usuario al formulario con un mensaje de
                # error
                messages.error(request, 'Ha habido un error al editar el perfil')
                messages.error(request, e.args[0])
                context.update({
                    'form': form,
                    'validated': True, 
                    'form_class': 'was-validated'
                })
                return render(request, self.template_name, context)
            # Si se ha realizado correctamente la edición se pide al usuario que vuelvaa a hacer login y se le
            # muestra un mensaje de éxito
            messages.success(request, 'Se ha editado el perfil con exito')
            return HttpResponseRedirect(reverse('login'))
        # Si el formulario tiene errores de validación
        else:
            # Se muestra un mensaje de error al usuario y se le devuelve al formulario
            form.clean()
            messages.error(request, 'Ha habido un error al editar el perfil')
            # Se dan los datos necesarios para crear el formulario y darle estilo
            context.update({
                'form': form,
                'validated': True, 
                'form_class': 'was-validated'
            })
            return render(request, self.template_name, context)

class CreacionAnexoView(LoginRequiredMixin, View):
    template_name = 'perfil/formulario_anexo.html'

    def get(self, request):
        context = {}
        # Se busca al usuario
        usuario = Usuario.objects.get(django_user_id = request.user.id)
        # Se crea el formulario de creación del anexo
        form = AnexoForm()
        # Se dan los datos necesarios para crear el formulario y darle estilo
        context.update({
            'form': form, 
            'validated': False, 
            'form_class': 'needs-validation'
        })
        return render(request, self.template_name, context)

    def post(self, request):
        context = {}
        form = AnexoForm(request.POST)
        # Si el formulario es válido
        if form.is_valid():
            # Trata y obtiene los datos del formulario
            form.clean()
            form_data = form.cleaned_data
            # Se trata de crear el usuario
            usuario = Usuario.objects.get(django_user_id = request.user.id)
            try:
                crea_anexo(form_data, usuario)
            # El usuario no está permitido, por lo que se le redirige a los detalles del perfil
            except UnallowedUserException as e:
                messages.error(request, e.msg)
                return HttpResponseRedirect(reverse('perfil_detalles'))
            # Si no se encuentra el anexo se redirige al usuario a los detalles del perfil
            except ObjectDoesNotExist as e:
                messages.error(request, 'No se ha encontrado el anexo')
                return HttpResponseRedirect(reverse('perfil_detalles'))
            # En cualquier otro caso, se permanece en el formulario y se incluye un mensaje
            except Exception as e:
                messages.error(request, 'Se ha producido un error al crear el anexo')
                context.update({
                    'form': form, 
                    'validated': True, 
                    'form_class': 'was-validated'
                })
                return render(request, self.template_name, context)
            # Redirige a los detalles del perfil con un mensaje de éxito
            messages.success(request, 'Se ha creado el anexo con exito')
            return HttpResponseRedirect(reverse('perfil_detalles'))
        else:
            # Vuelve al formulario cuando haya un error de validacion y muestra un mensaje de error
            form.clean()
            messages.error(request, 'Se ha producido un error al crear el anexo')
            context.update({
                'form': form, 
                'validated': True, 
                'form_class': 'was-validated'
            })
            return render(request, self.template_name, context)

class EdicionAnexoView(LoginRequiredMixin, View):
    template_name = 'perfil/formulario_anexo.html'

    def get(self, request, anexo_id):
        context = {}
        usuario = Usuario.objects.get(django_user_id = request.user.id)
        # Trata de encontrar el anexo que se quiere editar
        try:
            anexo = Anexo.objects.get(pk=anexo_id)
        # Si no existe el anexo, se notifica al usuario y se le devuelve a su perfil
        except ObjectDoesNotExist as e:
            messages.error(request, 'No se ha encontrado el anexo')
            return HttpResponseRedirect(reverse('perfil_detalles'))
        # Si el anexo es de otro usuario, entonces se indica que no tiene autoridad para editarlo
        if anexo.usuario != usuario:
            messages.error(request, 'No tienes los permisos o requisitos necesarios para realizar esta accion')
            return HttpResponseRedirect(reverse('perfil_detalles'))
        # Crea el objeto formulario y lo incluye en el contexto
        form = anexo_formulario(anexo)  
        context.update({
            'anexo_id': anexo_id, 
            'form': form, 
            'validated': False, 
            'form_class': 'needs-validation'
        })
        return render(request, self.template_name, context)

    def post(self, request, anexo_id):
        context = {}
        form = AnexoForm(request.POST)
        try:
            usuario = Usuario.objects.get(django_user_id = request.user.id)
        except ObjectDoesNotExist as e:
            messages.error(request, 'Se debe estar autenticado para acceder a la edicion de anexos')
            return HttpResponseRedirect(reverse('perfil_detalles'))
        # Se busca el anexo que se va a editar
        try: 
            anexo = Anexo.objects.get(pk=anexo_id)
        # Si no se encuentra el anexo, se redirige al usuario a los detalles del perfil con un mensaje de error
        except ObjectDoesNotExist as e:
            messages.error(request, 'No se ha encontrado el anexo')
            return HttpResponseRedirect(reverse('perfil_detalles'))
        # Si el anexo no pertenece al usuario, se redirige al usuario a los detalles del perfil con un mensaje de error
        if anexo.usuario != usuario:
            messages.error(request, 'No tienes los permisos o requisitos necesarios para realizar esta accion')
            return HttpResponseRedirect(reverse('perfil_detalles'))
        # Si el formulario es válido
        if form.is_valid():
            # Trata los datos del formulario y trata de edita el anexo
            form.clean()
            form_data = form.cleaned_data
            try:
                edita_anexo(anexo, form_data, usuario)
            # El usuario no está permitido, por lo que se le redirige a los detalles del perfil
            except UnallowedUserException as e:
                messages.error(request, e.msg)
                return HttpResponseRedirect(reverse('perfil_detalles'))
            # En cualquier otro caso, se permanece en el formulario y se incluye un mensaje de error
            except Exception as e:
                messages.error(request, 'Se ha producido un error al editar el anexo')
                context.update({
                    'anexo_id': anexo_id,
                    'form': form, 
                    'validated': True, 
                    'form_class': 'was-validated'
                })
            # Si no se han producido errores, se redirige al usuario a los detalles del perfil con un mensaje de éxito
            messages.success(request, 'Se ha editado el anexo con exito')
            return HttpResponseRedirect(reverse('perfil_detalles'))
        else:
            # Vuelve al formulario cuando haya un error de validacion, mostrando un mensaje de error
            form.clean()
            messages.error(request, 'Se ha producido un error al editar el anexo')
            context.update({
                'anexo_id': anexo_id,
                'form': form, 
                'validated': True, 
                'form_class': 'was-validated'
            })
            return render(request, self.template_name, context)

class EliminacionAnexoView(LoginRequiredMixin, View):
    template_name = 'perfil/detalles_perfil.html'

    def get(self, request, anexo_id):
        context = {}
        usuario = Usuario.objects.get(django_user_id = request.user.id)
        # Se trata de hallar el anexo y eliminarlo
        try:
            anexo = Anexo.objects.get(pk=anexo_id)
            elimina_anexo(anexo, usuario)
        # Si el usuario no tiene permisos, se le redirige a los detalles del perfil con un mensaje de error
        except UnallowedUserException as e:
            messages.error(request, e.msg)
            return HttpResponseRedirect(reverse('perfil_detalles'))
        # Si no existe el anexo, se redirige al usuario a los detalles del perfil con un mensaje de error
        except ObjectDoesNotExist as e:
            messages.error(request, 'No se ha encontrado el anexo')
            return HttpResponseRedirect(reverse('perfil_detalles'))
        # Si hay cualquier otro error, se redirige al usuario a los detalles del perfil con un mensaje de error
        except Exception as e:
            messages.error(request, 'Se ha producido un error al eliminar el anexo')
            messages.error(request, e.args)
            return HttpResponseRedirect(reverse('perfil_detalles'))
        # Si se elimina el anexo correctamente se redirige al usuario a los detalles del perfil con un mensaje de error
        messages.success(request, 'Se ha eliminado el anexo con exito')
        return HttpResponseRedirect(reverse('perfil_detalles'))      

