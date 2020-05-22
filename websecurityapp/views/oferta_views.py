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
from websecurityapp.forms.oferta_forms import OfertaCreacionForm, OfertaEdicionForm, OfertaVetoForm
from websecurityapp.models.oferta_models import Oferta, Solicitud
from websecurityapp.models.perfil_models import Usuario
from websecurityapp.services.oferta_services import crea_oferta, edita_oferta, elimina_oferta, veta_oferta, \
    levanta_veto_oferta, oferta_formulario, lista_ofertas, cierra_oferta, solicita_oferta, retira_solicitud_oferta, \
    lista_ofertas_propias, lista_solicitudes_propias
from websecurityapp.views.utils import get_ofertas_solicitables_y_ofertas_retirables, es_oferta_solicitable_o_retirable, \
    get_ofertas_con_actividades_vetadas
from websecurityserver.settings import numero_objetos_por_pagina



class ListadoOfertaView(LoginRequiredMixin, View):
    template_name = 'oferta/listado_ofertas.html'

    def get(self, request):
        context = {}
        # Se consulta que usuario esta autenticado en este momento
        try:
            usuario = Usuario.objects.get(django_user_id = request.user.id)
        except ObjectDoesNotExist:
            usuario = None
        # Se obtiene el listado de ofertas y se pagina
        ofertas = lista_ofertas(request)
        paginator = Paginator(ofertas, numero_objetos_por_pagina)
        page_number = request.GET.get('page')
        page_obj_ofertas = paginator.get_page(page_number)
        # De la página que se está mostrando, se obtienen las ofertas que se el usuario puede solicitar y las que el 
        # usuario puede retirar
        [ofertas_solicitables, ofertas_retirables] = get_ofertas_solicitables_y_ofertas_retirables(usuario, page_obj_ofertas)
        # Se obtienen las ofertas de la página que tienen actividades vetadas, para poder marcarlas
        ofertas_actividades_vetadas = get_ofertas_con_actividades_vetadas(page_obj_ofertas)
        # Se añaden al contexto las ofertas y el usuario y se muestra el listado
        context.update({
            'page_obj_ofertas': page_obj_ofertas,
            'usuario': usuario,
            'ofertas_solicitables': ofertas_solicitables,
            'ofertas_retirables': ofertas_retirables,
            'ofertas_actividades_vetadas': ofertas_actividades_vetadas,
            'titulo_pagina': 'Listado de ofertas',
        })
        return render(request, self.template_name, context)

class ListadoOfertaPropiaView(LoginRequiredMixin, View):
    template_name = 'oferta/listado_ofertas.html'

    def get(self, request):
        context = {}
        # Se consulta que usuario esta autenticado en este momento
        try:
            usuario = Usuario.objects.get(django_user_id = request.user.id)
        except ObjectDoesNotExist:
            usuario = None
        # Se obtiene el listado de ofertas propias y se pagina
        ofertas = lista_ofertas_propias(request)
        paginator = Paginator(ofertas, numero_objetos_por_pagina)
        page_number = request.GET.get('page')
        page_obj_ofertas = paginator.get_page(page_number)
        # Se obtienen las ofertas de la página que tienen actividades vetadas, para poder marcarlas
        ofertas_actividades_vetadas = get_ofertas_con_actividades_vetadas(page_obj_ofertas)
        # Se añaden al contexto las ofertas y el usuario y se muestra el listado
        context.update({
            'page_obj_ofertas': page_obj_ofertas,
            'usuario': usuario,
            'ofertas_actividades_vetadas': ofertas_actividades_vetadas,
            'titulo_pagina': 'Mis ofertas',
        })
        return render(request, self.template_name, context)

