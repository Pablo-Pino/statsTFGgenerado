from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from datetime import date
import re

from websecurityapp.models.perfil_models import Usuario
from websecurityapp.models.actividad_models import Actividad, SesionActividad


class PerfilTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        exec(open('populate_database.py').read())

    # Método que simula un login
    def login(self, username, password):
        response = self.client.post('/login/', {'username': username, 'password': password})
        usuario = Usuario.objects.get(django_user__username=username)
        return usuario

    # Método que simula un logout
    def logout(self):
        self.client.get('/logout/')



    # CREACIÓN DE SESIONACTIVIDAD

    # Se crea el token de sesión en una actividad para el usuario
    def test_crea_sesionactividad(self):
        # Se usuario se loguea en el sistema
        username = 'usuario3'
        password = 'usuario3'
        usuario = self.login(username, password)
        numero_sesionactividad_antes = SesionActividad.objects.count()
        enlace = 'http://localhost:8000' + reverse('ejercicio_mock_1')
        actividad = Actividad.objects.get(enlace = enlace)
        # Se accede al ejercicio de ejemplo
        response = self.client.get('http://localhost:8000' + reverse('sesionactividad_comienzo', kwargs={'identificador': actividad.identificador}))
        # Se comprueba que la respuesta es correcta
        self.assertEquals(response.status_code, 200)
        # Se comprueba que se ha generado una nueva sesion de actividad para el usuario y la actividad
        numero_sesionactividad_despues = SesionActividad.objects.count()
        es_sesionactividad_creada = True
        try:
            SesionActividad.objects.get(actividad = actividad, usuario = usuario)
        except ObjectDoesNotExist as e:
            es_sesionactividad_creada = False
        self.assertEquals(numero_sesionactividad_antes, numero_sesionactividad_despues - 1)
        self.assertTrue(es_sesionactividad_creada)
        # El usuario se desloguea
        self.logout()

    # Se crea el token de sesion en una actividad para un usuario no autenticado
    def test_crea_sesionactividad_sin_autenticar(self):
        # Se usuario se loguea en el sistema
        numero_sesionactividad_antes = SesionActividad.objects.count()
        enlace = 'http://localhost:8000' + reverse('ejercicio_mock_1')
        actividad = Actividad.objects.get(enlace = enlace)
        # Se accede al ejercicio de ejemplo
        response = self.client.get('http://localhost:8000' + reverse('sesionactividad_comienzo', kwargs={'identificador': actividad.identificador}))
        # Se comprueba que la respuesta es correcta
        self.assertEquals(response.status_code, 500)
        # Se comprueba que se ha generado una nueva sesion de actividad para el usuario y la actividad
        numero_sesionactividad_despues = SesionActividad.objects.count()
        self.assertEquals(numero_sesionactividad_antes, numero_sesionactividad_despues)
        # El usuario se desloguea
        self.logout()

    # Se crea el token de sesion en la actividad para un usuario que ya tiene un token de sesion en dicha actividad
    def test_crea_sesionactividad_refresca(self):
        # El usuario se loguea en el sistema
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        numero_sesionactividad_antes = SesionActividad.objects.count()
        enlace = 'http://localhost:8000' + reverse('ejercicio_mock_2')
        actividad = Actividad.objects.filter(enlace = enlace).exclude(autor = usuario).first()
        # Se accede al ejercicio de ejemplo
        response = self.client.get('http://localhost:8000' + reverse('sesionactividad_comienzo', kwargs={'identificador': actividad.identificador}))
        # Se comprueba que la respuesta es correcta
        self.assertEquals(response.status_code, 200)
        # Se comprueba que se ha generado una nueva sesion de actividad para el usuario y la actividad
        numero_sesionactividad_despues = SesionActividad.objects.count()
        es_sesionactividad_creada = True
        try:
            SesionActividad.objects.get(actividad=actividad, usuario=usuario)
        except ObjectDoesNotExist as e:
            es_sesionactividad_creada = False
        self.assertEquals(numero_sesionactividad_antes, numero_sesionactividad_despues)
        self.assertTrue(es_sesionactividad_creada)
        # El usuario se desloguea
        self.logout()



    # ELIMINACIÓN DE SESIONACTIVIDAD

    # Se elimina una sesion
    def test_elimina_sesionactividad(self):
        # Se usuario se loguea en el sistema
        username = 'usuario2'
        password = 'usuario2'
        usuario = self.login(username, password)
        numero_sesionactividad_antes = SesionActividad.objects.count()
        enlace = 'http://localhost:8000' + reverse('ejercicio_mock_1')
        actividad = Actividad.objects.get(enlace=enlace)
        sesionactividad = SesionActividad.objects.get(actividad=actividad, usuario=usuario)
        # Se accede al ejercicio de ejemplo
        response = self.client.post('http://localhost:8000' + reverse('sesionactividad_final', kwargs={'identificador': actividad.identificador}), {
            'token': sesionactividad.token
        }, content_type="application/json")
        # Se comprueba que la respuesta es correcta
        self.assertEquals(response.status_code, 201)
        # Se comprueba que se ha generado una nueva sesion de actividad para el usuario y la actividad
        numero_sesionactividad_despues = SesionActividad.objects.count()
        es_sesionactividad_eliminada = False
        try:
            SesionActividad.objects.get(actividad=actividad, usuario=usuario)
        except ObjectDoesNotExist as e:
            es_sesionactividad_eliminada = True
        self.assertEquals(numero_sesionactividad_antes, numero_sesionactividad_despues + 1)
        self.assertTrue(es_sesionactividad_eliminada)
        # Se comprueba que ahora la actividad está registrada como actividad realizada por el usuario
        usuario_despues = Usuario.objects.get(pk=usuario.id)
        actividades_realizadas_despues = usuario_despues.actividades_realizadas.all()
        self.assertTrue(actividad in actividades_realizadas_despues)
        # El usuario se desloguea
        self.logout()

    # Se elimina el token de sesion de una actividad para un usuario no autenticado
    def test_elimina_sesionactividad_sin_autenticar(self):
        # Se usuario se loguea en el sistema
        numero_sesionactividad_antes = SesionActividad.objects.count()
        enlace = 'http://localhost:8000' + reverse('ejercicio_mock_1')
        actividad = Actividad.objects.get(enlace=enlace)
        sesionactividad = SesionActividad.objects.get(actividad=actividad)
        # Se accede al ejercicio de ejemplo
        response = self.client.post('http://localhost:8000' + reverse('sesionactividad_final', kwargs={'identificador': actividad.identificador}), {
            'token': sesionactividad.token
        }, content_type="application/json")
        # Se comprueba que la respuesta es correcta
        self.assertEquals(response.status_code, 500)
        # Se comprueba que se ha generado una nueva sesion de actividad para el usuario y la actividad
        numero_sesionactividad_despues = SesionActividad.objects.count()
        self.assertEquals(numero_sesionactividad_antes, numero_sesionactividad_despues)
        # El usuario se desloguea
        self.logout()

    # Se elimina el token de sesion en la actividad para un usuario sin haber actividad
    # def test_elimina_sesionactividad_sin_actividad(self):

    # Se elimina una sesion que no existe
    def test_elimina_sesionactividad_no_existente(self):
        # El usuario se loguea en el sistema
        username = 'usuario3'
        password = 'usuario3'
        usuario = self.login(username, password)
        enlace = 'http://localhost:8000' + reverse('ejercicio_mock_2')
        numero_sesionactividad_antes = SesionActividad.objects.count()
        actividad = Actividad.objects.filter(enlace=enlace).exclude(autor=usuario).first()
        # Se accede al ejercicio de ejemplo
        response = self.client.post('http://localhost:8000' + reverse('sesionactividad_final', kwargs={'identificador': actividad.identificador}), {
            'token': ''
        }, content_type="application/json")
        self.assertEquals(response.status_code, 500)
        # Se comprueba que se ha generado una nueva sesion de actividad para el usuario y la actividad
        numero_sesionactividad_despues = SesionActividad.objects.count()
        self.assertEquals(numero_sesionactividad_antes, numero_sesionactividad_despues)
        # El usuario se desloguea
        self.logout()

    # Se elimina una sesion de una actividad que el usuario ya ha realizado previamente

