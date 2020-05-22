from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from datetime import date
import re

from websecurityapp.models.perfil_models import Usuario, Anexo
from websecurityapp.test_unit.utils import test_listado

class PerfilTestCase(TestCase):
    
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



    # DETALLES

    # Un usuario accede a los detalles de su perfil
    def test_detalles_mi_perfil(self):
        # El usuario se loguea y se inicializan las variables
        username = 'usuario1'
        password = 'usuario1'
        usuario_perfil_esperado = Usuario.objects.get(django_user__username = username)
        anexos_esperados = list(Anexo.objects.filter(usuario = usuario_perfil_esperado).order_by('id'))
        actividades_realizadas_esperadas = list(usuario_perfil_esperado.actividades_realizadas.all())
        usuario_esperado = self.login(username, password)
        # Se accede al perfil del usuario
        response = self.client.get(reverse('perfil_detalles'))
        # Se obtienen los valores recibidos
        usuario_perfil_recibido = response.context['usuario_perfil']
        usuario_recibido = response.context['usuario']
        anexos_recibidos = list(response.context['anexos'])
        # Se comprueba que se ha accedido correctemente a la página de detalles del perfil y que
        # se han obtenido los datos correctos
        self.assertEqual(response.status_code, 200)
        self.assertEqual(usuario_perfil_recibido, usuario_perfil_esperado)
        self.assertEqual(usuario_recibido, usuario_esperado)
        self.assertListEqual(anexos_recibidos, anexos_esperados)
        # Se comprueba el listado de actividades realizadas
        test_listado(self,
            lista_esperada = actividades_realizadas_esperadas,
            url = reverse('perfil_detalles'),
            page_param = 'page',
            datos_esperados = dict(),
            dato_lista = 'page_obj_actividades_realizadas',
            status_code = 200)
        # El usuario se desloguea
        self.logout()

    # Un usuario accede a los detalles del perfil de otro usuario
    def test_detalles_perfil_ajeno(self):
        # El usuario se loguea y se inicializan las variables
        username = 'usuario1'
        password = 'usuario1'
        usuario_perfil_esperado = Usuario.objects.exclude(django_user__username=username).first()
        anexos_esperados = list(Anexo.objects.filter(usuario=usuario_perfil_esperado).order_by('id'))
        actividades_realizadas_esperadas = list(usuario_perfil_esperado.actividades_realizadas.filter(vetada=False))
        usuario_esperado = self.login(username, password)
        # Se accede al perfil del usuario
        response = self.client.get(reverse('perfil_detalles_ajeno', kwargs={'usuario_id': usuario_perfil_esperado.id}))
        # Se obtienen los valores recibidos
        usuario_perfil_recibido = response.context['usuario_perfil']
        anexos_recibidos = list(response.context['anexos'])
        usuario_recibido = response.context['usuario']
        # Se comprueba que se ha accedido correctemente a la página de detalles del perfil y que
        # se han obtenido los datos correctos
        self.assertEqual(response.status_code, 200)
        self.assertEqual(usuario_recibido, usuario_esperado)
        self.assertEqual(usuario_perfil_recibido, usuario_perfil_esperado)
        self.assertListEqual(anexos_recibidos, anexos_esperados)
        # Se comprueba el listado de actividades realizadas
        test_listado(self,
            lista_esperada=actividades_realizadas_esperadas,
            url=reverse('perfil_detalles_ajeno', kwargs={'usuario_id': usuario_perfil_esperado.id}),
            page_param='page',
            datos_esperados=dict(),
            dato_lista='page_obj_actividades_realizadas',
            status_code=200)
        # El usuario se desloguea
        self.logout()



    # EDICIÓN

    # Un usuario edita su perfil
    def test_editar_mi_perfil(self):
        # El usuario se loguea y se inicializan las variables
        username = 'usuario1'
        password = 'usuario1'
        nombre_usuario = 'nuevo_nombre'
        contraseña = 'nueva_contraseña'
        nombre = 'nombre'
        apellidos = 'apellidos'
        email = 'email@gmail.com'
        telefono = '123456789'
        empresa_u_equipo = 'la empresa 1'
        self.login(username, password)
        # Se accede a la edición del perfil del usuario
        response = self.client.post(reverse('perfil_edicion'), {
            'nombre_usuario': nombre_usuario,
            'contrasenna': contraseña, 
            'nombre': nombre,
            'apellidos': apellidos,
            'email': email,
            'telefono': telefono,
            'empresa_u_equipo': empresa_u_equipo
        })
        # Se obtienen los valores recibidos
        usuario_recibido = Usuario.objects.get(django_user__username = nombre_usuario)
        django_recibido = usuario_recibido.django_user
        # Se comprueba que el usuario ha sido redirido a la página de login, debido a que al
        # editarse un usuario el sistema lo desloguea. Se comprueba además que el usuario ha
        # sido editado correctamente
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))
        self.assertEqual(django_recibido.first_name, nombre)
        self.assertEqual(django_recibido.last_name, apellidos)
        self.assertEqual(django_recibido.email, email)
        self.assertEqual(usuario_recibido.telefono, telefono)
        self.assertEqual(usuario_recibido.empresa_u_equipo, empresa_u_equipo)
        # El usuario se desloguea
        self.logout()
        # Para comprobar que se han guardado bien el nombre de usuario y contraseña, 
        # se vuelve a producir el login y se observa que no hay problemas
        response = self.login(nombre_usuario, contraseña)
        response = self.client.get(reverse('perfil_detalles'))
        self.assertEqual(response.status_code, 200)
        # El usuario se vuelve a desloguear
        self.logout()

    # Un usuario edita su perfil sin estar autenticado
    def test_editar_mi_perfil_sin_autenticar(self):
        # Se inicializan las variables
        nombre_usuario = 'nuevo_nombre'
        contraseña = 'nueva_contraseña'
        nombre = 'nombre'
        apellidos = 'apellidos'
        email = 'email@gmail.com'
        telefono = '123456789'
        empresa_u_equipo = 'la empresa 1'
        # Se accede a la edición del perfil del usuario
        response = self.client.post(reverse('perfil_edicion'), {
            'nombre_usuario': nombre_usuario,
            'contrasenna': contraseña, 
            'nombre': nombre,
            'apellidos': apellidos,
            'email': email,
            'telefono': telefono,
            'empresa_u_equipo': empresa_u_equipo
        })
        # Se compueba que se ha redirigido al usuario a la página de login  puesto a que hay que
        # estar autenticado para editar el perfil
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/perfil/edicion/')

    # Un usuario edita su perfil insertando datos incorrectos
    def test_editar_mi_perfil_incorrecto(self):
        # El usuario se loguea y se inicializan las variables
        username = 'usuario1'
        password = 'usuario1'
        usuario_antes = Usuario.objects.get(django_user__username = username)
        django_antes = usuario_antes.django_user
        nombre_usuario = 'nuevo_nombre'
        contraseña = 'nueva_contraseña'
        nombre = 'nombre'
        apellidos = 'apellidos'
        email = 'emailgmailcom'
        telefono = '123456789'
        empresa_u_equipo = 'la empresa 1'
        self.login(username, password)
        # Se accede a la edición del perfil del usuario
        response = self.client.post(reverse('perfil_edicion'), {
            'nombre_usuario': nombre_usuario,
            'contrasenna': contraseña, 
            'nombre': nombre,
            'apellidos': apellidos,
            'email': email,
            'telefono': telefono,
            'empresa_u_equipo': empresa_u_equipo
        })
        # Se comprueba que el usuario permanece en le formulario debido a que hba sucedido un
        # error de validación y que se ha obtenido el formualrio correctamente
        self.assertEqual(response.status_code, 200)
        # Se comprueba que ninguno de los valores del usuario han cambiado
        usuario_despues = Usuario.objects.get(django_user__username = username)
        django_despues = usuario_despues.django_user
        self.assertEqual(django_antes.username, django_despues.username)
        self.assertEqual(django_antes.password, django_despues.password)
        self.assertEqual(django_antes.first_name, django_despues.first_name)
        self.assertEqual(django_antes.last_name, django_despues.last_name)
        self.assertEqual(django_antes.email, django_despues.email)
        self.assertEqual(usuario_antes.telefono, usuario_despues.telefono)
        self.assertEqual(usuario_antes.empresa_u_equipo, usuario_despues.empresa_u_equipo)
        # El usuario se desloguea
        self.logout()



    # ADICIÓN DE ANEXOS

    # Un usuario añade un anexo a su perfil
    def test_añadir_anexo(self):
        # El usuario se loguea y se inicializan las variables
        username = 'usuario1'
        password = 'usuario1'
        usuario = Usuario.objects.get(django_user__username = username)
        anexo = 'http://nuevoanexotesting.com'
        numero_anexos_antes = Anexo.objects.filter(usuario = usuario).count()
        self.login(username, password)
        # Se accede a la creación de anexos
        response = self.client.post(reverse('anexo_creacion'), {
            'anexo': anexo
        })
        # Se obtienen los valores recibidos
        anexos_recibidos = Anexo.objects.filter(usuario = usuario)
        numero_anexos_despues = Anexo.objects.filter(usuario = usuario).count()
        anexo_creado = Anexo.objects.filter(usuario = usuario).order_by('-id').first()
        # Se comprueba que se ha creado el anexo correctamente y que el usuario ha sido redirigido a los detalles
        # de la actividad
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('perfil_detalles'))
        self.assertEquals(numero_anexos_antes + 1, numero_anexos_despues)
        self.assertEquals(anexo_creado in anexos_recibidos, True)
        self.assertEqual(anexo_creado.usuario, usuario)
        self.assertEqual(anexo_creado.anexo, anexo)
        # El usuario se desloguea
        self.logout()

    # Un usuario añade un anexo a su perfil sin estar autenticado
    def test_añadir_anexo_sin_autenticar(self):
        # Se inicializan las variables
        anexo = 'http://nuevoanexotesting.com'
        numero_anexos_antes = Anexo.objects.all().count()
        # Se accede a la creación de anexos
        response = self.client.post(reverse('anexo_creacion'), {
            'anexo': anexo
        })
        # Se obtienen los valores recibidos
        numero_anexos_despues = Anexo.objects.all().count()
        # Se comprueba que no se ha creado ningún anexo y que se ha redirigido al usuario al login, puesto a que hay 
        # que estar autenticado para crear un nuevo anexo 
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/anexo/creacion_edicion/')
        self.assertEquals(numero_anexos_antes, numero_anexos_despues)

    # Un usuario añade un anexo a su perfil usando datos incorrectos
    def test_añadir_anexo_incorrecto(self):
        # El usuario se loguea y se inicializan las variables
        username = 'usuario1'
        password = 'usuario1'
        usuario = Usuario.objects.get(django_user__username = username)
        anexo = 'nuevoanexotesting'
        numero_anexos_antes = Anexo.objects.filter(usuario = usuario).count()
        self.login(username, password)
        # Se accede a la creación de anexos
        response = self.client.post(reverse('anexo_creacion'), {
            'anexo': anexo
        })
        # Se obtienen los valores recibidos
        numero_anexos_despues = Anexo.objects.filter(usuario = usuario).count()
        # Se comprueba que el usuario permanece en el formulario de creación de anexos y que ha accedido correctamente, 
        # puesto a que ha insertado datos no válidos. Se comprueba además que no se ha creado ningún nuevo anexo.
        self.assertEqual(response.status_code, 200)
        self.assertEquals(numero_anexos_antes, numero_anexos_despues)
        # El usuario se desloguea
        self.logout()



    # EDICIÓN DE ANEXOS

    # El usuario edita un anexo de su perfil
    def test_editar_anexo(self):
        # El usuario se loguea y se inicializan las variables
        username = 'usuario1'
        password = 'usuario1'
        usuario = Usuario.objects.get(django_user__username = username)
        anexo_dado = Anexo.objects.filter(usuario = usuario).first()
        anexo = 'http://editadoanexotesting.com'
        self.login(username, password)
        # Se accede a la edición del anexo
        response = self.client.post(reverse('anexo_edicion', kwargs = {'anexo_id': anexo_dado.id}), {
            'anexo': anexo
        })
        # Se obtienen los valores recibidos
        anexo_recibido = Anexo.objects.get(pk = anexo_dado.id)
        # Se comprueba que el usuario es redirigido a los detalles del perfil y que el anexo ha sido editado correctamente
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('perfil_detalles'))
        self.assertEquals(anexo_recibido.anexo, anexo)
        # El usuario se desloguea
        self.logout()

    # El usuario edita un anexo que no existe
    def test_editar_anexo_inexistente(self):
        # El usuario se loguea y se inicializan las variables
        username = 'usuario1'
        password = 'usuario1'
        usuario = Usuario.objects.get(django_user__username = username)
        anexo = 'http://editadoanexotesting.com'
        self.login(username, password)
        # Se accede a la edición del anexo
        response = self.client.post(reverse('anexo_edicion', kwargs = {'anexo_id': 0}), {
            'anexo': anexo
        })
        # Se comprueba que el usuario ha sido redirigido a los detalles del perfil, puesto a que no se puede editar un
        # anexo que no existe
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('perfil_detalles'))
        # El usuario se desloguea
        self.logout()

    # El usuario edita un anexo sin estar autenticado
    def test_editar_anexo_sin_autenticar(self):
        # El usuario se loguea y se inicializan las variables
        anexo_dado = Anexo.objects.all().first()
        anexo = 'http://editadoanexotesting.com'
        # Se accede a la edicón del perfil del usuario
        response = self.client.post(reverse('anexo_edicion', kwargs = {'anexo_id': anexo_dado.id}), {
            'anexo': anexo
        })
        # Se obtienen las variables de salida
        anexo_recibido = Anexo.objects.get(pk = anexo_dado.id)
        # Se comprueba que se ha redirigido al usuario a la página de login, puesto a que no está autenticado, y que no
        # se han producido cambios en el anexo
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/anexo/creacion_edicion/{}/'.format(anexo_dado.id))
        self.assertEqual(anexo_dado.anexo, anexo_recibido.anexo)
        self.assertEqual(anexo_dado.usuario, anexo_recibido.usuario)
        # El usuario se desloguea
        self.logout()

    # Un usuario edita un anexo que no le pertenece
    def test_editar_anexo_ajeno(self):
        # El usuario se loguea y se inicializan las variables
        username = 'usuario1'
        password = 'usuario1'
        usuario = Usuario.objects.get(django_user__username = username)
        anexo_dado = Anexo.objects.exclude(usuario = usuario).first()
        anexo = 'http://editadoanexotesting.com'
        self.login(username, password)
        # Se accede a la edición del anexo
        response = self.client.post(reverse('anexo_edicion', kwargs = {'anexo_id': anexo_dado.id}), {
            'anexo': anexo
        })
        # Se obtienen las variables de salida
        anexo_recibido = Anexo.objects.get(pk = anexo_dado.id)
        # Se comprueba que el usuario es redirigido a los detalles del perfil y que el anexo no ha sufrido cambios. 
        # Esto se debe a que un usuario no puede editar un anexo que no le pertenezca
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('perfil_detalles'))
        self.assertEqual(anexo_dado.anexo, anexo_recibido.anexo)
        self.assertEqual(anexo_dado.usuario, anexo_recibido.usuario)
        # El usuario se desloguea
        self.logout()

    # Un usuario edita un anexo introduciendo vaalores incorrectos
    def test_editar_anexo_incorrecto(self):
        # El usuario se loguea y se inicializan las variables
        username = 'usuario1'
        password = 'usuario1'
        usuario = Usuario.objects.get(django_user__username = username)
        anexo_dado = Anexo.objects.filter(usuario = usuario).first()
        anexo = 'editadoanexotesting'
        self.login(username, password)
        # Se accede a la edicón del perfil del usuario
        response = self.client.post(reverse('anexo_edicion', kwargs = {'anexo_id': anexo_dado.id}), {
            'anexo': anexo
        })
        # Se obtienen los valores recibidos
        anexo_recibido = Anexo.objects.get(pk = anexo_dado.id)
        # Se comprueba que el usuario permanece correctamente en el formulario y que el anexo no ha sufrido cambios, 
        # debido a que se ha producido un error de validación
        self.assertEqual(response.status_code, 200)
        self.assertEquals(anexo_recibido.anexo, anexo_dado.anexo)
        self.assertEqual(anexo_recibido.usuario, anexo_dado.usuario)
        # El usuario se desloguea
        self.logout()



    # ELIMINACIÓN DE ANEXOS

    # Un usuario elimina un anexo
    def test_eliminar_anexo(self):
        # El usuario se loguea y se inicializan las variables
        username = 'usuario1'
        password = 'usuario1'
        usuario = Usuario.objects.get(django_user__username = username)
        anexo_dado = Anexo.objects.filter(usuario = usuario).first()
        numero_anexos_antes = Anexo.objects.count()
        self.login(username, password)
        # Se accede a la eliminación del anexo
        response = self.client.get(reverse('anexo_eliminacion', kwargs = {'anexo_id': anexo_dado.id}))
        # Se obtienen los valores recibidos. Para saber si el anexo ha sido eliminado o no se  trata de captura la 
        # excepción que se produce al tratar de conseguir una entidad que no existe
        anexo_eliminado = False
        try:
            anexo_recibido = Anexo.objects.get(pk = anexo_dado.id)
        except ObjectDoesNotExist as e:
            anexo_eliminado = True
        numero_anexos_despues = Anexo.objects.count()
        # Se comprueba que el usuario ha sido redirigido a los detalles de su perfil y que el anexo ha sido eliminado
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse('perfil_detalles'))
        self.assertEquals(anexo_eliminado, True)
        self.assertEquals(numero_anexos_antes, numero_anexos_despues + 1)
        # El usuario se desloguea
        self.logout()

    # Un usuario elimina un anexo que no existe
    def test_eliminar_anexo_inexistente(self):
        # El usuario se loguea y se inicializan las variables
        username = 'usuario1'
        password = 'usuario1'
        usuario = Usuario.objects.get(django_user__username = username)
        self.login(username, password)
        # Se accede a la eliminación del anexo
        response = self.client.get(reverse('anexo_eliminacion', kwargs = {'anexo_id': 0}))
        # Se comprueba que el usuario ha sido redirigido a los detalles del perfil, puesto a que no se puede eliminar un
        # anexo que no existe
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('perfil_detalles'))
        # El usuario se desloguea
        self.logout()

    # Un usuario elimina un anexo sin estar autenticado 
    def test_eliminar_anexo_sin_autenticar(self):
        # El usuario se loguea y se inicializan las variables
        anexo_dado = Anexo.objects.all().first()
        numero_anexos_antes = Anexo.objects.count()
        # Se accede a la elimainción del anexo
        response = self.client.get(reverse('anexo_eliminacion', kwargs = {'anexo_id': anexo_dado.id}))
        # Se obtienen los valores recibidos. Para saber si el anexo ha sido eliminado o no se  trata de captura la 
        # excepción que se produce al tratar de conseguir una entidad que no existe
        anexo_eliminado = False
        try:
            anexo_recibido = Anexo.objects.get(pk = anexo_dado.id)
        except ObjectDoesNotExist as e:
            anexo_eliminado = True
        numero_anexos_despues = Anexo.objects.count()
        # Se comprueba que el usuario ha sido redirigido a la página de login y que el anexo no ha sido eliminado. Esto
        # se debe a que el usuario debe estar autenticado para eliminar un anexo.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/anexo/eliminacion/{}/'.format(anexo_dado.id))
        self.assertEqual(anexo_eliminado, False)
        self.assertEqual(numero_anexos_antes, numero_anexos_despues)

    # Un usuario elimina un anexo que no le pertenece
    def test_eliminar_anexo_ajeno(self):
        # El usuario se loguea
        username = 'usuario1'
        password = 'usuario1'
        usuario = self.login(username, password)
        numero_anexos_antes = Anexo.objects.count()
        # Se inicializan las variables necesarias para el test
        anexo_dado = Anexo.objects.exclude(usuario = usuario).first()
        # Se accede a la edicón del perfil del usuario
        response = self.client.get(reverse('anexo_eliminacion', kwargs = {'anexo_id': anexo_dado.id}))
        # Se obtienen los valores recibidos. Para saber si el anexo ha sido eliminado o no se  trata de captura la 
        # excepción que se produce al tratar de conseguir una entidad que no existe
        anexo_eliminado = False
        try:
            anexo_recibido = Anexo.objects.get(pk = anexo_dado.id)
        except ObjectDoesNotExist as e:
            anexo_eliminado = True
        numero_anexos_despues = Anexo.objects.count()
        # Se comprueba que el usuario ha sido redirigido a los detalles del perfil y que el anexo no ha sido eliminado.
        # Esto se debe a que un usuario no puede eliminar un anexo que no le pertenece.
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse('perfil_detalles'))
        self.assertEquals(anexo_eliminado, False)
        self.assertEquals(numero_anexos_antes, numero_anexos_despues)
        # El usuario se desloguea
        self.logout()