class CreacionOfertaView(LoginRequiredMixin, View):
    # Todas las comprobaciones de permisos de esta vista las realiza el LoginRequiredMixin
    template_name = 'oferta/creacion_ofertas.html'

    def get(self, request):
        context = {}
        # Se genera el formulario vacio de la oferta a crear
        form = OfertaCreacionForm()
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
        # Se crea un objeto formulario con los parametros de entrada dados
        form = OfertaCreacionForm(request.POST)
        # Si el formulario es valido, se trata el formulario y se crea la oferta
        if form.is_valid():
            # Se valida el formulario con mas detalle
            form.clean()
            form_data = form.cleaned_data
            # Se inserta el campo autor en el diccionario que representa el formulario
            autor = Usuario.objects.get(django_user_id = request.user.id)
            form_data.update({'autor': autor})
            # Se intenta crear la oferta
            try:
                oferta_creada = crea_oferta(form_data, request)
            # Si hay una excepcion al crear la oferta se permanece en el formulario y se incluye un mensaje de error
            except Exception as e:
                messages.error(request, 'Se ha producido un error al crear la oferta')
                # Se mete en el contexto el formulario y las variables para el estilo
                context.update({
                    'form': form, 
                    'validated': True, 
                    'form_class': 'was-validated'
                })
                # Se muestra el formulario de creación de la oferta
                return render(request, self.template_name, context)
            # Redirige al usuario a los detalles de la oferta con un mensaje de éxito
            messages.success(request, 'Se ha creado la oferta con exito')
            return HttpResponseRedirect(reverse('oferta_detalles', kwargs = {'oferta_id': oferta_creada.id}))
        # Si el formulario no es valido
        else:
            # Vuelve al formulario cuando haya un error de validacion
            # Se valida el formulario con mas detalle
            form.clean()
            # Se da un mensaje de error 
            messages.error(request, 'Se ha producido un error al crear la oferta')
            # Se mete en el contexto el formulario y las variables para el estilo
            context.update({
                'form': form, 
                'validated': True, 
                'form_class': 'was-validated'
            })
            # Se muestra el formulario de la creación de la oferta
            return render(request, self.template_name, context)

class EdicionOfertaView(LoginRequiredMixin, View):
    # Para visitar esta pagina se requiere estar autenticado y ser el autor de la
    # oferta
    # El LoginRequiredMixin comprueba que el usuario esta autenticado
    # Se debe comprobar de forma programatica que el usuario es el autor de la oferta
    template_name = 'oferta/edicion_ofertas.html'

    def get(self, request, oferta_id):
        context = {}
        # Se comprueba la que se puede editar la oferta
        res = comprueba_editar_oferta(request, oferta_id)
        # Si se ha devuelto una oferta, entoces se asigna a la variable correspondiente
        if isinstance(res, Oferta):
            oferta = res
        # Si se ha devuelto una redirección, entonces se devuelve la redirección
        elif isinstance(res, HttpResponseRedirect):
            return res
        # Se genera un formulario en base a los datos de la oferta
        form = oferta_formulario(oferta)
        # Se mete el formulario y la variables de estilo en el contexto, aparte de 
        # la id de la oferta para el atributo action del formulario
        context.update({
            'oferta_id': oferta_id, 
            'form': form, 
            'validated': False, 
            'form_class': 'needs-validation'
        })
        # Se muestra el formulario de edición de la oferta
        return render(request, self.template_name, context)

    def post(self, request, oferta_id):
        context = {}
        # Se comprueba la que se puede editar la oferta
        res = comprueba_editar_oferta(request, oferta_id)
        # Si se ha devuelto una oferta, entoces se asigna a la variable correspondiente
        if isinstance(res, Oferta):
            oferta = res
        # Si se ha devuelto una redireccion, entonces se devuelve la redirección
        elif isinstance(res, HttpResponseRedirect):
            return res
        # Se crea un objeto formulario en base a los datos recibidos
        form = OfertaEdicionForm(request.POST)
        # Si el formulario es válido, se trata el formulario y se edita la oferta
        if form.is_valid():
            # Se trata el formulario con más detalle
            form.clean()
            form_data = form.cleaned_data
            # Se prueba a editar la oferta
            try:
                edita_oferta(request, form_data, oferta)
            # En caso de excepción, se permanece en el formulario
            except Exception as e:
                # Se da un mensaje de error
                messages.error(request, 'Se ha producido un error al editar la oferta')
                # Se meten en el contexto el formulario, las variables para el estilo de 
                # la validación y la id de la oferta para el atributo action del formulario
                context.update({
                    'oferta_id': oferta_id, 
                    'form': form, 
                    'validated': True, 
                    'form_class': 'was-validated'
                })
                # Se muestra el formulario de edicion de la oferta
                return render(request, self.template_name, context)
            # Si no sucede ningún error, se redirige a los detalles de la oferta junto con un mensaje de éxito
            messages.success(request, 'Se ha editado la oferta con éxito')
            return HttpResponseRedirect(reverse('oferta_detalles', kwargs = {'oferta_id': oferta.id}))
        # Si el formulario no es valido
        else:
            # Se valida el formulario con más detalle
            form.clean()
            # Se da un mensaje de error
            messages.error(request, 'Se ha producido un error al editar la oferta')
            # Se inserta en el contexto el formulario, las variables para el estilo de la 
            # validación y el id de la oferta para el atributo action del formulario
            context.update({
                'oferta_id': oferta_id, 
                'form': form, 
                'validated': True, 
                'form_class': 'was-validated'
            })
            # Se muestra el formulario de edición al usuario
            return render(request, self.template_name, context)

