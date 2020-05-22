from django.core.paginator import Paginator
from django.shortcuts import render
from django.http import HttpResponse, QueryDict, HttpResponseRedirect
from django.views import View
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from websecurityapp.exceptions import UnallowedUserException
from websecurityapp.forms.actividad_forms import ActividadCreacionForm, ActividadEdicionForm, ActividadVetoForm
from websecurityapp.models.actividad_models import Actividad
from websecurityapp.models.perfil_models import Usuario
from websecurityapp.services.actividad_services import crea_actividad, edita_actividad, elimina_actividad, veta_actividad, \
        levanta_veto_actividad, actividad_formulario, listado_actividades, listado_actividades_propias
from websecurityserver.settings import numero_objetos_por_pagina


class ListadoActividadesView(LoginRequiredMixin, View):
    template_name = 'actividad/listado_actividades.html'

    def get(self, request):
        context = {}
        # Se consulta que usuario esta autenticado en este momento
        try:
            usuario = Usuario.objects.get(django_user_id = request.user.id)
        except ObjectDoesNotExist:
            usuario = None
        # Se obtiene el listado de actividades y se pagina
        actividades = listado_actividades(request)
        paginator = Paginator(actividades, numero_objetos_por_pagina)
        page_number = request.GET.get('page')
        page_obj_actividades = paginator.get_page(page_number)
        # Se añaden al contexto las actividades y el usuario y se muestra el listado
        context.update({
            'page_obj_actividades': page_obj_actividades,
            'usuario': usuario,
            # Se incluyen las actividades realizadas por el usuario, para poder marcarlas al mostrar el listado
            'actividades_realizadas': usuario.actividades_realizadas.all(),
            'titulo_pagina': 'Listado de actividades',
        })
        return render(request, self.template_name, context)

class ListadoActividadesPropiasView(LoginRequiredMixin, View):
    template_name = 'actividad/listado_actividades.html'

    def get(self, request):
        context = {}
        # Se consulta que usuario esta autenticado en este momento
        try:
            usuario = Usuario.objects.get(django_user_id = request.user.id)
        except ObjectDoesNotExist:
            usuario = None
        # Se obtiene el listado de actividades propias y se pagina
        actividades = listado_actividades_propias(request)
        paginator = Paginator(actividades, numero_objetos_por_pagina)
        page_number = request.GET.get('page')
        page_obj_actvidades = paginator.get_page(page_number)
        # Se añaden al contexto las actividades y el usuario y se muestra el listado
        context.update({
            'page_obj_actividades': page_obj_actvidades,
            'usuario': usuario,
            'titulo_pagina': 'Mis actividades',
        })
        return render(request, self.template_name, context)

class CreacionActividadesView(LoginRequiredMixin, View):
    # Todas las comprobaciones de permisos de esta vista las realiza el LoginRequiredMixin
    template_name = 'actividad/creacion_actividades.html'

    def get(self, request):
        context = {}
        # Se genera el formulario vacio de la actividad a crear
        form = ActividadCreacionForm()
        # Se mete el formulario en el contexto y las variables para el estilo de validacion
        # ademas de mostrar el formulario
        context.update({
            'form': form, 
            'validated': False, 
            'form_class': 'needs-validation'
        })
        return render(request, self.template_name, context)

    def post(self, request):
        context = {}
        # Se crea un objeto formulario con los paramentros de entrada dados
        form = ActividadCreacionForm(request.POST)
        # Si el formulario es valido, se trata el formulario y se crea la actividad
        if form.is_valid():
            # Se valida el formulario con mas detalle
            form.clean()
            form_data = form.cleaned_data
            # Se inserta el campo autor en el diccionario que representa el formulario
            autor = Usuario.objects.get(django_user_id = request.user.id)
            form_data.update({'autor': autor})
            # Se intenta crear la actividad
            try:
                actividad_creada = crea_actividad(form_data, request)
            # Si hay una excepcion al crear la actividad se permanece en el formulario 
            # y se incluye un mensaje de error
            except Exception as e:
                messages.error(request, 'Se ha producido un error al crear la actividad')
                # Se mete en el contexto el formulario y las variables para el estilo
                context.update({
                    'form': form, 
                    'validated': True, 
                    'form_class': 'was-validated'
                })
                # Se muestra el formulario de creación de la actividad
                return render(request, self.template_name, context)
            # Redirige al los detalles de la actividad con un mensaje de exito
            messages.success(request, 'Se ha creado la actividad con exito')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_creada.id}))
        # Si el formulario no es valido
        else:
            # Vuelve al formulario cuando haya un error de validacion
            # Se valida el formulario con mas detalle
            form.clean()
            # Se da un mensaje de error 
            messages.error(request, 'Se ha producido un error al crear la actividad')
            # Se mete en el contexto el formulario y las variables para el estilo
            context.update({
                'form': form, 
                'validated': True, 
                'form_class': 'was-validated'
            })
            # Se muestra el formulario de la creacion de la actividad
            return render(request, self.template_name, context)

