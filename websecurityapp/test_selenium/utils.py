from django.db.models import Q, OuterRef, Exists
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait

from websecurityapp.models.oferta_models import Oferta, Solicitud
from websecurityapp.test_unit.utils import paginar_lista
from websecurityapp.views.utils import get_ofertas_solicitables_y_ofertas_retirables, tiene_actividad_vetada


def evaluar_columnas_listado_actividades(test_case, actividades_esperadas, usuario, resalta_resueltas, page_param, **kwargs):
    try:
        parent_element = test_case.selenium.find_element_by_id(kwargs['parent_element'])
    except KeyError as e:
        parent_element = test_case.selenium
    # Organizar las actividades esperadas por paginas
    dict_actividades_paginadas = paginar_lista(actividades_esperadas)
    # Por cada pagina se evaluan las actividades que deben aparecer en la pagina
    for index_dict_actividades in dict_actividades_paginadas.keys():
        i = 2
        # Por cada una de las actividades que debe aparecer
        for actividad in dict_actividades_paginadas[index_dict_actividades]:
            fila = parent_element.find_element_by_xpath('//tr[{}]'.format(i))
            # Si la actividad está vetada, debe aparecer con un background rojizo
            if actividad.vetada:
                test_case.assertEqual(fila.value_of_css_property('background-color'), 'rgba(255, 0, 0, 0.4)')
            # Si la actividad está resuelta y no vetada, entonces el background es verdoso
            # Esto solo se aplica cuando no se estan listando las propias ofertas
            elif actividad in usuario.actividades_realizadas.all() and resalta_resueltas:
                test_case.assertEqual(fila.value_of_css_property('background-color'), 'rgba(0, 255, 0, 0.4)')
            # Se comprueba el título
            titulo = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[1]'.format(i)).text
            test_case.assertEqual(titulo, actividad.titulo)
            # Se comprueba las descripción
            descripcion = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[2]'.format(i)).text
            test_case.assertEqual(descripcion, actividad.descripcion)
            # Se comprueba la fecha de creación
            fecha_creacion = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[3]'.format(i)).text
            test_case.assertEqual(fecha_creacion, actividad.fecha_creacion.strftime('%d/%m/%Y'))
            # Se comprueba el autor
            autor = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[4]'.format(i)).text
            test_case.assertEqual(autor, '{} {}'.format(actividad.autor.django_user.first_name,
                actividad.autor.django_user.last_name))
            # Se comprueba que está el botón de detalles
            boton_detalles = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[5]/child::button'.format(i))
            test_case.assertEqual(boton_detalles.get_attribute('onclick'),
                'window.location.href = \'/actividad/detalles/{}/\''.format(actividad.id))
            j = 6
            # Se comprueba que esté el botón de editar si procede
            try:
                boton_editar = parent_element.find_element_by_xpath(
                    '//tbody/child::tr[{}]/child::td[{}]/child::button'.format(i, j))
                if usuario == actividad.autor and actividad.borrador:
                    test_case.assertEqual(boton_editar.get_attribute('onclick'),
                        'window.location.href = \'/actividad/edicion/{}/\''.format(actividad.id))
                    boton_editar = True
                    j = j + 1
                else:
                    test_case.assertEqual(
                        boton_editar.get_attribute('onclick') == 'window.location.href = \'/actividad/edicion/{}/\''.format(
                            actividad.id), False)
                    boton_editar = False
            except NoSuchElementException:
                boton_editar = False
            test_case.assertEqual(usuario == actividad.autor and actividad.borrador, boton_editar)
            # Se comprueba que está el botón de eliminar si procede
            try:
                boton_eliminar = parent_element.find_element_by_xpath(
                    '//tbody/child::tr[{}]/child::td[{}]/child::button'.format(i, j))
                if usuario == actividad.autor and actividad.borrador:
                    test_case.assertEqual(boton_eliminar.get_attribute('onclick'),
                        'alerta_redireccion(\'Desea eliminar esta actividad ?\', \'/actividad/eliminacion/{}/\')'.format(
                        actividad.id))
                    boton_eliminar = True
                    j = j + 1
                else:
                    test_case.assertEqual(boton_eliminar.get_attribute(
                        'onclick') == 'alerta_redireccion(\'Desea eliminar esta actividad ?\', \'/actividad/eliminacion/{}/\')'.format(
                        actividad.id), False)
                    boton_eliminar = False
            except NoSuchElementException:
                boton_eliminar = False
            test_case.assertEqual(usuario == actividad.autor and actividad.borrador, boton_eliminar)
            # Se comprueba que está el botón de vetar si procede
            try:
                boton_veto = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[{}]/child::button'.format(i, j))
                if usuario.es_admin and not actividad.borrador and not actividad.vetada:
                    test_case.assertEqual(boton_veto.get_attribute('onclick'),
                                          'window.location.href = \'/actividad/veto/{}/\''.format(actividad.id))
                    boton_veto = True
                    j = j + 1
                else:
                    test_case.assertEqual(
                        boton_veto.get_attribute('onclick') == 'window.location.href = \'/actividad/veto/{}/\''.format(
                            actividad.id), False)
                    boton_veto = False
            except NoSuchElementException:
                boton_veto = False
            test_case.assertEqual(usuario.es_admin and not actividad.borrador and not actividad.vetada, boton_veto)
            # Se comprueba que está el botón de levantar veto si procede
            try:
                boton_levanta_veto = parent_element.find_element_by_xpath(
                    '//tbody/child::tr[{}]/child::td[{}]/child::button'.format(i, j))
                if usuario.es_admin and not actividad.borrador and actividad.vetada:
                    test_case.assertEqual(boton_levanta_veto.get_attribute('id'),
                        'button_levantar_veto_{}'.format(actividad.id))
                    boton_levanta_veto = True
                    j = j + 1
                else:
                    test_case.assertEqual(boton_levanta_veto.get_attribute('id'),
                                          'button_levantar_veto_{}'.format(actividad.id), False)
                    boton_levanta_veto = False
            except NoSuchElementException:
                boton_levanta_veto = False
            test_case.assertEqual(usuario.es_admin and not actividad.borrador and actividad.vetada, boton_levanta_veto)
            i = i + 1
        # Una vez se ha evaluado el listado de una página se pasa a la siguiente, y así hasta el final
        if not index_dict_actividades == len(dict_actividades_paginadas.keys()):
            parent_element.find_element_by_id('id_{}_siguiente'.format(page_param)).click()
            # Refresca la referencia al parent element tras cambiar de paǵina
            try:
                parent_element = test_case.selenium.find_element_by_id(kwargs['parent_element'])
            except KeyError as e:
                parent_element = test_case.selenium