class EliminacionOfertaView(LoginRequiredMixin, View):
    # Para visitar esta pagina se requiere estar autenticado y ser el autor de la
    # oferta
    # El LoginRequiredMixin comprueba que el usuario esta autenticado
    # Se debe comprobar de forma programatica que el usuario es el autor de la oferta
    template_name = 'oferta/listado_ofertas.html'

    def get(self, request, oferta_id):
        context = {}
        # Se comprueba que se puede eliminar la oferta
        res = comprueba_eliminar_oferta(request, oferta_id)
        # Si devuelve una oferta, entonces se almacena en la variable correspondiente
        if isinstance(res, Oferta):
            oferta = res
        # Si devuelve una redirección, entonces se aplica dicha redirección
        elif isinstance(res, HttpResponseRedirect):
            return res
        # Se intenta eliminar la oferta
        try:
            elimina_oferta(request, oferta)
        # Si hay cualquier excepción, se redirige al usuario los detalles de la oferta
        # y se da un mensaje de error
        except Exception as e:
            messages.error(request, 'Se ha producido un error al eliminar la oferta')
            return HttpResponseRedirect(reverse('oferta_detalles', kwargs = {'oferta_id': oferta_id}))
        # Si se elimina la oferta correctamente se redirige al usuario al listado de 
        # mensajes y se muestra un mensaje de éxito
        messages.success(request, 'Se ha eliminado la oferta con exito')
        return HttpResponseRedirect(reverse('oferta_listado'))        