class EdicionActividadesView(LoginRequiredMixin, View):
    # Para visitar esta pagina se requiere estar autenticado y ser el autor de la
    # actividad
    # El LoginRequiredMixin comprueba que el usuario esta autenticado
    # Se debe comprobar de forma programatica que el usuario es el autor de la actividad
    template_name = 'actividad/edicion_actividades.html'

    def get(self, request, actividad_id):
        context = {}
        # Se comprueba que existe la actividad
        try:
            actividad = Actividad.objects.get(pk=actividad_id)
        # Si la actividad no existe, se redirige al usuario al listado de actividades
        except ObjectDoesNotExist as e:
            return actividad_no_hallada(request)
        # Si la actividad no está en modo borrador, no se puede editar
        if not actividad.borrador:
            messages.error(request, 'No se puede editar una actividad que no está en modo borrador')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_id}))
        # Se comprueba que el usuario es el autor de la actividad
        # Si el usuario no es el autor de la actividad, se redirige al usuario a la 
        # página de los detalles de la actividad con un mensaje de error
        if not request.user.id == actividad.autor.django_user.id:
            messages.error(request, 'No se poseen los permisos necesarios para editar la actividad')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_id}))
        # Se genera un formulario en base a los datos de la actividad
        form = actividad_formulario(actividad)
        # Se mete el formulario y las variables de estilo en el contexto, además de
        # la id de la actividad para el atributo action del formulario
        context.update({
            'actividad_id': actividad_id, 
            'form': form, 
            'validated': False, 
            'form_class': 'needs-validation'
        })
        # Se muestra el formulario de edición de la actividad
        return render(request, self.template_name, context)

    def post(self, request, actividad_id):
        context = {}
        # Comprueba que la actividad existe
        try:
            actividad = Actividad.objects.get(pk=actividad_id)
        # Si no existe la actividad, redirige al usuario al listado de actividades
        except ObjectDoesNotExist as e:
            return actividad_no_hallada(request)
        # Si la actividad no está en modo borrador, no se puede editar
        if not actividad.borrador:
            messages.error(request, 'No se puede editar una actividad que no está en modo borrador')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_id}))
        # Se comprueba que el usuario es el autor de la actividad
        # Si el usuario no es el autor de la actividad, se redirige al usuario a la
        # página de los detalles de la actividad con un mensaje de error
        if not request.user.id == actividad.autor.django_user.id:
            messages.error(request, 'No se poseen los permisos necesarios para editar la actividad')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_id}))
        # Se crea un objeto formulario en base a los datos recibidos
        form = ActividadEdicionForm(request.POST)
        # Si el formulario es valido, se trata el formulario y se edita la actividad
        if form.is_valid():
            # Se trata el formulario con más detalle
            form.clean()
            form_data = form.cleaned_data
            # Se prueba a editar la actividad
            try:
                edita_actividad(request, form_data, actividad)
            # En caso de excepción, se permanece en el formulario
            except Exception as e:
                # Se da un mensaje de error
                messages.error(request, 'Se ha producido un error al editar la actividad')
                # Se meten en el contexto el formulario, las variables para el estilo de 
                # la validación y la id de la actividad para el atributo action del formulario
                context.update({
                    'actividad_id': actividad_id, 
                    'form': form, 
                    'validated': True, 
                    'form_class': 'was-validated'
                })
                # Se muestra el formulario de edicion de la actividad
                return render(request, self.template_name, context)
            # Si no sucede ningún error, se redirige a los detalles de la actividad junto con un mensaje de éxito
            messages.success(request, 'Se ha editado la actividad con exito')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad.id}))
        # Si el formulario no es valido
        else:
            # Se valida el formulario con más detalle
            form.clean()
            # Se da un mensaje de error
            messages.error(request, 'Se ha producido un error al editar la actividad')
            # Se inserta en el contexto el formulario, las variables para el estilo de la 
            # validación y el id de la actividad para el atributo action del formulario
            context.update({
                'actividad_id': actividad_id, 
                'form': form, 
                'validated': True, 
                'form_class': 'was-validated'
            })
            # Se muestra el formulario de edición al usuario
            return render(request, self.template_name, context)

