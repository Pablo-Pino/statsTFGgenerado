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

from websecurityapp.models.perfil_models import Usuario
from websecurityapp.models.actividad_models import Actividad
from websecurityapp.test_selenium.utils import evaluar_columnas_listado_actividades, buscar_boton_listado
from websecurityapp.views.actividad_views import CreacionActividadesView

import datetime

class ActividadTestCase(StaticLiveServerTestCase):
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



    # TESTS DE LISTADO

    # Un usuario que no es administrador accede al listado de actividades
    def test_listado_actividades_no_admin(self):
        # Se accede al listado de actividades como el usuario1
        self.login('usuario1', 'usuario1')
        # Se accede al listado de actividades
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/listado'))
        # Se comprueba que aparecen las actividades correctas
        usuario = Usuario.objects.get(django_user__username = 'usuario1')
        actividades_esperadas = Actividad.objects.filter(Q(autor=usuario) | Q(borrador=False, vetada=False)).distinct().order_by('id')
        actividades_mostradas = self.selenium.find_elements_by_tag_name('tr')
        # self.assertEqual(len(actividades_esperadas), len(actividades_mostradas) - 1)
        # Se comprueba que el contenido de la tabla es correcto
        evaluar_columnas_listado_actividades(self, actividades_esperadas, usuario, True, 'page')
        # Se cierra sesion
        self.logout()

    # Un usuario que es administrador accede al listado de actividades
    def test_listado_actividades_admin(self):
         # Se accede al listado de actividades como el usuario2
        self.login('usuario2', 'usuario2')
        # Se accede al listado de actividades
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/listado'))
        # Se comprueba que aparecen las actividades correctas
        usuario = Usuario.objects.get(django_user__username = 'usuario2')
        actividades_esperadas = Actividad.objects.filter(Q(autor=usuario) | Q(borrador=False)).distinct().order_by('id')
        actividades_mostradas = self.selenium.find_elements_by_tag_name('tr')
        # self.assertEqual(len(actividades_esperadas), len(actividades_mostradas) - 1)
        # Se comprueba que el contenido de la tabla es correcto
        evaluar_columnas_listado_actividades(self, actividades_esperadas, usuario, True, 'page')
        # Se cierra sesion
        self.logout()

    # Un usuario accede al listado de sus propias actividades
    def test_listado_actividades_propias(self):
        # Se accede al listado de actividades propias como el usuario1
        usuario = self.login('usuario1', 'usuario1')
        # Se accede al listado de actividades
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/listado_propio'))
        # Se comprueba que aparecen las actividades correctas
        actividades_esperadas = Actividad.objects.filter(autor=usuario).distinct().order_by('id')
        actividades_mostradas = self.selenium.find_elements_by_tag_name('tr')
        # self.assertEqual(len(actividades_esperadas), len(actividades_mostradas) - 1)
        # Se comprueba que el contenido de la tabla es correcto
        evaluar_columnas_listado_actividades(self, actividades_esperadas, usuario, False, 'page')
        # Se cierra sesion
        self.logout()



    # TEST DE DETALLES

    # Para comprobar los botones de vetar y levantar el veto, además del motivo de veto y el enlace a la actividad

    # Un usuario accede a los detalles de una actividad no baneada y no es administrador
    def test_detalles_actividad_no_baneada_no_admin(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        usuario = self.login('usuario1', 'usuario1')
        actividad = Actividad.objects.filter(borrador=False).first()
        # Se comprueban que los datos mostrados son correctos
        self.detalles_actividad(actividad, usuario)
        # El usuario se desloguea
        self.logout()

    # Un usuario accede a los detalles de una actividad no baneada y es administrador
    def test_detalles_actividad_no_baneada_admin(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        usuario = self.login('usuario2', 'usuario2')
        actividad = Actividad.objects.filter(borrador=False).first()
        # Se comprueban que los datos mostrados son correctos
        self.detalles_actividad(actividad, usuario)
        # El usuario se desloguea
        self.logout()

    # Un usuario accede a los detalles de una actividad baneada y no es administrador
    def test_detalles_actividad_baneada_no_admin(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        usuario = self.login('usuario1', 'usuario1')
        actividad = Actividad.objects.filter(Q(borrador=False) & Q(vetada=True)).first()
        # Se comprueban que los datos mostrados son correctos
        self.detalles_actividad(actividad, usuario)
        # El usuario se desloguea
        self.logout()

    # Un usuario accede a los detalles de una actividad baneada y es administrador
    def test_detalles_actividad_baneada_admin(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        usuario = self.login('usuario1', 'usuario1')
        actividad = Actividad.objects.filter(Q(borrador=False) & Q(vetada=True)).first()
        # Se comprueban que los datos mostrados son correctos
        self.detalles_actividad(actividad, usuario)
        # El usuario se desloguea
        self.logout()

    # Para comprobar los botones de editar y eliminar

    # Un usuario accede a los detalles de una de sus actividades en modo borrador
    def test_detalles_actividad_propia_borrador(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        usuario = self.login('usuario1', 'usuario1')
        actividad = Actividad.objects.filter(Q(borrador=True) & Q(autor=usuario)).first()
        # Se comprueban que los datos mostrados son correctos
        self.detalles_actividad(actividad, usuario)
        # El usuario se desloguea
        self.logout()

    # Un usuario accede a los detalles de una de sus actividades en modo no borrador
    def test_detalles_actividad_propia_no_borrador(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        usuario = self.login('usuario1', 'usuario1')
        actividad = Actividad.objects.filter(Q(borrador=False) & Q(autor=usuario)).first()
        # Se comprueban que los datos mostrados son correctos
        self.detalles_actividad(actividad, usuario)
        # El usuario se desloguea
        self.logout()

    # Un usuario accede a los detalles de una actividad ajena en modo borrador
    def test_detalles_actividad_ajena_borrador(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        usuario = self.login('usuario3', 'usuario3')
        actividad = Actividad.objects.filter(borrador=True).exclude(autor=usuario).first()
        # Se accede a los detalles de la actividad
        self.selenium.get('{}{}'.format(self.live_server_url, '/actividad/detalles/{}'.format(actividad.id)))
        # Se comprueban que el usuario no ha podido acceder a los detalles de la actividad y se le ha redirigido al
        # listado de actividades
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/actividad/listado/')
        # Se comprueba que se muestra el mensaje de error correctamente
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se tienen los permisos necesarios para acceder a la actividad')
        # El usuario se desloguea
        self.logout()

    # Un usuario accede a los detalles de una actividad ajena en modo no borrador
    def test_detalles_actividad_ajena_no_borrador(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        usuario = self.login('usuario1', 'usuario1')
        actividad = Actividad.objects.filter(borrador=False).exclude(autor=usuario).first()
        # Se comprueban que los datos mostrados son correctos
        self.detalles_actividad(actividad, usuario)
        # El usuario se desloguea
        self.logout()

    # Otras casuísticas de detalles

    # Un usuario accede a una actividad inexistente
    def test_detalles_actividad_no_existe(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        self.login('usuario1', 'usuario1')
        # Se accede a la página de detalles de la actividad
        self.selenium.get('{}{}'.format(self.live_server_url, '/actividad/detalles/0'))
        # Se comprueba que se ha redirigido al usuario al listado de actividades
        self.assertEqual('{}/actividad/listado/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que se muestra el mensaje de error correctamente
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se ha encontrado la actividad')
        # El usuario se desloguea
        self.logout()

    def detalles_actividad(self, actividad, usuario):
        # Se accede a los detalles de la actividad
        self.selenium.get('{}{}'.format(self.live_server_url, '/actividad/detalles/{}'.format(actividad.id)))
        # Se comprueba que el encabezado es el correcto
        h1_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual(h1_text, 'Detalles de actividades')
        # Se comprueba que el identificador aparece corretamente
        identificador_text = self.selenium.find_element_by_tag_name('h3').text
        self.assertEqual(identificador_text, 'Identificador : {}'.format(actividad.identificador))
        # Si la actividad está vetada, se comprueba que se está indicando que está vetada
        if actividad.vetada:
            h_vetada = self.selenium.find_element_by_id('h4_vetada')
            self.assertEqual(h_vetada.text, 'VETADA')
            self.assertEqual(h_vetada.value_of_css_property('color'), 'rgb(255, 0, 0)')
        # Si al actividad está resuelta, se comprueba que se está indicando que está resuelta
        if actividad in usuario.actividades_realizadas.all():
            h_realizada = self.selenium.find_element_by_id('h4_realizada')
            self.assertEqual(h_realizada.text, 'REALIZADA')
            self.assertEqual(h_realizada.value_of_css_property('color'), 'rgb(0, 128, 0)')
        # Se comprueba que el resto de campos aparece correctemente
        actividad_fecha_creacion = self.i18_fecha(actividad.fecha_creacion.strftime('%-d de %B de %Y'))
        texts = [element.text for element in self.selenium.find_elements_by_tag_name('p')]
        self.assertEqual(texts[0], 'Titulo : {}'.format(actividad.titulo))
        self.assertEqual(texts[1], 'Descripcion : {}'.format(actividad.descripcion))
        self.assertEqual(texts[2], 'Fecha de creacion : {}'.format(actividad_fecha_creacion) )
        self.assertEqual(texts[3], 'Autor : {} {}'.format(actividad.autor.django_user.first_name, actividad.autor.django_user.last_name))
        # Se comprueba que existe un boton de detalles del autor y que su contenido es correcto
        boton_detalles_autor = None
        try:
            boton_detalles_autor = self.selenium.find_element_by_id('button_detalles_autor')
        except NoSuchElementException as e:
            pass
        self.assertIsNotNone(boton_detalles_autor)
        self.assertEquals(boton_detalles_autor.text, 'Detalles del autor')
        # Mira si hay un boton de editar
        existe_boton_editar = True
        try:
            self.selenium.find_element_by_id('button_editar')
        except NoSuchElementException as e:
            existe_boton_editar = False
        # Mira si hay un boton de eliminar
        existe_boton_eliminar = True
        try:
            self.selenium.find_element_by_id('button_eliminar')
        except NoSuchElementException as e:
            existe_boton_eliminar = False
        # Mira si hay un boton de vetar
        existe_boton_vetar = True
        try:
            self.selenium.find_element_by_id('button_vetar')
        except NoSuchElementException as e:
            existe_boton_vetar = False
        # Mira si hay un boton de levantar el veto
        existe_boton_levantar_veto = True
        try:
            self.selenium.find_element_by_id('button_levantar_veto')
        except NoSuchElementException as e:
            existe_boton_levantar_veto = False
        # Si el usuario es el autor de la actividad, entonces debe poder editarla o eliminarla si la actividad está en
        # modo borrador
        if actividad.borrador and not actividad.vetada and actividad.autor == usuario:
            self.assertTrue(existe_boton_editar)
            self.assertTrue(existe_boton_eliminar)
        # En cualquier otro caso, comprueba que no aparecen los botones
        else:
            self.assertFalse(existe_boton_eliminar)
            self.assertFalse(existe_boton_editar)
        # Si la actividad no está en modo borrador, ni vetada y el usuario es un administrador, entonces aparece el botón
        # de vetar
        if not actividad.borrador and not actividad.vetada and usuario.es_admin:
            self.assertTrue(existe_boton_vetar)
        # En cualquier otro caso no aparece el boton de vetar
        else:
            self.assertFalse(existe_boton_vetar)
        # Si la actividad no está en modo borrador, está vetada y el usuario es un administrador, entonces aparece el botón
        # de levantar el veto
        if not actividad.borrador and actividad.vetada and usuario.es_admin:
            self.assertTrue(existe_boton_levantar_veto)
        # En cualquier otro caso no aparece el boton de levantar el veto
        else:
            self.assertFalse(existe_boton_levantar_veto)
        # Se mira si está el enlace a la actividad
        existe_enlace = True
        try:
            enlace = self.selenium.find_element_by_xpath('//p/child::a["Enlace a la actividad"]').get_attribute('href')
        except NoSuchElementException as e:
            existe_enlace = False
        # Se mira si está el motivo de veto de la actividad
        existe_motivo_veto = True
        try:
            motivo_veto = self.selenium.find_element_by_xpath('//p[contains(., "Motivo de veto")]').text
        except NoSuchElementException as e:
            existe_motivo_veto = False
        # Si la actividad no está baneada, entonces se debe mostrar el enlace a la actividad, miestras que si está
        # baneada se tiene que mostrar el motivo de veto de la actividad
        if actividad.vetada:
            self.assertTrue(existe_motivo_veto)
            self.assertFalse(existe_enlace)
            self.assertEqual(motivo_veto, 'Motivo de veto : {}'.format(actividad.motivo_veto))
        else:
            self.assertTrue(existe_enlace)
            self.assertFalse(existe_motivo_veto)
            self.assertEqual(enlace, actividad.enlace)

    def i18_fecha(self, fecha):
        fecha = fecha.replace('January', 'Enero')
        fecha = fecha.replace('February', 'Febrero')
        fecha = fecha.replace('March', 'Marzo')
        fecha = fecha.replace('April', 'Abril')
        fecha = fecha.replace('May', 'Mayo')
        fecha = fecha.replace('June', 'Junio')
        fecha = fecha.replace('July', 'Julio')
        fecha = fecha.replace('August', 'Agosto')
        fecha = fecha.replace('September', 'Septiembre')
        fecha = fecha.replace('October', 'Octubre')
        fecha = fecha.replace('November', 'Noviembre')
        fecha = fecha.replace('December', 'Diciembre')
        return fecha

    

    # TESTS CREACIÓN

    # Un usuario crea una actividad
    def test_crear_actividad(self):
        # Se loguea el usuario
        self.login('usuario1', 'usuario1')
        # Se accede al formulario de creación de la actividad
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/creacion'))
        # Se comprueba que el título de la página sea el correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Creacion de actividades' in title_text, True)
        # Se rellenan los campos del formulario
        input_descripcion = self.selenium.find_element_by_id('id_descripcion')
        input_titulo = self.selenium.find_element_by_id('id_titulo')
        input_comentable = self.selenium.find_element_by_id('id_comentable')
        input_enlace = self.selenium.find_element_by_id('id_enlace')
        input_descripcion.send_keys('descripcion')
        input_titulo.send_keys('titulo')
        input_enlace.send_keys('https://enlace.com')
        input_comentable.click()
        # Se envía el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click() 
        # Se obtiene la nueva actividad
        nueva_actividad = Actividad.objects.order_by('-id').first()
        # Se comprueba que el usuario ha sido redirigido a los detalles de la nueva actividad
        self.assertEqual('{}/actividad/detalles/{}/'.format(self.live_server_url, nueva_actividad.id), self.selenium.current_url)
        # Se comprueba que se muestra el mensaje de éxito correctamente
        message_success = self.selenium.find_element_by_class_name('alert-success')
        self.assertEqual(message_success.text, 'Se ha creado la actividad con exito')
        # El usuario se desloguea
        self.logout()

    # Un usuario crea una actividad con errores de validación
    def test_crear_actividad_con_errores(self):
        # El usuario se loguea
        self.login('usuario1', 'usuario1')
        # Se accede a la creación de la actividad
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/creacion'))
        # Se comprueba el título de la página
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Creacion de actividades' in title_text, True)
        # Se rellenan los campos del formulario
        input_descripcion = self.selenium.find_element_by_id('id_descripcion')
        input_titulo = self.selenium.find_element_by_id('id_titulo')
        input_comentable = self.selenium.find_element_by_id('id_comentable')
        input_enlace = self.selenium.find_element_by_id('id_enlace')
        input_descripcion.send_keys('')
        input_titulo.send_keys('')
        input_enlace.send_keys('a')
        # Se envía el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click() 
        # Se comprueba que el usuario permanece en el formulario
        self.assertEqual('{}/actividad/creacion/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que los errores de validación se muestran correctamente
        error_titulo = self.selenium.find_element_by_xpath('//input[@id="id_titulo"]/following::div[@class="invalid-feedback"][1]')
        error_descripcion = self.selenium.find_element_by_xpath('//input[@id="id_descripcion"]/following::div[@class="invalid-feedback"][1]')
        error_enlace = self.selenium.find_element_by_xpath('//input[@id="id_enlace"]/following::div[@class="invalid-feedback"][1]')
        self.assertEqual(error_titulo.text, 'Este campo es requerido.')
        self.assertEqual(error_descripcion.text, 'Este campo es requerido.')
        self.assertEqual(error_enlace.text, 'Introduzca una URL válida.')
        # El usuario se desloguea
        self.logout()

    # Un usuario crea una actividad sin estar autenticado
    def test_crear_actividad_sin_autenticar(self):
        # Se accede a la creación de la actividad
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/creacion'))
        # Se verifica que se ha redirigido al usuario a la página de login, puesto a que no está autenticado
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/login/?next=/actividad/creacion/')



    # TESTS EDICIÓN

    # Un usuario edita una actividad
    def test_editar_actividad(self):
        # EL usuario se loguea
        self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        usuario = Usuario.objects.get(django_user__username = 'usuario1')
        actividad = Actividad.objects.filter(Q(autor = usuario) & Q(borrador = True) & Q(vetada = False)).first()
        # Se accede al listado de actvidades
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/listado/'))
        # Se accede a la edición de la actividad
        boton_editar = buscar_boton_listado(self,
            id_listado='id_div_listado_actividades',
            id_boton='button_editar_{}'.format(actividad.id),
            page_param='page')
        boton_editar.click()
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/actividad/edicion/{}/'.format(self.live_server_url, actividad.id))
        # Se comprueba que el título de la página es correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Edicion de actividades' in title_text, True)
        # Se rellenan los campos del formulario
        input_descripcion = self.selenium.find_element_by_id('id_descripcion')
        input_titulo = self.selenium.find_element_by_id('id_titulo')
        input_comentable = self.selenium.find_element_by_id('id_comentable')
        input_enlace = self.selenium.find_element_by_id('id_enlace')
        input_borrador = self.selenium.find_element_by_id('id_borrador')
        input_descripcion.clear()
        input_descripcion.send_keys('descripcioneditada')
        input_titulo.clear()
        input_titulo.send_keys('tituloeditado')
        input_enlace.clear()
        input_enlace.send_keys('https://enlaceeditado.com')
        input_comentable.click()
        # Se envía el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click()
        # Se comprueba que el usuario ha sido redirigido a los detalles de la actividad
        self.assertEqual('{}/actividad/detalles/{}/'.format(self.live_server_url, actividad.id), self.selenium.current_url)
        # Se comprueba que el mensaje de éxito se muestra correctamente
        message_success = self.selenium.find_element_by_class_name('alert-success')
        self.assertEqual(message_success.text, 'Se ha editado la actividad con exito')
        # El usuario se desloguea
        self.logout()

    # El usuario edita una actividad dejándola vacía
    def test_editar_actividad_vacia(self):
        # El usuario se loguea
        self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        usuario = Usuario.objects.get(django_user__username = 'usuario1')
        actividad = Actividad.objects.filter(Q(autor = usuario) & Q(borrador = True) & Q(vetada = False)).first()
        # Se accede al listado de actvidades
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/listado/'))
        # El usuario accede a la edición de la actividad
        boton_editar = buscar_boton_listado(self,
            id_listado='id_div_listado_actividades',
            id_boton='button_editar_{}'.format(actividad.id),
            page_param='page')
        boton_editar.click()
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/actividad/edicion/{}/'.format(self.live_server_url, actividad.id))
        # Se comprueba que el texto es correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Edicion de actividades' in title_text, True)
        # Se vacían los campos del formulario
        input_descripcion = self.selenium.find_element_by_id('id_descripcion')
        input_titulo = self.selenium.find_element_by_id('id_titulo')
        input_comentable = self.selenium.find_element_by_id('id_comentable')
        input_enlace = self.selenium.find_element_by_id('id_enlace')
        input_descripcion.clear()
        input_titulo.clear()
        input_enlace.clear()
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click()
        # Se comprueba que el usuario permanece en el formulario
        self.assertEqual('{}/actividad/edicion/{}/'.format(self.live_server_url, actividad.id), self.selenium.current_url)
        # Se comprueba que los errores de validación se muestran adecuadamente
        error_titulo = self.selenium.find_element_by_xpath('//input[@id="id_titulo"]/following::div[@class="invalid-feedback"][1]')
        error_descripcion = self.selenium.find_element_by_xpath('//input[@id="id_descripcion"]/following::div[@class="invalid-feedback"][1]')
        error_enlace = self.selenium.find_element_by_xpath('//input[@id="id_enlace"]/following::div[@class="invalid-feedback"][1]')
        self.assertEqual(error_titulo.text, 'Este campo es requerido.')
        self.assertEqual(error_descripcion.text, 'Este campo es requerido.')
        self.assertEqual(error_enlace.text, 'Este campo es requerido.')
        # El usuario se desloguea
        self.logout()
        
    # Un usuario edita una actividad si estar autenticado
    def test_editar_actividad_sin_autenticar(self):
        # Se obtienen las variables necesarias para el test
        actividad = Actividad.objects.filter(borrador=True).first()
        # Se accede a la edición de la actividad
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/edicion/{}/'.format(actividad.id)))
        # Se comprueba que el usuario es redirigido a la página de login
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/login/?next=/actividad/edicion/{}/'.format(actividad.id))

    # Un usuario edita una actividad ajena
    def test_editar_actividad_usuario_incorrecto(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se obtienen variables necesarias para el test
        actividad = Actividad.objects.exclude(autor=usuario).filter(borrador=True).first()
        # Se accede a la edición de la actividad
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/edicion/{}/'.format(actividad.id)))
        # Se comprueba que el usuario ha sido redirigido al listado de actviidades, puesto a que no puede redirigir a los
        # detalles de la actividad al estar la actividad en modo borrador y no pertenecer al usuario
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/actividad/listado/'.format(actividad.id))
        # Se comprueba que se muestra el mensaje de error correctamente
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se poseen los permisos necesarios para editar la actividad')
        # El usuario se desloguea
        self.logout()
    
    # Un usuario edita una actividad que no está en modo borrador
    def test_editar_actividad_no_borrador(self):
        # El usuario se loguea
        usuario = self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        actividad = Actividad.objects.filter(autor=usuario, borrador=False).first()
        # Se accede a la edición de la actividad
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/edicion/{}/'.format(actividad.id)))
        # Se comprueba que el usuario ha sido redirigido a los detalles de la actividad
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/actividad/detalles/{}/'.format(actividad.id))
        # Se comprueba que se muestra el mensaje de error correctamente
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede editar una actividad que no está en modo borrador')
        # El usuario se desloguea
        self.logout()

    # Un usuario edita una actividad que no existe
    def test_editar_actividad_inexistente(self):
        # El usuario se loguea
        usuario = self.login('usuario1', 'usuario1')
        # Se accede a la edición de la actividad
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/edicion/{}/'.format(0)))
        # Se comprueba que el usuario ha sido redirigido a los detalles de la actividad
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/actividad/listado/')
        # Se comprueba que se muestra el mensaje de error correctamente
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se ha encontrado la actividad')
        # El usuario se desloguea
        self.logout()



    # TESTS ELIMINACIÓN

    # Un usuario elimina una actividad
    def test_eliminar_actividad(self):
        # El usuario se loguea
        usuario = self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        actividad = Actividad.objects.filter(Q(autor = usuario) & Q(borrador = True)).first()
        numero_actividades_antes = Actividad.objects.count()
        # Se accede al listado de las actividades
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/listado/'))
        # Se pulsa el botón de eliminar actividad y se acepta
        boton_eliminar = buscar_boton_listado(self,
            id_listado='id_div_listado_actividades',
            id_boton='button_eliminar_{}'.format(actividad.id),
            page_param='page')
        boton_eliminar.click()
        self.selenium.switch_to.alert.accept()
        # Se comprueba que el usuario vuelve al listado de actividades
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/actividad/listado/')
        # Aparece el mensaje de eliminacion correctamente
        message_success = self.selenium.find_element_by_class_name('alert-success')
        self.assertEqual(message_success.text, 'Se ha eliminado la actividad con exito')
        # Se comrpueba que se ha eliminado la actividad de la base de datos
        numero_actividades_despues = Actividad.objects.count()
        self.assertEqual(numero_actividades_antes, numero_actividades_despues + 1)  
        actividad_eliminada = True
        try:
            Actividad.objects.get(pk = actividad.id)
            actividad_eliminada = False
        except ObjectDoesNotExist as e:
            pass
        self.assertEqual(actividad_eliminada, True)
        # El usuario se desloguea
        self.logout()     

    # Un usuario elimina una actividad, pero lo cancela en el último momento
    def test_eliminar_actividad_sin_aceptar(self):
        # El usuario se loguea
        usuario = self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        numero_actividades_antes = Actividad.objects.count()
        actividad = Actividad.objects.filter(Q(autor = usuario) & Q(borrador = True)).first()
        # Se accede al listado de actividades
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/listado/'))
        # Se obtienen las actividades listadas
        actividades_listado_antes = self.selenium.find_elements_by_xpath('//tbody/child::tr')
        # Se pulsa el botón de eliminar actividad pero rechaza la eliminación
        boton_eliminar = buscar_boton_listado(self,
            id_listado='id_div_listado_actividades',
            id_boton='button_eliminar_{}'.format(actividad.id),
            page_param='page')
        boton_eliminar.click()
        self.selenium.switch_to.alert.dismiss()
        # Se comprueba que el usuario permanece en el listado de actividades
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/actividad/listado/')
        # Se comprueba que no se ha eliminado ninguna actividad
        numero_actividades_despues = Actividad.objects.count()
        self.assertEqual(numero_actividades_antes, numero_actividades_despues)  
        actividad_eliminada = True
        try:
            Actividad.objects.get(pk = actividad.id)
            actividad_eliminada = False
        except ObjectDoesNotExist as e:
            pass
        self.assertEqual(actividad_eliminada, False)
        actividades_listado_despues = self.selenium.find_elements_by_xpath('//tbody/child::tr')
        self.assertEqual(len(actividades_listado_antes), len(actividades_listado_despues))
        # El usuario se desloguea
        self.logout()

    # Un usuario no autenticado elimina una actividad
    def test_eliminar_actividad_sin_autenticar(self):
        # Se obtienen variables necesarias para el test
        actividad = Actividad.objects.filter(borrador=True).first()
        # Se accede a la eliminación de la actividad
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/eliminacion/{}/'.format(actividad.id)))
        # Se redirige al usuario al login
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/login/?next=/actividad/eliminacion/{}/'.format(actividad.id))

    # Un usuario trata de eliminar una actividad que no le pertenece
    def test_eliminar_actividad_usuario_incorrecto(self):
        # Un usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se obtienen variables necesarias para el test
        actividad = Actividad.objects.filter(borrador=True).exclude(autor=usuario).first()
        # Se accede a la eliminación de la actividad
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/eliminacion/{}/'.format(actividad.id)))
        # Se comprueba que se está en la página de listado de actividades, puesto a que no puede acceder a los detalles
        # de una actividad en modo borrador que no le pertenece
        self.assertEqual('{}/actividad/listado/'.format(self.live_server_url, actividad.id), self.selenium.current_url)
        # Se comprueba que el mensaje de error se muestra correctamente
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se poseen los permisos necesarios para eliminar la actividad')
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de eliminar una actividad que no está en modo borrador
    def test_eliminar_actividad_no_borrador(self):
        # Se loguea el usuario
        usuario = self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        actividad = Actividad.objects.filter(borrador=False, autor=usuario).first()
        # Se accede a la eliminación de la actividad
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/eliminacion/{}/'.format(actividad.id)))
        # Se comprueba que se ha redirigido al usuario a la página de detalles de la actividad correctamente
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/actividad/detalles/{}/'.format(actividad.id))
        # Se comprueba que se muestra el mensaje de error correctamente
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede eliminar una actividad que no está en modo borrador')
        # El usuario se desloguea
        self.logout()

    # Un usuario elimina una actividad que no existe
    def test_eliminar_actividad_inexistente(self):
        # El usuario se loguea
        usuario = self.login('usuario1', 'usuario1')
        # Se accede a la eliminación de la actividad
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/eliminacion/{}/'.format(0)))
        # Se comprueba que el usuario ha sido redirigido a los detalles de la actividad
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/actividad/listado/')
        # Se comprueba que se muestra el mensaje de error correctamente
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se ha encontrado la actividad')
        # El usuario se desloguea
        self.logout()



    # TESTS VETO

    # Un admnistrador trata de vetar una actividad
    def test_veta_actividad(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se obtienen las variables que se van a usar en el test
        actividad = Actividad.objects.filter(Q(vetada = False) & Q(borrador = False)).first()
        motivo_veto = 'Veto selenium test'
        # Se accede al listado de actvidades
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/listado/'))
        # Se acccede al formulario de vetar la actividad
        boton_veto = buscar_boton_listado(self,
            id_listado='id_div_listado_actividades',
            id_boton='button_vetar_{}'.format(actividad.id),
            page_param='page')
        boton_veto.click()
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/actividad/veto/{}/'.format(self.live_server_url, actividad.id))
        # Se comprueba que el título de la página es el correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual(title_text, 'Veto a actividades')
        # Se comprueba que aparecen los campos necesarios
        input_motivo_veto = self.selenium.find_element_by_id('id_motivo_veto')
        input_motivo_veto.clear()
        input_motivo_veto.send_keys(motivo_veto)
        # Se busca el botón de envío, lo pulsa y acepta el veto
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click()
        self.selenium.switch_to.alert.accept() 
        # Se comprueba que se está en la página de detalles de la actividad
        # Pero antes hay que esperar a que redirija
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(lambda driv : driv.current_url == '{}/actividad/detalles/{}/'.format(self.live_server_url, actividad.id))
        self.assertEqual('{}/actividad/detalles/{}/'.format(self.live_server_url, actividad.id), self.selenium.current_url)
        # Se busca el mensaje de éxito y se comprueba que es correcto
        message_success = self.selenium.find_element_by_class_name('alert-success')
        self.assertEqual(message_success.text, 'Se ha vetado la actividad con exito')
        # Se busca el motivo de veto en la vista de detalles a la que se ha redirigido
        output_motivo_veto = self.selenium.find_element_by_xpath('//p[text()="Motivo de veto : {}"]'.format(motivo_veto))
        self.assertEqual(output_motivo_veto != None, True)
        # La actividad ha sido vetada
        actividad_recibida = Actividad.objects.get(pk=actividad.id)
        self.assertEqual(actividad_recibida.motivo_veto, motivo_veto)
        self.assertEqual(actividad_recibida.vetada, True)
        # El usuario se desloguea
        self.logout()

    # Un admnistrador trata de vetar una actividad pero no acepta el veto
    def test_veta_actividad_sin_aceptar(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se obtienen las variables que se van a usar en el test
        actividad = Actividad.objects.filter(Q(vetada = False) & Q(borrador = False)).first()
        motivo_veto = 'Veto selenium test'
        # Se accede al listado de actvidades
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/listado/'))
        # Se acccede al formulario de vetar la actividad
        boton_veto = buscar_boton_listado(self,
            id_listado='id_div_listado_actividades',
            id_boton='button_vetar_{}'.format(actividad.id),
            page_param='page')
        boton_veto.click()
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/actividad/veto/{}/'.format(self.live_server_url, actividad.id))
        # Se comprueba que el título de la página es el correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual(title_text, 'Veto a actividades')
        # Se comprueba que aparecen los campos necesarios
        input_motivo_veto = self.selenium.find_element_by_id('id_motivo_veto')
        input_motivo_veto.clear()
        input_motivo_veto.send_keys(motivo_veto)
        # Se busca el botón de envío, se pulsa y se cancela el veto
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click() 
        self.selenium.switch_to.alert.dismiss()
        # Se comprueba que se está en el formulario de veto
        self.assertEqual('{}/actividad/veto/{}/'.format(self.live_server_url, actividad.id), self.selenium.current_url)
        # Se comprueba que no ha cambiado la actividad
        actividad_recibida = Actividad.objects.get(pk=actividad.id)
        self.assertEqual(actividad, actividad_recibida)
        self.assertEqual(actividad_recibida.vetada, False)
        self.assertEqual(actividad_recibida.motivo_veto, None)
        # El usuario se desloguea
        self.logout()

    # Un administrador veta la actividad sin estar autenticado
    def test_veta_actividad_sin_loguear(self):
        # Se obtienen las variables que se van a usar en el test
        actividad = Actividad.objects.filter(Q(vetada = False) & Q(borrador = False)).first()
        motivo_veto = 'Veto selenium test'
        # Se acccede al formulario de vetar la actividad
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/veto/{}/'.format(actividad.id)))
        # Se comprueba que se está en la página de login
        self.assertEqual('{}/login/?next=/actividad/veto/{}/'.format(self.live_server_url, actividad.id), self.selenium.current_url)

    # Un administrador que no es administrador trata de vetar la actividad
    def test_veta_actividad_usuario_incorrecto(self):
        # El usuario se loguea
        usuario = self.login('usuario1', 'usuario1')
        # Se obtienen las vriaables que se van a usar en el test
        actividad = Actividad.objects.filter(Q(vetada = False) & Q(borrador = False)).first()
        motivo_veto = 'Veto selenium test'
        # Se acccede al formulario de vetar la actividad
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/veto/{}/'.format(actividad.id)))
        # Se comprueba que se ha redirigido a la página de detalles de la oferta
        self.assertEqual('{}/actividad/detalles/{}/'.format(self.live_server_url, actividad.id),
                         self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se poseen los permisos necesarios para vetar la actividad')
        # El usuario se desloguea
        self.logout()
    
    # Un admninistrador trata de vetar una actividad ya vetada
    def test_veta_actividad_vetada(self):
        # El usuario se loguea y se obtienen las vriaables que se van a usar en el test
        self.login('usuario2', 'usuario2')
        usuario = Usuario.objects.get(django_user__username = 'usuario2')
        actividad = Actividad.objects.filter(Q(vetada = True) & Q(borrador = False)).first()
        # Se acccede al formulario de vetar la actividad
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/veto/{}/'.format(actividad.id)))
        # Se comprueba que se ha redirigido a la página de detalles de la actividad
        self.assertEqual('{}/actividad/detalles/{}/'.format(self.live_server_url, actividad.id), self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede vetar una actividad ya vetada')
        # El usuario se desloguea
        self.logout()

    # Un administrador trata de vetar una actividad que no existe
    def test_veta_actividad_inexistente(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se obtienen las vriaables que se van a usar en el test        
        motivo_veto = 'Veto selenium test'
        # Se acccede al formulario de vetar la actividad
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/veto/{}/'.format(0)))
        # Se comprueba que se está en la página de listado de actividades
        self.assertEqual('{}/actividad/listado/'.format(self.live_server_url), self.selenium.current_url)
        # Se busca el mensaje de éxito y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se ha encontrado la actividad')
        # El usuario se desloguea
        self.logout()

    # Un administrador trata de vetar una actividad usando un motivo de veto inválido
    def test_veta_actividad_incorrecta(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se obtienen las variables que se van a usar en el test
        actividad = Actividad.objects.filter(Q(vetada = False) & Q(borrador = False)).first()
        motivo_veto = ''
        # Se acccede al formulario de vetar la actividad
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/veto/{}/'.format(actividad.id)))
        # Se comprueba que el título de la página es el correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual(title_text, 'Veto a actividades')
        # Se comprueba que aparecen los campos necesarios
        input_motivo_veto = self.selenium.find_element_by_id('id_motivo_veto')
        input_motivo_veto.clear()
        input_motivo_veto.send_keys(motivo_veto)
        # Se busca el botón de envío y se pulsa
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click() 
        self.selenium.switch_to.alert.accept()
        # Se busca el mensaje de error de validación y se comprueba que es correcto
        motivo_error_veto = self.selenium.find_element_by_xpath('//form/child::input[@id="id_motivo_veto"]/following-sibling::div[@class="invalid-feedback"][1]')
        self.assertEqual(motivo_error_veto.text, 'Este campo es requerido.')
        # Se comprueba que se está en la página de veto de la actividad
        self.assertEqual('{}/actividad/veto/{}/'.format(self.live_server_url, actividad.id), self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'Se ha producido un error al vetar la actividad')
        # El usuario se desloguea
        self.logout()

    # Un administrador trata de vetar una actividad que está en modo borrador
    def test_veta_actividad_borrador(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se obtienen las variables que se van a usar en el test
        actividad = Actividad.objects.filter(Q(vetada = False) & Q(borrador = True)).first()
        # Se acccede al formulario de vetar la actividad
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/veto/{}/'.format(actividad.id)))
        # Se comprueba que se está en la página de listado de actividades, puesto a que no puede acceder a los detalles
        # de una actividad en modo borrador que no le pertenece
        self.assertEqual('{}/actividad/listado/'.format(self.live_server_url, actividad.id), self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede vetar una actividad que está en modo borrador')
        # El usuario se desloguea
        self.logout()



    # TESTS LEVANTAMIENTO VETO

    # Un administrador levanta el veto sobre una actividad
    def test_levanta_veto_actividad(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario2', 'usuario2')
        actividad = Actividad.objects.filter(Q(vetada = True) & Q(borrador = False)).first()
        # Se acccede a la url de listado de actividades
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/listado/'))
        # Se selecciona una actividad para levantar el veto y se acepta
        boton_veto = buscar_boton_listado(self,
            id_listado = 'id_div_listado_actividades',
            id_boton = 'button_levantar_veto_{}'.format(actividad.id),
            page_param = 'page')
        boton_veto.click()
        self.selenium.switch_to.alert.accept()
        # Se comprueba que se está en la página de detalles de la actividad
        # Pero antes se tiene que esperar a que redirija a la página
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(lambda driv : driv.current_url == '{}/actividad/detalles/{}/'.format(self.live_server_url, actividad.id))
        self.assertEqual('{}/actividad/detalles/{}/'.format(self.live_server_url, actividad.id), self.selenium.current_url)
        # Se busca el mensaje de éxito y se comprueba que es correcto
        message_success = self.selenium.find_element_by_class_name('alert-success')
        self.assertEqual(message_success.text, 'Se ha levantado el veto sobre la actividad con éxito')
        # Se comprueba que se ha levantado el veto
        actividad_recibida = Actividad.objects.get(pk=actividad.id)
        self.assertEqual(actividad_recibida.motivo_veto, None)
        self.assertEqual(actividad_recibida.vetada, False)
        # El usuario se desloguea
        self.logout()

    # Un administrador levanta el veto sobre una actividad pero cancela el levantamiento del veto
    def test_levanta_veto_actividad_sin_aceptar(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario2', 'usuario2')
        actividad = Actividad.objects.filter(Q(vetada = True) & Q(borrador = False)).first()
        # Se acccede a la url de listado de actividades
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/listado/'))
        # Se selecciona una actividad para levantar el veto y se acepta
        boton_veto = buscar_boton_listado(self,
            id_listado='id_div_listado_actividades',
            id_boton='button_levantar_veto_{}'.format(actividad.id),
            page_param='page')
        boton_veto.click()
        self.selenium.switch_to.alert.dismiss()
        # Se comprueba que se está en la página de listado de las actividades
        self.assertTrue(self.selenium.current_url.startswith('{}/actividad/listado/'.format(self.live_server_url)))
        # Se comprueba que la actividad no ha sufrido cambios
        actividad_recibida = Actividad.objects.get(pk=actividad.id)
        self.assertEqual(actividad_recibida.motivo_veto, actividad.motivo_veto)
        self.assertEqual(actividad_recibida.vetada, True)
        # El usuario se desloguea
        self.logout()

    # Un usuario levanta el veto sin estar autenticado
    def test_levanta_veto_actividad_sin_loguear(self):
        # Se obtienen las variables que se van a usar en el test
        actividad = Actividad.objects.filter(Q(vetada = True) & Q(borrador = False)).first()
        # Se acccede a la url de levantamiento de veto
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/levantamiento_veto/{}/'.format(actividad.id)))
        # Se comprueba que se he redirigido al usuario al login
        self.assertEqual('{}/login/?next=/actividad/levantamiento_veto/{}/'.format(self.live_server_url, actividad.id), self.selenium.current_url)

    # Un usuario que no tiene permisos de administrador levanta el veto sobre una actividad
    def test_levanta_veto_actividad_usuario_incorrecto(self):
        # El usuario se loguea y 
        usuario = self.login('usuario1', 'usuario1')
        # Se obtienen las variables que se van a usar en el test
        actividad = Actividad.objects.filter(Q(vetada = True) & Q(borrador = False)).first()
        # Se acccede a la url de levantamiento de veto
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/levantamiento_veto/{}/'.format(actividad.id)))
        # Se comprueba que se ha redirigido a la página de detalles de la oferta
        self.assertEqual('{}/actividad/detalles/{}/'.format(self.live_server_url, actividad.id),
            self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se poseen los permisos necesarios para levantar el veto sobre la actividad')
        # El usuario se desloguea
        self.logout()

    # Un administrador levanta el veto sobre una actividad no vetada
    def test_levanta_veto_actividad_no_vetada(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se obtienen las variables que se van a usar en el test
        actividad = Actividad.objects.filter(Q(vetada = False) & Q(borrador = False)).first()
        # Se acccede a la url de levantamiento de veto
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/levantamiento_veto/{}/'.format(actividad.id)))
        # Se comprueba que se está en la página de detalles de la actividad
        self.assertEqual('{}/actividad/detalles/{}/'.format(self.live_server_url, actividad.id), self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede levantar el veto a una actividad sin vetar')
        # El usuario se desloguea
        self.logout()
 
    # Un administrador levanta el veto sobre una actividad inexistente
    def test_levanta_veto_actividad_inexistente(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se acccede a la url de levantamiento de veto
        self.selenium.get('%s%s' % (self.live_server_url, '/actividad/levantamiento_veto/0/'))
        # Se comprueba que se está en la página de listado de actividades
        self.assertEqual('{}/actividad/listado/'.format(self.live_server_url), self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se ha encontrado la actividad')
        # El usuario se desloguea
        self.logout()