class DetallesOfertaView(LoginRequiredMixin, View):
    # Se requiere estar autenticado para visitar esta página
    template_name = 'oferta/detalles_ofertas.html'

    def get(self, request, oferta_id):
        context = {}
        # Se obtiene el usuario autenticado
        try:
            usuario = Usuario.objects.get(django_user_id = request.user.id)
        except ObjectDoesNotExist as e:
            usuario = None
        # Se busca la oferta
        try:
            oferta = Oferta.objects.get(pk=oferta_id)
        # En caso de que no se encuentre la oferta, se redirige al usuario al listado de oferta
        except ObjectDoesNotExist as e:
            return oferta_no_hallada(request)
        # En caso de que la oferta no pertenezca al usuario y esté en modo borrador, entonces se redirige al usuario al
        # listado de ofertas, indicando que no puede acceder a los detalles de la oferta
        if oferta.borrador and oferta.autor != usuario:
            messages.error(request, 'No se tienen los permisos necesarios para acceder a la oferta')
            return HttpResponseRedirect(reverse('oferta_listado'))
        # Se mira si se puede solicitar o retirar la oferta, para saber si poner los botones de solicitud o retirada
        # de solicitud
        [solicitable, retirable] = es_oferta_solicitable_o_retirable(usuario, oferta)
        solicitantes = []
        if usuario == oferta.autor:
            for solicitud in list(Solicitud.objects.filter(oferta=oferta)):
                solicitantes.append(solicitud.usuario)
        # Se obtienen los solicitantes de la oferta y se paginan
        paginator_solicitantes = Paginator(solicitantes, numero_objetos_por_pagina)
        page_number_solicitantes = request.GET.get('page_solicitantes')
        page_obj_solicitantes = paginator_solicitantes.get_page(page_number_solicitantes)
        # Se obtienen las actividades requeridas en la oferta y se paginan
        actividades = oferta.actividades.all()
        paginator_actividades = Paginator(actividades, numero_objetos_por_pagina)
        page_number_actividades = request.GET.get('page_actividades')
        page_obj_actividades = paginator_actividades.get_page(page_number_actividades)
        # Se añaden al contexto la oferta y el usuario, además de las variables y listas obtenidas anteriormente
        context.update({
            'oferta': oferta,
            'usuario': usuario,
            'page_obj_actividades': page_obj_actividades,
            'retirable': retirable,
            'solicitable': solicitable,
            'page_obj_usuarios': page_obj_solicitantes,
        })
        # Se muestra la vista de detalles
        return render(request, self.template_name, context)

class VetoOfertaView(LoginRequiredMixin, View):
    # Se requiere estar autenticado para visitar esta página
    template_name = 'oferta/veto_ofertas.html'

    def get(self, request, oferta_id):
        context = {}
        # Se comprueba que se puede vetar la oferta
        res = comprueba_vetar_oferta(request, oferta_id)
        # Si el resultado es una oferta, se almacena en la variable correspondiente
        if isinstance(res, Oferta):
            oferta = res
        # Si el resultado es una redirección, entonces se aplica la redirección
        elif isinstance(res, HttpResponseRedirect):
            return res
        # Se crea un formulario vacío para el veto de oferta
        form = OfertaVetoForm()
        # Se inserta en el contexto el formulario, las variables para el estilo de 
        # validación y el id de la oferta para el atributo action del formulario
        context.update({
            'oferta_id': oferta_id, 
            'form': form, 
            'validated': False, 
            'form_class': 'needs-validation'
        })
        # Se muestra el formulario de veto de oferta
        return render(request, self.template_name, context)
        
    def post(self, request, oferta_id):
        context = {}
        # Se comprueba que se puede vetar la oferta
        res = comprueba_vetar_oferta(request, oferta_id)
        # Si el resultado es una oferta, se almacena en la variable correspondiente
        if isinstance(res, Oferta):
            oferta = res
        # Si el resultado es una redirección, entonces se aplica la redirección
        elif isinstance(res, HttpResponseRedirect):
            return res
        # Se genera un formulario con los datos introducidos
        form = OfertaVetoForm(request.POST)
        # Si el formulario es válido
        if form.is_valid():
            # Se realiza una validación con más detalle
            form.clean()
            form_data = form.cleaned_data
            # Trata de vetar la oferta
            try:
                veta_oferta(request, form_data, oferta)
            # En cualquier otro caso, se permanece en el formulario y se incluye un mensaje de error
            except Exception as e:                    
                messages.error(request, 'Se ha producido un error al vetar la oferta')
                # Se introduce en el contexto el formulario, las variables para el estilo
                # de la validación y el id de la oferta para el atributo action del formulario
                context.update({
                    'oferta_id': oferta_id, 
                    'form': form, 
                    'validated': True, 
                    'form_class': 'was-validated'
                })
                # Se muestra el formulario de veto de la oferta
                return render(request, self.template_name, context)
            # Si se ha tenido éxito, se redirige al usuario a los detalles de la oferta junto con un mensaje de éxito
            messages.success(request, 'Se ha vetado la oferta con exito')
            return HttpResponseRedirect(reverse('oferta_detalles', kwargs = {'oferta_id': oferta_id}))
        # Si el formulario no es válido
        else:
            # Se realiza una validación con más detalle
            form.clean()
            # Se muestra un mensaje de error
            messages.error(request, 'Se ha producido un error al vetar la oferta')
            # Se introduce en el contexto el formulario, las variables para el estilo de 
            # la validación y el id de la oferta para el atributo action del formulario
            context.update({
                'oferta_id': oferta_id, 
                'form': form, 
                'validated': True, 
                'form_class': 'was-validated',
            })
            # Se muestra el formulario de veto de la oferta
            return render(request, self.template_name, context)
            
