from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.db.models import Q, OuterRef, Exists
from django.core.exceptions import ObjectDoesNotExist

from datetime import date
import re

from websecurityapp.models.actividad_models import Actividad
from websecurityapp.models.oferta_models import Oferta, Solicitud
from websecurityapp.models.perfil_models import Usuario
from websecurityapp.models.oferta_models import Oferta
from websecurityapp.views.oferta_views import CreacionOfertaView
from websecurityapp.views.utils import get_ofertas_solicitables_y_ofertas_retirables, es_oferta_solicitable_o_retirable
from websecurityapp.test_unit.utils import test_listado, numero_paginas, paginar_lista
from websecurityserver.settings import numero_objetos_por_pagina

class OfertaTestCase(TestCase):
    
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        exec(open('populate_database.py').read())

    # Método que simula un login
    def login(self, username, password):
        response = self.client.post('/login/', {'username': username, 'password': password})
        usuario = Usuario.objects.get(django_user__username = username)
        return usuario

    # Método que simula un logout
    def logout(self):
        self.client.get('/logout/')



    # LISTADO

    # Un usuario accede al listado de ofertas correctamente
    def test_lista_ofertas(self):
        # Se inicializan variables y el usuario se loguea
        username = 'usuario1'
        password = 'usuario1'
        self.login(username, password)
        # Se crean variables con los datos correctos
        usuario_esperado = Usuario.objects.get(django_user__username=username)
        ofertas_esperadas = Oferta.objects.annotate(actividades_vetadas=Exists(
                Oferta.objects.filter(id=OuterRef('id'), actividades__vetada=True))
            ).exclude((Q(cerrada=True) | Q(borrador=True) | Q(vetada=True) | Q(actividades_vetadas=True)) & ~Q(autor=usuario_esperado)
            ).order_by('id')
        datos_esperados = dict()
        datos_esperados['usuario'] = usuario_esperado
        # Se van a obtener las ofertas solicitables y retirables por pagina
        dict_ofertas_solicitables_esperadas = dict()
        dict_ofertas_retirables_esperadas = dict()
        dict_ofertas_esperadas = paginar_lista(ofertas_esperadas)
        # Se recorren todas las paginas y se obtienen los diccionarios con sendos grupos de actividades paginadas
        for n_pagina in range(1, numero_paginas(ofertas_esperadas) + 1):
            [dict_ofertas_solicitables_esperadas[n_pagina], dict_ofertas_retirables_esperadas[n_pagina]] \
                = get_ofertas_solicitables_y_ofertas_retirables(usuario_esperado, dict_ofertas_esperadas[n_pagina])
        datos_esperados['ofertas_solicitables'] = dict_ofertas_solicitables_esperadas
        datos_esperados['ofertas_retirables'] = dict_ofertas_retirables_esperadas
        datos_esperados['titulo_pagina'] = 'Listado de ofertas'
        # Se comprueban los listados
        test_listado(self,
            url = reverse('oferta_listado'),
            status_code = 200,
            dato_lista = 'page_obj_ofertas',
            page_param = 'page',
            datos_esperados = datos_esperados,
            lista_esperada = ofertas_esperadas
        )
        # El usuario se desloguea
        self.logout()

    # Un administrador accede al listado de ofertas correctamente
    def test_lista_ofertas_admin(self):
        # Se inicializan variables y el usuario se loguea
        username = 'usuario2'
        password = 'usuario2'
        self.login(username, password)
        # Se crean variables con los datos correctos
        usuario_esperado = Usuario.objects.get(django_user__username=username)
        ofertas_esperadas = Oferta.objects.filter(Q(autor__django_user__username=username) |
            (Q(borrador=False) & Q(cerrada=False))).order_by('id')
        datos_esperados = dict()
        datos_esperados['usuario'] = usuario_esperado
        # Se van a obtener las ofertas solicitables y retirables por pagina
        dict_ofertas_solicitables_esperadas = dict()
        dict_ofertas_retirables_esperadas = dict()
        dict_ofertas_esperadas = paginar_lista(ofertas_esperadas)
        # Se recorren todas las paginas y se obtienen los diccionarios con sendos grupos de actividades paginadas
        for n_pagina in range(1, numero_paginas(ofertas_esperadas) + 1):
            [dict_ofertas_solicitables_esperadas[n_pagina], dict_ofertas_retirables_esperadas[n_pagina]] \
                = get_ofertas_solicitables_y_ofertas_retirables(usuario_esperado, dict_ofertas_esperadas[n_pagina])
        datos_esperados['ofertas_solicitables'] = dict_ofertas_solicitables_esperadas
        datos_esperados['ofertas_retirables'] = dict_ofertas_retirables_esperadas
        datos_esperados['titulo_pagina'] = 'Listado de ofertas'
        # Se comprueban los listados
        test_listado(self,
            url = reverse('oferta_listado'),
            status_code = 200,
            dato_lista = 'page_obj_ofertas',
            page_param = 'page',
            datos_esperados = datos_esperados,
            lista_esperada = ofertas_esperadas
        )
        # El usuario se desloguea
        self.logout()

    # Un usuario accede al listado de ofertas propias correctamente
    def test_lista_ofertas_propias(self):
        # Se inicializan variables y el usuario se loguea
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se crean variables con los datos correctos
        usuario_esperado = Usuario.objects.get(django_user__username=username)
        ofertas_esperadas = Oferta.objects.filter(autor=usuario).order_by('id')
        datos_esperados = dict()
        datos_esperados['usuario'] = usuario_esperado
        datos_esperados['titulo_pagina'] = 'Mis ofertas'
        # Se comprueban los listados
        test_listado(self,
            url = reverse('oferta_listado_propio'),
            status_code = 200,
            dato_lista = 'page_obj_ofertas',
            page_param = 'page',
            datos_esperados = datos_esperados,
            lista_esperada = ofertas_esperadas
        )
        # El usuario se desloguea
        self.logout()

    # Un usuario accede al listado de ofertas que ha solicitado
    def test_lista_solicitudes_propias(self):
        # Se inicializan variables y el usuario se loguea
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se crean variables con los datos correctos
        usuario_esperado = Usuario.objects.get(django_user__username=username)
        ofertas_esperadas = []
        for solicitud in list(Solicitud.objects.filter(usuario=usuario).order_by('id')):
            ofertas_esperadas.append(solicitud.oferta)
        datos_esperados = dict()
        datos_esperados['usuario'] = usuario_esperado
        datos_esperados = dict()
        datos_esperados['usuario'] = usuario_esperado
        # Se van a obtener las ofertas solicitables y retirables por pagina
        dict_ofertas_retirables_esperadas = dict()
        dict_ofertas_esperadas = paginar_lista(ofertas_esperadas)
        # Se recorren todas las paginas y se obtienen los diccionarios con sendos grupos de actividades paginadas
        for n_pagina in range(1, numero_paginas(ofertas_esperadas) + 1):
            dict_ofertas_retirables_esperadas[n_pagina] = get_ofertas_solicitables_y_ofertas_retirables(
                usuario_esperado, dict_ofertas_esperadas[n_pagina])[1]
        datos_esperados['ofertas_retirables'] = dict_ofertas_retirables_esperadas
        datos_esperados['titulo_pagina'] = 'Mis solicitudes'
        # Se comprueban los listados
        test_listado(self,
            url = reverse('oferta_listado_solicitud_propio'),
            status_code = 200,
            dato_lista = 'page_obj_ofertas',
            page_param = 'page',
            datos_esperados = datos_esperados,
            lista_esperada = ofertas_esperadas
        )
        # El usuario se desloguea
        self.logout()



    # DETALLES

    # Un usuario accede a los detalles de una oferta correctamente
    def test_detalles_oferta(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        self.login(username, password)
        # Se obtienen los datos esperados
        usuario_esperado = Usuario.objects.get(django_user__username = username)
        oferta_esperada = Oferta.objects.filter(Q(autor__django_user__username = username) & Q(borrador = True)).first()
        [es_solicitable, es_retirable] = es_oferta_solicitable_o_retirable(usuario_esperado, oferta_esperada)
        actividades_esperadas = oferta_esperada.actividades.all()
        solicitantes_esperados = []
        for solicitud in list(Solicitud.objects.filter(oferta=oferta_esperada)):
            solicitantes_esperados.append(solicitud.usuario)
        # Se simula que el usuario accede a los detalles de la oferta
        response = self.client.get('/oferta/detalles/{}/'.format(oferta_esperada.id))
        # Se obtienen los datos recibidos en la petición
        usuario_recibido = response.context['usuario']
        oferta_recibida = response.context['oferta']
        # Se comprueba que los datos son correctos
        self.assertEqual(response.status_code, 200)
        self.assertEqual(oferta_esperada, oferta_recibida)
        self.assertEqual(usuario_esperado, usuario_recibido)
        self.assertEqual(es_retirable, response.context['retirable'])
        self.assertEqual(es_solicitable, response.context['solicitable'])
        # Se comprueban los listados
        test_listado(self,
            lista_esperada = actividades_esperadas,
            page_param = 'page_actividades',
            dato_lista = 'page_obj_actividades',
            url = reverse('oferta_detalles', kwargs={'oferta_id': oferta_esperada.id}),
            datos_esperados = dict(),
            status_code = 200)
        test_listado(self,
            lista_esperada = solicitantes_esperados,
            page_param = 'page_solicitantes',
            dato_lista = 'page_obj_usuarios',
            url = reverse('oferta_detalles', kwargs={'oferta_id': oferta_esperada.id}),
            datos_esperados = dict(),
            status_code = 200)
        # El usuario se desloguea
        self.logout()

    # Un usuario accede a los detalles de una oferta que no existe
    def test_detalles_oferta_no_existe(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        id = 0
        self.login(username, password)
        # Se simula que el usuario accede a los detalles de la oferta
        response = self.client.get('/oferta/detalles/{}/'.format(id))
        # Se comprueba que los datos son correctos, el usuario es redirigido al listado al no poder hallarse
        # la oferta cuyos detalles se quieren ver
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/listado/')
        # El usuario se desloguea
        self.logout()



    # CREACIÓN

    # Un usuario crea una oferta correctamente
    def test_crea_oferta(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se sacan las variables necesarias para comparar los datos
        numero_ofertas_antes = Oferta.objects.all().count()
        autor_esperado = Usuario.objects.get(django_user__username = 'usuario1')
        # Se asignan variables para los datos de entrada
        titulo = 'test_crea'
        descripcion = 'test_crea'
        actividades = list(Actividad.objects.filter(borrador=False, vetada=False))[:2]
        actividades_post = []
        for actividad in actividades:
            actividades_post.append(actividad.id)
        # Se realiza la petición para crear la oferta
        response = self.client.post('/oferta/creacion/', {
            'titulo': titulo,
            'descripcion': descripcion,
            'actividades': actividades_post
        })
        # Se obtienen las variables de salida
        numero_ofertas_despues = Oferta.objects.all().count()
        oferta_creada = Oferta.objects.all().order_by('id').last()
        # Se comparan los datos, se comprueba que el usuario es redirigido a la página de detalles de la oferta
        # tras crearla
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta_creada.id))
        self.assertEqual(numero_ofertas_antes, numero_ofertas_despues - 1)
        # Se comprueba que los datos almacenados son los esperados
        self.assertEqual(oferta_creada.titulo, titulo)
        self.assertEqual(oferta_creada.descripcion, descripcion)
        self.assertEqual(list(oferta_creada.actividades.all()), actividades)
        self.assertFalse(oferta_creada.cerrada)
        self.assertTrue(oferta_creada.borrador)
        self.assertFalse(oferta_creada.vetada)
        self.assertIsNone(oferta_creada.motivo_veto)
        self.assertEqual(oferta_creada.fecha_creacion, date.today())
        self.assertEqual(oferta_creada.autor, usuario)
        # Se comprueba que el identificador de la oferta sigue el patrón indicado
        indentificador_regex = re.compile('^OFR-\w{10}$')
        self.assertEqual(indentificador_regex.match(oferta_creada.identificador) != None, True)
        # El usuario se desloguea
        self.logout()
        
    # Un usuario crea una oferta sin estar autenticado
    def test_crea_oferta_sin_loguear(self):
        # Se sacan las variables necesarias para comparar los datos
        numero_ofertas_antes = Oferta.objects.all().count()
        # Se asignan variables para los datos de entrada
        titulo = 'test_crea_sin_loguear'
        descripcion = 'test_crea_sin_loguear'
        actividades = list(Actividad.objects.filter(borrador=False, vetada=False))[:2]
        actividades_post = []
        for actividad in actividades:
            actividades_post.append(actividad.id)
        # Se realiza la petición para crear la oferta
        response = self.client.post('/oferta/creacion/', {
            'titulo': titulo, 
            'descripcion': descripcion,
            'actividades': actividades_post,
        })
        # Se obtienen las varibles de salida
        numero_ofertas_despues = Oferta.objects.all().count()
        # Se comparan los datos y se comprueba que no se ha creado la oferta, además de que el usuario ha sido
        # redirigido a la página de login al acceder a una página que requiere autenticación
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/oferta/creacion/')
        self.assertEqual(numero_ofertas_antes, numero_ofertas_despues)

    # Un usuario crea una oferta usando datos no válidos
    def test_crea_oferta_incorrecta(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        self.login(username, password)
        # Se sacan las variables necesarias para comparar los datos
        numero_ofertas_antes = Oferta.objects.all().count()
        # Se asignan variables para los datos de entrada
        titulo = ''
        descripcion = 'test_crea_incorrecta'
        actividades = list(Actividad.objects.filter(borrador=False, vetada=False))[:2]
        actividades_post = []
        for actividad in actividades:
            actividades_post.append(actividad.id)
        # Se realiza la petición para crear la oferta
        response = self.client.post('/oferta/creacion/', {
            'descripcion': descripcion,
            'actividades': actividades_post
        })
        # Se obtienen las variables de salida
        numero_ofertas_despues = Oferta.objects.all().count()
        # Se comparan los datos y se comprueba que no se ha creado la oferta, se debe comprobar además que se ha
        # obtenido la página sin redirección y que se ha obtenido correctamente, debido a que se permanece en el 
        # formulario al suceder un error de validación
        self.assertEqual(response.status_code, 200)
        self.assertEqual(numero_ofertas_antes, numero_ofertas_despues)
        # Se desloguea el usuario
        self.logout()

    # Un usuario crea una oferta usando una actividad vetada
    def test_crea_oferta_actividad_vetada(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        self.login(username, password)
        # Se sacan las variables necesarias para comparar los datos
        numero_ofertas_antes = Oferta.objects.all().count()
        # Se asignan variables para los datos de entrada
        titulo = 'test_crea_vetada'
        descripcion = 'test_crea_vetada'
        actividades = list(Actividad.objects.filter(borrador=False, vetada=False))[:2]
        actividades_post = []
        for actividad in actividades:
            actividades_post.append(actividad.id)
        actividad_vetada = Actividad.objects.filter(vetada=True).first()
        actividades_post.append(actividad_vetada)
        # Se realiza la petición para crear la oferta
        response = self.client.post('/oferta/creacion/', {
            'titulo': titulo,
            'descripcion': descripcion,
            'actividades': actividades_post
        })
        # Se obtienen las varibles de salida
        numero_ofertas_despues = Oferta.objects.all().count()
        # Se comparan los datos y se comprueba que no se ha creado la oferta, se debe comprobar además que se ha
        # obtenido la página sin redirección y que se ha obtenido correctamente, debido a que se permanece en el
        # formulario al suceder un error de validación
        self.assertEqual(response.status_code, 200)
        self.assertEqual(numero_ofertas_antes, numero_ofertas_despues)
        # Se desloguea el usuario
        self.logout()

    # Un usuario crea una oferta usando una actividad en modo borrador
    def test_crea_oferta_actividad_borrador(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        self.login(username, password)
        # Se sacan las variables necesarias para comparar los datos
        numero_ofertas_antes = Oferta.objects.all().count()
        # Se asignan variables para los datos de entrada
        titulo = 'test_crea_vetada'
        descripcion = 'test_crea_vetada'
        actividades = list(Actividad.objects.filter(borrador=False, vetada=False))[:2]
        actividades_post = []
        for actividad in actividades:
            actividades_post.append(actividad.id)
        actividad_borrador = Actividad.objects.filter(borrador=True).first()
        actividades_post.append(actividad_borrador)
        # Se realiza la petición para crear la oferta
        response = self.client.post('/oferta/creacion/', {
            'titulo': titulo,
            'descripcion': descripcion,
            'actividades': actividades_post
        })
        # Se obtienen las variables de salida
        numero_ofertas_despues = Oferta.objects.all().count()
        # Se comparan los datos y se comprueba que no se ha creado la oferta, se debe comprobar además que se ha
        # obtenido la página sin redirección y que se ha obtenido correctamente, debido a que se permanece en el
        # formulario al suceder un error de validación
        self.assertEqual(response.status_code, 200)
        self.assertEqual(numero_ofertas_antes, numero_ofertas_despues)
        # Se desloguea el usuario
        self.logout()



    # EDICIÓN
    
    # Un usuario edita una oferta correctamente
    def test_edita_oferta(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        oferta = Oferta.objects.filter(autor__django_user__username=username, borrador=True, cerrada=False).first()
        self.login(username, password)
        # Se asignan variables para los datos de entrada
        titulo = 'test_edita'
        descripcion = 'test_edita'
        borrador = False
        actividades = list(Actividad.objects.filter(borrador=False, vetada=False))[:2]
        actividades_post = []
        for actividad in actividades:
            actividades_post.append(actividad.id)
        # Se realiza la petición para editar la oferta
        response = self.client.post('/oferta/edicion/{}/'.format(oferta.id), {
            'titulo': titulo, 
            'descripcion': descripcion,
            'actividades': actividades_post,
            'borrador': borrador
        })
        # Se obtienen las variables de salida
        oferta_editada = Oferta.objects.get(pk = oferta.id)
        # Se comparan los datos, se debe comprobar que el usuario ha sido redirigido a la página de detalles de la 
        # oferta tras ser editada
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        # Se comprueba que los datos almacenados son los esperados
        self.assertEqual(oferta, oferta_editada)
        self.assertEqual(oferta_editada.titulo, titulo)
        self.assertEqual(oferta_editada.descripcion, descripcion)
        self.assertEqual(oferta_editada.borrador, borrador)
        self.assertEqual(list(oferta_editada.actividades.all()), actividades)
        self.assertFalse(oferta_editada.vetada)
        self.assertIsNone(oferta_editada.motivo_veto)
        self.assertEqual(oferta_editada.fecha_creacion, oferta.fecha_creacion)
        self.assertEqual(oferta_editada.identificador, oferta.identificador)
        # El usuario se desloguea
        self.logout()

    # Un usuario edita un oferta sin estar autenticado
    def test_edita_oferta_sin_loguear(self):
        # Se inicializan variables y se loguea el usuario
        oferta = Oferta.objects.filter(borrador=True, cerrada=False).first()
        # Se asignan variables para los datos de entrada
        titulo = 'test_edita_sin_loguear'
        descripcion = 'test_edita_sin_loguear'
        borrador = False
        actividades = list(Actividad.objects.filter(borrador=False, vetada=False))[:2]
        actividades_post = []
        for actividad in actividades:
            actividades_post.append(actividad.id)
        # Se realiza la petición para editar la oferta
        response = self.client.post('/oferta/edicion/{}/'.format(oferta.id), {
            'titulo': titulo, 
            'descripcion': descripcion,
            'borrador': borrador,
            'actividades': actividades_post
        })
        oferta_despues = Oferta.objects.get(pk = oferta.id)
        # Se comparan los datos, se debe comprobar que el usuario ha sido redirigido a la página de login, puesto a que 
        # ha accedido a una página que require autenticación sin estar autenticado
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/oferta/edicion/{}/'.format(oferta.id))
        # Se comprueba que no se ha editado ninguno de los campos editables
        self.assertEqual(oferta_despues.titulo, oferta.titulo)
        self.assertEqual(oferta_despues.descripcion, oferta.descripcion)
        self.assertEqual(oferta_despues.borrador, oferta.borrador)
        self.assertEqual(oferta_despues.actividades, oferta.actividades)
        # El usuario se desloguea
        self.logout()

    # Un usuario edita una oferta que no es suya
    def test_edita_oferta_usuario_incorrecto(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        oferta = Oferta.objects.filter(borrador=True, cerrada=False).exclude(autor__django_user__username=username).first()
        self.login(username, password)
        # Se asignan variables para los datos de entrada
        titulo = 'test_edita_incorrecto'
        descripcion = 'test_edita_incorrecto'
        borrador = False
        actividades = list(Actividad.objects.filter(borrador=False, vetada=False))[:2]
        actividades_post = []
        for actividad in actividades:
            actividades_post.append(actividad.id)
        # Se realiza la petición para editar la oferta
        response = self.client.post('/oferta/edicion/{}/'.format(oferta.id), {
            'titulo': titulo, 
            'descripcion': descripcion,
            'borrador': borrador,
            'actividades' : actividades_post
        })
        oferta_despues = Oferta.objects.get(pk = oferta.id)
        # Se comparan los datos y se comprueba que el usuario ha sido redirigido a la página de detalles de la 
        # oferta. Esto se debe a que no puede editar una oferta que no le pertenece.
        self.assertEqual(response.status_code, 302)
        # Se indica que se espera un codigo 302 en la respuesta debido  otra redireccion
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id), target_status_code=302)
        # Se comprueba que no se ha editado ninguno de los campos editables
        self.assertEqual(oferta_despues.titulo, oferta.titulo)
        self.assertEqual(oferta_despues.descripcion, oferta.descripcion)
        self.assertEqual(oferta_despues.borrador, oferta.borrador)
        self.assertEqual(oferta_despues.actividades, oferta.actividades)
        # El usuario se desloguea
        self.logout()

    # Un usuario edita una oferta que no está en modo borrador
    def test_edita_oferta_no_borrador(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        oferta = Oferta.objects.filter(borrador=False, autor__django_user__username=username, cerrada=False).first()
        self.login(username, password)
        # Se asignan variables para los datos de entrada
        titulo = 'test_edita_incorrecto'
        descripcion = 'test_edita_incorrecto'
        borrador = False
        actividades = list(Actividad.objects.filter(borrador=False, vetada=False))[:2]
        actividades_post = []
        for actividad in actividades:
            actividades_post.append(actividad.id)
        # Se realiza la petición para editar la oferta
        response = self.client.post('/oferta/edicion/{}/'.format(oferta.id), {
            'titulo': titulo, 
            'descripcion': descripcion,
            'actividades' : actividades_post,
            'borrador': borrador
        })
        oferta_despues = Oferta.objects.get(pk = oferta.id)
        # Se comparan los datos y se comprueba que el usuario ha sido redirigido a la página de detalles de la 
        # oferta. Esto se debe a que no puede editar una oferta que no está en modo borrador.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        # Se comprueba que no se ha editado nada
        self.assertEqual(oferta_despues.titulo, oferta.titulo)
        self.assertEqual(oferta_despues.descripcion, oferta.descripcion)
        self.assertEqual(oferta_despues.borrador, oferta.borrador)
        self.assertEqual(oferta_despues.actividades, oferta.actividades)
        # El usuario se desloguea
        self.logout()

    # Un usuario edita una oferta que está cerrada
    def test_edita_oferta_cerrada(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        oferta = Oferta.objects.filter(autor__django_user__username=username, cerrada=True).first()
        self.login(username, password)
        # Se asignan variables para los datos de entrada
        titulo = 'test_edita_incorrecto'
        descripcion = 'test_edita_incorrecto'
        borrador = False
        actividades = list(Actividad.objects.filter(borrador=False, vetada=False))[:2]
        actividades_post = []
        for actividad in actividades:
            actividades_post.append(actividad.id)
        # Se realiza la petición para editar la oferta
        response = self.client.post('/oferta/edicion/{}/'.format(oferta.id), {
            'titulo': titulo,
            'descripcion': descripcion,
            'actividades': actividades_post,
            'borrador': borrador
        })
        oferta_despues = Oferta.objects.get(pk=oferta.id)
        # Se comparan los datos y se comprueba que el usuario ha sido redirigido a la página de detalles de la
        # oferta. Esto se debe a que no puede editar una oferta que está cerrada.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        # Se comprueba que no se ha editado nada
        self.assertEqual(oferta_despues.titulo, oferta.titulo)
        self.assertEqual(oferta_despues.descripcion, oferta.descripcion)
        self.assertEqual(oferta_despues.borrador, oferta.borrador)
        self.assertEqual(oferta_despues.actividades, oferta.actividades)
        # El usuario se desloguea
        self.logout()

    # Un usuario edita una oferta usando datos no válidos
    def test_edita_oferta_incorrecta(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        oferta = Oferta.objects.filter(borrador=True, autor__django_user__username=username, cerrada=False).first()
        self.login(username, password)
        # Se asignan variables para los datos de entrada
        descripcion = 'test_edita_incorrecta'
        borrador = False
        actividades = list(Actividad.objects.filter(borrador=False, vetada=False))[:2]
        actividades_post = []
        for actividad in actividades:
            actividades_post.append(actividad.id)
        # Se realiza la petición para editar la oferta
        response = self.client.post('/oferta/edicion/{}/'.format(oferta.id), {
            'descripcion': descripcion,
            'borrador': borrador,
            'actividades': actividades_post
        })
        oferta_despues = Oferta.objects.get(pk = oferta.id)
        # Se comparan los datos. Se comprueba que no ha sucedido ninguna redirección y que la página se ha obtenido
        # correctamente. Esto se debe a que al haber un error de validación el usuario permanece en el formulario.
        self.assertEqual(response.status_code, 200)
        # Se comprueba que no se ha editado nada
        self.assertEqual(oferta_despues.titulo, oferta.titulo)
        self.assertEqual(oferta_despues.descripcion, oferta.descripcion)
        self.assertEqual(oferta_despues.borrador, oferta.borrador)
        self.assertEqual(oferta_despues.actividades, oferta.actividades)
        # El usuario se desloguea
        self.logout()

    # Un usuario edita una oferta insertando actividades vetadas
    def test_edita_oferta_actividad_vetada(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        oferta = Oferta.objects.filter(autor__django_user__username=username, cerrada=False, borrador=True).first()
        self.login(username, password)
        # Se asignan variables para los datos de entrada
        titulo = 'test_edita_incorrecto'
        descripcion = 'test_edita_incorrecto'
        borrador = False
        actividades = list(Actividad.objects.filter(borrador=False, vetada=False))[:2]
        actividades_post = []
        for actividad in actividades:
            actividades_post.append(actividad.id)
        actividad_vetada = Actividad.objects.filter(borrador=False, vetada=True)
        actividades_post.append(actividad_vetada)
        # Se realiza la petición para editar la oferta
        response = self.client.post('/oferta/edicion/{}/'.format(oferta.id), {
            'titulo': titulo,
            'descripcion': descripcion,
            'actividades': actividades_post,
            'borrador': borrador
        })
        oferta_despues = Oferta.objects.get(pk=oferta.id)
        # Se comparan los datos. Se comprueba que no ha sucedido ninguna redirección y que la página se ha obtenido
        # correctamente. Esto se debe a que al haber un error de validación el usuario permanece en el formulario.
        self.assertEqual(response.status_code, 200)
        # self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        # Se comprueba que no se ha editado nada
        self.assertEqual(oferta_despues.titulo, oferta.titulo)
        self.assertEqual(oferta_despues.descripcion, oferta.descripcion)
        self.assertEqual(oferta_despues.borrador, oferta.borrador)
        self.assertEqual(oferta_despues.actividades, oferta.actividades)
        # El usuario se desloguea
        self.logout()

    # Un usuario edita una oferta insertando actividades en modo borrador
    def test_edita_oferta_actividad_borrador(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        oferta = Oferta.objects.filter(autor__django_user__username=username, cerrada=False, borrador=True).first()
        self.login(username, password)
        # Se asignan variables para los datos de entrada
        titulo = 'test_edita_incorrecto'
        descripcion = 'test_edita_incorrecto'
        borrador = False
        actividades = list(Actividad.objects.filter(borrador=False, vetada=False))[:2]
        actividades_post = []
        for actividad in actividades:
            actividades_post.append(actividad.id)
        actividad_borrador = Actividad.objects.filter(borrador=True, vetada=False)
        actividades_post.append(actividad_borrador)
        # Se realiza la petición para editar la oferta
        response = self.client.post('/oferta/edicion/{}/'.format(oferta.id), {
            'titulo': titulo,
            'descripcion': descripcion,
            'actividades': actividades_post,
            'borrador': borrador
        })
        oferta_despues = Oferta.objects.get(pk=oferta.id)
        # Se comparan los datos. Se comprueba que no ha sucedido ninguna redirección y que la página se ha obtenido
        # correctamente. Esto se debe a que al haber un error de validación el usuario permanece en el formulario.
        self.assertEqual(response.status_code, 200)
        # self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        # Se comprueba que no se ha editado nada
        self.assertEqual(oferta_despues.titulo, oferta.titulo)
        self.assertEqual(oferta_despues.descripcion, oferta.descripcion)
        self.assertEqual(oferta_despues.borrador, oferta.borrador)
        self.assertEqual(oferta_despues.actividades, oferta.actividades)
        # El usuario se desloguea
        self.logout()



    # ELIMINACIÓN

    # Un usuario elimina una oferta correctamente
    def test_elimina_oferta(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        oferta = Oferta.objects.filter(autor__django_user__username=username, borrador=True, cerrada=False).first()
        numero_ofertas_antes = Oferta.objects.all().count()
        self.login(username, password)
        # Se realiza la petición para eliminar la oferta
        response = self.client.get('/oferta/eliminacion/{}/'.format(oferta.id))
        # Se obtienen las variables de salida. Se busca la oferta y se trata de capturar la excepción que se produce
        # cuando se busca una oferta que no existe. Si se captura la excepción, entonces se puede verificar que la 
        # oferta ha sido eliminada
        oferta_eliminada = False
        try:
            Oferta.objects.get(pk = oferta.id)
        except ObjectDoesNotExist as e:
            oferta_eliminada = True
        numero_ofertas_despues = Oferta.objects.all().count()
        # Se comparan los datos. Se comprueba que el usuario ha sido redirigido al listado de ofertas y que la
        # oferta ha sido eliminada
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/listado/')
        self.assertEqual(oferta_eliminada, True)
        self.assertEqual(numero_ofertas_antes, numero_ofertas_despues + 1)
        # El usuario se desloguea
        self.logout()

    # Un usuario elimina una oferta sin estar autenticado
    def test_elimina_oferta_sin_loguear(self):
        # Se inicializan variables
        oferta = Oferta.objects.filter(borrador=True, cerrada=False).first()
        numero_ofertas_antes = Oferta.objects.all().count()
        # Se realiza la petición para eliminar la oferta
        response = self.client.get('/oferta/eliminacion/{}/'.format(oferta.id))
        # Se obtienen las variables de salida. Se busca la oferta y se trata de capturar la excepción que se produce
        # cuando se busca una oferta que no existe. Si se captura la excepción, entonces se puede verificar que la 
        # oferta ha sido eliminada
        oferta_eliminada = False
        try:
            Oferta.objects.get(pk = oferta.id)
        except ObjectDoesNotExist as e:
            oferta_eliminada = True
        numero_ofertas_despues = Oferta.objects.all().count()
        # Se comparan los datos. Se comprueba que el usuario, al tratar de acceder a una página que requiere 
        # autenticación sin estar autenticado, es redirigido a la página de login. Se comprueba además que no se ha 
        # eliminado la oferta
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/oferta/eliminacion/{}/'.format(oferta.id))
        self.assertEqual(oferta_eliminada, False)
        self.assertEqual(numero_ofertas_antes, numero_ofertas_despues)

    # Un usuario elimina una oferta que no es suya
    def test_elimina_oferta_usuario_incorrecto(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        oferta = Oferta.objects.exclude(autor__django_user__username=username).filter(borrador=True, cerrada=False).first()
        numero_ofertas_antes = Oferta.objects.all().count()
        self.login(username, password)
        # Se realiza la petición para eliminar la oferta
        response = self.client.get('/oferta/eliminacion/{}/'.format(oferta.id))
        # Se obtienen las variables de salida. Se busca la oferta y se trata de capturar la excepción que se produce
        # cuando se busca una oferta que no existe. Si se captura la excepción, entonces se puede verificar que la 
        # oferta ha sido eliminada
        oferta_eliminada = False
        try:
            Oferta.objects.get(pk = oferta.id)
        except ObjectDoesNotExist as e:
            oferta_eliminada = True
        numero_ofertas_despues = Oferta.objects.all().count()
        # Se comparan los datos. Se comprueba que el usuario ha sido redirigido a los detalles de la oferta y que no
        # se ha eliminado la oferta. Esto se debe a que un usuario no puede eliminar una oferta que no le pertenece.
        self.assertEqual(response.status_code, 302)
        # Se indica que se espera un codigo 302 en la respuesta debido otra redireccion
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id), target_status_code=302)
        self.assertEqual(numero_ofertas_antes, numero_ofertas_despues)
        self.assertEqual(oferta_eliminada, False)
        # El usuario se desloguea
        self.logout()

    # Un usuario elimina una oferta que no estaba en modo borrador
    def test_elimina_oferta_no_borrador(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        oferta = Oferta.objects.filter(autor__django_user__username=username, borrador=False, cerrada=False).first()
        numero_ofertas_antes = Oferta.objects.all().count()
        self.login(username, password)
        # Se realiza la petición para crear la oferta
        response = self.client.get('/oferta/eliminacion/{}/'.format(oferta.id))
        # Se obtienen las variables de salida. Se busca la oferta y se trata de capturar la excepción que se produce
        # cuando se busca una oferta que no existe. Si se captura la excepción, entonces se puede verificar que la 
        # oferta ha sido eliminada
        oferta_eliminada = False
        try:
            Oferta.objects.get(pk = oferta.id)
        except ObjectDoesNotExist as e:
            oferta_eliminada = True
        numero_ofertas_despues = Oferta.objects.all().count()
        # Se comparan los datos. Se comprueba que el usuario ha sido redirigido a los detalles de la oferta y que no
        # se ha eliminado la oferta. Esto se debe a que un usuario no puede eliminar una oferta que está en modo borrador.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertEqual(numero_ofertas_antes, numero_ofertas_despues)
        self.assertEqual(oferta_eliminada, False)
        # El usuario se desloguea
        self.logout()



    # VETO

    # Un administrador veta una oferta
    def test_veta_oferta(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        oferta = Oferta.objects.filter(vetada=False, borrador=False, cerrada=False).first()
        motivo_veto = 'Testing'
        self.login(username, password)
        # Se realiza la petición para vetar la oferta
        response = self.client.post('/oferta/veto/{}/'.format(oferta.id), {'motivo_veto': motivo_veto})
        # Se obtienen las variables de salida
        oferta_despues = Oferta.objects.get(pk = oferta.id)
        # Se comparan los datos. Se comprueba que el usuario ha sido redirigido a la paǵina de detalles y que la
        # oferta se ha vetado correctemente, además de guardarse el motivo de veto.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertEqual(oferta_despues.vetada, True)
        self.assertEqual(oferta_despues.motivo_veto, motivo_veto)
        # El usuario se desloguea
        self.logout()
    
    # Un usuario no autenticado veta una oferta
    def test_veta_oferta_sin_loguear(self):
        # Se inicializan variables y se loguea el usuario        
        oferta = Oferta.objects.filter(vetada=False, cerrada=False, borrador = False).first()
        motivo_veto = 'Testing'
        # Se realiza la petición para vetar la oferta
        response = self.client.post('/oferta/veto/{}/'.format(oferta.id), {'motivo_veto': motivo_veto})
        # Se obtienen las variables de salida
        oferta_despues = Oferta.objects.get(pk = oferta.id)
        # Se comparan los datos. Se comprueba que la oferta no ha sufrido cambios y que el usuario ha sido redirigido
        # al login debido a que hay que estar autenticado para vetar una oferta.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/oferta/veto/{}/'.format(oferta.id))
        # Se comprueba que la oferta no ha sido vetada
        self.assertEqual(oferta_despues.vetada, False)
        self.assertEqual(oferta_despues.motivo_veto, None)
        # El usuario se desloguea
        self.logout()

    # Un usuario que no es administrador veta la oferta
    def test_veta_oferta_usuario_incorrecto(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        oferta = Oferta.objects.filter(vetada=False, borrador=False, cerrada=False).first()
        motivo_veto = 'Testing'
        self.login(username, password)
        # Se realiza la petición para vetar la oferta
        response = self.client.post('/oferta/veto/{}/'.format(oferta.id), {'motivo_veto': motivo_veto})
        # Se obtienen las variables de salida
        oferta_despues = Oferta.objects.get(pk = oferta.id)
        # Se comparan los datos. Se comprueba que la oferta no ha sufrido cambios y que se ha redirigido al usuario a la
        # página de detalles de la oferta debido a que el usuario no tiene los permisos de administrador
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertEqual(oferta_despues.vetada, False)
        self.assertEqual(oferta_despues.motivo_veto, None)
        # El usuario se desloguea
        self.logout()

    # Un administrador veta una oferta ya vetada
    def test_veta_oferta_vetada(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        oferta = Oferta.objects.filter(Q(vetada=True, cerrada=False, borrador=False)).first()
        motivo_veto = oferta.motivo_veto + 'Testing'
        self.login(username, password)
        # Se realiza la petición para vetar la oferta
        response = self.client.post('/oferta/veto/{}/'.format(oferta.id), {'motivo_veto': motivo_veto})
        # Se obtienen las variables de salida
        oferta_despues = Oferta.objects.get(pk = oferta.id)
        # Se comparan los datos. Se comprueba que la oferta no ha sufrido cambios y que el usuario ha sido redirigido
        # a los detalles de la oferta debido a que no se puede vetar una oferta ya vetada.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertEqual(oferta_despues.vetada, True)
        self.assertEqual(oferta_despues.motivo_veto, oferta.motivo_veto)
        # El usuario se desloguea
        self.logout()

    # Un administrador veta una oferta cerrada
    def test_veta_oferta_cerrada(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        oferta = Oferta.objects.filter(vetada=False, cerrada=True, borrador=False).first()
        self.login(username, password)
        # Se realiza la petición para vetar la oferta
        response = self.client.post('/oferta/veto/{}/'.format(oferta.id), {'motivo_veto': 'Perejil'})
        # Se obtienen las variables de salida
        oferta_despues = Oferta.objects.get(pk=oferta.id)
        # Se comparan los datos. Se comprueba que la oferta no ha sufrido cambios y que el usuario ha sido redirigido
        # a los detalles de la oferta debido a que no se puede vetar una oferta cerrada.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertEqual(oferta_despues.vetada, False)
        self.assertEqual(oferta_despues.motivo_veto, oferta.motivo_veto)
        # El usuario se desloguea
        self.logout()

    # Un administrador veta una oferta que no existe
    def test_veta_oferta_inexistente(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        motivo_veto = 'Testing'
        self.login(username, password)
        # Se realiza la petición para vetar la oferta
        response = self.client.post('/oferta/veto/0/', {'motivo_veto': motivo_veto})
        # Se comparan los datos. El usuario es redirigido al listado de ofertas debido a que no se puede encontrar 
        # la oferta que se quiere vetar
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/listado/')
        # El usuario se desloguea
        self.logout()

    # Un adminsitrador veta una oferta insertando un motivo de veto no válido
    def test_veta_oferta_incorrecta(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        motivo_veto = 'Testing'
        oferta = Oferta.objects.filter(vetada=False, cerrada=False, borrador=False).first()
        self.login(username, password)
        # Se realiza la petición para vetar la oferta
        response = self.client.post('/oferta/veto/{}/'.format(oferta.id))
        # Se obtienen las variables de salida
        oferta_despues = Oferta.objects.get(pk = oferta.id)
        # Se comparan los datos. Se comprueba que la oferta no ha sufrido cambios y que el usuario permanece el 
        # formulario de veto debido a que se ha insertado un motivo de veto no válido
        self.assertEqual(response.status_code, 200)
        self.assertEqual(oferta_despues.vetada, False)
        self.assertEqual(oferta_despues.motivo_veto, None)
        # El usuario se desloguea
        self.logout()

    # Un administrador veta una oferta que está en modo borrador
    def test_veta_oferta_borrador(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        motivo_veto = 'Testing'
        oferta = Oferta.objects.filter(vetada=False, borrador=True, cerrada=False).first()
        self.login(username, password)
        # Se realiza la petición para vetar la oferta
        response = self.client.post('/oferta/veto/{}/'.format(oferta.id), {'motivo_veto': motivo_veto})
        # Se obtienen las variables de salida
        oferta_despues = Oferta.objects.get(pk = oferta.id)
        # Se comparan los datos. Se comprueba que la oferta no ha sufrido cambios y que el usuario ha sido
        # redirigido a los detalles de la oferta puesto a que no se puede vetar una oferta en modo borrador 
        self.assertEqual(response.status_code, 302)
        # Se indica que se espera un codigo 302 en la respuesta debido  otra redireccion
        self.assertRedirects(response, reverse('oferta_detalles', kwargs = {'oferta_id': oferta.id}), target_status_code=302)
        self.assertEqual(oferta_despues.vetada, False)
        self.assertEqual(oferta_despues.motivo_veto, None)
        # El usuario se desloguea
        self.logout()



    # LEVANTAMIENTO VETO

    # Un administrador levanta el veto sobre una oferta
    def test_levanta_veto_oferta(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        oferta = Oferta.objects.filter(vetada=True, cerrada=False, borrador=False).first()
        self.login(username, password)
        # Se realiza la petición para levantar el veto sobre la oferta
        response = self.client.get('/oferta/levantamiento_veto/{}/'.format(oferta.id))
        # Se obtienen las variables de salida
        oferta_despues = Oferta.objects.get(pk = oferta.id)
        # Se comparan los datos. Se comprueba que la oferta ya no está vetada y que no aparece el motivo de veto. Se
        # comprueba además que el usuario ha sido redirigido a los detalles de la oferta.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertEqual(oferta_despues.vetada, False)
        self.assertEqual(oferta_despues.motivo_veto, None)
        # El usuario se desloguea
        self.logout()

    # Un usuario levanta el veto sobre una oferta sin estar logueado
    def test_levanta_veto_oferta_sin_loguear(self):
        # Se inicializan variables y se loguea el usuario        
        oferta = Oferta.objects.filter(vetada=True, cerrada=False, borrador = False).first()
        # Se realiza la petición para levantar el veto sobre la oferta
        response = self.client.get('/oferta/levantamiento_veto/{}/'.format(oferta.id))
        # Se obtienen las variables de salida
        oferta_despues = Oferta.objects.get(pk = oferta.id)
        # Se comparan los datos. Se comprueba que la oferta no ha sufrido cambios y que se ha redirigido al usuario al
        # login, puesto a que se require autenticación para levantar el veto sobre una oferta.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/oferta/levantamiento_veto/{}/'.format(oferta.id))
        self.assertEqual(oferta_despues.vetada, True)
        self.assertEqual(oferta_despues.motivo_veto, oferta.motivo_veto)
        # El usuario se desloguea
        self.logout()

    # Un usuario levanta el veto sobre una oferta sin ser administrador
    def test_levanta_veto_oferta_usuario_incorrecto(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        oferta = Oferta.objects.filter(vetada=True, cerrada=False, borrador=False).first()
        self.login(username, password)
        # Se realiza la petición para levantar el veto sobre la oferta
        response = self.client.get('/oferta/levantamiento_veto/{}/'.format(oferta.id))
        # Se obtienen las variables de salida
        oferta_despues = Oferta.objects.get(pk = oferta.id)
        # Se comparan los datos. Se comprueba que la oferta no ha sufrido cambios y que se ha redirigido al usuario a los
        # detalles de la oferta debido a que el usuario no tiene los permisos de administrador necesarios.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('oferta_detalles', kwargs={'oferta_id': oferta.id}))
        self.assertEqual(oferta_despues.vetada, True)
        self.assertEqual(oferta_despues.motivo_veto, oferta.motivo_veto)
        # El usuario se desloguea
        self.logout()

    # Un usuario levanta el veto sobre una oferta no vetada
    def test_levanta_veto_oferta_no_vetada(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        oferta = Oferta.objects.filter(Q(vetada=False, cerrada=False ,borrador=False)).first()
        self.login(username, password)
        # Se realiza la petición para levantar el veto sobre la oferta
        response = self.client.get('/oferta/levantamiento_veto/{}/'.format(oferta.id))
        # Se obtienen las variables de salida
        oferta_despues = Oferta.objects.get(pk = oferta.id)
        # Se comparan los datos. Se comprueba que la oferta no ha sufrido cambios y que se ha redirido al usuario a los
        # detalles de la oferta, puesto a que no se puede levantar el veto sobre una oferta que no está vetada.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertEqual(oferta_despues.vetada, False)
        self.assertEqual(oferta_despues.motivo_veto, None)
        # El usuario se desloguea
        self.logout()

    # Un usuario levanta el veto sobre una oferta que no existe
    def test_levanta_veto_oferta_inexistente(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        self.login(username, password)
        # Se realiza la petición para levantar el veto sobre la oferta
        response = self.client.get('/oferta/levantamiento_veto/0/')
        # Se comparan los datos. Se comprueba que al no existir la oferta, se ha redirigido al usuario al listado de
        # ofertas
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/listado/')
        # El usuario se desloguea
        self.logout()



    # CIERRE

    # Un usuario trata de cerrar una oferta con éxito
    def test_cierra_oferta(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se busca una oferta para cerrarla
        oferta = Oferta.objects.filter(autor=usuario, cerrada=False, borrador=False, vetada=False).first()
        # Se realiza la petición para cerrar la oferta
        response = self.client.get('/oferta/cierre/{}/'.format(oferta.id))
        # Se comparan los datos. Se comprueba que la oferta ha sido cerrada
        oferta_despues = Oferta.objects.get(pk=oferta.id)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertTrue(oferta_despues.cerrada)
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de cerrar una oferta que ya está cerrada
    def test_cierra_oferta_cerrada(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se busca una oferta para cerrarla
        oferta = Oferta.objects.filter(autor=usuario, cerrada=True, borrador=False, vetada=False).first()
        # Se realiza la petición para cerrar la oferta
        response = self.client.get('/oferta/cierre/{}/'.format(oferta.id))
        # Se comparan los datos. Se comprueba que, al estar la oferta cerrada, no se ha realizado nada
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de cerrar una oferta en modo borrador
    def test_cierra_oferta_borrador(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se busca una oferta para cerrarla
        oferta = Oferta.objects.filter(autor=usuario, cerrada=False, borrador=True, vetada=False).first()
        # Se realiza la petición para cerrar la oferta
        response = self.client.get('/oferta/cierre/{}/'.format(oferta.id))
        # Se comparan los datos. Se comprueba que, al estar la oferta en modo borrador, la oferta no se ha cerrado
        oferta_despues = Oferta.objects.get(pk=oferta.id)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertFalse(oferta_despues.cerrada)
        self.assertTrue(oferta_despues.borrador)
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de cerrar una oferta vetada
    def test_cierra_oferta_vetada(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se busca una oferta para cerrarla
        oferta = Oferta.objects.filter(autor=usuario, cerrada=False, borrador=False, vetada=True).first()
        # Se realiza la petición para cerrar la oferta
        response = self.client.get('/oferta/cierre/{}/'.format(oferta.id))
        # Se comparan los datos. Se comprueba que, al estar la oferta en modo borrador, la oferta no se ha cerrado
        oferta_despues = Oferta.objects.get(pk=oferta.id)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertFalse(oferta_despues.cerrada)
        self.assertTrue(oferta_despues.vetada)
        self.assertEqual(oferta_despues.motivo_veto, oferta.motivo_veto)
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de cerrar una oferta sin estar autenticado
    def test_cierra_oferta_sin_autenticar(self):
        # Se inicializan variables
        oferta = Oferta.objects.filter(vetada=False, cerrada=False, borrador=False).first()
        # Se realiza la petición para cerrar la oferta
        response = self.client.get('/oferta/cierre/{}/'.format(oferta.id))
        # Se obtienen las variables de salida
        oferta_despues = Oferta.objects.get(pk=oferta.id)
        # Se comparan los datos. Se comprueba que la oferta no ha sufrido cambios y que se ha redirigido al usuario al
        # login, puesto a que se require autenticación para cerrar una oferta.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/oferta/cierre/{}/'.format(oferta.id))
        self.assertEqual(oferta_despues.cerrada, False)
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de cerrar una oferta que no le pertenece
    def test_cierra_oferta_ajena(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se busca una oferta para cerrarla
        oferta = Oferta.objects.filter(cerrada=False, borrador=False, vetada=False).exclude(autor=usuario).first()
        # Se realiza la petición para cerrar la oferta
        response = self.client.get('/oferta/cierre/{}/'.format(oferta.id))
        # Se comparan los datos. Se comprueba que, al estar la oferta en modo borrador, la oferta no se ha cerrado
        oferta_despues = Oferta.objects.get(pk=oferta.id)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertFalse(oferta_despues.cerrada)
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de cerrar una oferta que no existe
    def test_cierra_oferta_inexistente(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        oferta_id = 0
        # Se realiza la petición para cerrar la oferta
        response = self.client.get('/oferta/cierre/{}/'.format(oferta_id))
        # Se comparan los datos. Se comprueba que, al no existir la oferta, se redirige al usuario al listado de ofertas
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/listado/')
        # El usuario se desloguea
        self.logout()



    # SOLICITUD

    # Un usuario solicita una oferta
    def test_solicita_oferta(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        usuario = self.login(username, password)
        numero_solicitudes_antes = Solicitud.objects.all().count()
        # Se busca una oferta para solicitarla
        # Se buscan las ofertas que ya han sido solicitadas para descartarlas
        ofertas_solicitadas = []
        for solicitud in list(Solicitud.objects.filter(usuario=usuario).only('oferta')):
            ofertas_solicitadas.append(solicitud.oferta)
        # Se agrupan aquellas ofertas que, en principio podrían ser solicitadas ppor cualquier usuario, siempre que
        # cumpla los requisitos
        ofertas_posibles = []
        for oferta_for in list(Oferta.objects.filter(borrador=False, vetada=False, cerrada=False)):
            ofertas_posibles.append(oferta_for)
        # Se agrupan las actividades realizadas por el usuario, para luego comprobar que se cumplen los requisitos
        actividades_realizadas = Usuario.objects.get(pk=usuario.id).actividades_realizadas.all()
        # Se comprueba que no se ha solicitado antes la oferta y que se han realizado las actividades necesarias
        oferta = None
        # Se evalua cada oferta marcada como posible para evaluar si se cumplen sus requisitos
        for oferta_posible in ofertas_posibles:
            # Se asume que la actividad se puede solicitar
            puede_solicitar = True
            # Si no se ha solicitado la oferta antes
            if not oferta_posible in ofertas_solicitadas:
                # Comprueba que se han realizado las tareas marcadas como requisitos
                actividades_requisitos = oferta_posible.actividades.all()
                for actividad_requisito in actividades_requisitos:
                    # En el momento en que no se tiene uno de los requisitos, la oferta no se puede solicitar
                    if not actividad_requisito in actividades_realizadas:
                        puede_solicitar = False
                        break
                # Si la oferta cumple todos los requisitos, se selecciona como oferta a seleccionar
                if puede_solicitar:
                    oferta = oferta_posible
                    break
        # Se realiza la petición para solicitar la oferta
        response = self.client.get('/oferta/solicitud/{}/'.format(oferta.id))
        # Se comparan los datos. Se comprueba que la oferta ha sido solicitada
        numero_solicitudes_despues = Solicitud.objects.all().count()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertEqual(numero_solicitudes_antes + 1, numero_solicitudes_despues)
        try:
            solicitud_creada = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud_creada = None
        self.assertIsNotNone(solicitud_creada)
        # El usuario se desloguea
        self.logout()

    # Un usuario solicita una oferta sin haber cumplido los requisitos para solicitarla
    def test_solicita_oferta_sin_requisitos(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario3'
        password = 'usuario3'
        usuario = self.login(username, password)
        numero_solicitudes_antes = Solicitud.objects.all().count()
        # Se busca una oferta para solicitarla
        # Se buscan las ofertas que ya han sido solicitadas para descartarlas
        ofertas_solicitadas = []
        for solicitud in list(Solicitud.objects.filter(usuario=usuario).only('oferta')):
            ofertas_solicitadas.append(solicitud.oferta)
        # Se agrupan aquellas ofertas que, en principio podrían ser solicitadas ppor cualquier usuario, siempre que
        # cumpla los requisitos
        ofertas_posibles = []
        for oferta in list(Oferta.objects.filter(borrador=False, vetada=False, cerrada=False)):
            ofertas_posibles.append(oferta)
        # Se agrupan las actividades realizadas por el usuario, para luego comprobar que se cumplen los requisitos
        actividades_realizadas = Usuario.objects.get(pk=usuario.id).actividades_realizadas.all()
        # Se comprueba que no se ha solicitado antes la oferta y que se han realizado las actividades necesarias
        oferta = None
        # Se evalua cada oferta marcada como posible para evaluar si se cumplen sus requisitos
        for oferta_posible in ofertas_posibles:
            # Se asume que la actividad se puede solicitar
            puede_solicitar = True
            # Si no se ha solicitado la oferta antes
            if not oferta_posible in ofertas_solicitadas:
                # Comprueba que se han realizado las tareas anteriores
                actividades_requisitos = oferta_posible.actividades.all()
                for actividad_requisito in actividades_requisitos:
                    # En el momento en que no se tiene uno de los requisitos, la oferta no se puede solicitar
                    if not actividad_requisito in actividades_realizadas:
                        puede_solicitar = False
                        break
                # En este caso, coge una oferta cuyos requisitos el usuario no cumple
                if not puede_solicitar:
                    oferta = oferta_posible
                    break
        # Se realiza la petición para solicitar la oferta
        response = self.client.get('/oferta/solicitud/{}/'.format(oferta.id))
        # Se comparan los datos. Se comprueba que no se ha creado la solicitud, puesto a que se tienen que cumplir los
        # requisitos para poder pedirla
        numero_solicitudes_despues = Solicitud.objects.all().count()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertEqual(numero_solicitudes_despues, numero_solicitudes_antes)
        try:
            solicitud_creada = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud_creada = None
        self.assertIsNone(solicitud_creada)
        # El usuario se desloguea
        self.logout()

    # Un usuario solicita una oferta en modo borrador
    def test_solicita_oferta_borrador(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario3'
        password = 'usuario3'
        usuario = self.login(username, password)
        numero_solicitudes_antes = Solicitud.objects.all().count()
        # Se busca una oferta para solicitarla, en este caso, la oferta va a estar en modo borrador
        # Se buscan las ofertas que ya han sido solicitadas para descartarlas
        ofertas_solicitadas = []
        for solicitud in list(Solicitud.objects.filter(usuario=usuario).only('oferta')):
            ofertas_solicitadas.append(solicitud.oferta)
        ofertas_posibles = []
        for oferta in list(Oferta.objects.filter(borrador=True, vetada=False, cerrada=False)):
            ofertas_posibles.append(oferta)
        # Se agrupan las actividades realizadas por el usuario, para luego comprobar que se cumplen los requisitos
        actividades_realizadas = Usuario.objects.get(pk=usuario.id).actividades_realizadas.all()
        # Se comprueba que no se ha solicitado antes la oferta y que se han realizado las actividades necesarias
        oferta = None
        for oferta_posible in ofertas_posibles:
            puede_solicitar = True
            # Si no se ha solicitado al oferta antes
            if not oferta_posible in ofertas_solicitadas:
                # Comprueba que se han realizado las tareas anteriores
                actividades_requisitos = oferta_posible.actividades.all()
                for actividad_requisito in actividades_requisitos:
                    # En el momento en que no se tiene uno de los requisitos, la oferta no se puede solicitar
                    if not actividad_requisito in actividades_realizadas:
                        puede_solicitar = False
                        break
                # Si la oferta cumple todos los requisitos, se selecciona como oferta a seleccionar
                if puede_solicitar:
                    oferta = oferta_posible
                    break
        # Se realiza la petición para solicitar la oferta
        response = self.client.get('/oferta/solicitud/{}/'.format(oferta.id))
        # Se comparan los datos. Se comprueba que no se ha creado la solicitud puesto a que no se puede solicitar una
        # oferta que está en modo borrador
        numero_solicitudes_despues = Solicitud.objects.all().count()
        self.assertEqual(response.status_code, 302)
        # Se indica que se espera un codigo 302 en la respuesta debido  otra redireccion
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id), target_status_code=302)
        self.assertEqual(numero_solicitudes_antes, numero_solicitudes_despues)
        try:
            solicitud_creada = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud_creada = None
        self.assertIsNone(solicitud_creada)
        # El usuario se desloguea
        self.logout()

    # Un usuario solicita una oferta cerrada
    def test_solicita_oferta_cerrada(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        numero_solicitudes_antes = Solicitud.objects.all().count()
        # Se busca una oferta para solicitarla, en este caso, la oferta va a estar cerrada
        ofertas_solicitadas = []
        for solicitud in list(Solicitud.objects.filter(usuario=usuario)):
            ofertas_solicitadas.append(solicitud.oferta)
        # Se agrupan aquellas ofertas que, en principio podrían ser solicitadas por cualquier usuario, siempre que
        # cumpla los requisitos. En este caso las actividades deben estar cerradas para poder realizar el test correctamente
        ofertas_posibles = []
        for oferta in list(Oferta.objects.filter(borrador=False, vetada=False, cerrada=True)):
            ofertas_posibles.append(oferta)
        # Se agrupan las actividades realizadas por el usuario, para luego comprobar que se cumplen los requisitos
        actividades_realizadas = Usuario.objects.get(pk=usuario.id).actividades_realizadas.all()
        # Se comprueba que no se ha solicitado antes la oferta y que se han realizado las actividades necesarias
        oferta = None
        for oferta_posible in ofertas_posibles:
            puede_solicitar = True
            # Si no se ha solicitado al oferta antes
            if not oferta_posible in ofertas_solicitadas:
                # Comprueba que se han realizado las tareas anteriores
                actividades_requisitos = oferta_posible.actividades.all()
                for actividad_requisito in actividades_requisitos:
                    if not actividad_requisito in actividades_realizadas:
                        puede_solicitar = False
                        break
                if puede_solicitar:
                    oferta = oferta_posible
                    break
        # Se realiza la petición para solicitar la oferta
        response = self.client.get('/oferta/solicitud/{}/'.format(oferta.id))
        # Se comparan los datos. Se comprueba que no se ha creado la solicitud
        numero_solicitudes_despues = Solicitud.objects.all().count()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertEqual(numero_solicitudes_antes, numero_solicitudes_despues)
        try:
            solicitud_creada = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud_creada = None
        self.assertIsNone(solicitud_creada)
        # El usuario se desloguea
        self.logout()

    # Un usuario solicita una oferta vetada
    def test_solicita_oferta_vetada(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        numero_solicitudes_antes = Solicitud.objects.all().count()
        # Se busca una oferta para solicitarla, en este caso, la oferta va a estar vetada
        # Se agrupan aquellas ofertas que el usuario ya ha solicitado para descartarlas posteriormente
        ofertas_solicitadas = []
        for solicitud in list(Solicitud.objects.filter(usuario=usuario).only('oferta')):
            ofertas_solicitadas.append(solicitud.oferta)
        # Se obtienen aquellas ofertas que cualquier usuario podría solicitar si cumpliera los requisitos. En este caso,
        # estas ofertas deben estar vetadas para que se realice el test correctamente
        ofertas_posibles = []
        for oferta in list(Oferta.objects.filter(borrador=False, vetada=True, cerrada=False)):
            ofertas_posibles.append(oferta)
        # Se obtienen las actividades realizadas por el usuario para comparar los requistos más tarde
        actividades_realizadas = Usuario.objects.get(pk=usuario.id).actividades_realizadas.all()
        # Se comprueba que no se ha solicitado antes la oferta y que se han realizado las actividades necesarias
        oferta = None
        for oferta_posible in ofertas_posibles:
            puede_solicitar = True
            # Si no se ha solicitado al oferta antes
            if not oferta_posible in ofertas_solicitadas:
                # Comprueba que se han realizado las tareas marcadas como requisitos
                actividades_requisitos = oferta_posible.actividades.all()
                for actividad_requisito in actividades_requisitos:
                    # Si alguna de las actividades marcadas como requisitos no ha sido realizada por el usuario, entonces
                    # la oferta no se puede solicitar
                    if not actividad_requisito in actividades_realizadas:
                        puede_solicitar = False
                        break
                # Si la oferta se puede solicitar, entinces se marca como la oferta a solicitar
                if puede_solicitar:
                    oferta = oferta_posible
                    break
        # Se realiza la petición para solicitar la oferta
        response = self.client.get('/oferta/solicitud/{}/'.format(oferta.id))
        # Se comparan los datos. Se comprueba que no se ha creado la solicitud, puesto a que no se puede solicitar una
        # oferta vetada
        numero_solicitudes_despues = Solicitud.objects.all().count()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertEqual(numero_solicitudes_antes, numero_solicitudes_despues)
        try:
            solicitud_creada = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud_creada = None
        self.assertIsNone(solicitud_creada)
        # El usuario se desloguea
        self.logout()

    # Un usuario solicita una oferta con su autoría
    def test_solicita_oferta_propia(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        numero_solicitudes_antes = Solicitud.objects.all().count()
        # Se busca una oferta para solicitarla
        # Se buscan las ofertas que ya han sido solicitadas para descartarlas
        ofertas_solicitadas = []
        for solicitud in list(Solicitud.objects.filter(usuario=usuario).only('oferta')):
            ofertas_solicitadas.append(solicitud.oferta)
        # Se agrupan aquellas ofertas que, en principio podrían ser solicitadas ppor cualquier usuario, siempre que
        # cumpla los requisitos. En este caso además, se busca que la oferta sea de la autoría del usuario
        ofertas_posibles = []
        for oferta_for in list(Oferta.objects.filter(borrador=False, vetada=False, cerrada=False, autor=usuario)):
            ofertas_posibles.append(oferta_for)
        # Se agrupan las actividades realizadas por el usuario, para luego comprobar que se cumplen los requisitos
        actividades_realizadas = Usuario.objects.get(pk=usuario.id).actividades_realizadas.all()
        # Se comprueba que no se ha solicitado antes la oferta y que se han realizado las actividades necesarias
        oferta = None
        # Se evalua cada oferta marcada como posible para evaluar si se cumplen sus requisitos
        for oferta_posible in ofertas_posibles:
            # Se asume que la actividad se puede solicitar
            puede_solicitar = True
            # Si no se ha solicitado la oferta antes
            if not oferta_posible in ofertas_solicitadas:
                # Comprueba que se han realizado las tareas marcadas como requisitos
                actividades_requisitos = oferta_posible.actividades.all()
                for actividad_requisito in actividades_requisitos:
                    # En el momento en que no se tiene uno de los requisitos, la oferta no se puede solicitar
                    if not actividad_requisito in actividades_realizadas:
                        puede_solicitar = False
                        break
                # Si la oferta cumple todos los requisitos, se selecciona como oferta a seleccionar
                if puede_solicitar:
                    oferta = oferta_posible
                    break
        # Se realiza la petición para solicitar la oferta
        response = self.client.get('/oferta/solicitud/{}/'.format(oferta.id))
        # Se comparan los datos. Se comprueba que la oferta no ha sido solicitada, puesto a que no se puede solicitar
        # una oferta de propia autoría
        numero_solicitudes_despues = Solicitud.objects.all().count()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertEqual(numero_solicitudes_antes, numero_solicitudes_despues)
        try:
            solicitud_creada = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud_creada = None
        self.assertIsNone(solicitud_creada)
        # El usuario se desloguea
        self.logout()

    # Un usuario solicita una oferta sin estar autenticado
    def test_solicita_oferta_sin_autenticar(self):
        # Se inicializan variables
        numero_solicitudes_antes = Solicitud.objects.all().count()
        # Se busca una oferta para solicitarla
        ofertas_posibles = []
        for oferta in list(Oferta.objects.filter(borrador=False, vetada=False, cerrada=False)):
            ofertas_posibles.append(oferta)
        oferta = ofertas_posibles[0]
        # Se realiza la petición para solicitar la oferta
        response = self.client.get('/oferta/solicitud/{}/'.format(oferta.id))
        # Se comparan los datos. Se comprueba que no se ha creado la solicitud, puesto a que se debe estar autenticado
        # para solicitar una oferta. Se comprueba a demás que en este caso no se redirige a la página de detalles de la
        # oferta, sino a la página de login
        numero_solicitudes_despues = Solicitud.objects.all().count()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/oferta/solicitud/{}/'.format(oferta.id))
        self.assertEqual(numero_solicitudes_antes, numero_solicitudes_despues)

    # Un usuario solicita una oferta que no existe
    def test_solicita_oferta_inexistente(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        numero_solicitudes_antes = Solicitud.objects.all().count()
        # Se realiza la petición para solicitar la oferta poniendo una oferta que no existe
        response = self.client.get('/oferta/solicitud/0/')
        # Se comparan los datos. Se comprueba que la oferta ha sido solicitada, puesto a que no existe la oferta.
        # Se redirige al listado de ofertas debido a que es donde el listado de detalles redirige cuando hay un error,
        # puesto a qu eno se pueden mostrar los detalles de una actividad que no existe
        numero_solicitudes_despues = Solicitud.objects.all().count()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/listado/')
        self.assertEqual(numero_solicitudes_antes, numero_solicitudes_despues)
        # El usuario se desloguea
        self.logout()



    # RETIRO DE SOLICITUD

    # Un usuario retira su solicitud de una oferta
    def test_retira_solicitud(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        numero_solicitudes_antes = Solicitud.objects.all().count()
        # Se busca una oferta para retirar la solicitud realizada por el usuario
        oferta = Solicitud.objects.filter(usuario=usuario, oferta__vetada=False, oferta__cerrada=False,
                oferta__borrador=False).only('oferta').first().oferta
        # Se realiza la petición para retirar la solicitud de la oferta
        response = self.client.get('/oferta/retiro_solicitud/{}/'.format(oferta.id))
        # Se comparan los datos. Se comprueba que la solicitud ha sido retirada
        numero_solicitudes_despues = Solicitud.objects.all().count()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertEqual(numero_solicitudes_antes - 1, numero_solicitudes_despues)
        try:
            solicitud = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud = None
        self.assertIsNone(solicitud)
        # El usuario se desloguea
        self.logout()

    def test_retira_solicitud_sin_solicitar(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        numero_solicitudes_antes = Solicitud.objects.all().count()
        # Se busca una oferta donde el usuario no haya solicitado
        # Se agrupan aquellas ofertas en la que el usuario ha solicitado
        ofertas = []
        for solicitud in list(
            Solicitud.objects.filter(usuario=usuario).only('oferta')):
            ofertas.append(solicitud.oferta)
        for oferta_for in Oferta.objects.all():
            if not oferta_for in ofertas:
                oferta = oferta_for
        # Se realiza la petición para retirar la solicitud de la oferta
        response = self.client.get('/oferta/retiro_solicitud/{}/'.format(oferta.id))
        # Se comparan los datos. Se comprueba que no se ha retirado ninguna solicitud. Esto se debe a que no había
        # ninguna solicitud que retirar
        numero_solicitudes_despues = Solicitud.objects.all().count()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertEqual(numero_solicitudes_antes, numero_solicitudes_despues)
        try:
            solicitud = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud = None
        self.assertIsNone(solicitud)
        # El usuario se desloguea
        self.logout()

    # Un usuario retira su solciitud de una oferta vetada
    def test_retira_solicitud_oferta_vetada(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        numero_solicitudes_antes = Solicitud.objects.all().count()
        # Se busca una solicitud de una oferta vetada para retirarla
        oferta = Solicitud.objects.filter(usuario=usuario, oferta__vetada=True, oferta__cerrada=False,
                oferta__borrador=False).only('oferta').first().oferta
        # Se realiza la petición para retirar la solicitud de la oferta
        response = self.client.get('/oferta/retiro_solicitud/{}/'.format(oferta.id))
        # Se comparan los datos. Se comprueba que la solicitud no ha sido retirada, puesto a que no se puede retirar
        # una solicitud de una oferta vetada
        numero_solicitudes_despues = Solicitud.objects.all().count()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertEqual(numero_solicitudes_antes, numero_solicitudes_despues)
        try:
            solicitud = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud = None
        self.assertIsNotNone(solicitud)
        # El usuario se desloguea
        self.logout()

    # Un usuario retira su solicitud de in oferta cerrada
    def test_retira_solicitud_oferta_cerrada(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario3'
        password = 'usuario3'
        usuario = self.login(username, password)
        numero_solicitudes_antes = Solicitud.objects.all().count()
        # Se busca una solicitud de una oferta cerrada para retirarla
        oferta = Solicitud.objects.filter(usuario=usuario, oferta__vetada=False, oferta__cerrada=True,
                oferta__borrador=False).only('oferta').first().oferta
        # Se realiza la petición para retirar la solicitud de la oferta
        response = self.client.get('/oferta/retiro_solicitud/{}/'.format(oferta.id))
        # Se comparan los datos. Se comprueba que la solicitud no ha sido retirada, puesto a que no se puede retirar una
        # solicitud de una oferta cerrada
        numero_solicitudes_despues = Solicitud.objects.all().count()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/detalles/{}/'.format(oferta.id))
        self.assertEqual(numero_solicitudes_antes, numero_solicitudes_despues)
        try:
            solicitud = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud = None
        self.assertIsNotNone(solicitud)
        # El usuario se desloguea
        self.logout()

    # Un usuario sin autenticar retira su solicitud de una oferta
    def test_retira_solicitud_oferta_sin_autenticar(self):
        # Se inicializan variables y se loguea el usuario
        numero_solicitudes_antes = Solicitud.objects.all().count()
        # Se busca una solicitud para retirarla
        oferta = Solicitud.objects.filter(oferta__vetada=False, oferta__cerrada=False, oferta__borrador=False
                ).only('oferta').first().oferta
        # Se realiza la petición para retirar la solicitud de la oferta
        response = self.client.get('/oferta/retiro_solicitud/{}/'.format(oferta.id))
        # Se comparan los datos. Se comprueba que la solicitud no ha sido retirada, puesto a que el usuario debe estar
        # autenticado para hacerlo. Se comprueba además que se ha redirigido al usuario a la página de login.
        numero_solicitudes_despues = Solicitud.objects.all().count()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/oferta/retiro_solicitud/{}/'.format(oferta.id))
        self.assertEqual(numero_solicitudes_antes, numero_solicitudes_despues)
        # El usuario se desloguea
        self.logout()

    # Un usuario retira su solicitud de una oferta inexistente
    def test_retira_solicitud_oferta_inexistente(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        numero_solicitudes_antes = Solicitud.objects.all().count()
        # Se realiza la petición para retirar la solicitud de la oferta
        response = self.client.get('/oferta/retiro_solicitud/{}/'.format(0))
        # Se comparan los datos. Se comprueba que la solicitud no ha sido retirada, puesto a que no se ha dado ninguna
        # oferta de la que retirarla. Se comprueba además que, debido a que los detalles de la oferta dan error por no
        # darse una oferta válida, estos redirigen al listado de las ofertas
        numero_solicitudes_despues = Solicitud.objects.all().count()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/oferta/listado/')
        self.assertEqual(numero_solicitudes_antes, numero_solicitudes_despues)
        # El usuario se desloguea
        self.logout()