class EliminacionActividadesView(LoginRequiredMixin, View):
    # Para visitar esta pagina se requiere estar autenticado y ser el autor de la
    # actividad
    # El LoginRequiredMixin comprueba que el usuario esta autenticado
    # Se debe comprobar de forma programatica que el usuario es el autor de la actividad
    template_name = 'actividad/listado_actividades.html'

    def get(self, request, actividad_id):
        context = {}
        # Se comprueba que existe la actividad
        try:
            actividad = Actividad.objects.get(pk=actividad_id)
        # Si la actividad no existe, se redirige al usuario al listado de actividades
        except ObjectDoesNotExist as e:
            return actividad_no_hallada(request)
        # Si la actividad no está en modo borrador, no se puede eliminar
        if not actividad.borrador:
            messages.error(request, 'No se puede eliminar una actividad que no está en modo borrador')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_id}))
        # Se comprueba que el usuario es el autor de la actividad
        # Si el usuario no es el autor de la actividad, se redirige al usuario a la 
        # página de los detalles de la actividad con un mensaje de error
        if not request.user.id == actividad.autor.django_user.id:
            messages.error(request, 'No se poseen los permisos necesarios para eliminar la actividad')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_id}))
        # Se intenta eliminar la actividad
        try:
            elimina_actividad(request, actividad)
        # Si hay cualquier excepción, se redirige al usuario los detalles de la actividad y se da un mensaje de error
        except Exception as e:
            messages.error(request, 'Se ha producido un error al eliminar la actividad')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_id}))
        # Si se elimina la actividad correctamente se redirige al usuario al listado de 
        # mensajes y se muestra un mensaje de éxito
        messages.success(request, 'Se ha eliminado la actividad con exito')
        return HttpResponseRedirect(reverse('actividad_listado'))        

class DetallesActividadesView(LoginRequiredMixin, View):
    # No se requiere estar autenticado para visitar esta página
    template_name = 'actividad/detalles_actividades.html'

    def get(self, request, actividad_id):
        context = {}
        # Se obtiene el usuario autenticado
        try:
            usuario = Usuario.objects.get(django_user_id = request.user.id)
        except ObjectDoesNotExist as e:
            usuario = None
        # Se busca la actividad
        try:
            actividad = Actividad.objects.get(pk=actividad_id)
        # En caso de que no se encuentre la actividad, se redirige al usuario al listado de actividades
        except ObjectDoesNotExist as e:
            return actividad_no_hallada(request)
        # En caso de que la actividad no pertenezca al usuario y esté en modo borrador, entonces se redirige al usuario
        # al listado de actividades, indicando que no puede acceder a los detalles de la actividad
        if actividad.borrador and actividad.autor != usuario:
            messages.error(request, 'No se tienen los permisos necesarios para acceder a la actividad')
            return HttpResponseRedirect(reverse('actividad_listado'))
        # Se mira si el usuario ha realizado la actividad, para indicarselo en la vista
        actividad_realizada = False
        if actividad in usuario.actividades_realizadas.all():
            actividad_realizada = True
        # Se añaden al contexto la actividad y el usuario
        context.update({
            'actividad': actividad,
            'usuario': usuario,
            'actividad_realizada': actividad_realizada,
        })
        # Se muestra la vista de detalles
        return render(request, self.template_name, context)