def evaluar_columnas_listado_oferta(test_case, oferta_esperadas, usuario, listado_propio, page_param, **kwargs):
    try:
        parent_element = test_case.selenium.find_element_by_id(kwargs['parent_element'])
    except KeyError as e:
        parent_element = test_case.selenium
    # Organizar las actividades esperadas por paginas
    dict_ofertas_paginadas = paginar_lista(oferta_esperadas)
    # Por cada pagina se evaluan las actividades que deben aparecer en la pagina
    for index_dict_ofertas in dict_ofertas_paginadas.keys():
        i = 2
        if listado_propio:
            ofertas = Oferta.objects.filter(autor=usuario).distinct().order_by('id')
        else:
            if usuario.es_admin:
                ofertas = list(Oferta.objects.exclude((Q(cerrada=True) | Q(borrador=True)) & ~Q(autor=usuario)))
            else:
                ofertas = list(Oferta.objects.annotate(actividades_vetadas=Exists(
                    Oferta.objects.filter(id=OuterRef('id'), actividades__vetada=True))
                ).exclude((Q(cerrada=True) | Q(borrador=True) | Q(vetada=True) | Q(actividades_vetadas=True)) & ~Q(autor=usuario)
                ).order_by('id'))
        [ofertas_solicitables, ofertas_retirables] = get_ofertas_solicitables_y_ofertas_retirables(usuario, oferta_esperadas)
        # Por cada una de las oferta que debe aparecer
        for oferta in dict_ofertas_paginadas[index_dict_ofertas]:
            # Se comprueba el backgorund-color de las filas
            fila = parent_element.find_element_by_xpath('//tr[{}]'.format(i))
            # Si la oferta está cerrada o vetaada el background color el rojizo
            if oferta.vetada or oferta.cerrada or tiene_actividad_vetada(oferta):
                test_case.assertEqual(fila.value_of_css_property('background-color'), 'rgba(255, 0, 0, 0.4)')
            # Si el usuario puede solicitar la oferta, entonces el background es verdoso
            elif oferta in ofertas_solicitables and not listado_propio:
                test_case.assertEqual(fila.value_of_css_property('background-color'), 'rgba(0, 255, 0, 0.4)')
            # Se comprueba el título
            titulo = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[1]'.format(i)).text
            test_case.assertEqual(titulo, oferta.titulo)
            # Se comprueba las descripción
            descripcion = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[2]'.format(i)).text
            test_case.assertEqual(descripcion, oferta.descripcion)
            # Se comprueba la fecha de creación
            fecha_creacion = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[3]'.format(i)).text
            test_case.assertEqual(fecha_creacion, oferta.fecha_creacion.strftime('%d/%m/%Y'))
            # Se comprueba el autor
            autor = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[4]'.format(i)).text
            test_case.assertEqual(autor, '{} {}'.format(oferta.autor.django_user.first_name, oferta.autor.django_user.last_name))
            # Se comprueba que está el botón de detalles
            boton_detalles = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[5]/child::button'.format(i))
            test_case.assertEqual(boton_detalles.get_attribute('onclick'), 'window.location.href = \'/oferta/detalles/{}/\''.format(oferta.id))
            j = 6
            # Se comprueba que esté el botón de editar si procede
            try:
                boton_editar = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[{}]/child::button'.format(i, j))
                if usuario == oferta.autor and oferta.borrador:
                    test_case.assertEqual(boton_editar.get_attribute('onclick'), 'window.location.href = \'/oferta/edicion/{}/\''.format(oferta.id))
                    boton_editar = True
                    j = j + 1
                else:
                    test_case.assertEqual(boton_editar.get_attribute('onclick') == 'window.location.href = \'/oferta/edicion/{}/\''.format(oferta.id), False)
                    boton_editar = False
            except NoSuchElementException:
                boton_editar = False
            test_case.assertEqual(usuario == oferta.autor and oferta.borrador, boton_editar)
            # Se comprueba que está el botón de eliminar si procede
            try:
                boton_eliminar = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[{}]/child::button'.format(i, j))
                if usuario == oferta.autor and oferta.borrador:
                    test_case.assertEqual(boton_eliminar.get_attribute('onclick'), 'alerta_redireccion(\'Desea eliminar esta oferta ?\', \'/oferta/eliminacion/{}/\')'.format(oferta.id))
                    boton_eliminar = True
                    j = j + 1
                else:
                    test_case.assertEqual(boton_eliminar.get_attribute('onclick') == 'alerta_redireccion(\'Desea eliminar esta oferta ?\', \'/oferta/eliminacion/{}/\')'.format(oferta.id), False)
                    boton_eliminar = False
            except NoSuchElementException:
                boton_eliminar = False
            test_case.assertEqual(usuario == oferta.autor and oferta.borrador, boton_eliminar)
            # Se comprueba que está el botón de cerrar si procede
            try:
                boton_cierre = parent_element.find_element_by_xpath(
                    '//tbody/child::tr[{}]/child::td[{}]/child::button'.format(i, j))
                if usuario==oferta.autor and not oferta.borrador and not oferta.vetada and not oferta.cerrada:
                    test_case.assertEqual(boton_cierre.get_attribute('onclick'), 'alerta_redireccion(\'Desea cerrar esta oferta ?\', \'/oferta/cierre/{}/\')'.format(oferta.id))
                    boton_cierre = True
                    j = j + 1
                else:
                    test_case.assertNotEqual(boton_cierre.get_attribute('onclick'), 'alerta_redireccion(\'Desea cerrar esta oferta ?\', \'/oferta/cierre/{}/\')'.format(oferta.id))
                    boton_cierre = False
            except NoSuchElementException:
                boton_cierre = False
            test_case.assertEqual(usuario == oferta.autor and not oferta.borrador and not oferta.vetada and not oferta.cerrada, boton_cierre)
            # Se comprueba que está el botón de vetar si procede
            try:
                boton_veto = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[{}]/child::button'.format(i, j))
                if usuario.es_admin and not oferta.borrador and not oferta.vetada:
                    test_case.assertEqual(boton_veto.get_attribute('onclick'), 'window.location.href = \'/oferta/veto/{}/\''.format(oferta.id))
                    boton_veto = True
                    j = j + 1
                else:
                    test_case.assertEqual(boton_veto.get_attribute('onclick') == 'window.location.href = \'/oferta/veto/{}/\''.format(oferta.id), False)
                    boton_veto = False
            except NoSuchElementException:
                boton_veto = False
            test_case.assertEqual(usuario.es_admin and not oferta.borrador and not oferta.vetada and not oferta.cerrada, boton_veto)
            # Se comprueba que está el botón de levantar veto si procede
            try:
                boton_levanta_veto = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[{}]/child::button'.format(i, j))
                if usuario.es_admin and not oferta.borrador and oferta.vetada:
                    test_case.assertEqual(boton_levanta_veto.get_attribute('id'), 'button_levantar_veto_{}'.format(oferta.id))
                    boton_levanta_veto = True
                    j = j + 1
                else:
                    test_case.assertEqual(boton_levanta_veto.get_attribute('id') == 'button_levantar_veto_{}'.format(oferta.id), False)
                    boton_levanta_veto = False
            except NoSuchElementException:
                boton_levanta_veto = False
            test_case.assertEqual(usuario.es_admin and not oferta.borrador and oferta.vetada, boton_levanta_veto)
            # Si no es el listado de ofertas propias, pueden aparecer los botones relacionados con las solicitudes
            if not listado_propio:
                # Se comprueba que está el botón de solicitar la oferta, si procede
                existe_boton_solicitud = True
                try:
                    boton_solicitud = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[{}]/child::button'.format(i, j))
                    if oferta in ofertas_solicitables:
                        test_case.assertEqual(boton_solicitud.get_attribute('id'), 'button_solicitar_oferta_{}'.format(oferta.id))
                        j = j + 1
                    else:
                        test_case.assertEqual(boton_solicitud.get_attribute('id') == 'button_solicitar_oferta_{}'.format(oferta.id), False)
                        existe_boton_solicitud = False
                except NoSuchElementException:
                    existe_boton_solicitud = False
                test_case.assertEqual(oferta in ofertas_solicitables, existe_boton_solicitud)
                # Se comprueba que está el botón de retirar la oferta, si procede
                existe_boton_retiro_solicitud = True
                try:
                    boton_retiro_solicitud = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[{}]/child::button'.format(i, j))
                    if oferta in ofertas_retirables:
                        test_case.assertEqual(boton_retiro_solicitud.get_attribute('id'), 'button_retirar_solicitud_oferta_{}'.format(oferta.id))
                        j = j + 1
                    else:
                        test_case.assertEqual(boton_retiro_solicitud.get_attribute('id') == 'button_retirar_solicitud_oferta_{}'.format(oferta.id), False)
                        existe_boton_retiro_solicitud = False
                except NoSuchElementException:
                    existe_boton_retiro_solicitud = False
                test_case.assertEqual(oferta in ofertas_retirables, existe_boton_retiro_solicitud)
            i = i + 1
        # Una vez se ha evaluado el listado de una página se pasa a la siguiente, y así hasta el final
        if not index_dict_ofertas == len(dict_ofertas_paginadas.keys()):
            parent_element.find_element_by_id('id_{}_siguiente'.format(page_param)).click()
            try:
                parent_element = test_case.selenium.find_element_by_id(kwargs['parent_element'])
            except KeyError as e:
                parent_element = test_case.selenium

