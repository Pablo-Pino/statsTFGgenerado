from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.db.models import Q, Exists, OuterRef
from django.core.exceptions import ObjectDoesNotExist
from selenium.webdriver import FirefoxProfile, ActionChains

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

from websecurityapp.models.actividad_models import Actividad
from websecurityapp.models.oferta_models import Oferta, Solicitud
from websecurityapp.models.perfil_models import Usuario
from websecurityapp.models.oferta_models import Oferta
from websecurityapp.test_selenium.utils import evaluar_columnas_listado_oferta, evaluar_columnas_listado_actividades, \
    evaluar_columnas_listado_usuario, buscar_boton_listado
from websecurityapp.views.utils import get_ofertas_solicitables_y_ofertas_retirables, es_oferta_solicitable_o_retirable

import datetime



class OfertaTestCase(StaticLiveServerTestCase):
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
    
    # Un usuario que no es administrador accede al listado de ofertas
    def test_listado_ofertas_no_admin(self):
        # Se accede al listado de oferta como el usuario1
        self.login('usuario1', 'usuario1')
        # Se accede al listado de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado'))
        # Se comprueba que aparecen las ofertas correctas
        usuario = Usuario.objects.get(django_user__username = 'usuario1')
        ofertas_esperadas = Oferta.objects.annotate(actividades_vetadas=Exists(
            Oferta.objects.filter(id=OuterRef('id'), actividades__vetada=True))
        ).exclude((Q(cerrada=True) | Q(borrador=True) | Q(vetada=True) | Q(actividades_vetadas=True)) & ~Q(autor=usuario)
        ).order_by('id')
        ofertas_mostradas = self.selenium.find_elements_by_tag_name('tr')
        # self.assertEqual(len(ofertas_esperadas), len(ofertas_mostradas) - 1)
        # Se comprueba que el contenido de la tabla es correcto
        evaluar_columnas_listado_oferta(self, ofertas_esperadas, usuario, False, 'page')
        # Se cierra sesion
        self.logout()

    # Un usuario que es administrador accede al listado de ofertas
    def test_listado_ofertas_admin(self):
         # Se accede al listado de oferta como el usuario2
        self.login('usuario2', 'usuario2')
        # Se accede al listado de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado'))
        # Se comprueba que aparecen las oferta correctas
        usuario = Usuario.objects.get(django_user__username = 'usuario2')
        ofertas_esperadas = Oferta.objects.filter(Q(autor=usuario) | Q(borrador=False, cerrada=False)).distinct().order_by('id')
        ofertas_mostradas = self.selenium.find_elements_by_tag_name('tr')
        # self.assertEqual(len(ofertas_esperadas), len(ofertas_mostradas) - 1)
        # Se comprueba que el contenido de la tabla es correcto
        evaluar_columnas_listado_oferta(self, ofertas_esperadas, usuario, False, 'page')
        # Se cierra sesion
        self.logout()

    # Un usuario que accede al listado de ofertas propias
    def test_listado_ofertas_propias(self):
         # Se accede al listado de oferta como el usuario1
         self.login('usuario1', 'usuario1')
         # Se accede al listado de ofertas propias
         self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado_propio'))
         # Se comprueba que aparecen las ofertas correctas
         usuario = Usuario.objects.get(django_user__username='usuario1')
         ofertas_esperadas = Oferta.objects.filter(autor=usuario).distinct().order_by('id')
         ofertas_mostradas = self.selenium.find_elements_by_tag_name('tr')
         # self.assertEqual(len(ofertas_esperadas), len(ofertas_mostradas) - 1)
         # Se comprueba que el contenido de la tabla es correcto
         evaluar_columnas_listado_oferta(self, ofertas_esperadas, usuario, True, 'page')
         # Se cierra sesion
         self.logout()

    # Un usuario que accede al listado de ofertas que ha solicitado
    def test_listado_solicitudes_propias(self):
        # Se accede al listado de oferta como el usuario1
        self.login('usuario1', 'usuario1')
        # Se accede al listado de ofertas solicitadas propias
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado_solicitud_propio'))
        # Se comprueba que aparecen las ofertas correctas
        usuario = Usuario.objects.get(django_user__username='usuario1')
        ofertas_esperadas = []
        for solicitud in list(Solicitud.objects.filter(usuario=usuario).order_by('id')):
            ofertas_esperadas.append(solicitud.oferta)
        ofertas_mostradas = self.selenium.find_elements_by_tag_name('tr')
        # self.assertEqual(len(ofertas_esperadas), len(ofertas_mostradas) - 1)
        # Se comprueba que el contenido de la tabla es correcto
        evaluar_columnas_listado_oferta(self, ofertas_esperadas, usuario, True, 'page')
        # Se cierra sesion
        self.logout()



    # TEST DE DETALLES

    # Un usuario accede a los detalles de una oferta no baneada y no es administrador
    def test_detalles_oferta_no_baneada_no_admin(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        usuario = self.login('usuario1', 'usuario1')
        oferta = Oferta.objects.filter(borrador=False, cerrada=False, vetada=False).first()
        # Se comprueban que los datos mostrados son correctos
        self.detalles_oferta(oferta, usuario)
        # El usuario se desloguea
        self.logout()

    # Un usuario accede a los detalles de una oferta no baneada y es administrador
    def test_detalles_oferta_no_baneada_admin(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        usuario = self.login('usuario2', 'usuario2')
        oferta = Oferta.objects.filter(borrador=False, cerrada=False, vetada=False).first()
        # Se comprueban que los datos mostrados son correctos
        self.detalles_oferta(oferta, usuario)
        # El usuario se desloguea
        self.logout()
    
    # Un usuario accede a los detalles de una oferta baneada y no es administrador
    def test_detalles_oferta_baneada_no_admin(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        usuario = self.login('usuario1', 'usuario1')
        oferta = Oferta.objects.filter(borrador=False, vetada=True, cerrada=False).first()
        # Se comprueban que los datos mostrados son correctos
        self.detalles_oferta(oferta, usuario)
        # El usuario se desloguea
        self.logout()

    # Un usuario accede a los detalles de una oferta baneada y es administrador
    def test_detalles_oferta_baneada_admin(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        usuario = self.login('usuario1', 'usuario1')
        oferta = Oferta.objects.filter(borrador=False, vetada=True, cerrada=False).first()
        # Se comprueban que los datos mostrados son correctos
        self.detalles_oferta(oferta, usuario)
        # El usuario se desloguea
        self.logout()

    # Un usuario accede a los detalles de una oferta cerrada
    def test_detalles_oferta_cerrada(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        usuario = self.login('usuario1', 'usuario1')
        oferta = Oferta.objects.filter(borrador=False, vetada=False, cerrada=True).first()
        # Se comprueban que los datos mostrados son correctos
        self.detalles_oferta(oferta, usuario)
        # El usuario se desloguea
        self.logout()

    # Un usuario accede a los detalles de una de sus ofertas en modo borrador
    def test_detalles_oferta_propia_borrador(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        usuario = self.login('usuario1', 'usuario1')
        oferta = Oferta.objects.filter(borrador=True, autor=usuario).first()
        # Se comprueban que los datos mostrados son correctos
        self.detalles_oferta(oferta, usuario)
        # El usuario se desloguea
        self.logout()

    # Un usuario accede a los detalles de una de sus ofertas en modo no borrador
    def test_detalles_oferta_propia_no_borrador(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        usuario = self.login('usuario1', 'usuario1')
        oferta = Oferta.objects.filter(borrador=False, autor=usuario, cerrada=False, vetada=False).first()
        # Se comprueban que los datos mostrados son correctos
        self.detalles_oferta(oferta, usuario)
        # El usuario se desloguea
        self.logout()

    # Un usuario accede a los detalles de una oferta ajena en modo borrador
    def test_detalles_oferta_ajena_borrador(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        usuario = self.login('usuario1', 'usuario1')
        oferta = Oferta.objects.filter(borrador=True, cerrada=False, vetada=False).exclude(autor=usuario).first()
        # Se accede a los detalles de la oferta
        self.selenium.get('{}{}'.format(self.live_server_url, '/oferta/detalles/{}'.format(oferta.id)))
        # Se comprueba que el usuario ha sido redirigido al listado de ofertas con un mensaje de error
        self.assertEqual('{}/oferta/listado/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que el mensaje de error se muestra correctamente
        message_error = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_error.text, 'No se tienen los permisos necesarios para acceder a la oferta')
        # El usuario se desloguea
        self.logout()
    
    # Un usuario accede a los detalles de una oferta ajena en modo no borrador
    def test_detalles_oferta_ajena_no_borrador(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        usuario = self.login('usuario1', 'usuario1')
        oferta = Oferta.objects.filter(borrador=False, cerrada=False, vetada=False).exclude(autor=usuario).first()
        # Se comprueban que los datos mostrados son correctos
        self.detalles_oferta(oferta, usuario)
        # El usuario se desloguea
        self.logout()

    # Otras casuísticas de detalles

    # Un usuario accede a una oferta inexistente
    def test_detalles_oferta_no_existe(self):
        # El usuario se loguea y se inicializan las variables más relevantes
        self.login('usuario1', 'usuario1')
        # Se accede a la página de detalles de la oferta
        self.selenium.get('{}{}'.format(self.live_server_url, '/oferta/detalles/0'))
        # Se comprueba que se ha redirigido al usuario al listado de ofertas
        self.assertEqual('{}/oferta/listado/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que se muestra el mensaje de error correctamente
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se ha encontrado la oferta')
        # El usuario se desloguea
        self.logout()

    def detalles_oferta(self, oferta, usuario):
        # Se inicializan variables necesarias
        ofertas = []
        if usuario.es_admin:
            ofertas = list(Oferta.objects.exclude((Q(cerrada=True) | Q(borrador=True)) & ~Q(autor=usuario)))
        else:
            ofertas = list(
                Oferta.objects.exclude((Q(cerrada=True) | Q(borrador=True) | Q(vetada=True)) & ~Q(autor=usuario)))
        [es_solicitable, es_retirable] = es_oferta_solicitable_o_retirable(usuario, oferta)
        # Se accede a los detalles de la oferta
        self.selenium.get('{}{}'.format(self.live_server_url, '/oferta/detalles/{}'.format(oferta.id)))
        # Se comprueba que el encabezado es el correcto
        h1_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual(h1_text, 'Detalles de ofertas')
        # Se comprueba que el identificador aparece corretamente
        identificador_text = self.selenium.find_element_by_tag_name('h3').text
        self.assertEqual(identificador_text, 'Identificador : {}'.format(oferta.identificador))
        # Se comprueba que si está vetada, se indica con un texto en rojo
        existe_aviso_veto = True
        try:
            aviso_vetada = self.selenium.find_element_by_tag_name('h4')
            self.assertEqual(aviso_vetada.text, 'VETADA')
            self.assertEqual(str(aviso_vetada.value_of_css_property('color')), 'rgb(255, 0, 0)')
        except Exception as e:
            existe_aviso_veto = False
        self.assertEqual(oferta.vetada, existe_aviso_veto)
        # Se comprueba que si está cerrada, se indica con un texto en rojo
        existe_aviso_cierre = True
        try:
            aviso_cierre = self.selenium.find_element_by_tag_name('h4')
            self.assertEqual(aviso_cierre.text, 'CERRADA')
            self.assertEqual(aviso_cierre.value_of_css_property('color'), 'rgb(255, 0, 0)')
        except Exception as e:
            existe_aviso_cierre = False
        self.assertEqual(oferta.cerrada, existe_aviso_cierre)
        # Se comprueba que el resto de campos aparece correctemente
        oferta_fecha_creacion = self.i18_fecha(oferta.fecha_creacion.strftime('%-d de %B de %Y'))
        texts = [element.text for element in self.selenium.find_elements_by_tag_name('p')]
        self.assertEqual(texts[0], 'Titulo : {}'.format(oferta.titulo))
        self.assertEqual(texts[1], 'Descripcion : {}'.format(oferta.descripcion))
        self.assertEqual(texts[2], 'Fecha de creacion : {}'.format(oferta_fecha_creacion))
        self.assertEqual(texts[3], 'Autor : {} {}'.format(oferta.autor.django_user.first_name, oferta.autor.django_user.last_name))
        # Comprueba que hay un boton de detalles del autor y que es correcto
        boton_detalles_autor = None
        try:
            boton_detalles_autor = self.selenium.find_element_by_id('button_detalles_autor')
        except NoSuchElementException as e:
            pass
        self.assertIsNotNone(boton_detalles_autor)
        self.assertEquals(boton_detalles_autor.text, 'Detalles del autor')
        # Comprueba el fieldset de actividades
        fieldset_actividades = self.selenium.find_element_by_id('fieldset_actividades')
        # Comprueba el legend del fieldset
        legend_actividades = fieldset_actividades.find_element_by_tag_name('legend')
        self.assertEqual(legend_actividades.text, 'Actividades')
        # Comprueba el listado de actividades
        evaluar_columnas_listado_actividades(test_case = self,
            actividades_esperadas = oferta.actividades.all(),
            usuario = usuario,
            resalta_resueltas = False,
            page_param = 'page_actividades',
            parent_element = 'fieldset_actividades')
        # Si el usuario es el autor de la oferta, debe apareecer otro fieldset con los solicitantes
        # Busca el fieldset
        try:
            fieldset_solicitantes = self.selenium.find_element_by_id('fieldset_solicitantes')
        except NoSuchElementException as e:
            fieldset_solicitantes = None
        if usuario == oferta.autor and not oferta.borrador:
            solicitantes_esperados = []
            for solicitud in Solicitud.objects.filter(oferta = oferta):
                solicitantes_esperados.append(solicitud.usuario)
            self.assertIsNotNone(fieldset_solicitantes)
            # Comprueba el legend del fieldset
            legend_solicitantes = fieldset_solicitantes.find_element_by_tag_name('legend')
            self.assertEqual(legend_solicitantes.text, 'Solicitantes')
            # Comprueba el listado de solicitantes
            evaluar_columnas_listado_usuario(test_case=self,
                usuarios_esperados = solicitantes_esperados,
                usuario = usuario,
                resalta_resueltas = False,
                page_param = 'page_solicitantes',
                parent_element = 'fieldset_solicitantes')
        else:
            self.assertIsNone(fieldset_solicitantes)
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
        # Mira si hay un boton de cerrar
        existe_boton_cerrar = True
        try:
            self.selenium.find_element_by_id('button_cerrar')
        except NoSuchElementException as e:
            existe_boton_cerrar = False
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
        # Mira si hay un boton de solicitar la oferta
        existe_boton_solicitar = True
        try:
            self.selenium.find_element_by_id('button_solicitar')
        except NoSuchElementException as e:
            existe_boton_solicitar = False
        # Mira si hay un boton de retirar la solicitud de la oferta
        existe_boton_retirar_solicitud = True
        try:
            self.selenium.find_element_by_id('button_retirar_solicitud')
        except NoSuchElementException as e:
            existe_boton_retirar_solicitud = False
        # Si el usuario es el autor de la oferta, entonces debe poder editarla o eliminarla si la oferta está en
        # modo borrador
        if oferta.autor == usuario and oferta.borrador and not oferta.vetada and not oferta.cerrada:
            self.assertTrue(existe_boton_editar)
            self.assertTrue(existe_boton_eliminar)
        # En cualquier otro caso, comprueba que no aparecen los botones
        else:
            self.assertFalse(existe_boton_eliminar)
            self.assertFalse(existe_boton_editar)
        # Si el usuario es el autor de la oferta, entonces debe poder cerrarla si la oferta no está en
        # modo borrador y no está ni vetada, ni cerrada
        if oferta.autor == usuario and not oferta.borrador and not oferta.vetada and not oferta.cerrada:
            self.assertTrue(existe_boton_cerrar)
        # En cualquier otro caso, comprueba que no aparecen los botones
        else:
            self.assertFalse(existe_boton_cerrar)
        # Si la oferta no está en modo borrador, ni vetada y el usuario es un administrador, entonces aparece el botón
        # de vetar
        if not oferta.borrador and not oferta.vetada and not oferta.cerrada and usuario.es_admin:
            self.assertTrue(existe_boton_vetar)
        # En cualquier otro caso no aparece el boton de vetar
        else:
            self.assertFalse(existe_boton_vetar)
        # Si la oferta no está en modo borrador, está vetada y el usuario es un administrador, entonces aparece el botón
        # de levantar el veto
        if not oferta.borrador and oferta.vetada and usuario.es_admin:
            self.assertTrue(existe_boton_levantar_veto)
        # En cualquier otro caso no aparece el boton de levantar el veto
        else:
            self.assertFalse(existe_boton_levantar_veto)
        # Si la oferta se puede solicitar, se muestra el botón de solicitar oferta
        if es_solicitable:
            self.assertTrue(existe_boton_solicitar)
        else:
            self.assertFalse(existe_boton_solicitar)
        # Si se puede retirar la solicitud de la oferta, se muestra el botón de retirar la solcitud
        if es_retirable:
            self.assertTrue(existe_boton_retirar_solicitud)
        else:
            self.assertFalse(existe_boton_retirar_solicitud)
        # Se mira si está el motivo de veto de la oferta
        existe_motivo_veto = True
        try:
            motivo_veto = self.selenium.find_elements_by_tag_name('p')[4].text
            self.assertEqual(motivo_veto, 'Motivo de veto : {}'.format(oferta.motivo_veto))
        except Exception as e:
            existe_motivo_veto = False
        # Si la oferta está baneada se tiene que mostrar el motivo de veto de la oferta
        self.assertEqual(oferta.vetada, existe_motivo_veto)

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

    # Un usuario crea una oferta
    def test_crear_oferta(self):
        # Se loguea el usuario
        self.login('usuario1', 'usuario1')
        # Se accede al formulario de creación de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/creacion'))
        # Se comprueba que el título de la página sea el correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Creacion de ofertas' in title_text, True)
        # Se rellenan los campos del formulario
        input_descripcion = self.selenium.find_element_by_id('id_descripcion')
        input_titulo = self.selenium.find_element_by_id('id_titulo')
        input_actividades = self.selenium.find_element_by_id('id_actividades')
        options_actividades = input_actividades.find_elements_by_tag_name('option')
        # Se comprueba que ninguna de las actividades que aparecen en el select está vetada o en modo borrador
        for option in options_actividades:
            id_actividad = option.get_attribute('value')
            actividad = Actividad.objects.get(pk=id_actividad)
            self.assertFalse(actividad.borrador or actividad.vetada)
        # Se insertan los inputs
        input_descripcion.send_keys('descripcion')
        input_titulo.send_keys('titulo')
        # Se seleccionan varias actividades del select para añadirlas a la oferta
        for option in options_actividades[:2]:
            ActionChains(self.selenium).key_down(Keys.LEFT_CONTROL).click(option).key_up(Keys.LEFT_CONTROL).perform()
        # Se envía el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click()
        # Se obtiene la nueva oferta
        nueva_oferta = Oferta.objects.order_by('-id').first()
        # Se comprueba que el usuario ha sido redirigido a los detalles de la nueva oferta
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, nueva_oferta.id),
                         self.selenium.current_url)
        # Se comprueba que se muestra el mensaje de éxito correctamente
        message_success = self.selenium.find_element_by_class_name('alert-success')
        self.assertEqual(message_success.text, 'Se ha creado la oferta con exito')
        # El usuario se desloguea
        self.logout()

    # Un usuario crea una oferta con errores de validación
    def test_crear_oferta_con_errores(self):
        # Se loguea el usuario
        self.login('usuario1', 'usuario1')
        # Se accede al formulario de creación de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/creacion'))
        # Se comprueba que el título de la página sea el correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Creacion de ofertas' in title_text, True)
        # Se envía el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click()
        # Se comprueba que el usuario permanece en el formulario
        self.assertEqual('{}/oferta/creacion/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que los errores de validación se muestran correctamente
        error_titulo = self.selenium.find_element_by_xpath(
            '//input[@id="id_titulo"]/following::div[@class="invalid-feedback"][1]')
        error_descripcion = self.selenium.find_element_by_xpath(
            '//input[@id="id_descripcion"]/following::div[@class="invalid-feedback"][1]')
        error_actividades = self.selenium.find_element_by_xpath(
            '//select[@id="id_actividades"]/following::div[@class="invalid-feedback"][1]')
        self.assertEqual(error_titulo.text, 'Este campo es requerido.')
        self.assertEqual(error_descripcion.text, 'Este campo es requerido.')
        self.assertEqual(error_actividades.text, 'Este campo es requerido.')
        # El usuario se desloguea
        self.logout()

    # Un usuario crea una oferta sin estar autenticado
    def test_crear_oferta_sin_autenticar(self):
        # Se accede a la creación de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/creacion'))
        # Se verifica que se ha redirigido al usuario a la página de login, puesto a que no está autenticado
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/login/?next=/oferta/creacion/')

    # Un usuario crea una oferta introduciendo una actividad en modo borrador
    def test_creacion_oferta_actividad_borrador(self):
        # El usuario se loguea
        self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        usuario = Usuario.objects.get(django_user__username='usuario1')
        # Se obtiene la actividad en modo borrador que se va a introducir en lugar de la actividad correcta
        actividad_borrador = Actividad.objects.filter(borrador=True).first()
        # Se accede a la edición de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/creacion/'))
        # Se comprueba que el título de la página es correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Creacion de ofertas' in title_text, True)
        # Se rellenan los campos del formulario
        input_descripcion = self.selenium.find_element_by_id('id_descripcion')
        input_titulo = self.selenium.find_element_by_id('id_titulo')
        input_actividades = self.selenium.find_element_by_id('id_actividades')
        options_actividades = input_actividades.find_elements_by_tag_name('option')
        # Se comprueba que ninguna de las actividades que aparecen en el select está vetada o en modo borrador
        for option in options_actividades:
            id_actividad = option.get_attribute('value')
            actividad = Actividad.objects.get(pk=id_actividad)
            self.assertFalse(actividad.borrador or actividad.vetada)
        input_descripcion.clear()
        input_descripcion.send_keys('descripcioneditada')
        input_titulo.clear()
        input_titulo.send_keys('tituloeditado')
        # Se seleccionan varias actividades del select para añadirlas a la oferta
        option = options_actividades[0]
        self.script_cambiar_id_actividad_option(option, actividad_borrador)
        ActionChains(self.selenium).key_down(Keys.LEFT_CONTROL).click(option).key_up(Keys.LEFT_CONTROL).perform()
        # Se envía el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click()
        # Se comprueba que el usuario permanece en el formulario
        self.assertEqual('{}/oferta/creacion/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que el mensaje de error se muestra correctamente
        message_error = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_error.text, 'Se ha producido un error al crear la oferta')
        # Se comprueba que el mensaje de validacion aparece correctamente
        error_actividades = self.selenium.find_element_by_xpath(
            '//select[@id="id_actividades"]/following::div[@class="invalid-feedback"][1]')
        self.assertEqual(error_actividades.text,
            'Escoja una opción válida. {} no es una de las opciones disponibles.'.format(actividad_borrador.id))
        # El usuario se desloguea
        self.logout()

    # Un usuario crea una oferta introduciendo una actividad vetada
    def test_creacion_oferta_actividad_vetada(self):
        # El usuario se loguea
        self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        usuario = Usuario.objects.get(django_user__username='usuario1')
        oferta = Oferta.objects.filter(Q(autor=usuario) & Q(borrador=True) & Q(vetada=False)).first()
        # Se obtiene la actividad vetada que se va a introducir en lugar de la actividad correcta
        actividad_vetada = Actividad.objects.filter(vetada=True).first()
        # Se accede a la edición de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/creacion/'))
        # Se comprueba que el título de la página es correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Creacion de ofertas' in title_text, True)
        # Se rellenan los campos del formulario
        input_descripcion = self.selenium.find_element_by_id('id_descripcion')
        input_titulo = self.selenium.find_element_by_id('id_titulo')
        input_actividades = self.selenium.find_element_by_id('id_actividades')
        options_actividades = input_actividades.find_elements_by_tag_name('option')
        # Se comprueba que ninguna de las actividades que aparecen en el select está vetada o en modo borrador
        for option in options_actividades:
            id_actividad = option.get_attribute('value')
            actividad = Actividad.objects.get(pk=id_actividad)
            self.assertFalse(actividad.borrador or actividad.vetada)
        input_descripcion.clear()
        input_descripcion.send_keys('descripcioneditada')
        input_titulo.clear()
        input_titulo.send_keys('tituloeditado')
        # Se seleccionan varias actividades del select para añadirlas a la oferta
        option = options_actividades[0]
        self.script_cambiar_id_actividad_option(option, actividad_vetada)
        ActionChains(self.selenium).key_down(Keys.LEFT_CONTROL).click(option).key_up(Keys.LEFT_CONTROL).perform()
        # Se envía el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click()
        # Se comprueba que el usuario permanece en el formulario
        self.assertEqual('{}/oferta/creacion/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que el mensaje de error se muestra correctamente
        message_error = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_error.text, 'Se ha producido un error al crear la oferta')
        # Se comprueba que el mensaje de validacion aparece correctamente
        error_actividades = self.selenium.find_element_by_xpath(
            '//select[@id="id_actividades"]/following::div[@class="invalid-feedback"][1]')
        self.assertEqual(error_actividades.text,
            'Escoja una opción válida. {} no es una de las opciones disponibles.'.format(actividad_vetada.id))
        # El usuario se desloguea
        self.logout()



    # TESTS EDICIÓN

    # Un usuario edita una ofertas
    def test_editar_oferta(self):
        # EL usuario se loguea
        self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        usuario = Usuario.objects.get(django_user__username='usuario1')
        oferta = Oferta.objects.filter(Q(autor=usuario) & Q(borrador=True) & Q(vetada=False)).first()
        # Se accede a la edición de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado'))
        boton_editar = buscar_boton_listado(self,
            id_listado='id_div_listado_ofertas',
            id_boton='button_editar_{}'.format(oferta.id),
            page_param='page')
        boton_editar.click()
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/oferta/edicion/{}/'.format(self.live_server_url, oferta.id))
        # Se comprueba que el título de la página es correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Edicion de ofertas' in title_text, True)
        # Se rellenan los campos del formulario
        input_descripcion = self.selenium.find_element_by_id('id_descripcion')
        input_titulo = self.selenium.find_element_by_id('id_titulo')
        input_borrador = self.selenium.find_element_by_id('id_borrador')
        input_actividades = self.selenium.find_element_by_id('id_actividades')
        options_actividades = input_actividades.find_elements_by_tag_name('option')
        # Se comprueba que ninguna de las actividades que aparecen en el select está vetada o en modo borrador
        for option in options_actividades:
            id_actividad = option.get_attribute('value')
            actividad = Actividad.objects.get(pk=id_actividad)
            self.assertFalse(actividad.borrador or actividad.vetada)
        input_descripcion.clear()
        input_descripcion.send_keys('descripcioneditada')
        input_titulo.clear()
        input_titulo.send_keys('tituloeditado')
        # Se seleccionan varias actividades del select para añadirlas a la oferta
        for option in options_actividades[:2]:
            ActionChains(self.selenium).key_down(Keys.LEFT_CONTROL).click(option).key_up(Keys.LEFT_CONTROL).perform()
        # Se envía el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click()
        # Se comprueba que el usuario ha sido redirigido a los detalles de la oferta
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se comprueba que el mensaje de éxito se muestra correctamente
        message_success = self.selenium.find_element_by_class_name('alert-success')
        self.assertEqual(message_success.text, 'Se ha editado la oferta con éxito')
        # El usuario se desloguea
        self.logout()

    # El usuario edita una oferta dejándola vacía
    def test_editar_oferta_vacia(self):
        # El usuario se loguea
        self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        usuario = Usuario.objects.get(django_user__username='usuario1')
        oferta = Oferta.objects.filter(Q(autor=usuario) & Q(borrador=True) & Q(vetada=False)).first()
        # El usuario accede a la edición de la ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado'))
        boton_editar = buscar_boton_listado(self,
            id_listado='id_div_listado_ofertas',
            id_boton='button_editar_{}'.format(oferta.id),
            page_param='page')
        boton_editar.click()
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/oferta/edicion/{}/'.format(self.live_server_url, oferta.id))
        # Se comprueba que el texto es correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Edicion de oferta' in title_text, True)
        # Se vacían los campos del formulario
        input_descripcion = self.selenium.find_element_by_id('id_descripcion')
        input_titulo = self.selenium.find_element_by_id('id_titulo')
        input_descripcion.clear()
        input_titulo.clear()
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click()
        # Se comprueba que el usuario permanece en el formulario
        self.assertEqual('{}/oferta/edicion/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se comprueba que los errores de validación se muestran adecuadamente
        error_titulo = self.selenium.find_element_by_xpath(
            '//input[@id="id_titulo"]/following::div[@class="invalid-feedback"][1]')
        error_descripcion = self.selenium.find_element_by_xpath(
            '//input[@id="id_descripcion"]/following::div[@class="invalid-feedback"][1]')
        error_actividades = self.selenium.find_element_by_xpath(
            '//select[@id="id_actividades"]/following::div[@class="invalid-feedback"][1]')
        self.assertEqual(error_titulo.text, 'Este campo es requerido.')
        self.assertEqual(error_descripcion.text, 'Este campo es requerido.')
        self.assertEqual(error_actividades.text, 'Este campo es requerido.')
        # El usuario se desloguea
        self.logout()

    # Un usuario edita una oferta si estar autenticado
    def test_editar_oferta_sin_autenticar(self):
        # Se obtienen las variables necesarias para el test
        oferta = Oferta.objects.filter(borrador=True).first()
        # Se accede a la edición de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/edicion/{}/'.format(oferta.id)))
        # Se comprueba que el usuario es redirigido a la página de login
        self.assertEqual(self.selenium.current_url,
                         self.live_server_url + '/login/?next=/oferta/edicion/{}/'.format(oferta.id))

    # Un usuario edita una oferta ajena
    def test_editar_usuario_incorrecto(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se obtienen variables necesarias para el test
        oferta = Oferta.objects.exclude(autor=usuario).filter(borrador=True).first()
        # Se accede a la edición de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/edicion/{}/'.format(oferta.id)))
        # Se comprueba que el usuario ha sido redirigido al listado de ofertas, puesto a que no puede acceder a los
        # detalles de la oferta, por ser ajena y en borrador
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/oferta/listado/')
        # Se comprueba que se muestra el mensaje de error correctamente
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se poseen los permisos necesarios para editar la oferta')
        # El usuario se desloguea
        self.logout()

    # Un usuario edita una oferta que no está en modo borrador
    def test_editar_oferta_no_borrador(self):
        # El usuario se loguea
        usuario = self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        oferta = Oferta.objects.filter(autor=usuario, borrador=False).first()
        # Se accede a la edición de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/edicion/{}/'.format(oferta.id)))
        # Se comprueba que el usuario ha sido redirigido a los detalles de la oferta
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/oferta/detalles/{}/'.format(oferta.id))
        # Se comprueba que se muestra el mensaje de error correctamente
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede editar una oferta que no está en modo borrador')
        # El usuario se desloguea
        self.logout()

    # Un usuario edita una oferta introduciendo una actividad en modo borrador
    def test_editar_oferta_actividad_borrador(self):
        # El usuario se loguea
        self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        usuario = Usuario.objects.get(django_user__username='usuario1')
        oferta = Oferta.objects.filter(Q(autor=usuario) & Q(borrador=True) & Q(vetada=False)).first()
        # Se obtiene la actividad en modo borrador que se va a introducir en lugar de la actividad correcta
        actividad_borrador = Actividad.objects.filter(borrador=True).first()
        # Se accede a la edición de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/edicion/{}/'.format(oferta.id)))
        # Se comprueba que el título de la página es correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Edicion de ofertas' in title_text, True)
        # Se rellenan los campos del formulario
        input_descripcion = self.selenium.find_element_by_id('id_descripcion')
        input_titulo = self.selenium.find_element_by_id('id_titulo')
        input_borrador = self.selenium.find_element_by_id('id_borrador')
        input_actividades = self.selenium.find_element_by_id('id_actividades')
        options_actividades = input_actividades.find_elements_by_tag_name('option')
        # Se comprueba que ninguna de las actividades que aparecen en el select está vetada o en modo borrador
        for option in options_actividades:
            id_actividad = option.get_attribute('value')
            actividad = Actividad.objects.get(pk=id_actividad)
            self.assertFalse(actividad.borrador or actividad.vetada)
        input_descripcion.clear()
        input_descripcion.send_keys('descripcioneditada')
        input_titulo.clear()
        input_titulo.send_keys('tituloeditado')
        # Se seleccionan varias actividades del select para añadirlas a la oferta
        option = options_actividades[0]
        self.script_cambiar_id_actividad_option(option, actividad_borrador)
        ActionChains(self.selenium).key_down(Keys.LEFT_CONTROL).click(option).key_up(Keys.LEFT_CONTROL).perform()
        # Se envía el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click()
        # Se comprueba que el usuario permanece en el formulario
        self.assertEqual('{}/oferta/edicion/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se comprueba que el mensaje de error se muestra correctamente
        message_error = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_error.text, 'Se ha producido un error al editar la oferta')
        # Se comprueba que el mensaje de validacion aparece correctamente
        error_actividades = self.selenium.find_element_by_xpath(
            '//select[@id="id_actividades"]/following::div[@class="invalid-feedback"][1]')
        self.assertEqual(error_actividades.text,
                         'Escoja una opción válida. {} no es una de las opciones disponibles.'.format(
                             actividad_borrador.id
                         ))
        # El usuario se desloguea
        self.logout()

    # Un usuario edita una oferta introduciendo una actividad vetada
    def test_editar_oferta_actividad_vetada(self):
        # El usuario se loguea
        self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        usuario = Usuario.objects.get(django_user__username='usuario1')
        oferta = Oferta.objects.filter(Q(autor=usuario) & Q(borrador=True) & Q(vetada=False)).first()
        # Se obtiene la actividad vetada que se va a introducir en lugar de la actividad correcta
        actividad_vetada = Actividad.objects.filter(vetada=True).first()
        # Se accede a la edición de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/edicion/{}/'.format(oferta.id)))
        # Se comprueba que el título de la página es correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Edicion de ofertas' in title_text, True)
        # Se rellenan los campos del formulario
        input_descripcion = self.selenium.find_element_by_id('id_descripcion')
        input_titulo = self.selenium.find_element_by_id('id_titulo')
        input_borrador = self.selenium.find_element_by_id('id_borrador')
        input_actividades = self.selenium.find_element_by_id('id_actividades')
        options_actividades = input_actividades.find_elements_by_tag_name('option')
        # Se comprueba que ninguna de las actividades que aparecen en el select está vetada o en modo borrador
        for option in options_actividades:
            id_actividad = option.get_attribute('value')
            actividad = Actividad.objects.get(pk=id_actividad)
            self.assertFalse(actividad.borrador or actividad.vetada)
        input_descripcion.clear()
        input_descripcion.send_keys('descripcioneditada')
        input_titulo.clear()
        input_titulo.send_keys('tituloeditado')
        # Se seleccionan varias actividades del select para añadirlas a la oferta
        option = options_actividades[0]
        self.script_cambiar_id_actividad_option(option, actividad_vetada)
        ActionChains(self.selenium).key_down(Keys.LEFT_CONTROL).click(option).key_up(Keys.LEFT_CONTROL).perform()
        # Se envía el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click()
        # Se comprueba que el usuario permanece en el formulario
        self.assertEqual('{}/oferta/edicion/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se comprueba que el mensaje de error se muestra correctamente
        message_error = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_error.text, 'Se ha producido un error al editar la oferta')
        # Se comprueba que el mensaje de validacion aparece correctamente
        error_actividades = self.selenium.find_element_by_xpath(
            '//select[@id="id_actividades"]/following::div[@class="invalid-feedback"][1]')
        self.assertEqual(error_actividades.text,
            'Escoja una opción válida. {} no es una de las opciones disponibles.'.format(actividad_vetada.id))
        # El usuario se desloguea
        self.logout()

    # Un usuario edita una oferta introduciendo una actividad en modo borrador
    def test_editar_oferta_actividad_borrador(self):
        # El usuario se loguea
        self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        usuario = Usuario.objects.get(django_user__username='usuario1')
        oferta = Oferta.objects.filter(Q(autor=usuario) & Q(borrador=True) & Q(vetada=False)).first()
        # Se obtiene la actividad en modo borrador que se va a introducir en lugar de la actividad correcta
        actividad_borrador = Actividad.objects.filter(borrador=True).first()
        # Se accede a la edición de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/edicion/{}/'.format(oferta.id)))
        # Se comprueba que el título de la página es correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Edicion de ofertas' in title_text, True)
        # Se rellenan los campos del formulario
        input_descripcion = self.selenium.find_element_by_id('id_descripcion')
        input_titulo = self.selenium.find_element_by_id('id_titulo')
        input_borrador = self.selenium.find_element_by_id('id_borrador')
        input_actividades = self.selenium.find_element_by_id('id_actividades')
        options_actividades = input_actividades.find_elements_by_tag_name('option')
        # Se comprueba que ninguna de las actividades que aparecen en el select está vetada o en modo borrador
        for option in options_actividades:
            id_actividad = option.get_attribute('value')
            actividad = Actividad.objects.get(pk=id_actividad)
            self.assertFalse(actividad.borrador or actividad.vetada)
        input_descripcion.clear()
        input_descripcion.send_keys('descripcioneditada')
        input_titulo.clear()
        input_titulo.send_keys('tituloeditado')
        # Se seleccionan varias actividades del select para añadirlas a la oferta
        option = options_actividades[0]
        self.script_cambiar_id_actividad_option(option, actividad_borrador)
        ActionChains(self.selenium).key_down(Keys.LEFT_CONTROL).click(option).key_up(Keys.LEFT_CONTROL).perform()
        # Se envía el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click()
        # Se comprueba que el usuario permanece en el formulario
        self.assertEqual('{}/oferta/edicion/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se comprueba que el mensaje de error se muestra correctamente
        message_error = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_error.text, 'Se ha producido un error al editar la oferta')
        # Se comprueba que el mensaje de validacion aparece correctamente
        error_actividades = self.selenium.find_element_by_xpath(
            '//select[@id="id_actividades"]/following::div[@class="invalid-feedback"][1]')
        self.assertEqual(error_actividades.text, 'Escoja una opción válida. {} no es una de las opciones disponibles.'.format(
            actividad_borrador.id
        ))
        # El usuario se desloguea
        self.logout()

    # Un usuario edita una oferta introduciendo una actividad vetada
    def test_editar_oferta_actividad_vetada(self):
        # El usuario se loguea
        self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        usuario = Usuario.objects.get(django_user__username='usuario1')
        oferta = Oferta.objects.filter(Q(autor=usuario) & Q(borrador=True) & Q(vetada=False)).first()
        # Se obtiene la actividad vetada que se va a introducir en lugar de la actividad correcta
        actividad_vetada = Actividad.objects.filter(vetada=True).first()
        # Se accede a la edición de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/edicion/{}/'.format(oferta.id)))
        # Se comprueba que el título de la página es correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual('Edicion de ofertas' in title_text, True)
        # Se rellenan los campos del formulario
        input_descripcion = self.selenium.find_element_by_id('id_descripcion')
        input_titulo = self.selenium.find_element_by_id('id_titulo')
        input_borrador = self.selenium.find_element_by_id('id_borrador')
        input_actividades = self.selenium.find_element_by_id('id_actividades')
        options_actividades = input_actividades.find_elements_by_tag_name('option')
        # Se comprueba que ninguna de las actividades que aparecen en el select está vetada o en modo borrador
        for option in options_actividades:
            id_actividad = option.get_attribute('value')
            actividad = Actividad.objects.get(pk=id_actividad)
            self.assertFalse(actividad.borrador or actividad.vetada)
        input_descripcion.clear()
        input_descripcion.send_keys('descripcioneditada')
        input_titulo.clear()
        input_titulo.send_keys('tituloeditado')
        # Se seleccionan varias actividades del select para añadirlas a la oferta
        option = options_actividades[0]
        self.script_cambiar_id_actividad_option(option, actividad_vetada)
        ActionChains(self.selenium).key_down(Keys.LEFT_CONTROL).click(option).key_up(Keys.LEFT_CONTROL).perform()
        # Se envía el formulario
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click()
        # Se comprueba que el usuario permanece en el formulario
        self.assertEqual('{}/oferta/edicion/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se comprueba que el mensaje de error se muestra correctamente
        message_error = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_error.text, 'Se ha producido un error al editar la oferta')
        # Se comprueba que el mensaje de validacion aparece correctamente
        error_actividades = self.selenium.find_element_by_xpath(
            '//select[@id="id_actividades"]/following::div[@class="invalid-feedback"][1]')
        self.assertEqual(error_actividades.text, 'Escoja una opción válida. {} no es una de las opciones disponibles.'.format(
            actividad_vetada.id
        ))
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de editar una oferta que no existe
    def test_editar_oferta_inexistente(self):
        # Se loguea el usuario
        usuario = self.login('usuario1', 'usuario1')
        # Se accede a la edición de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/edicion/{}/'.format(0)))
        # Se comprueba que se ha redirigido al usuario a la página de listado de ofertas, puesto a que se le redirige
        # desde la página de detalles, que no puede mostrar los detalles de una oferta que no existe.
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/oferta/listado/')
        # Se comprueba que se muestra el mensaje de error correctamente
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se ha encontrado la oferta')
        # El usuario se desloguea
        self.logout()



    # TESTS ELIMINACIÓN

    # Un usuario elimina una oferta
    def test_eliminar_oferta(self):
        # El usuario se loguea
        usuario = self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        oferta = Oferta.objects.filter(autor=usuario, borrador=True).first()
        numero_ofertas_antes = Oferta.objects.count()
        # Se accede al listado de las ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado/'))
        # Se obtienen las ofertas listadas
        ofertas_listado_antes = self.selenium.find_elements_by_xpath('//tbody/child::tr')
        # Se pulsa el botón de eliminar oferta y se acepta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado'))
        boton_eliminar = buscar_boton_listado(self,
            id_listado='id_div_listado_ofertas',
            id_boton='button_eliminar_{}'.format(oferta.id),
            page_param='page')
        boton_eliminar.click()
        self.selenium.switch_to.alert.accept()
        # Se comprueba que el usuario vuelve al listado de ofertas
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/oferta/listado/')
        # Aparece el mensaje de eliminacion correctamente
        message_success = self.selenium.find_element_by_class_name('alert-success')
        self.assertEqual(message_success.text, 'Se ha eliminado la oferta con exito')
        # Se comprueba que se ha eliminado la oferta de la base de datos
        numero_ofertas_despues = Oferta.objects.count()
        self.assertEqual(numero_ofertas_antes, numero_ofertas_despues + 1)
        oferta_eliminada = True
        try:
            Oferta.objects.get(pk=oferta.id)
            oferta_eliminada = False
        except ObjectDoesNotExist as e:
            pass
        self.assertEqual(oferta_eliminada, True)
        ofertas_listado_despues = self.selenium.find_elements_by_xpath('//tbody/child::tr')
        # El usuario se desloguea
        self.logout()

    # Un usuario va a eliminar una oferta, pero lo cancela en el ultimo momento
    def test_eliminar_oferta_sin_aceptar(self):
        # El usuario se loguea
        usuario = self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        numero_ofertas_antes = Oferta.objects.count()
        oferta = Oferta.objects.filter(autor=usuario, borrador=True).first()
        # Se accede al listado de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado/'))
        # Se obtienen las ofertas listadas
        ofertas_listado_antes = self.selenium.find_elements_by_xpath('//tbody/child::tr')
        # Se pulsa el botón de eliminar oferta pero rechaza la eliminación
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado'))
        boton_eliminar = buscar_boton_listado(self,
            id_listado='id_div_listado_ofertas',
            id_boton='button_eliminar_{}'.format(oferta.id),
            page_param='page')
        boton_eliminar.click()
        self.selenium.switch_to.alert.dismiss()
        # Se comprueba que el usuario permanece en el listado de ofertas
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/oferta/listado/')
        # Se comprueba que no se ha eliminado ninguna oferta
        numero_ofertas_despues = Oferta.objects.count()
        self.assertEqual(numero_ofertas_antes, numero_ofertas_despues)
        oferta_eliminada = True
        try:
            Oferta.objects.get(pk=oferta.id)
            oferta_eliminada = False
        except ObjectDoesNotExist as e:
            pass
        self.assertEqual(oferta_eliminada, False)
        ofertas_listado_despues = self.selenium.find_elements_by_xpath('//tbody/child::tr')
        # El usuario se desloguea
        self.logout()

    # Un usuario elimina una oferta sin estar autenticado
    def test_eliminar_oferta_sin_autenticar(self):
        # Se obtienen variables necesarias para el test
        oferta = Oferta.objects.filter(borrador=True).first()
        # Se accede a la eliminación de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/eliminacion/{}/'.format(oferta.id)))
        # Se redirige al usuario al login
        self.assertEqual(self.selenium.current_url,
                         self.live_server_url + '/login/?next=/oferta/eliminacion/{}/'.format(oferta.id))

    # Un usuario trata de eliminar una oferta que no le pertenece
    def test_eliminar_oferta_usuario_incorrecto(self):
        # Un usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se obtienen variables necesarias para el test
        oferta = Oferta.objects.filter(borrador=True).exclude(autor=usuario).first()
        # Se accede a la eliminación de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/eliminacion/{}/'.format(oferta.id)))
        # Se comprueba que el usuario ha sido redirigido al listado de ofertas, puesto a que no puede acceder a los
        # detalles de una actividad ajena en modo borrador
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/oferta/listado/')
        # Se comprueba que el mensaje de error se muestra correctamente
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se poseen los permisos necesarios para editar la oferta')
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de eliminar una oferta que no está en modo borrador
    def test_eliminar_oferta_no_borrador(self):
        # Se loguea el usuario
        usuario = self.login('usuario1', 'usuario1')
        # Se obtienen variables necesarias para el test
        oferta = Oferta.objects.filter(borrador=False, autor=usuario).first()
        # Se accede a la eliminación de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/eliminacion/{}/'.format(oferta.id)))
        # Se comprueba que se ha redirigido al usuario a la página de detalles de la oferta correctamente
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/oferta/detalles/{}/'.format(oferta.id))
        # Se comprueba que se muestra el mensaje de error correctamente
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede eliminar una oferta que no está en modo borrador')
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de eliminar una oferta que no existe
    def test_eliminar_oferta_inexistente(self):
        # Se loguea el usuario
        usuario = self.login('usuario1', 'usuario1')
        # Se accede a la eliminación de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/eliminacion/{}/'.format(0)))
        # Se comprueba que se ha redirigido al usuario a la página de listado de ofertas, puesto a que se le redirige
        # desde la página de detalles, que no puede mostrar los detalles de una oferta que no existe.
        self.assertEqual(self.selenium.current_url, self.live_server_url + '/oferta/listado/')
        # Se comprueba que se muestra el mensaje de error correctamente
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se ha encontrado la oferta')
        # El usuario se desloguea
        self.logout()


    
    # TESTS VETO

    # Un admnistrador trata de vetar una oferta
    def test_veta_oferta(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se obtienen las variables que se van a usar en el test
        oferta = Oferta.objects.filter(vetada=False, borrador=False, cerrada=False).first()
        motivo_veto = 'Veto selenium test'
        # Se acccede al formulario de vetar la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado'))
        boton_veto = buscar_boton_listado(self,
            id_listado='id_div_listado_ofertas',
            id_boton='button_vetar_{}'.format(oferta.id),
            page_param='page')
        boton_veto.click()
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/oferta/veto/{}/'.format(self.live_server_url, oferta.id))
        # Se comprueba que el título de la página es el correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual(title_text, 'Veto a ofertas')
        # Se comprueba que aparecen los campos necesarios
        input_motivo_veto = self.selenium.find_element_by_id('id_motivo_veto')
        input_motivo_veto.clear()
        input_motivo_veto.send_keys(motivo_veto)
        # Se busca el botón de envío, lo pulsa y acepta el veto
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click()
        self.selenium.switch_to.alert.accept()
        # Se comprueba que se está en la página de detalles de la oferta
        # Pero antes hay que esperar a que redirija
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id))
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se busca el mensaje de éxito y se comprueba que es correcto
        message_success = self.selenium.find_element_by_class_name('alert-success')
        self.assertEqual(message_success.text, 'Se ha vetado la oferta con exito')
        # Se busca el motivo de veto en la vista de detalles a la que se ha redirigido
        output_motivo_veto = self.selenium.find_element_by_xpath(
            '//p[text()="Motivo de veto : {}"]'.format(motivo_veto))
        self.assertEqual(output_motivo_veto != None, True)
        # La oferta ha sido vetada
        oferta_recibida = Oferta.objects.get(pk=oferta.id)
        self.assertEqual(oferta_recibida.motivo_veto, motivo_veto)
        self.assertEqual(oferta_recibida.vetada, True)
        # El usuario se desloguea
        self.logout()

    # Un admnistrador trata de vetar una oferta pero no acepta el veto
    def test_veta_oferta_sin_aceptar(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se obtienen las variables que se van a usar en el test
        oferta = Oferta.objects.filter(vetada=False, cerrada=False, borrador=False).first()
        motivo_veto = 'Veto selenium test'
        # Se acccede al formulario de vetar la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado'))
        boton_veto = buscar_boton_listado(self,
            id_listado='id_div_listado_ofertas',
            id_boton='button_vetar_{}'.format(oferta.id),
            page_param='page')
        boton_veto.click()
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/oferta/veto/{}/'.format(self.live_server_url, oferta.id))
        # Se comprueba que el título de la página es el correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual(title_text, 'Veto a ofertas')
        # Se comprueba que aparecen los campos necesarios
        input_motivo_veto = self.selenium.find_element_by_id('id_motivo_veto')
        input_motivo_veto.clear()
        input_motivo_veto.send_keys(motivo_veto)
        # Se busca el botón de envío, se pulsa y se cancela el veto
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click()
        self.selenium.switch_to.alert.dismiss()
        # Se comprueba que se está en el formulario de veto
        self.assertEqual('{}/oferta/veto/{}/'.format(self.live_server_url, oferta.id), self.selenium.current_url)
        # Se comprueba que no ha cambiado la oferta
        oferta_recibida = Oferta.objects.get(pk=oferta.id)
        self.assertEqual(oferta, oferta_recibida)
        self.assertEqual(oferta_recibida.vetada, False)
        self.assertEqual(oferta_recibida.motivo_veto, None)
        # El usuario se desloguea
        self.logout()

    # Un administrador veta la oferta sin estar autenticado
    def test_veta_oferta_sin_loguear(self):
        # Se obtienen las variables que se van a usar en el test
        oferta = Oferta.objects.filter(vetada=False, borrador=False, cerrada=False).first()
        motivo_veto = 'Veto selenium test'
        # Se acccede al formulario de vetar la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/veto/{}/'.format(oferta.id)))
        # Se comprueba que se está en la página de login
        self.assertEqual('{}/login/?next=/oferta/veto/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)

    # Un administrador que no es administrador trata de vetar la oferta
    def test_veta_oferta_usuario_incorrecto(self):
        # El usuario se loguea
        usuario = self.login('usuario1', 'usuario1')
        # Se obtienen las variables que se van a usar en el test
        oferta = Oferta.objects.filter(vetada=False, borrador=False, cerrada=False).first()
        motivo_veto = 'Veto selenium test'
        # Se acccede al formulario de vetar la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/veto/{}/'.format(oferta.id)))
        # Se comprueba que se ha redirigido a la página de detalles de la oferta
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se poseen los permisos necesarios para vetar la oferta')
        # El usuario se desloguea
        self.logout()

    # Un admninistrador trata de vetar una oferta ya vetada
    def test_veta_oferta_vetada(self):
        # El usuario se loguea y se obtienen las vriaables que se van a usar en el test
        self.login('usuario2', 'usuario2')
        usuario = Usuario.objects.get(django_user__username='usuario2')
        oferta = Oferta.objects.filter(vetada=True, borrador=False, cerrada=False).first()
        # Se acccede al formulario de vetar la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/veto/{}/'.format(oferta.id)))
        # Se comprueba que se ha redirigido a la página de detalles de la oferta
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede vetar una oferta ya vetada')
        # El usuario se desloguea
        self.logout()

    # Un administrador trata de vetar una oferta que no existe
    def test_veta_oferta_inexistente(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se obtienen las vriaables que se van a usar en el test
        motivo_veto = 'Veto selenium test'
        # Se acccede al formulario de vetar la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/veto/{}/'.format(0)))
        # Se comprueba que se está en la página de listado de ofertas
        self.assertEqual('{}/oferta/listado/'.format(self.live_server_url), self.selenium.current_url)
        # Se busca el mensaje de éxito y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se ha encontrado la oferta')
        # El usuario se desloguea
        self.logout()

    # Un administrador trata de vetar una oferta usando un motivo de veto inválido
    def test_veta_oferta_incorrecta(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se obtienen las variables que se van a usar en el test
        oferta = Oferta.objects.filter(vetada=False, borrador=False, cerrada=False).first()
        motivo_veto = ''
        # Se acccede al formulario de vetar la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/veto/{}/'.format(oferta.id)))
        # Se comprueba que el título de la página es el correcto
        title_text = self.selenium.find_element_by_tag_name('h1').text
        self.assertEqual(title_text, 'Veto a ofertas')
        # Se comprueba que aparecen los campos necesarios
        input_motivo_veto = self.selenium.find_element_by_id('id_motivo_veto')
        input_motivo_veto.clear()
        input_motivo_veto.send_keys(motivo_veto)
        # Se busca el botón de envío y se pulsa
        input_submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        input_submit.click()
        self.selenium.switch_to.alert.accept()
        # Se busca el mensaje de error de validación y se comprueba que es correcto
        motivo_error_veto = self.selenium.find_element_by_xpath(
            '//form/child::input[@id="id_motivo_veto"]/following-sibling::div[@class="invalid-feedback"][1]')
        self.assertEqual(motivo_error_veto.text, 'Este campo es requerido.')
        # Se comprueba que se está en la página de veto de la oferta
        self.assertEqual('{}/oferta/veto/{}/'.format(self.live_server_url, oferta.id), self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'Se ha producido un error al vetar la oferta')
        # El usuario se desloguea
        self.logout()

    # Un administrador trata de vetar una oferta que está en modo borrador
    def test_veta_oferta_borrador(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se obtienen las variables que se van a usar en el test
        oferta = Oferta.objects.filter(vetada=False, borrador=True).first()
        # Se acccede al formulario de vetar la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/veto/{}/'.format(oferta.id)))
        # Se comprueba que se está en la página de listado de las ofertas, puesto a que el usuario no puede acceder a
        # los detalles de una oferta que está en borrador y no le pertenece
        self.assertEqual('{}/oferta/listado/'.format(self.live_server_url, oferta.id), self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede vetar una oferta que está en modo borrador')
        # El usuario se desloguea
        self.logout()

    # Un administrador trata de vetar una oferta que está cerrada
    def test_veta_oferta_cerrada(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se obtienen las variables que se van a usar en el test
        oferta = Oferta.objects.filter(vetada=False, borrador=False, cerrada=True).first()
        # Se acccede al formulario de vetar la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/veto/{}/'.format(oferta.id)))
        # Se comprueba que se está en la página de detalles de la oferta
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede vetar una oferta que está cerrada')
        # El usuario se desloguea
        self.logout()
    
    

    # TESTS LEVANTAMIENTO VETO

    # Un administrador levanta el veto sobre una oferta
    def test_levanta_veto_oferta(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario2', 'usuario2')
        oferta = Oferta.objects.filter(Q(vetada=True) & Q(borrador=False)).first()
        # Se acccede a la url de listado de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado/'))
        # Se selecciona una oferta para levantar el veto y se acepta
        boton_veto = buscar_boton_listado(self,
            id_listado = 'id_div_listado_ofertas',
            id_boton = 'button_levantar_veto_{}'.format(oferta.id),
            page_param = 'page')
        boton_veto.click()
        self.selenium.switch_to.alert.accept()
        # Se comprueba que se está en la página de detalles de la oferta
        # Pero antes se tiene que esperar a que redirija a la página
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id))
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se busca el mensaje de éxito y se comprueba que es correcto
        message_success = self.selenium.find_element_by_class_name('alert-success')
        self.assertEqual(message_success.text, 'Se ha levantado el veto sobre la oferta con éxito')
        # Se comprueba que se ha levantado el veto
        oferta_recibida = Oferta.objects.get(pk=oferta.id)
        self.assertEqual(oferta_recibida.motivo_veto, None)
        self.assertEqual(oferta_recibida.vetada, False)
        # El usuario se desloguea
        self.logout()

    # Un administrador levanta el veto sobre una oferta pero cancela el levantamiento del veto
    def test_levanta_veto_oferta_sin_aceptar(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario2', 'usuario2')
        oferta = Oferta.objects.filter(Q(vetada=True) & Q(borrador=False)).first()
        # Se acccede a la url de listado de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado/'))
        # Se selecciona una oferta para levantar el veto y se acepta
        boton_veto = buscar_boton_listado(self,
            id_listado='id_div_listado_ofertas',
            id_boton='button_levantar_veto_{}'.format(oferta.id),
            page_param='page')
        boton_veto.click()
        self.selenium.switch_to.alert.dismiss()
        # Se comprueba que se está en la página de listado de las ofertas
        self.assertTrue(self.selenium.current_url.startswith('{}/oferta/listado/'.format(self.live_server_url)))
        # Se comprueba que la oferta no ha sufrido cambios
        oferta_recibida = Oferta.objects.get(pk=oferta.id)
        self.assertEqual(oferta_recibida.motivo_veto, oferta.motivo_veto)
        self.assertEqual(oferta_recibida.vetada, True)
        # El usuario se desloguea
        self.logout()

    # Un usuario levanta el veto sin estar autenticado
    def test_levanta_veto_oferta_sin_loguear(self):
        # Se obtienen las variables que se van a usar en el test
        oferta = Oferta.objects.filter(Q(vetada=True) & Q(borrador=False)).first()
        # Se acccede a la url de levantamiento de veto
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/levantamiento_veto/{}/'.format(oferta.id)))
        # Se comprueba que se he redirigido al usuario al login
        self.assertEqual('{}/login/?next=/oferta/levantamiento_veto/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)

    # Un usuario que no tiene permisos de administrador levanta el veto sobre una oferta
    def test_levanta_veto_oferta_usuario_incorrecto(self):
        # El usuario se loguea y
        usuario = self.login('usuario1', 'usuario1')
        # Se obtienen las variables que se van a usar en el test
        oferta = Oferta.objects.filter(Q(vetada=True) & Q(borrador=False)).first()
        # Se acccede a la url de levantamiento de veto
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/levantamiento_veto/{}/'.format(oferta.id)))
        # Se comprueba que se ha redirigido a la página de detalles de la oferta
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se poseen los permisos necesarios para levantar el veto sobre la oferta')
        # El usuario se desloguea
        self.logout()

    # Un administrador levanta el veto sobre una oferta no vetada
    def test_levanta_veto_oferta_no_vetada(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se obtienen las variables que se van a usar en el test
        oferta = Oferta.objects.filter(Q(vetada=False) & Q(borrador=False)).first()
        # Se acccede a la url de levantamiento de veto
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/levantamiento_veto/{}/'.format(oferta.id)))
        # Se comprueba que se está en la página de detalles de la oferta
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede levantar el veto a una oferta sin vetar')
        # El usuario se desloguea
        self.logout()

    # Un administrador levanta el veto sobre una oferta inexistente
    def test_levanta_veto_oferta_inexistente(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se acccede a la url de levantamiento de veto
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/levantamiento_veto/0/'))
        # Se comprueba que se está en la página de listado de ofertas
        self.assertEqual('{}/oferta/listado/'.format(self.live_server_url), self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se ha encontrado la oferta')
        # El usuario se desloguea
        self.logout()
        


    # TESTS CIERRE

    # Un usuario cierra una oferta
    def test_cierra_oferta(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario1', 'usuario1')
        oferta = Oferta.objects.filter(vetada=False, borrador=False, cerrada=False, autor=usuario).first()
        # Se acccede a la url de listado de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado/'))
        # Se selecciona una oferta para levantar el veto y se acepta
        boton_cierre = buscar_boton_listado(self,
            id_listado = 'id_div_listado_ofertas',
            id_boton = 'button_cerrar_{}'.format(oferta.id),
            page_param = 'page')
        boton_cierre.click()
        self.selenium.switch_to.alert.accept()
        # Se comprueba que se está en la página de detalles de la oferta
        # Pero antes se tiene que esperar a que redirija a la página
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id))
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se busca el mensaje de éxito y se comprueba que es correcto
        message_success = self.selenium.find_element_by_class_name('alert-success')
        self.assertEqual(message_success.text, 'Se ha cerrado la oferta con éxito')
        # Se comprueba que se ha levantado el veto
        oferta_recibida = Oferta.objects.get(pk=oferta.id)
        self.assertTrue(oferta_recibida.cerrada)
        # El usuario se desloguea
        self.logout()

    # Un usuario cierra una oferta pero cancela el cierre
    def test_cierra_oferta_sin_aceptar(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario1', 'usuario1')
        oferta = Oferta.objects.filter(vetada=False, autor=usuario, cerrada=False, borrador=False).first()
        # Se acccede a la url de listado de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado/'))
        # Se selecciona una oferta para levantar el veto y se acepta
        boton_cierre = buscar_boton_listado(self,
            id_listado='id_div_listado_ofertas',
            id_boton='button_cerrar_{}'.format(oferta.id),
            page_param='page')
        boton_cierre.click()
        self.selenium.switch_to.alert.dismiss()
        # Se comprueba que se está en la página de listado de las ofertas
        self.assertEqual('{}/oferta/listado/'.format(self.live_server_url), self.selenium.current_url)
        # Se comprueba que la oferta no ha sufrido cambios
        oferta_recibida = Oferta.objects.get(pk=oferta.id)
        self.assertFalse(oferta_recibida.cerrada)
        # El usuario se desloguea
        self.logout()

    # Un usuario cierra una oferta sin estar autenticado
    def test_cierra_oferta_sin_loguear(self):
        # Se obtienen las variables que se van a usar en el test
        oferta = Oferta.objects.filter(vetada=False, cerrada=False, borrador=False).first()
        # Se acccede a la url de levantamiento de veto
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/cierre/{}/'.format(oferta.id)))
        # Se comprueba que se he redirigido al usuario al login
        self.assertEqual('{}/login/?next=/oferta/cierre/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)

    # Un usuario cierra la oferta de otro usuario
    def test_cierra_oferta_ajena(self):
        # El usuario se loguea y
        usuario = self.login('usuario1', 'usuario1')
        # Se obtienen las variables que se van a usar en el test
        oferta = Oferta.objects.filter(vetada=False, borrador=False, cerrada=False).exclude(autor=usuario).first()
        # Se acccede a la url de levantamiento de veto
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/cierre/{}/'.format(oferta.id)))
        # Se comprueba que se está en la página de detalles
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id), self.selenium.current_url)
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id), self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se poseen los permisos o requisitos necesarios para realizar esta accion')
        # El usuario se desloguea
        self.logout()

    # Un usuario cierra una oferta ya cerrada
    def test_cierra_oferta_cerrada(self):
        # El usuario se loguea
        usuario = self.login('usuario1', 'usuario1')
        # Se obtienen las variables que se van a usar en el test
        oferta = Oferta.objects.filter(vetada=False, borrador=False, cerrada=True, autor=usuario).first()
        # Se acccede a la url de levantamiento de veto
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/cierre/{}/'.format(oferta.id)))
        # Se comprueba que se está en la página de detalles de la oferta
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede cerrar una oferta que está cerrada')
        # El usuario se desloguea
        self.logout()

    # Un usuario cierra una oferta inexistente
    def test_cierra_oferta_inexistente(self):
        # El usuario se loguea
        usuario = self.login('usuario2', 'usuario2')
        # Se acccede a la url de levantamiento de veto
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/cierre/0/'))
        # Se comprueba que se está en la página de listado de ofertas
        self.assertEqual('{}/oferta/listado/'.format(self.live_server_url), self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se ha encontrado la oferta')
        # El usuario se desloguea
        self.logout()



    # TESTS SOLICITUD

    # Un usuario solicita una oferta con éxito
    def test_solicita_oferta(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario1', 'usuario1')
        # Se busca una oferta que se pueda solicitar
        ofertas = Oferta.objects.exclude((Q(cerrada=True) | Q(borrador=True) | Q(vetada=True)) & ~Q(autor=usuario)).order_by('id')
        ofertas_solicitables = get_ofertas_solicitables_y_ofertas_retirables(
            usuario=usuario, ofertas=ofertas)[0]
        oferta = ofertas_solicitables[0]
        # Se acccede a la url de listado de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado/'))
        # Se selecciona una oferta para solicitar
        boton_solicitud = buscar_boton_listado(self,
            id_listado = 'id_div_listado_ofertas',
            id_boton = 'button_solicitar_oferta_{}'.format(oferta.id),
            page_param = 'page')
        boton_solicitud.click()
        # Se comprueba que se está en la página de detalles de la oferta
        # Pero antes se tiene que esperar a que redirija a la página
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id))
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se busca el mensaje de éxito y se comprueba que es correcto
        message_success = self.selenium.find_element_by_class_name('alert-success')
        self.assertEqual(message_success.text, 'Se ha realizado la solicitud con éxito')
        # Se comprueba que se ha solicitado la oferta
        try:
            solicitud = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud = None
        self.assertIsNotNone(solicitud)
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de solicitar una oferta cuyos requisitos no cumple
    def test_solicita_oferta_sin_requisitos(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario3', 'usuario3')
        # Se busca una oferta que se pueda solicitar
        ofertas_solicitadas = []
        for solicitud in list(Solicitud.objects.filter(usuario=usuario).only('oferta')):
            ofertas_solicitadas.append(solicitud.oferta)
        ofertas_posibles = []
        for oferta_for in list(Oferta.objects.filter(borrador=False, vetada=False, cerrada=False)):
            ofertas_posibles.append(oferta_for)
        actividades_realizadas = Usuario.objects.get(pk=usuario.id).actividades_realizadas.all()
        # Se comprueba que no se ha solicitado antes la oferta y que se han realizado las actividades necesarias
        oferta = None
        for oferta_posible in ofertas_posibles:
            puede_solicitar = False
            # Si no se ha solicitado al oferta antes
            if not oferta_posible in ofertas_solicitadas:
                # Comprueba que se han realizado las tareas anteriores
                actividades_requisitos = oferta_posible.actividades.all()
                for actividad_requisito in actividades_requisitos:
                    if not actividad_requisito in actividades_realizadas:
                        puede_solicitar = True
                        break
                if puede_solicitar:
                    oferta = oferta_posible
                    break
        # Se acccede a la url de solicitud de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/solicitud/{}'.format(oferta.id)))
        # Se comprueba que se está en la página de detalles de la oferta
        # Pero antes se tiene que esperar a que redirija a la página
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id))
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id), self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede solicitar una oferta cuyos actividades requeridas no se han resuelto')
        # Se comprueba que se ha solicitado la oferta
        try:
            solicitud = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud = None
        self.assertIsNone(solicitud)
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de solicitar una oferta que está en modo borrador
    def test_solicita_oferta_borrador(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario3', 'usuario3')
        # Se busca una oferta que se pueda solicitar
        ofertas_solicitadas = []
        for solicitud in list(Solicitud.objects.filter(usuario=usuario).only('oferta')):
            ofertas_solicitadas.append(solicitud.oferta)
        ofertas_posibles = []
        for oferta_for in list(Oferta.objects.filter(borrador=True, vetada=False, cerrada=False)):
            ofertas_posibles.append(oferta_for)
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
        # Se acccede a la url de solicitud de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/solicitud/{}'.format(oferta.id)))
        # Se comprueba que se está en la página de listado de las ofertas
        # Pero antes se tiene que esperar a que redirija a la página
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/oferta/listado/'.format(self.live_server_url, oferta.id))
        self.assertEqual('{}/oferta/listado/'.format(self.live_server_url), self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        messages_error = self.selenium.find_elements_by_class_name('alert-danger')
        mensaje_error_correcto = False
        for mensaje_error in messages_error:
            if mensaje_error.text == 'No se puede solicitar una oferta que está en modo borrador':
                mensaje_error_correcto = True
                break
        self.assertTrue(mensaje_error_correcto)
        # Se comprueba que se ha solicitado la oferta
        try:
            solicitud = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud = None
        self.assertIsNone(solicitud)
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de solicitar una oferta que está cerrada
    def test_solicita_oferta_cerrada(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario1', 'usuario1')
        # Se busca una oferta que se pueda solicitar
        ofertas_solicitadas = []
        for solicitud in list(Solicitud.objects.filter(usuario=usuario).only('oferta')):
            ofertas_solicitadas.append(solicitud.oferta)
        ofertas_posibles = []
        for oferta_for in list(Oferta.objects.filter(borrador=False, vetada=False, cerrada=True)):
            ofertas_posibles.append(oferta_for)
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
        # Se acccede a la url de solicitud de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/solicitud/{}'.format(oferta.id)))
        # Se comprueba que se está en la página de detalles de la oferta
        # Pero antes se tiene que esperar a que redirija a la página
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id))
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede solicitar una oferta que está cerrada')
        # Se comprueba que se ha solicitado la oferta
        try:
            solicitud = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud = None
        self.assertIsNone(solicitud)
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de solicitar una oferta que está vetada
    def test_solicita_oferta_vetada(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario1', 'usuario1')
        # Se busca una oferta que se pueda solicitar
        ofertas_solicitadas = []
        for solicitud in list(Solicitud.objects.filter(usuario=usuario).only('oferta')):
            ofertas_solicitadas.append(solicitud.oferta)
        ofertas_posibles = []
        for oferta_for in list(Oferta.objects.filter(borrador=False, vetada=True, cerrada=False)):
            ofertas_posibles.append(oferta_for)
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
        # Se acccede a la url de solicitud de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/solicitud/{}'.format(oferta.id)))
        # Se comprueba que se está en la página de detalles de la oferta
        # Pero antes se tiene que esperar a que redirija a la página
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id))
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede solicitar una oferta vetada')
        # Se comprueba que se ha solicitado la oferta
        try:
            solicitud = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud = None
        self.assertIsNone(solicitud)
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de solicitar una oferta de su autoría
    def test_solicita_oferta_propia(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario1', 'usuario1')
        # Se busca una oferta que se pueda solicitar. En este caso se añade la condición de que el usuario debe ser el
        # autor de la oferta
        ofertas_solicitadas = []
        for solicitud in list(Solicitud.objects.filter(usuario=usuario).only('oferta')):
            ofertas_solicitadas.append(solicitud.oferta)
        ofertas_posibles = []
        for oferta_for in list(Oferta.objects.filter(borrador=False, vetada=False, cerrada=False, autor=usuario)):
            ofertas_posibles.append(oferta_for)
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
        # Debido a que no aparece el botón para solicitar, se introduce la url directamente
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/solicitud/{}/'.format(oferta.id)))
        # Se comprueba que se está en la página de detalles de la oferta
        # Pero antes se tiene que esperar a que redirija a la página
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id))
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se busca el mensaje de error y se comprueba que es correcto
        message_error = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_error.text, 'No se puede solicitar una oferta de la que se es autor')
        # Se comprueba que no se ha solicitado la oferta
        try:
            solicitud = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud = None
        self.assertIsNone(solicitud)
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de solicitar una oferta sin estar autenticado
    def test_solicita_oferta_sin_autenticar(self):
        # Se busca una oferta que se pueda solicitar
        ofertas_posibles = []
        for oferta_for in list(Oferta.objects.filter(borrador=False, vetada=False, cerrada=False)):
            ofertas_posibles.append(oferta_for)
        # Se comprueba que no se ha solicitado antes la oferta y que se han realizado las actividades necesarias
        oferta = ofertas_posibles[0]
        # Se acccede a la url de solicitud de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/solicitud/{}/'.format(oferta.id)))
        # Se comprueba que se está en la página de login
        self.assertEqual('{}/login/?next=/oferta/solicitud/{}/'.format(self.live_server_url, oferta.id), self.selenium.current_url)

    # Un usuario trata de solicitar una oferta que no existe
    def test_solicita_oferta_inexistente(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario1', 'usuario1')
        numero_solicitudes_antes = Solicitud.objects.all().count()
        # Se acccede a la url de solicitud de la oferta
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/solicitud/0/'))
        # Se comprueba que el mensaje de error es correcto
        message_error = self.selenium.find_element_by_class_name('alert-danger')  
        self.assertEqual(message_error.text, 'No se ha encontrado la oferta')
        # Se comprueba que no ha solicitado la oferta
        numero_solicitudes_despues = Solicitud.objects.all().count()
        self.assertEqual(numero_solicitudes_antes, numero_solicitudes_despues)
        # El usuario se desloguea
        self.logout()

    # Un usuario solicita una oferta que tiene un requisito vetado
    def test_solicita_oferta_requisito_vetado(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario2', 'usuario2')
        # Se busca una oferta que se pueda solicitar. En este caso se añade la condición de que uno de los requisitos de
        # la oferta debe estar vetado
        ofertas_solicitadas = []
        for solicitud in list(Solicitud.objects.filter(usuario=usuario).only('oferta')):
            ofertas_solicitadas.append(solicitud.oferta)
        ofertas_posibles = []
        for oferta_for in list(Oferta.objects.filter(borrador=False, vetada=False, cerrada=False)):
            ofertas_posibles.append(oferta_for)
        actividades_realizadas = Usuario.objects.get(pk=usuario.id).actividades_realizadas.all()
        # Se comprueba que no se ha solicitado antes la oferta y que se han realizado las actividades necesarias
        oferta = None
        for oferta_posible in ofertas_posibles:
            puede_solicitar = True
            actividad_vetada = False
            # Si no se ha solicitado al oferta antes
            if not oferta_posible in ofertas_solicitadas:
                # Comprueba que se han realizado las tareas anteriores
                actividades_requisitos = oferta_posible.actividades.all()
                for actividad_requisito in actividades_requisitos:
                    actividad_vetada = actividad_vetada or actividad_requisito.vetada
                    if not actividad_requisito in actividades_realizadas:
                        puede_solicitar = False
                        break
                puede_solicitar = puede_solicitar and actividad_vetada
                if puede_solicitar:
                    oferta = oferta_posible
                    break
        # Debido a que no aparece el botón para solicitar, se introduce la url directamente
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/solicitud/{}/'.format(oferta.id)))
        # Se comprueba que se está en la página de detalles de la oferta
        # Pero antes se tiene que esperar a que redirija a la página
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id))
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se busca el mensaje de error y se comprueba que es correcto
        message_error = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_error.text, 'No se puede solicitar una oferta que tiene entre sus requisitos actividades vetadas')
        # Se comprueba que no se ha solicitado la oferta
        try:
            solicitud = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud = None
        self.assertIsNone(solicitud)
        # El usuario se desloguea
        self.logout()


    
    # TESTS RETIRO SOLICITUD

    # Un usuario retira una de sus solicitudes
    def test_retira_solicitud(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario2', 'usuario2')
        # Se busca una oferta que se pueda retirar
        oferta = Solicitud.objects.filter(oferta__vetada=False, oferta__borrador=False, oferta__cerrada=False).first().oferta
        # Se acccede a la url de listado de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/listado/'))
        # Se selecciona una oferta para retirar la solicitud
        boton_retira_solicitud = buscar_boton_listado(self,
            id_listado = 'id_div_listado_ofertas',
            id_boton = 'button_retirar_solicitud_oferta_{}'.format(oferta.id),
            page_param = 'page')
        boton_retira_solicitud.click()
        # Se comprueba que se está en la página de detalles de la oferta
        # Pero antes se tiene que esperar a que redirija a la página
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(lambda driv: driv.current_url == '{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id))
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id), self.selenium.current_url)
        # Se busca el mensaje de éxito y se comprueba que es correcto
        message_success = self.selenium.find_element_by_class_name('alert-success')
        self.assertEqual(message_success.text, 'Se ha retirado la solicitud con éxito')
        # Se comprueba que se ha retirado la solicitud de la oferta
        try:
            solicitud = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud = None
        self.assertIsNone(solicitud)
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de retirar una solicitud de una oferta que no ha solicitado
    def test_retira_solicitud_sin_solicitar(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario1', 'usuario1')
        # Se busca una oferta que se pueda retirar, pero que no haya sido solicitada por el usuario
        oferta = None
        solicitudes = list(Solicitud.objects.filter(oferta__vetada=False, oferta__borrador=False, oferta__cerrada=False))
        for oferta_for in Oferta.objects.filter(vetada=False, borrador=False, cerrada=False):
            oferta = oferta_for
            for solicitud in solicitudes:
                if solicitud.oferta == oferta:
                    oferta = None
                    break
            if oferta != None:
                break
        # Se acccede a la url de retirada de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/retiro_solicitud/{}/'.format(oferta.id)))
        # Se comprueba que se está en la página de detalles de la oferta
        # Pero antes se tiene que esperar a que redirija a la página
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id))
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id), self.selenium.current_url)
        # Se busca el mensaje de error y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede retirar la solicitud de una oferta en la que no se tiene una solicitud')
        # Se comprueba que no existe la solicitud de la oferta
        try:
            solicitud = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud = None
        self.assertIsNone(solicitud)
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de retirar una solicitud de una oferta que no está vetada
    def test_retira_solicitud_oferta_vetada(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario1', 'usuario1')
        # Se busca una oferta que se pueda retirar
        oferta = Solicitud.objects.filter(oferta__vetada=True, oferta__borrador=False, oferta__cerrada=False).first().oferta
        # Se acccede a la url de listado de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/retiro_solicitud/{}/'.format(oferta.id)))
        # Se comprueba que se está en la página de detalles de la oferta
        # Pero antes se tiene que esperar a que redirija a la página
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id))
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id), self.selenium.current_url)
        # Se busca el mensaje de error y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede retirar la solicitud de una oferta vetada')
        # Se comprueba que no se ha retirado la solicitud de la oferta
        try:
            solicitud = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud = None
        self.assertIsNotNone(solicitud)
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de retirar una solicitud de una oferta que está cerrada
    def test_retira_solicitud_oferta_cerrada(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario3', 'usuario3')
        # Se busca una oferta que se pueda retirar
        oferta = Solicitud.objects.filter(oferta__vetada=False, oferta__borrador=False, oferta__cerrada=True).first().oferta
        # Se acccede a la url de listado de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/retiro_solicitud/{}/'.format(oferta.id)))
        # Se comprueba que se está en la página de detalles de la oferta
        # Pero antes se tiene que esperar a que redirija a la página
        wait_driver = WebDriverWait(self.selenium, 3)
        wait_driver.until(
            lambda driv: driv.current_url == '{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id))
        self.assertEqual('{}/oferta/detalles/{}/'.format(self.live_server_url, oferta.id),
                         self.selenium.current_url)
        # Se busca el mensaje de error y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se puede retirar la solicitud de una oferta que está cerrada')
        # Se comprueba que no se ha retirado la solicitud de la oferta
        try:
            solicitud = Solicitud.objects.get(usuario=usuario, oferta=oferta)
        except ObjectDoesNotExist as e:
            solicitud = None
        self.assertIsNotNone(solicitud)
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de retirar una solicitud de una oferta si estar autenticado
    def test_retira_solicitud_oferta_sin_autenticar(self):
        # Se inicializan las variables necesarias
        numero_solicitudes_antes = Solicitud.objects.all().count()
        # Se busca una oferta que se pueda retirar
        oferta = Solicitud.objects.filter(oferta__vetada=False, oferta__borrador=False, oferta__cerrada=False).first().oferta
        # Se acccede a la url de listado de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/retiro_solicitud/{}'.format(oferta.id)))
        # Se comprueba que redirige a la página de login
        self.assertEqual('{}/login/?next=/oferta/retiro_solicitud/{}/'.format(self.live_server_url, oferta.id), self.selenium.current_url)
        # Se comprueba que no se ha retirado la solicitud de la oferta
        numero_solicitudes_despues = Solicitud.objects.all().count()
        self.assertEqual(numero_solicitudes_despues, numero_solicitudes_antes)
        # El usuario se desloguea
        self.logout()

    # Un usuario trata de retirar una solicitud de una oferta que no existe
    def test_retira_solicitud_oferta_inexistente(self):
        # El usuario se loguea y se obtienen las variables que se van a usar en el test
        usuario = self.login('usuario1', 'usuario1')
        # Se acccede a la url de retirada de ofertas
        self.selenium.get('%s%s' % (self.live_server_url, '/oferta/retiro_solicitud/{}/'.format(0)))
        # Se comprueba que se está en la página de listado de ofertas
        self.assertEqual('{}/oferta/listado/'.format(self.live_server_url), self.selenium.current_url)
        # Se busca el mensaje de fallo y se comprueba que es correcto
        message_danger = self.selenium.find_element_by_class_name('alert-danger')
        self.assertEqual(message_danger.text, 'No se ha encontrado la oferta')
        # El usuario se desloguea
        self.logout()



    # METODOS AUXILIARES

    def script_cambiar_id_actividad_option(self, option, actividad_despues):
        self.selenium.execute_script('''
            arguments[0].value = {};
            '''.format(actividad_despues.id), option)