class VetoActividadesView(LoginRequiredMixin, View):
    # Se requiere estar autenticado para visitar esta página
    template_name = 'actividad/veto_actividades.html'

    def get(self, request, actividad_id):
        context = {}
        # Se comprueba que existe la actividad
        try:
            actividad = Actividad.objects.get(pk=actividad_id)
        # Si no existe se redirige al usuario al listado de actividades
        except ObjectDoesNotExist as e:
            return actividad_no_hallada(request)
        # Si el usuario no es un administrador, entonces se le redirige a los detalles de la actividad
        usuario = Usuario.objects.get(django_user=self.request.user)
        if not usuario.es_admin:
            messages.error(request, 'No se poseen los permisos necesarios para vetar la actividad')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_id}))
        # Si la actividad está vetada no se puede vetar, por lo que se redirige al usuario a la vista de detalles
        if actividad.vetada:
            messages.error(request, 'No se puede vetar una actividad ya vetada')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_id}))
        # Si la actividad está en modo borrador, no se puede vetar, por lo que se redirige  al usuario a la vista de detalles
        if actividad.borrador:
            messages.error(request, 'No se puede vetar una actividad que está en modo borrador')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_id}))
        # Se crea un formulario vacío para el veto de actividades
        form = ActividadVetoForm()
        # Se inserta en el contexto el formulario, las variables para el estilo de 
        # validación y el id de la actividad para el atributo action del formulario
        context.update({
            'actividad_id': actividad_id, 
            'form': form, 
            'validated': False, 
            'form_class': 'needs-validation'
        })
        # Se muestra el formulario de veto de actividades
        return render(request, self.template_name, context)
        
    def post(self, request, actividad_id):
        context = {}
        # Se comprueba que existe la actividad
        try:
            actividad = Actividad.objects.get(pk=actividad_id)
        # Si no la halla redirige al usuario al listado de actividades
        except ObjectDoesNotExist as e:
            return actividad_no_hallada(request)
        # Si el usuario no es un administrador, entonces se le redirige a los detalles de la actividad
        usuario = Usuario.objects.get(django_user=self.request.user)
        if not usuario.es_admin:
            messages.error(request, 'No se poseen los permisos necesarios para vetar la actividad')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs={'actividad_id': actividad_id}))
        # Si la actividad está vetada no se puede vetar, por lo que se redirige al usuario a la vista de detalles
        if actividad.vetada:
            messages.error(request, 'No se puede vetar una actividad ya vetada')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_id}))
        # Si la actividad está en modo borrador, no se puede vetar, por lo que se redirige al usuario a la vista de detalles
        if actividad.borrador:
            messages.error(request, 'No se puede vetar una actividad que está en modo borrador')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_id}))
        # Se genera un formulario con los datos introducidos
        form = ActividadVetoForm(request.POST)
        # Si el formulario es válido
        if form.is_valid():
            # Se realiza una validación con más detalle
            form.clean()
            form_data = form.cleaned_data
            # Trata de vetar la actividad
            try:
                veta_actividad(request, form_data, actividad)
            # En cualquier otro caso, se permanece en el formulario y se incluye un 
            # mensaje de error
            except Exception as e:                    
                messages.error(request, 'Se ha producido un error al vetar la actividad')
                # Se introduce en el contexto el formulario, las variables para el estilo
                # de la validación y el id de la actividad para el atributo action del 
                # formulario
                context.update({
                    'actividad_id': actividad_id, 
                    'form': form, 
                    'validated': True, 
                    'form_class': 'was-validated'
                })
                # Se muestra el formulario de veto de la actividad
                return render(request, self.template_name, context)
            # Si se ha tenido éxito, se redirige al usuario a los detalles de la actividad
            # junto con un mensaje de éxito
            messages.success(request, 'Se ha vetado la actividad con exito')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_id}))
        # Si el formulario no es valido
        else:
            # Se realiza una validación con más detalle
            form.clean()
            # Se muestra un mensaje de error
            messages.error(request, 'Se ha producido un error al vetar la actividad')
            # Se introduce en el contexto el formulario, las variables para el estilo de 
            # la validación y el id de la actividad para el atributo action del formulario
            context.update({
                'actividad_id': actividad_id, 
                'form': form, 
                'validated': True, 
                'form_class': 'was-validated',
            })
            # Se muestra el formulario de veto de la actividad
            return render(request, self.template_name, context)
            
class LevantamientoVetoActividadesView(LoginRequiredMixin, View):
    # Se requiere estar autenticado para visitar esta página
    template_name = 'actividad/listado_actividades.html'

    # Se comprueba que el usuario es un administrador
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        usuario = Usuario.objects.get(django_user = self.request.user)
        return usuario.es_admin

    def get(self, request, actividad_id):
        context = {}
        # Se trata de obtener la actividad
        try:
            actividad = Actividad.objects.get(pk=actividad_id)
        # Si no se encuentra la actividad se redirige al listado de actividades
        except ObjectDoesNotExist as e:
            return actividad_no_hallada(request)
        # Si el usuario no es un administrador, entonces se le redirige a los detalles de la actividad
        usuario = Usuario.objects.get(django_user=self.request.user)
        if not usuario.es_admin:
            messages.error(request, 'No se poseen los permisos necesarios para levantar el veto sobre la actividad')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs={'actividad_id': actividad_id}))
        # Si la actividad no está vetada no se puede levantar el veto, por lo que se redirige al usuario a la vista de detalles
        if not actividad.vetada:
            messages.error(request, 'No se puede levantar el veto a una actividad sin vetar')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_id}))
        # Si la actividad está en modo borrador, no se puede levantar el veto,
        # por lo que se redirige al usuario a la vista de detalles
        if actividad.borrador:
            messages.error(request, 'No se puede levantar el veto a una actividad que está en modo borrador')
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_id}))
        # Se intenta levantar el veto sobre la actividad
        try:
            levanta_veto_actividad(request, actividad)
        # Si sucede alguna excepción, se redirige al usuario al listado de actividades con un mensaje de error
        except Exception as e:
            messages.error(request, 'No se poseen los permisos o requisitos necesarios para realizar esta accion')
            messages.error(request, e.args)
            return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_id}))
        # En caso de éxito, se redirige al usuario al listado de actividades con un mensaje de éxito
        messages.success(request, 'Se ha levantado el veto sobre la actividad con éxito')
        return HttpResponseRedirect(reverse('actividad_detalles', kwargs = {'actividad_id': actividad_id}))


#   Funciones utiles

def actividad_no_hallada(request):
    messages.error(request, 'No se ha encontrado la actividad')
    try:
        usuario = Usuario.objects.get(django_user_id = request.user.id)
    except ObjectDoesNotExist:
        usuario = None
    return HttpResponseRedirect(reverse('actividad_listado'))