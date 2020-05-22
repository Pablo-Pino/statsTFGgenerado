from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from selenium.webdriver import FirefoxProfile

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

from websecurityapp.models.perfil_models import Usuario, Anexo
from websecurityapp.models.actividad_models import Actividad

import datetime

from websecurityapp.test_selenium.utils import evaluar_columnas_listado_actividades


class PerfilTestCase(StaticLiveServerTestCase):
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


    
    # TEST DETALLES

    # Un usuario accede a los detalles de su perfil
    def test_detalles_mi_perfil(self):
        # El usuario se loguea
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se obtienen las variables necesarias para el test
        anexos_esperados = list(Anexo.objects.filter(usuario = usuario).order_by('id'))
        # Se accede a los detalles de mi perfil
        self.selenium.get('%s%s' % (self.live_server_url, '/perfil/detalles/'))
        # Se comprueba el titulo de la página
        h1_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual(h1_text, 'Perfil de {}'.format(username))
        # Se comprueba que aparecen el resto de campos salvo los anexos
        textos = [element.text for element in self.selenium.find_elements_by_xpath('//div[@id="id_body_detalles_perfil"]/child::p')]
        self.assertEqual(textos[0], 'Nombre : {}'.format(usuario.django_user.first_name))
        self.assertEqual(textos[1], 'Apellidos : {}'.format(usuario.django_user.last_name))
        self.assertEqual(textos[2], 'Email : {}'.format(usuario.django_user.email))
        self.assertEqual(textos[3], 'Telefono : {}'.format(usuario.telefono))
        self.assertEqual(textos[4], 'Empresa/equipo : {}'.format(usuario.empresa_u_equipo))
        # Se comprueba que aparecen los anexos
        anexos_recibidos = self.selenium.find_elements_by_xpath('//fieldset[@id="id_fieldset_anexos"]/child::ul/child::li')
        self.evaluar_anexos(usuario, usuario, anexos_recibidos, anexos_esperados)
        # Se comprueba el listado de actividades
        self.evalua_listado_actividades_detalles_perfil(usuario, usuario)
        # Se cierra sesion
        self.logout()

    # Un usuario accede a los detalles del perfil de otro usuario
    def test_detalles_perfil_ajeno(self):
        # El usuario se loguea
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se accede a los detalles del perfil de otro usuario
        usuario_perfil = Usuario.objects.exclude(pk=usuario.id).first()
        self.selenium.get('%s%s' % (self.live_server_url, '/perfil/detalles/{}/'.format(usuario_perfil.id)))
        # Se obtienen las variables necesarias para el test
        anexos_esperados = list(Anexo.objects.filter(usuario=usuario_perfil).order_by('id'))
        # Se comprueba el titulo de la página
        h1_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual(h1_text, 'Perfil de {}'.format(usuario_perfil.django_user.username))
        # Se comprueba que aparecen el resto de campos salvo los anexos
        textos = [element.text for element in self.selenium.find_elements_by_xpath('//div[@id="id_body_detalles_perfil"]/child::p')]
        self.assertEqual(textos[0], 'Nombre : {}'.format(usuario_perfil.django_user.first_name))
        self.assertEqual(textos[1], 'Apellidos : {}'.format(usuario_perfil.django_user.last_name))
        self.assertEqual(textos[2], 'Email : {}'.format(usuario_perfil.django_user.email))
        self.assertEqual(textos[3], 'Telefono : {}'.format(usuario_perfil.telefono))
        self.assertEqual(textos[4], 'Empresa/equipo : {}'.format(usuario_perfil.empresa_u_equipo))
        # Se comprueba que aparecen los anexos
        anexos_recibidos = self.selenium.find_elements_by_xpath('//fieldset[@id="id_fieldset_anexos"]/child::ul/child::li')
        self.evaluar_anexos(usuario, usuario_perfil, anexos_recibidos, anexos_esperados)
        # Se comprueba el listado de actividades
        self.evalua_listado_actividades_detalles_perfil(usuario, usuario_perfil)
        # Se cierra sesion
        self.logout()

    def evaluar_anexos(self, usuario, usuario_perfil, anexos_recibidos, anexos_esperados):
        # Se comprueba que aparece la información correspondiente a cada anexo
        for i in range(len(anexos_recibidos)):
            # Se crean variables para comparar los anexos más fácilmente
            anexo = anexos_recibidos[i]
            anexo_esperado = anexos_esperados[i]
            # Se comprueba que aparece el enlace de cada anexo
            enlace = anexo.find_element_by_tag_name('a')
            self.assertEqual(enlace.get_property('href'), anexo_esperado.anexo)
            self.assertEqual(enlace.text, anexo_esperado.anexo)
            # Se comprueba que aparecen los correspondientes botones de edición y eliminación
            if usuario == usuario_perfil:
                boton_edicion = anexo.find_element_by_id('id_boton_edicion_anexo_{}'.format(anexo_esperado.id))
                boton_eliminacion = anexo.find_element_by_id('id_boton_eliminacion_anexo_{}'.format(anexo_esperado.id))
                # Se comprueban los datos del botón de edición
                self.assertEqual(boton_edicion.get_attribute('onclick'), 'window.location.href = \'/anexo/creacion_edicion/{}/\''.format(anexo_esperado.id))
                self.assertEqual(boton_edicion.text, 'Editar anexo')
                # Se comprueban los datos del botón de eliminación
                self.assertEqual(boton_eliminacion.get_attribute('onclick'), 'window.location.href = \'/anexo/eliminacion/{}/\''.format(anexo_esperado.id))
                self.assertEqual(boton_eliminacion.text, 'Eliminar anexo')
            else:
                existe_boton_edicion = True
                existe_boton_eliminacion = True
                try:
                    anexo.find_element_by_id('id_boton_edicion_anexo_{}'.format(anexo.id))
                except NoSuchElementException as e:
                    existe_boton_edicion = False
                try:
                    anexo.find_element_by_id('id_boton_eliminacion_anexo_{}'.format(anexo.id))
                except NoSuchElementException as e:
                    existe_boton_eliminacion = False
                self.assertFalse(existe_boton_eliminacion)
                self.assertFalse(existe_boton_edicion)
        # Se comprueba que aparece el botón de creación
        if usuario == usuario_perfil:
            boton_creacion =  self.selenium.find_element_by_id('id_boton_creacion_anexo')
            self.assertEqual(boton_creacion.get_attribute('onclick'), 'window.location.href = \'/anexo/creacion_edicion/\'')
            self.assertEqual(boton_creacion.text, 'Crear nuevo anexo')
        else:
            existe_boton_creacion = True
            try:
                self.selenium.find_element_by_xpath('//fieldset/child::button')
            except NoSuchElementException as e:
                existe_boton_creacion = False
            self.assertFalse(existe_boton_creacion)

    # Se ha tenido problemas debido a que al usar los enlaces de paginacion el programa "olvida" las referencias que
    # ha usado para acceder a los distintos elementos previamente obtenidos
    def evalua_listado_actividades_detalles_perfil(self, usuario, usuario_perfil):
        # Se comprueba el listado de actividades resueltas
        fieldset_actividades = self.selenium.find_element_by_id('id_fieldset_actividades')
        actividades_esperadas = usuario_perfil.actividades_realizadas.filter(vetada=False)
        evaluar_columnas_listado_actividades(self,
            actividades_esperadas=actividades_esperadas,
            resalta_resueltas=False,
            page_param='page',
            usuario=usuario,
            parent_element='id_div_listado_actividades')



    # TEST EDICION PERFIL

    # Un usuario edita su perfil
    def test_editar_mi_perfil(self):
        # El usuario se loguea
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se obtienen las variables relevantes para el test
        nombre_usuario = 'nuevo_nombre'
        contraseña = 'nueva_contraseña'
        nombre = 'nombre'
        apellidos = 'apellidos'
        email = 'email@gmail.com'
        telefono = '123456789'
        empresa_u_equipo = 'la empresa 1'        
        # Se accede a la edición del perfil
        self.selenium.get('%s%s' % (self.live_server_url, '/perfil/edicion/'))
        # Se comprueba el título de la página
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Edicion de perfil', title_text)
        # Se insertan los datos necesarios en los campos del formulario
        input_nombre_usuario = self.selenium.find_element_by_id('id_nombre_usuario')
        input_contrasenna = self.selenium.find_element_by_id('id_contrasenna')
        input_nombre = self.selenium.find_element_by_id('id_nombre')
        input_apellidos = self.selenium.find_element_by_id('id_apellidos')
        input_email = self.selenium.find_element_by_id('id_email')
        input_telefono = self.selenium.find_element_by_id('id_telefono')
        input_empresa_u_equipo = self.selenium.find_element_by_id('id_empresa_u_equipo')
        input_nombre_usuario.clear()
        input_nombre_usuario.send_keys(nombre_usuario)
        input_contrasenna.clear()
        input_contrasenna.send_keys(contraseña)
        input_nombre.clear()
        input_nombre.send_keys(nombre)
        input_apellidos.clear()
        input_apellidos.send_keys(apellidos)
        input_email.clear()
        input_email.send_keys(email)
        input_telefono.clear()
        input_telefono.send_keys(telefono)
        input_empresa_u_equipo.clear()
        input_empresa_u_equipo.send_keys(empresa_u_equipo)
        # Se manda el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click() 
        # Se comprueba que se ha redirigido al usuario a la página de login
        self.assertEqual('{}/login/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que el mensaje de éxito es correcto
        message_success = self.selenium.find_element_by_class_name('alert-success')
        self.assertEqual(message_success.text, 'Se ha editado el perfil con exito')
        # El usuario se desloguea
        self.logout()

    # Un usuario edita su perfil introduciendo datos inválidos    
    def test_editar_mi_perfil_incorrecto(self):
        # El usuario se loguea 
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se obtienen las variables relevantes para el test
        nombre_usuario = 'nuevo_nombre'
        contraseña = 'nueva_contraseña'
        apellidos = 'apellidos'
        email = 'emailgmail.com'
        telefono = '123456789'
        empresa_u_equipo = 'la empresa 1'        
        # Se accede a la edición del perfil
        self.selenium.get('%s%s' % (self.live_server_url, '/perfil/edicion/'))
        # Se comprueba el título de la página
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Edicion de perfil', title_text)
        # Se insertan los datos necesarios en los campos del formulario
        input_nombre_usuario = self.selenium.find_element_by_id('id_nombre_usuario')
        input_contrasenna = self.selenium.find_element_by_id('id_contrasenna')
        input_nombre = self.selenium.find_element_by_id('id_nombre')
        input_apellidos = self.selenium.find_element_by_id('id_apellidos')
        input_email = self.selenium.find_element_by_id('id_email')
        input_telefono = self.selenium.find_element_by_id('id_telefono')
        input_empresa_u_equipo = self.selenium.find_element_by_id('id_empresa_u_equipo')
        input_nombre_usuario.clear()
        input_nombre_usuario.send_keys(nombre_usuario)
        input_contrasenna.clear()
        input_contrasenna.send_keys(contraseña)
        input_nombre.clear()
        input_apellidos.clear()
        input_apellidos.send_keys(apellidos)
        input_email.clear()
        input_email.send_keys(email)
        input_telefono.clear()
        input_telefono.send_keys(telefono)
        input_empresa_u_equipo.clear()
        input_empresa_u_equipo.send_keys(empresa_u_equipo)
        # Se manda el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click() 
        # Se comprueba que el usuario permanece en la página de edición
        self.assertEqual('{}/perfil/edicion/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que el mensaje de fallo es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'Ha habido un error al editar el perfil')
        # Se comprueba que los mensajes de error son correctos
        error_nombre_text = self.selenium.find_element_by_id('id_nombre_error').text
        error_email_text = self.selenium.find_element_by_id('id_email_error').text
        self.assertEqual(error_nombre_text, 'Este campo es requerido.')
        self.assertEqual(error_email_text, 'Introduzca una dirección de correo electrónico válida.')
        # El usuario se desloguea
        self.logout()



    # TEST ADICION ANEXO

    # Un usuario añade un anexo a su perfil
    def test_añadir_anexo(self):
        # El usuario se loguea
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # se obtienen las variables relevantes para el test
        anexo = 'http://elanexoparaeltesting.com'
        # Se accede a la creación del anexo
        self.selenium.get('%s%s' % (self.live_server_url, '/anexo/creacion_edicion/'))
        # Se comprueba el título de la página
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Creación de anexo', title_text)
        # Se insertan los datos necesarios en los campos del formulario
        input_anexo = self.selenium.find_element_by_id('id_anexo')
        input_anexo.clear()
        input_anexo.send_keys(anexo)
        # Se manda el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click() 
        # Se comprueba que se ha redirigido al usuario a la página de login
        self.assertEqual('{}/perfil/detalles/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que el mensaje de éxito es correcto
        message_success = self.selenium.find_element_by_class_name('alert-success')
        self.assertEqual(message_success.text, 'Se ha creado el anexo con exito')
        # El usuario se desloguea
        self.logout()
        
    # Un usuario añade un anexo  a su perfil insertando datos no válidos    
    def test_añadir_anexo_incorrecto(self):
        # El usuario se loguea
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se obtienen las variables relevantes para el test
        anexo = 'elanexoparaeltesting'
        # Se accede a la creación del anexo
        self.selenium.get('%s%s' % (self.live_server_url, '/anexo/creacion_edicion/'))
        # Se comprueba el título de la página
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Creación de anexo', title_text)
        # Se insertan los datos necesarios en los campos del formulario
        input_anexo = self.selenium.find_element_by_id('id_anexo')
        input_anexo.clear()
        input_anexo.send_keys(anexo)
        # Se manda el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click() 
        # Se comprueba que el usuario permanece en la página de creación de anexo
        self.assertEqual('{}/anexo/creacion_edicion/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que el mensaje de fallo es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'Se ha producido un error al crear el anexo')
        # Se comprueba que el mensaje de error del campo anexo es correcto
        error_anexo_text = self.selenium.find_element_by_id('id_anexo_error').text
        self.assertEqual(error_anexo_text, 'Introduzca una URL válida.')
        # El usuario se desloguea
        self.logout()
    
    # Un usuario edita un anexo
    def test_editar_anexo(self):
        # El usuario se loguea
        username = 'usuario1'
        password = 'usuario1'
        usuario =  self.login(username, password)
        # Se obtienen las variables relevantes para el test
        anexo = 'http://elanexoparaeltesting.com'       
        anexo_dado = Anexo.objects.filter(usuario = usuario).first()
        # Se accede a la edición del anexo
        self.selenium.get('%s%s' % (self.live_server_url, '/anexo/creacion_edicion/{}/'.format(anexo_dado.id)))
        # Se comprueba el título de la página
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Edición de anexo', title_text)
        # Se insertan los datos necesarios en los campos del formulario
        input_anexo = self.selenium.find_element_by_id('id_anexo')
        input_anexo.clear()
        input_anexo.send_keys(anexo)
        # Se manda el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click() 
        # Se comprueba que se ha redirigido al usuario a la página de detalles del perfil
        self.assertEqual('{}/perfil/detalles/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que el mensaje de éxito es correcto
        message_success = self.selenium.find_element_by_class_name('alert-success')
        self.assertEqual(message_success.text, 'Se ha editado el anexo con exito')
        # El usuario se desloguea
        self.logout()
        
    # Un usuario edita un anexo que no existe
    def test_editar_anexo_inexistente(self):
        # El usuario se loguea
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se obtienen las variables relevantes para el test
        anexo = 'http://elanexoparaeltesting.com'        
        # Se accede a la edición del anexo
        self.selenium.get('%s%s' % (self.live_server_url, '/anexo/creacion_edicion/0/'))
        # Se comprueba que se ha redirigido al usuario a la página de detalles del perfil
        self.assertEqual('{}/perfil/detalles/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que el mensaje de error es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se ha encontrado el anexo')
        # El usuario se desloguea
        self.logout()

    # Un usuario edita un anexo que no le pertenece
    def test_editar_anexo_ajeno(self):
        # El usuario se loguea
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se obtienen las variables relevantes para el test
        anexo = 'http://elanexoparaeltesting.com'
        anexo_dado = Anexo.objects.exclude(usuario = usuario).first()
        # Se accede a la edición del anexo
        self.selenium.get('%s%s' % (self.live_server_url, '/anexo/creacion_edicion/{}/'.format(anexo_dado.id)))
        # Se comprueba que se ha redirigido al usuario a la página de detalles del perfil
        self.assertEqual('{}/perfil/detalles/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que el mensaje de error es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No tienes los permisos o requisitos necesarios para realizar esta accion')
        # El usuario se desloguea
        self.logout()

    # Un usuario edita un anexo introduciendo datos inválidos
    def test_editar_anexo_incorrecto(self):
        # El usuario se loguea y 
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se obtienen las variables relevantes para el test
        anexo = 'elanexoparaeltesting'        
        anexo_dado = Anexo.objects.filter(usuario = usuario).first()
        # Se accede a la edición del anexo
        self.selenium.get('%s%s' % (self.live_server_url, '/anexo/creacion_edicion/{}/'.format(anexo_dado.id)))
        # Se comprueba el título de la página
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Edición de anexo', title_text)
        # Se insertan los datos necesarios en los campos del formulario
        input_anexo = self.selenium.find_element_by_id('id_anexo')
        input_anexo.clear()
        input_anexo.send_keys(anexo)
        # Se manda el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click() 
        # Se comprueba que el usuario permanece en la página de edición de anexo
        self.assertEqual('{}/anexo/creacion_edicion/{}/'.format(self.live_server_url, anexo_dado.id), self.selenium.current_url)
        # Se comprueba que el mensaje de fallo es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'Se ha producido un error al editar el anexo')
        # Se comprueba que el mensaje de error del campo anexo es correcto
        error_anexo_text = self.selenium.find_element_by_id('id_anexo_error').text
        self.assertEqual(error_anexo_text, 'Introduzca una URL válida.')
        # El usuario se desloguea
        self.logout()



    # TEST ELIMINACION ANEXO

    # Un usuario elimina un anexo
    def test_eliminar_anexo(self):
        # El usuario se loguea
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se obtienen las variables relevantes para el test
        anexo_dado = Anexo.objects.filter(usuario = usuario).first()
        # Se accede a la eliminación del anexo
        self.selenium.get('%s%s' % (self.live_server_url, '/anexo/eliminacion/{}/'.format(anexo_dado.id)))
        # Se comprueba que se ha redirigido al usuario a la página de detalles del perfil
        self.assertEqual('{}/perfil/detalles/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que el mensaje de éxito es correcto
        message_success = self.selenium.find_element_by_class_name('alert-success')
        self.assertEqual(message_success.text, 'Se ha eliminado el anexo con exito')
        # El usuario se desloguea
        self.logout()

    # Un usuario elimina un anexo que no existe
    def test_eliminar_anexo_inexistente(self):
        # El usuario se loguea y 
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se accede a la eliminación del anexo
        self.selenium.get('%s%s' % (self.live_server_url, '/anexo/eliminacion/0/'))
        # Se comprueba que se ha redirigido al usuario a la página de detalles del perfil
        self.assertEqual('{}/perfil/detalles/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que el mensaje de error es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se ha encontrado el anexo')
        # El usuario se desloguea
        self.logout()

    # Un usuario elimina un anexo que no le pertenece
    def test_eliminar_anexo_ajeno(self):
        # El usuario se loguea
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        # Se obtienen las variables relevantes para el test
        anexo_dado = Anexo.objects.exclude(usuario = usuario).first()
        # Se accede a la eliminación del anexo
        self.selenium.get('%s%s' % (self.live_server_url, '/anexo/eliminacion/{}/'.format(anexo_dado.id)))
        # Se comprueba que se ha redirigido al usuario a la página de detalles del perfil
        self.assertEqual('{}/perfil/detalles/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que el mensaje de error es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No tienes los permisos o requisitos necesarios para realizar esta accion')
        # El usuario se desloguea
        self.logout()
        