class LevantamientoVetoOfertaView(LoginRequiredMixin, View):
    # Se requiere estar autenticado para visitar esta página
    template_name = 'oferta/listado_ofertas.html'

    def get(self, request, oferta_id):
        context = {}
        # Se comprueba que se puede levantar el veto sobre la oferta
        res = comprueba_levantar_veto_oferta(request, oferta_id)
        # Si el resultado es una oferta, entonces se almacena en la variable correspondiente
        if isinstance(res, Oferta):
            oferta = res
        # Si el resultado es una redirección, entonces se aplica la redirección
        elif isinstance(res, HttpResponseRedirect):
            return res
        # Se intenta levantar el veto sobre la oferta
        try:
            levanta_veto_oferta(request, oferta)
        # Si sucede alguna excepción, se redirige al usuario al listado de oferta con un mensaje de error
        except Exception as e:
            messages.error(request, 'No se poseen los permisos o requisitos necesarios para realizar esta accion')
            return HttpResponseRedirect(reverse('oferta_detalles', kwargs = {'oferta_id': oferta_id}))
        # En caso de éxito, se redirige al usuario al listado de oferta con un mensaje de éxito
        messages.success(request, 'Se ha levantado el veto sobre la oferta con éxito')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs = {'oferta_id': oferta_id}))

class CierreOfertaView(LoginRequiredMixin, View):
    template_name = 'oferta/detalles_ofertas.html'

    def get(self, request, oferta_id):
        context = {}
        # Se comprueba que se puede cerrar la oferta
        res = comprueba_cerrar_oferta(request, oferta_id)
        # Si el resultado es una oferta, entonces se almacena en la variable correspondiente
        if isinstance(res, Oferta):
            oferta = res
        # Si el resultado es una redirección, entonces se aplica la redirección
        elif isinstance(res, HttpResponseRedirect):
            return res
        # Se intenta cerrar la oferta
        try:
            cierra_oferta(request, oferta)
        # Si sucede alguna excepción, se redirige al usuario a los detalles de la oferta con un mensaje de error
        except Exception as e:
            messages.error(request, 'No se poseen los permisos o requisitos necesarios para realizar esta accion')
            return HttpResponseRedirect(reverse('oferta_detalles', kwargs = {'oferta_id': oferta_id}))
        # En caso de éxito, se redirige al usuario a los detalles de la oferta con un mensaje de éxito
        messages.success(request, 'Se ha cerrado la oferta con éxito')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs = {'oferta_id': oferta_id}))

class ListadoSolicitudPropiaView(LoginRequiredMixin, View):
    template_name = 'oferta/listado_ofertas.html'

    def get(self, request):
        context = {}
        # Se consulta cuál usuario esta autenticado en este momento
        try:
            usuario = Usuario.objects.get(django_user_id=request.user.id)
        except ObjectDoesNotExist:
            usuario = None
        ofertas = lista_solicitudes_propias(request)
        paginator = Paginator(ofertas, numero_objetos_por_pagina)
        page_number = request.GET.get('page')
        page_obj_ofertas = paginator.get_page(page_number)
        # Se averigua cuáles ofertas de la página son retirables
        ofertas_retirables = []
        for oferta in page_obj_ofertas:
            if not oferta.cerrada and not oferta.vetada:
                ofertas_retirables.append(oferta)
        # Se añaden al contexto las ofertas y el usuario y se muestra el listado
        context.update({
            'page_obj_ofertas': page_obj_ofertas,
            'usuario': usuario,
            'ofertas_retirables': ofertas_retirables,
            'titulo_pagina': 'Mis solicitudes',
        })
        return render(request, self.template_name, context)

