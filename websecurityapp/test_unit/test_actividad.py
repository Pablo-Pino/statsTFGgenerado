from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from datetime import date
import re

from websecurityapp.models.perfil_models import Usuario
from websecurityapp.models.actividad_models import Actividad
from websecurityapp.views.actividad_views import CreacionActividadesView

from websecurityapp.test_unit.utils import test_listado

from websecurityserver.settings import numero_objetos_por_pagina

class ActividadTestCase(TestCase):
    
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

    # Un usuario accede al listado de actividades correctamente
    def test_lista_actividades(self):
        # Se inicializan variables y el usuario se loguea
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se crean variables con los datos correctos
        actividades_esperadas = Actividad.objects.filter(
            Q(autor__django_user__username=username) | Q(borrador=False) & Q(vetada=False)).order_by('id')
        datos_esperados = dict()
        datos_esperados['usuario'] = usuario
        datos_esperados['actividades_realizadas'] = usuario.actividades_realizadas.all()
        datos_esperados['titulo_pagina']: 'Listado de actividades'
        # Se realizan los tests
        test_listado(self,
            dato_lista = 'page_obj_actividades',
            datos_esperados = datos_esperados,
            lista_esperada = actividades_esperadas,
            page_param = 'page',
            url = reverse('actividad_listado'),
            status_code = 200)
        # El usuario se desloguea
        self.logout()

    # Un administrador accede al listado de actividades correctamente
    def test_lista_actividades_admin(self):
        # Se inicializan variables y el usuario se loguea
        username = 'usuario2'
        password = 'usuario2'
        usuario = self.login(username, password)
        # Se crean variables con los datos correctos
        actividades_esperadas = Actividad.objects.filter(
            Q(autor__django_user__username=username) | Q(borrador=False)).order_by('id')
        datos_esperados = dict()
        datos_esperados['usuario'] = usuario
        datos_esperados['actividades_realizadas'] = usuario.actividades_realizadas.all()
        datos_esperados['titulo_pagina']: 'Listado de actividades'
        # Se realizan los tests
        test_listado(self,
            dato_lista = 'page_obj_actividades',
            datos_esperados = datos_esperados,
            lista_esperada = actividades_esperadas,
            page_param = 'page',
            url = reverse('actividad_listado'),
            status_code = 200)
        # El usuario se desloguea
        self.logout()

    # Un usuario accede al listado de sus propias actividades
    def test_lista_actividades_propias(self):
        # Se inicializan variables y el usuario se loguea
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se crean variables con los datos correctos
        actividades_esperadas = Actividad.objects.filter(autor=usuario).order_by('id')
        datos_esperados = dict()
        datos_esperados['usuario'] = usuario
        datos_esperados['titulo_pagina']: 'Listado de actividades'
        # Se realizan los tests
        test_listado(self,
            dato_lista = 'page_obj_actividades',
            datos_esperados = datos_esperados,
            lista_esperada = actividades_esperadas,
            page_param = 'page',
            url = reverse('actividad_listado_propio'),
            status_code = 200)
        # El usuario se desloguea
        self.logout()



    # DETALLES

    # Un usuario accede a los detalles de una actividad correctamente
    def test_detalles_actividad(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        self.login(username, password)
        # Se obtienen los datos esperados
        usuario_esperado = Usuario.objects.get(django_user__username = username)
        actividad_esperada = Actividad.objects.filter(Q(autor__django_user__username = username) & Q(borrador = True)).first()
        # Se simula que el usuario accede a los detalles de la actividad
        response = self.client.get('/actividad/detalles/{}/'.format(actividad_esperada.id))
        # Se obtienen los datos recibidos en la petición
        usuario_recibido = response.context['usuario']
        actividad_recibida = response.context['actividad']
        # Se comprueba que los datos son correctos
        self.assertEqual(response.status_code, 200)
        self.assertEqual(actividad_esperada, actividad_recibida)
        self.assertEqual(usuario_esperado, usuario_recibido)
        # El usuario se desloguea
        self.logout()

    # Un usuario accede a los detalles de una actividad que no existe
    def test_detalles_actividad_no_existe(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        id = 0
        self.login(username, password)
        # Se simula que el usuario accede a los detalles de la actividad
        response = self.client.get('/actividad/detalles/{}/'.format(id))
        # Se comprueba que los datos son correctos, el usuario es redirigido al listado al no poder hallarse
        # la actividad cuyos detalles se quieren ver
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/actividad/listado/')
        # El usuario se desloguea
        self.logout()



    # CREACION

    # Un usuario crea una actividad correctamente
    def test_crea_actividad(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        self.login(username, password)
        # Se sacan las variables necesarias para comparar los datos
        numero_actividades_antes = Actividad.objects.count()
        autor_esperado = Usuario.objects.get(django_user__username = 'usuario1')
        # Se asignan variables para los datos de entrada
        titulo = 'test_crea'
        enlace = 'https://testcrea.com/'
        descripcion = 'test_crea'
        comentable = True
        # Se realiza la petición para crear la actividad
        response = self.client.post('/actividad/creacion/', {
            'titulo': titulo, 
            'enlace': enlace, 
            'descripcion': descripcion, 
            'comentable': comentable
        })
        # Se obtienen las varibles de salida
        numero_actividades_despues = Actividad.objects.count()
        actividad_creada = Actividad.objects.all().order_by('id').last()
        # Se comparan los datos, se comprueba que el usuario es redirigido a la página de detalles de la actividad
        # tras crearla
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/actividad/detalles/{}/'.format(actividad_creada.id))
        self.assertEqual(numero_actividades_antes, numero_actividades_despues - 1)
        # Se comprueba que los datos almacenados son los esperados
        self.assertEqual(actividad_creada.titulo, titulo)
        self.assertURLEqual(actividad_creada.enlace, enlace)
        self.assertEqual(actividad_creada.descripcion, descripcion)
        self.assertEqual(actividad_creada.borrador, True)
        self.assertEqual(actividad_creada.vetada, False)
        self.assertEqual(actividad_creada.motivo_veto, None)
        self.assertEqual(actividad_creada.fecha_creacion, date.today())
        self.assertEqual(actividad_creada.comentable, comentable)
        # Se comprueba que el identificador de la actividad sigue el patrón indicado
        indentificador_regex = re.compile('^ACT-\w{10}$')
        self.assertEqual(indentificador_regex.match(actividad_creada.identificador) != None, True)
        # El usuario se desloguea
        self.logout()
        
    # Un usuario crea una actividad sin estar autenticado
    def test_crea_actividad_sin_loguear(self):
        # Se sacan las variables necesarias para comparar los datos
        numero_actividades_antes = Actividad.objects.count()
        # Se asignan variables para los datos de entrada
        titulo = 'test_crea_sin_loguear'
        enlace = 'https://testcreasinloguear.com/'
        descripcion = 'test_crea_sin_loguear'
        comentable = True
        # Se realiza la petición para crear la actividad
        response = self.client.post('/actividad/creacion/', {
            'titulo': titulo, 
            'enlace': enlace, 
            'descripcion': descripcion, 
            'comentable': comentable
        })
        # Se obtienen las varibles de salida
        numero_actividades_despues = Actividad.objects.count()
        # Se comparan los datos y se comprueba que no se ha creado la actividad, además de que el usuario ha sido
        # redirigido a la página de login al acceder a una página que requiere autenticación
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/actividad/creacion/')
        self.assertEqual(numero_actividades_antes, numero_actividades_despues)

    # Un usuario crea una actividad usando datos no válidos
    def test_crea_actividad_incorrecta(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        self.login(username, password)
        # Se sacan las variables necesarias para comparar los datos
        numero_actividades_antes = Actividad.objects.count()
        # Se asignan variables para los datos de entrada
        titulo = 'test_crea_incorrecta'
        enlace = 'httpstestcrea_incorrecta.com/'
        descripcion = 'test_crea_incorrecta'
        comentable = True
        # Se realiza la petición para crear la actividad
        response = self.client.post('/actividad/creacion/', {
            'titulo': titulo, 
            'enlace': enlace, 
            'descripcion': descripcion, 
            'comentable': comentable
        })
        # Se obtienen las variables de salida
        numero_actividades_despues = Actividad.objects.count()
        # Se comparan los datos y se comprueba que no se ha creado la actividad, se debe comprobar además que se ha
        # obtenido la página sin redirección y que se ha obtenido correctamente, debido a que se permanece en el 
        # formulario al suceder un error de validación
        self.assertEqual(response.status_code, 200)
        self.assertEqual(numero_actividades_antes, numero_actividades_despues)
        # Se desloguea el usuario
        self.logout()



    # EDICION

    # Un usuario edita una actividad correctamente
    def test_edita_actividad(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        actividad = Actividad.objects.filter(Q(autor__django_user__username = username) & Q(borrador = True)).first()
        self.login(username, password)
        # Se asignan variables para los datos de entrada
        titulo = 'test_edita'
        enlace = 'https://testedita.com/'
        descripcion = 'test_edita'
        comentable = True
        borrador = False
        # Se realiza la petición para editar la actividad
        response = self.client.post('/actividad/edicion/{}/'.format(actividad.id), {
            'titulo': titulo, 
            'enlace': enlace, 
            'descripcion': descripcion, 
            'comentable': comentable, 
            'borrador': borrador
        })
        # Se obtienen las variables de salida
        actividad_editada = Actividad.objects.get(pk = actividad.id)
        # Se comparan los datos, se debe comprobar que el usuario ha sido redirigido a la página de detalles de la 
        # actividad tras ser editada
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/actividad/detalles/{}/'.format(actividad.id))
        # Se comprueba que los datos almacenados son los esperados
        self.assertEqual(actividad, actividad_editada)
        self.assertEqual(actividad_editada.titulo, titulo)
        self.assertURLEqual(actividad_editada.enlace, enlace)
        self.assertEqual(actividad_editada.descripcion, descripcion)
        self.assertEqual(actividad_editada.borrador, borrador)
        self.assertEqual(actividad_editada.vetada, False)
        self.assertEqual(actividad_editada.motivo_veto, None)
        self.assertEqual(actividad_editada.fecha_creacion, actividad.fecha_creacion)
        self.assertEqual(actividad_editada.comentable, comentable)
        self.assertEqual(actividad_editada.identificador, actividad.identificador)
        # El usuario se desloguea
        self.logout()

    # Un usuario edita un actividad sin estar autenticado
    def test_edita_actividad_sin_loguear(self):
        # Se inicializan variables y se loguea el usuario
        actividad = Actividad.objects.filter(borrador = True).first()
        # Se asignan variables para los datos de entrada
        titulo = 'test_edita_sin_loguear'
        enlace = 'https://testeditasinloguear.com/'
        descripcion = 'test_edita_sin_loguear'
        comentable = True
        borrador = False
        # Se realiza la petición para editar la actividad
        response = self.client.post('/actividad/edicion/{}/'.format(actividad.id), {
            'titulo': titulo, 
            'enlace': enlace, 
            'descripcion': descripcion, 
            'comentable': comentable, 
            'borrador': borrador
        })
        actividad_despues = Actividad.objects.get(pk = actividad.id)
        # Se comparan los datos, se debe comprobar que el usuario ha sido redirigido a la página de login, puesto a que 
        # ha accedido a una página que require autenticación sin estar autenticado
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/actividad/edicion/{}/'.format(actividad.id))
        # Se comprueba que no se ha editado ninguno de los campos editables
        self.assertEqual(actividad_despues.titulo, actividad.titulo)
        self.assertEqual(actividad_despues.descripcion, actividad.descripcion)
        self.assertURLEqual(actividad_despues.enlace, actividad.enlace)
        self.assertEqual(actividad_despues.borrador, actividad.borrador)
        self.assertEqual(actividad_despues.comentable, actividad.comentable)
        # El usuario se desloguea
        self.logout()

    # Un usuario edita una actividad que no es suya
    def test_edita_actividad_usuario_incorrecto(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        actividad = Actividad.objects.filter(borrador = True).exclude(autor__django_user__username = username).first()
        self.login(username, password)
        # Se asignan variables para los datos de entrada
        titulo = 'test_edita_incorrecto'
        enlace = 'https://testeditaincorrecto.com/'
        descripcion = 'test_edita_incorrecto'
        comentable = True
        borrador = False
        # Se realiza la petición para editar la actividad
        response = self.client.post('/actividad/edicion/{}/'.format(actividad.id), {
            'titulo': titulo, 
            'enlace': enlace, 
            'descripcion': descripcion, 
            'comentable': comentable, 
            'borrador': borrador
        })
        actividad_despues = Actividad.objects.get(pk = actividad.id)
        # Se comparan los datos y se comprueba que el usuario ha sido redirigido a la página de listado de las
        # actividades. Esto se debe a que no puede editar una actividad que no le pertenece y no puede acceder
        # a los detalles de una actividad ajena en modo borrador
        self.assertEqual(response.status_code, 302)
        # Se indica que se espera un codigo 302 en la respuesta debido  otra redireccion
        self.assertRedirects(response, '/actividad/detalles/{}/'.format(actividad.id), target_status_code=302)
        # Se comprueba que no se ha editado ninguno de los campos editables
        self.assertEqual(actividad_despues.titulo, actividad.titulo)
        self.assertEqual(actividad_despues.descripcion, actividad.descripcion)
        self.assertURLEqual(actividad_despues.enlace, actividad.enlace)
        self.assertEqual(actividad_despues.borrador, actividad.borrador)
        self.assertEqual(actividad_despues.comentable, actividad.comentable)
        # El usuario se desloguea
        self.logout()

    # Un usuario edita una actividad que no está en modo borrador
    def test_edita_actividad_no_borrador(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        actividad = Actividad.objects.filter(Q(borrador = False) & Q(autor__django_user__username = username)).first()
        self.login(username, password)
        # Se asignan variables para los datos de entrada
        titulo = 'test_edita_incorrecto'
        enlace = 'https://testeditaincorrecto.com/'
        descripcion = 'test_edita_incorrecto'
        comentable = True
        borrador = False
        # Se realiza la petición para editar la actividad
        response = self.client.post('/actividad/edicion/{}/'.format(actividad.id), {
            'titulo': titulo, 
            'enlace': enlace, 
            'descripcion': descripcion, 
            'comentable': comentable, 
            'borrador': borrador
        })
        actividad_despues = Actividad.objects.get(pk = actividad.id)
        # Se comparan los datos y se comprueba que el usuario ha sido redirigido a la página de detalles de la
        # actividad. Esto se debe a que no puede editar una actividad que no está en modo borrador.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/actividad/detalles/{}/'.format(actividad.id))
        # Se comprueba que no se ha editado nada
        self.assertEqual(actividad_despues.titulo, actividad.titulo)
        self.assertEqual(actividad_despues.descripcion, actividad.descripcion)
        self.assertURLEqual(actividad_despues.enlace, actividad.enlace)
        self.assertEqual(actividad_despues.borrador, actividad.borrador)
        self.assertEqual(actividad_despues.comentable, actividad.comentable)
        # El usuario se desloguea
        self.logout()

    # Un usuario edita una actividad usando datos no válidos
    def test_edita_actividad_incorrecta(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        actividad = Actividad.objects.filter(Q(borrador = True) & Q(autor__django_user__username = username)).first()
        self.login(username, password)
        # Se asignan variables para los datos de entrada
        titulo = 'test_edita_incorrecta'
        enlace = 'https://testedita_incorrecta.com/'
        descripcion = 'test_edita_incorrecta'
        comentable = True
        borrador = False
        # Se realiza la petición para editar la actividad
        response = self.client.post('/actividad/edicion/{}/'.format(actividad.id), {
            'titulo': titulo, 
            'enlace': enlace, 
            'descripcion': descripcion, 
            'comentable': comentable, 
            'borrador': borrador
        })
        actividad_despues = Actividad.objects.get(pk = actividad.id)
        # Se comparan los datos. Se comprueba que no ha sucedido ninguna redirección y que la página se ha obtenido
        # correctamente. Esto se debe a que al haber un error de validación el usuario permanece en el formulario.
        self.assertEqual(response.status_code, 200)
        # Se comprueba que no se ha editado nada
        self.assertEqual(actividad_despues.titulo, actividad.titulo)
        self.assertEqual(actividad_despues.descripcion, actividad.descripcion)
        self.assertURLEqual(actividad_despues.enlace, actividad.enlace)
        self.assertEqual(actividad_despues.borrador, actividad.borrador)
        self.assertEqual(actividad_despues.comentable, actividad.comentable)
        # El usuario se desloguea
        self.logout()



    # ELIMINACION

    # Un usuario elimina una actividad correctamente
    def test_elimina_actividad(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        actividad = Actividad.objects.filter(Q(autor__django_user__username = username) & Q(borrador = True)).first()
        numero_actividades_antes = Actividad.objects.count()
        self.login(username, password)
        # Se realiza la petición para eliminar la actividad
        response = self.client.get('/actividad/eliminacion/{}/'.format(actividad.id))
        # Se obtienen las variables de salida. Se busca la actividad y se trata de capturar la excepción que se produce
        # cuando se busca una actividad que no existe. Si se captura la excepción, entonces se puede verificar que la 
        # actividad ha sido eliminada
        actividad_eliminada = False
        try:
            Actividad.objects.get(pk = actividad.id)
        except ObjectDoesNotExist as e:
            actividad_eliminada = True
        numero_actividades_despues = Actividad.objects.count()
        # Se comparan los datos. Se comprueba que el usuario ha sido redirigido al listado de actividades y que la
        # actividad ha sido eliminada
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/actividad/listado/')
        self.assertEqual(actividad_eliminada, True)
        self.assertEqual(numero_actividades_antes, numero_actividades_despues + 1)
        # El usuario se desloguea
        self.logout()

    # Un usuario elimina una actividad sin estar autenticado
    def test_elimina_actividad_sin_loguear(self):
        # Se inicializan variables
        actividad = Actividad.objects.filter(borrador = True).first()
        numero_actividades_antes = Actividad.objects.count()
        # Se realiza la petición para eliminar la actividad
        response = self.client.get('/actividad/eliminacion/{}/'.format(actividad.id))
        # Se obtienen las variables de salida. Se busca la actividad y se trata de capturar la excepción que se produce
        # cuando se busca una actividad que no existe. Si se captura la excepción, entonces se puede verificar que la 
        # actividad ha sido eliminada
        actividad_eliminada = False
        try:
            Actividad.objects.get(pk = actividad.id)
        except ObjectDoesNotExist as e:
            actividad_eliminada = True
        numero_actividades_despues = Actividad.objects.count()
        # Se comparan los datos. Se comprueba que el usuario, al tratar de acceder a una página que requiere 
        # autenticación sin estar autenticado, es redirigido a la página de login. Se comprueba además que no se ha 
        # eliminado la actividad
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/actividad/eliminacion/{}/'.format(actividad.id))
        self.assertEqual(actividad_eliminada, False)
        self.assertEqual(numero_actividades_antes, numero_actividades_despues)

    # Un usuario elimina una actividad que no es suya
    def test_elimina_actividad_usuario_incorrecto(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        actividad = Actividad.objects.exclude(autor__django_user__username = username).filter(borrador = True).first()
        numero_actividades_antes = Actividad.objects.count()
        self.login(username, password)
        # Se realiza la petición para eliminar la actividad
        response = self.client.get('/actividad/eliminacion/{}/'.format(actividad.id))
        # Se obtienen las variables de salida. Se busca la actividad y se trata de capturar la excepción que se produce
        # cuando se busca una actividad que no existe. Si se captura la excepción, entonces se puede verificar que la 
        # actividad ha sido eliminada
        actividad_eliminada = False
        try:
            Actividad.objects.get(pk = actividad.id)
        except ObjectDoesNotExist as e:
            actividad_eliminada = True
        numero_actividades_despues = Actividad.objects.count()
        # Se comparan los datos. Se comprueba que el usuario ha sido redirigido al listado de las actividades y que no
        # se ha eliminado la actividad. Esto se debe a que un usuario no puede eliminar una actividad que no le
        # pertenece y y no puede acceder a los detalles de una actividad ajena en modo borrador
        self.assertEqual(response.status_code, 302)
        # Se indica que se espera un codigo 302 en la respuesta debido  otra redireccion
        self.assertRedirects(response, '/actividad/detalles/{}/'.format(actividad.id), target_status_code=302)
        self.assertEqual(numero_actividades_antes, numero_actividades_despues)
        self.assertEqual(actividad_eliminada, False)
        # El usuario se desloguea
        self.logout()

    # Un usuario elimina una actividad que no estaba en modo borrador
    def test_elimina_actividad_no_borrador(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        actividad = Actividad.objects.filter(Q(autor__django_user__username = username) & Q(borrador = False)).first()
        numero_actividades_antes = Actividad.objects.count()
        self.login(username, password)
        # Se realiza la petición para crear la actividad
        response = self.client.get('/actividad/eliminacion/{}/'.format(actividad.id))
        # Se obtienen las variables de salida. Se busca la actividad y se trata de capturar la excepción que se produce
        # cuando se busca una actividad que no existe. Si se captura la excepción, entonces se puede verificar que la 
        # actividad ha sido eliminada
        actividad_eliminada = False
        try:
            Actividad.objects.get(pk = actividad.id)
        except ObjectDoesNotExist as e:
            actividad_eliminada = True
        numero_actividades_despues = Actividad.objects.count()
        # Se comparan los datos
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/actividad/detalles/{}/'.format(actividad.id))
        self.assertEqual(numero_actividades_antes, numero_actividades_despues)
        self.assertEqual(actividad_eliminada, False)
        # El usuario se desloguea
        self.logout()



    # VETO

    # Un administrador veta una actividad
    def test_veta_actividad(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        actividad = Actividad.objects.filter(Q(vetada = False) & Q(borrador = False)).first()
        motivo_veto = 'Testing'
        self.login(username, password)
        # Se realiza la petición para vetar la actividad
        response = self.client.post('/actividad/veto/{}/'.format(actividad.id), {'motivo_veto': motivo_veto})
        # Se obtienen las variables de salida
        actividad_despues = Actividad.objects.get(pk = actividad.id)
        # Se comparan los datos. Se comprueba que el usuario ha sido redirigido a la paǵina de detalles y que la
        # actividad se ha vetado correctemente, además de guardarse el motivo de veto.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/actividad/detalles/{}/'.format(actividad.id))
        self.assertEqual(actividad_despues.vetada, True)
        self.assertEqual(actividad_despues.motivo_veto, motivo_veto)
        # El usuario se desloguea
        self.logout()
    
    # Un usuario no autenticado veta una actividad
    def test_veta_actividad_sin_loguear(self):
        # Se inicializan variables y se loguea el usuario        
        actividad = Actividad.objects.filter(Q(vetada = False) & Q(borrador = False)).first()
        motivo_veto = 'Testing'
        # Se realiza la petición para vetar la actividad
        response = self.client.post('/actividad/veto/{}/'.format(actividad.id), {'motivo_veto': motivo_veto})
        # Se obtienen las variables de salida
        actividad_despues = Actividad.objects.get(pk = actividad.id)
        # Se comparan los datos. Se comprueba que la actividad no ha sufrido cambios y que el usuario ha sido redirigido
        # al login debido a que hay que esrar autenticado para vetar una actividad.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/actividad/veto/{}/'.format(actividad.id))
        # Se comprueba que la actividad no ha sido vetada
        self.assertEqual(actividad_despues.vetada, False)
        self.assertEqual(actividad_despues.motivo_veto, None)
        # El usuario se desloguea
        self.logout()

    # Un usuario que no es administrador veta la actividad
    def test_veta_actividad_usuario_incorrecto(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        actividad = Actividad.objects.filter(Q(vetada = False) & Q(borrador = False)).first()
        motivo_veto = 'Testing'
        self.login(username, password)
        # Se realiza la petición para vetar la actividad
        response = self.client.post('/actividad/veto/{}/'.format(actividad.id), {'motivo_veto': motivo_veto})
        # Se obtienen las variables de salida
        actividad_despues = Actividad.objects.get(pk = actividad.id)
        # Se comparan los datos. Se comprueba que la actividad no ha sufrido cambios y que se ha redirigido al usuario
        # a los detalles de la actividad debido a que el usuario no tiene los permisos de administrador
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/actividad/detalles/{}/'.format(actividad.id))
        self.assertEqual(actividad_despues.vetada, False)
        self.assertEqual(actividad_despues.motivo_veto, None)
        # El usuario se desloguea
        self.logout()

    # Un administrador veta una actividad ya vetada
    def test_veta_actividad_vetada(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        actividad = Actividad.objects.filter(Q(vetada = True) & Q(borrador = False)).first()
        motivo_veto = actividad.motivo_veto + 'Testing'
        self.login(username, password)
        # Se realiza la petición para vetar la actividad
        response = self.client.post('/actividad/veto/{}/'.format(actividad.id), {'motivo_veto': motivo_veto})
        # Se obtienen las variables de salida
        actividad_despues = Actividad.objects.get(pk = actividad.id)
        # Se comparan los datos. Se comprueba que la actividad no ha sufrido cambios y que el usuario ha sido redirigido
        # a los detalles de la actividad debido a que no se puede vetar una actividad ya vetada.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/actividad/detalles/{}/'.format(actividad.id))
        self.assertEqual(actividad_despues.vetada, True)
        self.assertEqual(actividad_despues.motivo_veto, actividad.motivo_veto)
        # El usuario se desloguea
        self.logout()

    # Un administrador veta una actividad que ya existe
    def test_veta_actividad_inexistente(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        motivo_veto = 'Testing'
        self.login(username, password)
        # Se realiza la petición para vetar la actividad
        response = self.client.post('/actividad/veto/0/', {'motivo_veto': motivo_veto})
        # Se comparan los datos. El usuario es redirigido al listado de actividades debido a que no se puede encontrar 
        # la actividad que se quiere vetar
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/actividad/listado/')
        # El usuario se desloguea
        self.logout()

    # Un adminsitrador veta una actividad insertando un motivo de veto no válido
    def test_veta_actividad_incorrecta(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        motivo_veto = 'Testing'
        actividad = Actividad.objects.filter(Q(vetada = False) & Q(borrador = False)).first()
        self.login(username, password)
        # Se realiza la petición para vetar la actividad
        response = self.client.post('/actividad/veto/{}/'.format(actividad.id))
        # Se obtienen las variables de salida
        actividad_despues = Actividad.objects.get(pk = actividad.id)
        # Se comparan los datos. Se comprueba que la actividad no ha sufrido cambios y que el usuario permanece el 
        # formulario de veto debido a que se ha insertado un motivo de veto no válido
        self.assertEqual(response.status_code, 200)
        self.assertEqual(actividad_despues.vetada, False)
        self.assertEqual(actividad_despues.motivo_veto, None)
        # El usuario se desloguea
        self.logout()

    # Un administrador veta una actividad que está en modo borrador
    def test_veta_actividad_borrador(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        motivo_veto = 'Testing'
        actividad = Actividad.objects.filter(Q(vetada = False) & Q(borrador = True)).first()
        self.login(username, password)
        # Se realiza la petición para vetar la actividad
        response = self.client.post('/actividad/veto/{}/'.format(actividad.id), {'motivo_veto': motivo_veto})
        # Se obtienen las variables de salida
        actividad_despues = Actividad.objects.get(pk = actividad.id)
        # Se comparan los datos. Se comprueba que la actividad no ha sufrido cambios y que el usuario ha sido
        # redirigido a los detalles de la actividad puesto a que no se puede vetar una actividad en modo borrador y
        # y no puede acceder a los detalles de una actividad ajena en modo borrador
        self.assertEqual(response.status_code, 302)
        # Debido a que la redirección termina con otra redirección, se debe indicar que se espera un status code 302
        self.assertRedirects(response, reverse('actividad_detalles', kwargs = {'actividad_id': actividad.id}),
            target_status_code=302)
        self.assertEqual(actividad_despues.vetada, False)
        self.assertEqual(actividad_despues.motivo_veto, None)
        # El usuario se desloguea
        self.logout()



    # LEVANTAMIENTO VETO

    # Un administrador levanta el veto sobre una actividad
    def test_levanta_veto_actividad(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        actividad = Actividad.objects.filter(Q(vetada = True) & Q(borrador = False)).first()
        self.login(username, password)
        # Se realiza la petición para levantar el veto sobre la actividad
        response = self.client.get('/actividad/levantamiento_veto/{}/'.format(actividad.id))
        # Se obtienen las variables de salida
        actividad_despues = Actividad.objects.get(pk = actividad.id)
        # Se comparan los datos. Se comprueba que la actividad ya no está vetada y que no aparece el motivo de veto. Se
        # comprueba además que el usuario ha sido redirigido a los detalles de la actividad.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/actividad/detalles/{}/'.format(actividad.id))
        self.assertEqual(actividad_despues.vetada, False)
        self.assertEqual(actividad_despues.motivo_veto, None)
        # El usuario se desloguea
        self.logout()

    # Un usuario levanta el veto sobre una actividad sin estar logueado
    def test_levanta_veto_actividad_sin_loguear(self):
        # Se inicializan variables y se loguea el usuario        
        actividad = Actividad.objects.filter(Q(vetada = True) & Q(borrador = False)).first()
        # Se realiza la petición para levantar el veto sobre la actividad
        response = self.client.get('/actividad/levantamiento_veto/{}/'.format(actividad.id))
        # Se obtienen las variables de salida
        actividad_despues = Actividad.objects.get(pk = actividad.id)
        # Se comparan los datos. Se comprueba que la actividad no ha sufrido cambios y que se ha redirigido al usuario al
        # login, puesto a que se require autenticación para levantar el veto sobre una actividad.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/actividad/levantamiento_veto/{}/'.format(actividad.id))
        self.assertEqual(actividad_despues.vetada, True)
        self.assertEqual(actividad_despues.motivo_veto, actividad.motivo_veto)
        # El usuario se desloguea
        self.logout()

    # Un usuario levanta el veto sobre una actividad sin ser administrador
    def test_levanta_veto_actividad_usuario_incorrecto(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario1'
        password = 'usuario1'
        actividad = Actividad.objects.filter(Q(vetada = True) & Q(borrador = False)).first()
        self.login(username, password)
        # Se realiza la petición para levantar el veto sobre la actividad
        response = self.client.get('/actividad/levantamiento_veto/{}/'.format(actividad.id))
        # Se obtienen las variables de salida
        actividad_despues = Actividad.objects.get(pk = actividad.id)
        # Se comparan los datos. Se comprueba que la actividad no ha sufrido cambios y que se ha redirigido al usuario a
        # los detalles de la actividad debido a que el usuario no tiene los permisos de administrador necesarios.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/actividad/detalles/{}/'.format(actividad.id))
        self.assertEqual(actividad_despues.vetada, True)
        self.assertEqual(actividad_despues.motivo_veto, actividad.motivo_veto)
        # El usuario se desloguea
        self.logout()

    # Un usuario levanta el veto sobre una actividad no vetada
    def test_levanta_veto_actividad_no_vetada(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        actividad = Actividad.objects.filter(Q(vetada = False) & Q(borrador = False)).first()
        self.login(username, password)
        # Se realiza la petición para levantar el veto sobre la actividad
        response = self.client.get('/actividad/levantamiento_veto/{}/'.format(actividad.id))
        # Se obtienen las variables de salida
        actividad_despues = Actividad.objects.get(pk = actividad.id)
        # Se comparan los datos. Se comprueba que la actividad no ha sufrido cambios y que se ha redirido al usuario a los
        # detalles de la actividad, puesto a que no se puede levantar el veto sobre una actividad que no está vetada.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/actividad/detalles/{}/'.format(actividad.id))
        self.assertEqual(actividad_despues.vetada, False)
        self.assertEqual(actividad_despues.motivo_veto, None)
        # El usuario se desloguea
        self.logout()

    # Un usuario levanta el veto sobre una actividad que no existe
    def test_levanta_veto_actividad_inexistente(self):
        # Se inicializan variables y se loguea el usuario
        username = 'usuario2'
        password = 'usuario2'
        self.login(username, password)
        # Se realiza la petición para levantar el veto sobre la actividad
        response = self.client.get('/actividad/levantamiento_veto/0/')
        # Se comparan los datos. Se comprueba que al no existir la actividad, se ha redirigido al usuario al listado de
        # actividades
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/actividad/listado/')
        # El usuario se desloguea
        self.logout()