def evaluar_columnas_listado_usuario(test_case, usuarios_esperados, usuario, page_param, **kwargs):
    try:
        parent_element = test_case.selenium.find_element_by_id(kwargs['parent_element'])
    except KeyError as e:
        parent_element = test_case.selenium
    # Organizar las usuarios esperadas por paginas
    dict_usuarios_paginados = paginar_lista(usuarios_esperados)
    # Por cada pagina se evaluan las usuarios que deben aparecer en la pagina
    for index_dict_usuarios in dict_usuarios_paginados.keys():
        i = 2
        filas = parent_element.find_elements_by_tag_name('tr')
        # Por cada una de las usuarios que debe aparecer
        for usuario in dict_usuarios_paginados[index_dict_usuarios]:
            datos_fila = filas[i - 1].find_elements_by_tag_name('td')
            # Se comprueba el nombre de usuario
            # username = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[1]'.format(i)).text
            username = datos_fila[0].text
            test_case.assertEqual(username, usuario.django_user.username)
            # Se comprueba el nombre
            # nombre = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[2]'.format(i)).text
            nombre = datos_fila[1].text
            test_case.assertEqual(nombre, usuario.django_user.first_name)
            # Se comprueban los apellidos
            # apellidos = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[3]'.format(i)).text
            apellidos = datos_fila[2].text
            test_case.assertEqual(apellidos, usuario.django_user.last_name)
            # Se comprueba el email
            # email = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[4]'.format(i)).text
            email = datos_fila[3].text
            test_case.assertEqual(email, usuario.django_user.email)
            # Se comprueba que está el botón de detalles de perfil de usuario
            # boton_detalles = parent_element.find_element_by_xpath('//tbody/child::tr[{}]/child::td[5]/child::button'.format(i))
            boton_detalles = datos_fila[4].find_element_by_tag_name('button')
            test_case.assertEqual(boton_detalles.get_attribute('onclick'),
                'window.location.href = \'/perfil/detalles_ajeno/{}/\''.format(usuario.id))
            j = 6
            i = i + 1
        # Una vez se ha evaluado el listado de una página se pasa a la siguiente, y así hasta el final
        if not index_dict_usuarios == len(dict_usuarios_paginados.keys()):
            parent_element.find_element_by_id('id_{}_siguiente'.format(page_param)).click()
            try:
                parent_element = test_case.selenium.find_element_by_id(kwargs['parent_element'])
            except KeyError as e:
                parent_element = test_case.selenium