class SolicitudOfertaView(LoginRequiredMixin, View):
    template_name = 'oferta/detalles_ofertas.html'

    def get(self, request, oferta_id):
        context = {}
        # Se comprueba que se puede solicitar la oferta
        res = comprueba_solicitar_oferta(request, oferta_id)
        # Si el resultado es una oferta, entonces se almacena en la variable correspondiente
        if isinstance(res, Oferta):
            oferta = res
        # Si el resultado es una redirección, entonces se aplica la redirección
        elif isinstance(res, HttpResponseRedirect):
            return res
        # Se intenta solicitar la oferta
        try:
            solicita_oferta(request, oferta)
        # Si sucede alguna excepción, se redirige al usuario a los detalles de la oferta con un mensaje de error
        except Exception as e:
            messages.error(request, 'No se poseen los permisos o requisitos necesarios para realizar esta accion')
            return HttpResponseRedirect(reverse('oferta_detalles', kwargs = {'oferta_id': oferta_id}))
        # En caso de éxito, se redirige al usuario a los detalles de la oferta con un mensaje de éxito
        messages.success(request, 'Se ha realizado la solicitud con éxito')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs = {'oferta_id': oferta_id}))

class RetiroSolicitudOfertaView(LoginRequiredMixin, View):
    template_name = 'oferta/detalles_ofertas.html'

    def get(self, request, oferta_id):
        context = {}
        # Se comprueba que se puede retirar la solicitud de la oferta
        res = comprueba_retirar_solicitud_oferta(request, oferta_id)
        # Si el resultado es una solicitud, entonces se almacena en la variable correspondiente
        if isinstance(res, Solicitud):
            solicitud = res
        # Si el resultado es una redirección, entonces se aplica la redirección
        elif isinstance(res, HttpResponseRedirect):
            return res
        # Se intenta retirar la solicitud de la oferta
        try:
            retira_solicitud_oferta(request, solicitud)
        # Si sucede alguna excepción, se redirige al usuario a los detalles de la oferta con un mensaje de error
        except Exception as e:
            messages.error(request, 'No se poseen los permisos o requisitos necesarios para realizar esta accion')
            return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
        # En caso de éxito, se redirige al usuario a los detalles de la oferta con un mensaje de éxito
        messages.success(request, 'Se ha retirado la solicitud con éxito')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))



#   Funciones utiles

def oferta_no_hallada(request):
    messages.error(request, 'No se ha encontrado la oferta')
    try:
        usuario = Usuario.objects.get(django_user_id = request.user.id)
    except ObjectDoesNotExist:
        usuario = None
    return HttpResponseRedirect(reverse('oferta_listado'))

def comprueba_editar_oferta(request, oferta_id):
    try:
        oferta = Oferta.objects.get(pk=oferta_id)
    # Si no existe la oferta, redirige al usuario al listado de oferta
    except ObjectDoesNotExist as e:
        return oferta_no_hallada(request)
    # Si la oferta no está en modo borrador, no se puede editar
    if not oferta.borrador:
        messages.error(request, 'No se puede editar una oferta que no está en modo borrador')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # No se puede editar una oferta cerrada
    if oferta.cerrada:
        messages.error(request, 'No se puede editar una oferta cerrada')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # No se puede editar una ofeta vetada
    if oferta.vetada:
        messages.error(request, 'No se puede editar una oferta vetada')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Se comprueba que el usuario es el autor de la oferta
    # Si el usuario no es el autor de la oferta, se redirige al usuario a la
    # página de los detalles de la oferta con un mensaje de error
    if not request.user.id == oferta.autor.django_user.id:
        messages.error(request, 'No se poseen los permisos necesarios para editar la oferta')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Se devuelve la oferta comprobada para poder usarla más adelante
    return oferta

