import os

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

from websecurityapp.models.perfil_models import Usuario, Anexo
from websecurityapp.models.actividad_models import Actividad, SesionActividad
from selenium.webdriver.common.proxy import Proxy, ProxyType

# https://stackoverflow.com/questions/18719980/proxy-selenium-python-firefox

class SesionActividadTestCase(StaticLiveServerTestCase):
    fixtures = ['dumpdata.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def login(self, username, password):
        self.selenium.get('%s%s' % (self.live_server_url, '/login'))
        input_username = self.selenium.find_element_by_id('id_username')
        input_password = self.selenium.find_element_by_id('id_password')
        input_username.send_keys(username)
        input_password.send_keys(password)
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click()
        user = User.objects.get(username=username)
        h2_home = self.selenium.find_element_by_tag_name('h2')
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/')
        self.assertEqual('Bienvenido {} {}'.format(user.first_name, user.last_name) in h2_home.text, True)
        usuario = Usuario.objects.get(django_user = user)
        return usuario

    def logout(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/logout'))


    def script_inicio_actividad(self, actividad):
        self.selenium.execute_async_script('''
            call_script_inicio_actividad = arguments[0]
            fetch(\'{}/sesionactividad/comienzo/{}/\').then(
                (response) => {{
                    divAlert = document.getElementById(\'alert-div\');
                    divAlert.innerHTML = \'\';
                    divMensaje = document.createElement(\'div\');
                    divMensaje.id = \'message-div\';
                    if (response.status == 200)
                        divMensaje.className = \'alert alert-success\';
                    else if (response.status == 500)
                        divMensaje.className = \'alert alert-danger\';
                    divAlert.appendChild(divMensaje);
                    return response.json();
            }}).then(
                (data) => {{
                    Cookies.set(\'sesionactividad_token\', data[\'token\']);
                    divMensaje = document.getElementById(\'message-div\');
                    messageText = document.createTextNode(data[\'status\']);
                    divMensaje.appendChild(messageText);
                    call_script_inicio_actividad()
            }});
            '''.format(self.live_server_url, actividad.identificador))

    def script_final_actividad(self, actividad):
        self.selenium.execute_async_script('''
            call_script_final_actividad = arguments[0];
            token = Cookies.get(\'sesionactividad_token\');
            csrfToken = Cookies.get(\'csrftoken\');
            fetch(\'{}/sesionactividad/final/{}/\', {{
                method: \'POST\',
                headers: {{
                    \'Content-Type\': \'application/json\',
                    \'X-CSRFToken\': csrfToken
                }},
                body: JSON.stringify({{token: token}})
            }}).then(
                (response) => {{
                    jsonResponse = response.json();
                    divAlert = document.getElementById(\'alert-div\');
                    divAlert.innerHTML = \'\';
                    divMensaje = document.createElement(\'div\');
                    divMensaje.id = \'message-div\';
                    if (response.status == 201)
                        divMensaje.className = \'alert alert-success\';
                    else if (response.status == 500)
                        divMensaje.className = \'alert alert-danger\';
                    divAlert.appendChild(divMensaje);
                    return jsonResponse;
            }}).then(
                (data) => {{
                    divMensaje = document.getElementById(\'message-div\');
                    messageText = document.createTextNode(data.status);
                    divMensaje.appendChild(messageText);
                    call_script_final_actividad();
            }});
            '''.format(self.live_server_url, actividad.identificador))


    # TEST REALIZA ACTIVIDAD

    def test_realiza_actividad(self):
        # El usuario se autentica
        username = 'usuario3'
        password = 'usuario3'
        usuario = self.login(username, password)
        numero_sesionactividad_antes = SesionActividad.objects.count()
        enlace = 'http://localhost:8000' + reverse('ejercicio_mock_1')
        actividad = Actividad.objects.get(enlace=enlace)
        enlace = self.live_server_url + reverse('ejercicio_mock_1')
        # El usuario usa el enlace para acceder a la actividad
        self.selenium.get(enlace)
        # Se ejecuta el script de JavaScript asociado al inicio de la actividad
        self.script_inicio_actividad(actividad)
        # Se comprueba que se ha creado una sesionactividad para el usuario
        numero_sesionactividad_creacion = SesionActividad.objects.count()
        sesionactividad_creada = True
        try:
            SesionActividad.objects.get(usuario=usuario, actividad=actividad)
        except ObjectDoesNotExist as e:
            sesionactividad_creada = False
        self.assertEquals(numero_sesionactividad_antes, numero_sesionactividad_creacion - 1)
        self.assertTrue(sesionactividad_creada)
        # Se comprueba que se ha notificado que la actividad ha comenzado correctamente
        alerta_exito = self.selenium.find_element_by_class_name('alert-success')
        self.assertEquals(alerta_exito.text, 'Se ha comenzado la actividad correctamente')
        # El usuario realiza la actividad
        boton_mock = self.selenium.find_element_by_id('boton_resuelve_mock')
        boton_mock.click()
        # Se ejecuta el script de JavaScript asociado al final de la actividad
        self.script_final_actividad(actividad)
        # Se comprueba que se ha eliminado la sesión del usuario
        numero_sesionactividad_eliminacion = SesionActividad.objects.count()
        sesionactividad_eliminada = False
        try:
            SesionActividad.objects.get(usuario=usuario, actividad=actividad)
        except ObjectDoesNotExist as e:
            sesionactividad_eliminada = True
        self.assertEquals(numero_sesionactividad_antes, numero_sesionactividad_eliminacion)
        self.assertTrue(sesionactividad_eliminada)
        # Se comprueba que se ha notificado al usuario que la actividad ha terminado correctamente
        alerta_exito = self.selenium.find_element_by_class_name('alert-success')
        self.assertEquals(alerta_exito.text, 'Se ha realizado correctamente la actividad')
        self.assertTrue(actividad in usuario.actividades_realizadas.all())
        # El usuario se desloguea
        self.logout()

    def test_realiza_actividad_iniciada(self):
        # El usuario se autentica
        username = 'usuario2'
        password = 'usuario2'
        usuario = self.login(username, password)
        numero_sesionactividad_antes = SesionActividad.objects.count()
        enlace = 'http://localhost:8000' + reverse('ejercicio_mock_1')
        actividad = Actividad.objects.get(enlace=enlace)
        enlace = self.live_server_url + reverse('ejercicio_mock_1')
        # El usuario usa el enlace para acceder a la actividad
        self.selenium.get(enlace)
        # Se ejecuta el script de JavaScript asociado al inicio de la actividad
        self.script_inicio_actividad(actividad)
        # Se comprueba que se ha creado una sesionactividad para el usuario
        numero_sesionactividad_creacion = SesionActividad.objects.count()
        sesionactividad_creada = True
        try:
            SesionActividad.objects.get(usuario=usuario, actividad=actividad)
        except ObjectDoesNotExist as e:
            sesionactividad_creada = False
        self.assertEquals(numero_sesionactividad_antes, numero_sesionactividad_creacion)
        self.assertTrue(sesionactividad_creada)
        # Se comprueba que se ha notificado que la actividad ha comenzado correctamente
        alerta_exito = self.selenium.find_element_by_class_name('alert-success')
        self.assertEquals(alerta_exito.text, 'Se ha comenzado la actividad correctamente')
        # El usuario realiza la actividad
        boton_mock = self.selenium.find_element_by_id('boton_resuelve_mock')
        boton_mock.click()
        # Se ejecuta el script de JavaScript asociado al final de la actividad
        self.script_final_actividad(actividad)
        # Se comprueba que se ha eliminado la sesión del usuario
        numero_sesionactividad_eliminacion = SesionActividad.objects.count()
        sesionactividad_eliminada = False
        try:
            SesionActividad.objects.get(usuario=usuario, actividad=actividad)
        except ObjectDoesNotExist as e:
            sesionactividad_eliminada = True
        self.assertEquals(numero_sesionactividad_antes, numero_sesionactividad_eliminacion + 1)
        self.assertTrue(sesionactividad_eliminada)
        # Se comprueba que se ha notificado al usuario que la actividad ha terminado correctamente
        alerta_exito = self.selenium.find_element_by_class_name('alert-success')
        self.assertEquals(alerta_exito.text, 'Se ha realizado correctamente la actividad')
        self.assertTrue(actividad in usuario.actividades_realizadas.all())
        # El usuario se desloguea
        self.logout()

    # TEST INICIA ACTIVIDAD

    def test_inicia_actividad_sin_autenticar(self):
        # El usuario se autentica
        numero_sesionactividad_antes = SesionActividad.objects.count()
        enlace = 'http://localhost:8000' + reverse('ejercicio_mock_2')
        actividad = Actividad.objects.get(enlace=enlace)
        enlace = self.live_server_url + reverse('ejercicio_mock_2')
        # El usuario usa el enlace para acceder a la actividad
        self.selenium.get(enlace)
        # Se ejecuta el script de JavaScript asociado al inicio de la actividad
        self.script_inicio_actividad(actividad)
        # Se comprueba que no se ha creado una sesionactividad
        numero_sesionactividad_creacion = SesionActividad.objects.count()
        self.assertEquals(numero_sesionactividad_antes, numero_sesionactividad_creacion)
        # Se comprueba que se ha notificado que no se ha podido iniciar la actividad
        alerta_error = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEquals(alerta_error.text, 'Se debe iniciar sesión para acceder a la actividad')

    # TEST FINALIZA ACTIVIDAD

    def test_finaliza_actividad_sin_autenticar(self):
        # El usuario se autentica
        numero_sesionactividad_antes = SesionActividad.objects.count()
        enlace = 'http://localhost:8000' + reverse('ejercicio_mock_2')
        actividad = Actividad.objects.get(enlace=enlace)
        enlace = self.live_server_url + reverse('ejercicio_mock_2')
        # El usuario usa el enlace para acceder a la actividad
        self.selenium.get(enlace)
        # Se ejecuta el script de JavaScript asociado al inicio de la actividad
        self.script_inicio_actividad(actividad)
        # Se comprueba que no se ha creado una sesionactividad
        numero_sesionactividad_creacion = SesionActividad.objects.count()
        self.assertEquals(numero_sesionactividad_antes, numero_sesionactividad_creacion)
        # Se comprueba que se ha notificado que no se ha podido iniciar la actividad
        alerta_error = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEquals(alerta_error.text, 'Se debe iniciar sesión para acceder a la actividad')
        # El usuario realiza la actividad
        boton_mock = self.selenium.find_element_by_id('boton_resuelve_mock')
        boton_mock.click()
        # Se ejecuta el script de JavaScript asociado al final de la actividad
        self.script_final_actividad(actividad)
        # Se comprueba que no se ha eliminado ninguna sesion
        numero_sesionactividad_eliminacion = SesionActividad.objects.count()
        self.assertEquals(numero_sesionactividad_eliminacion, numero_sesionactividad_antes)
        # Se ha notificado al usuario que debe estar logueado
        alerta_error = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEquals(alerta_error.text, 'El usuario debe estar autenticado')

    def test_finaliza_actividad_finalizada(self):
        # El usuario se autentica
        username = 'usuario3'
        password = 'usuario3'
        usuario = self.login(username, password)
        numero_sesionactividad_antes = SesionActividad.objects.count()
        enlace = 'http://localhost:8000' + reverse('ejercicio_mock_1')
        actividad = Actividad.objects.get(enlace=enlace)
        enlace = self.live_server_url + reverse('ejercicio_mock_1')
        # El usuario usa el enlace para acceder a la actividad
        self.selenium.get(enlace)
        # Se ejecuta el script de JavaScript asociado al inicio de la actividad
        self.script_inicio_actividad(actividad)
        # Se comprueba que se ha creado una sesionactividad para el usuario
        numero_sesionactividad_creacion = SesionActividad.objects.count()
        sesionactividad_creada = True
        try:
            SesionActividad.objects.get(usuario=usuario, actividad=actividad)
        except ObjectDoesNotExist as e:
            sesionactividad_creada = False
        self.assertEquals(numero_sesionactividad_antes, numero_sesionactividad_creacion - 1)
        self.assertTrue(sesionactividad_creada)
        # Se comprueba que se ha notificado que la actividad ha comenzado correctamente
        alerta_exito = self.selenium.find_element_by_class_name('alert-success')
        self.assertEquals(alerta_exito.text, 'Se ha comenzado la actividad correctamente')
        # El usuario realiza la actividad
        boton_mock = self.selenium.find_element_by_id('boton_resuelve_mock')
        boton_mock.click()
        # Se ejecuta el script de JavaScript asociado al final de la actividad
        self.script_final_actividad(actividad)
        # Se comprueba que se ha eliminado la sesión del usuario
        numero_sesionactividad_eliminacion = SesionActividad.objects.count()
        sesionactividad_eliminada = False
        try:
            SesionActividad.objects.get(usuario=usuario, actividad=actividad)
        except ObjectDoesNotExist as e:
            sesionactividad_eliminada = True
        self.assertEquals(numero_sesionactividad_antes, numero_sesionactividad_eliminacion)
        self.assertTrue(sesionactividad_eliminada)
        # Se comprueba que se ha notificado al usuario que la actividad ha terminado correctamente
        alerta_exito = self.selenium.find_element_by_class_name('alert-success')
        self.assertEquals(alerta_exito.text, 'Se ha realizado correctamente la actividad')
        self.assertTrue(actividad in usuario.actividades_realizadas.all())
        # El usuario vuelve a intentar finalizar la actividad
        boton_mock.click()
        # Se ejecuta el script de JavaScript asociado al inicio de la actividad
        self.script_final_actividad(actividad)
        # Se notifica al usuario que ha habido un error al intentar finalizar la actividad de nuevo
        alerta_error = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEquals(alerta_error.text, 'Se ha producido un error en la conexión con el servidor')
        self.assertTrue(actividad in usuario.actividades_realizadas.all())
        # El usuario se desloguea
        self.logout()