# Obtiene los botones para la paginación
def get_botones(element, boton, page_param):
    if boton == 'primera':
        return element.find_element_by_id('id_{}_primera'.format(page_param))
    elif boton == 'anterior':
        return element.find_element_by_id('id_{}_anterior'.format(page_param))
    elif boton == 'siguiente':
        return element.find_element_by_id('id_{}_siguiente'.format(page_param))
    elif boton == 'ultima':
        return element.find_element_by_id('id_{}_ultima'.format(page_param))
    else:
        return None

# Busca un elemento en función de su id e indica si está presente
def aparece_elemento_por_id(element, id):
    try:
        element.find_element_by_id(id)
        return True
    except NoSuchElementException:
        return False

# Dados el id de un boton y un listado, busca ese botón dentro de las páginas del listado dado
def buscar_boton_listado(test_case, id_listado, id_boton, page_param, **kwargs):
    boton = None
    # Miestras no se haya hallado el botón
    while not boton:
        # Busca el elemento pagre indicado
        try:
            parent_element = test_case.selenium.find_element_by_id(kwargs['parent_element'])
        except KeyError as e:
            parent_element = test_case.selenium
        # Busca el listado y la sección de paginación
        listado = parent_element.find_element_by_id(id_listado)
        pagination = listado.find_element_by_id('id_pagination')
        # Busca el botón para pasar paǵina
        try:
            boton_siguiente = pagination.find_element_by_id('id_{}_siguiente'.format(page_param))
        except NoSuchElementException as e:
            boton_siguiente = None
        # Busca el botón objetivo
        try:
            return listado.find_element_by_id(id_boton)
        except NoSuchElementException as e:
            boton = None
        # Si no encuentra el boton objetivo y encuentra el de página siguiente, entonces pasa la página
        if not boton and boton_siguiente:
            boton_siguiente.click()
        else:
            return None