def comprueba_eliminar_oferta(request, oferta_id):
    # Se comprueba que existe la oferta
    try:
        oferta = Oferta.objects.get(pk=oferta_id)
    # Si la oferta no existe, se redirige al usuario al listado de oferta
    except ObjectDoesNotExist as e:
        return oferta_no_hallada(request)
    # Si la oferta no está en modo borrador, no se puede eliminar
    if not oferta.borrador:
        messages.error(request, 'No se puede eliminar una oferta que no está en modo borrador')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Si la oferta está cerrada, no se puede eliminar
    if oferta.cerrada:
        messages.error(request, 'No se puede eliminar una oferta cerrada')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Si la oferta está vetada, no se puede eliminar
    if oferta.vetada:
        messages.error(request, 'No se puede eliminar una oferta vetada')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Se comprueba que el usuario es el autor de la oferta
    # Si el usuario no es el autor de la oferta, se redirige al usuario a la
    # página de los detalles de la oferta con un mensaje de error
    if not request.user.id == oferta.autor.django_user.id:
        messages.error(request, 'No se poseen los permisos necesarios para editar la oferta')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Se devuelve la oferta para usarla más adelante
    return oferta

def comprueba_vetar_oferta(request, oferta_id):
    # Se comprueba que existe la oferta
    try:
        oferta = Oferta.objects.get(pk=oferta_id)
    # Si no existe se redirige al usuario al listado de oferta
    except ObjectDoesNotExist as e:
        return oferta_no_hallada(request)
    # Si el usuario no es un administrador, entonces se le redirige a los detalles de la oferta
    usuario = Usuario.objects.get(django_user__id=request.user.id)
    if not usuario.es_admin:
        messages.error(request, 'No se poseen los permisos necesarios para vetar la oferta')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Si la oferta está vetada, no se puede vetar
    if oferta.vetada:
        messages.error(request, 'No se puede vetar una oferta ya vetada')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Si la oferta está en modo borrador, no se puede vetar
    if oferta.borrador:
        messages.error(request, 'No se puede vetar una oferta que está en modo borrador')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Si la oferta está cerrada, no se puede vetar
    if oferta.cerrada:
        messages.error(request, 'No se puede vetar una oferta que está cerrada')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    return oferta

def comprueba_levantar_veto_oferta(request, oferta_id):
    # Se trata de obtener la oferta
    try:
        oferta = Oferta.objects.get(pk=oferta_id)
    # Si no se encuentra la oferta se redirige al listado de oferta
    except ObjectDoesNotExist as e:
        return oferta_no_hallada(request)
    # Si el usuario no es un administrador, entonces se le redirige a los detalles de la oferta
    usuario = Usuario.objects.get(django_user__id=request.user.id)
    if not usuario.es_admin:
        messages.error(request, 'No se poseen los permisos necesarios para levantar el veto sobre la oferta')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Si la oferta no está vetada, no se puede levantar el veto
    if not oferta.vetada:
        messages.error(request, 'No se puede levantar el veto a una oferta sin vetar')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Si la oferta está en modo borrador, no se puede levantar el veto
    if oferta.borrador:
        messages.error(request, 'No se puede levantar el veto a una oferta que está en modo borrador')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Si la oferta está cerrada, entonces no se puede levantar el veto
    if oferta.cerrada:
        messages.error(request, 'No se puede levantar el veto a una oferta que está cerrada')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    return oferta

def comprueba_cerrar_oferta(request, oferta_id):
    # Se trata de obtener la oferta
    try:
        oferta = Oferta.objects.get(pk=oferta_id)
    # Si no se encuentra la oferta, se redirige al listado de oferta
    except ObjectDoesNotExist as e:
        return oferta_no_hallada(request)
    # Si la oferta está vetada, no se puede cerrar
    if oferta.vetada:
        messages.error(request, 'No se puede cerrar una oferta vetada')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Si la oferta está en modo borrador, no se puede cerrar
    if oferta.borrador:
        messages.error(request, 'No se puede cerrar una oferta que está en modo borrador')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Si la oferta está cerrada, entonces no se puede cerrar
    if oferta.cerrada:
        messages.error(request, 'No se puede cerrar una oferta que está cerrada')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    return oferta

def comprueba_solicitar_oferta(request, oferta_id):
    # Se trata de obtener la oferta
    try:
        oferta = Oferta.objects.get(pk=oferta_id)
    # Si no se encuentra la oferta se redirige al listado de oferta
    except ObjectDoesNotExist as e:
        return oferta_no_hallada(request)
    # Si la oferta está vetada, no se puede solicitar
    if oferta.vetada:
        messages.error(request, 'No se puede solicitar una oferta vetada')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Si la oferta está en modo borrador, no se puede solicitar
    if oferta.borrador:
        messages.error(request, 'No se puede solicitar una oferta que está en modo borrador')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Si la oferta está cerrada, entonces no se puede solicitar
    if oferta.cerrada:
        messages.error(request, 'No se puede solicitar una oferta que está cerrada')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Comprueba que el usuario no sea el autor de la oferta
    usuario = Usuario.objects.get(django_user__id=request.user.id)
    if usuario == oferta.autor:
        messages.error(request, 'No se puede solicitar una oferta de la que se es autor')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Comprueba que el usuario no tenga ya una solicitud en la oferta
    tiene_solicitud = True
    try:
        Solicitud.objects.get(usuario=usuario, oferta=oferta)
    except ObjectDoesNotExist as e:
        tiene_solicitud = False
    if tiene_solicitud:
        messages.error(request, 'No se puede solicitar una oferta en la que ya se tiene una solicitud')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Comprueba que ninguna de las actividades marcadas como requisitos para solicitar la oferta ha sido vetada
    actividades_requeridas = oferta.actividades.all()
    actividades_realizadas = usuario.actividades_realizadas.all()
    for actividad_requerida in actividades_requeridas:
        if actividad_requerida.vetada:
            messages.error(request, 'No se puede solicitar una oferta que tiene entre sus requisitos actividades vetadas')
            return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Comprueba que el usuario cumple con los requisitos
    cumple_requisitos = True
    for actividad_requerida in actividades_requeridas:
        if not actividad_requerida in actividades_realizadas:
            cumple_requisitos = False
    if not cumple_requisitos:
        messages.error(request, 'No se puede solicitar una oferta cuyos actividades requeridas no se han resuelto')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    return oferta

def comprueba_retirar_solicitud_oferta(request, oferta_id):
    # Se trata de obtener la oferta
    try:
        oferta = Oferta.objects.get(pk=oferta_id)
    # Si no se encuentra la oferta se redirige al listado de oferta
    except ObjectDoesNotExist as e:
        return oferta_no_hallada(request)
    # Si la oferta está vetada, no se puede retirar la solicitud
    if oferta.vetada:
        messages.error(request, 'No se puede retirar la solicitud de una oferta vetada')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Si la oferta está en modo borrador, no se puede retirar la solicitud
    if oferta.borrador:
        messages.error(request, 'No se puede retirar la solicitud de una oferta que está en modo borrador')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Si la oferta está cerrada, entonces no se puede retirar la solicitud
    if oferta.cerrada:
        messages.error(request, 'No se puede retirar la solicitud de una oferta que está cerrada')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))
    # Si el usuario no ha solicitado la oferta, entonces no puede retirar la solicitud
    usuario = Usuario.objects.get(django_user__id=request.user.id)
    try:
        solicitud = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        return solicitud
    except ObjectDoesNotExist as e:
        messages.error(request, 'No se puede retirar la solicitud de una oferta en la que no se tiene una solicitud')
        return HttpResponseRedirect(reverse('oferta_detalles', kwargs={'oferta_id': oferta_id}))


