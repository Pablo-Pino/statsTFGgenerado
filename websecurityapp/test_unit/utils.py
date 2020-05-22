from django.core.paginator import Page
from django.db.models.query import QuerySet

from websecurityserver.settings import numero_objetos_por_pagina

# Comprueba los elementos del listado, pasando las páginas del listado
def test_listado(test_case, lista_esperada, url, page_param, datos_esperados, dato_lista, status_code):
    # Se haya el numero de paginas
    n_paginas = numero_paginas(lista_esperada)
    # Por cada pagina se comprueba el listado asociado
    for n_pagina in range(1, n_paginas + 1):
        # Se obtienen los datos de la lista
        datos_esperados[dato_lista] = lista_esperada[(n_pagina-1) * numero_objetos_por_pagina
            : n_pagina * numero_objetos_por_pagina]
        # Se manda la solicitud a través de la url
        response = test_case.client.get('{}?{}={}'.format(url, page_param, n_pagina))
        # Se comprueban los datos recibidos
        test_case.assertEqual(status_code, response.status_code)
        for key in datos_esperados.keys():
            comprueba_dato(test_case, datos_esperados[key], response.context[key], n_pagina=n_pagina)

# Compara y comprueba dos datos
def comprueba_dato(test_case, dato_esperado, dato_recibido, **kwargs):
    # Usa un assert distinto en función del dato que recibe
    if isinstance(dato_esperado, QuerySet):
        test_case.assertListEqual(list(dato_recibido), list(dato_esperado))
    elif isinstance(dato_esperado, list):
        if isinstance(dato_recibido, Page):
            test_case.assertListEqual(dato_recibido.object_list, dato_esperado)
        else:
            test_case.assertListEqual(dato_recibido, dato_esperado)
    # Si es un diccionario, entonces lo que ha recibido se considera una lista paginada
    elif isinstance(dato_esperado, dict):
        try:
            comprueba_dato(test_case, dato_esperado[kwargs['n_pagina']], dato_recibido)
        except KeyError as e:
            if isinstance(dato_recibido, list):
                test_case.assertListEqual([], dato_recibido)
            else:
                test_case.assertIsNone(dato_recibido)
    elif dato_esperado:
        test_case.assertTrue(dato_recibido)
    elif not dato_esperado:
        test_case.assertFalse(dato_recibido)
    else:
        test_case.assertEqual(dato_recibido, dato_esperado)

# Dada una lista, obtiene el número de páginas de dicha lista
def numero_paginas(lista):
    # Se halla el número de objetos
    if isinstance(lista, QuerySet):
        n_objetos = lista.count()
    elif isinstance(lista, list):
        n_objetos = len(lista)
    # Se haya el número de páginas
    if n_objetos % numero_objetos_por_pagina == 0:
        n_paginas = int(n_objetos / numero_objetos_por_pagina)
    else:
        n_paginas = int(n_objetos / numero_objetos_por_pagina) + 1
    return n_paginas

# Dada una lista, devuelve un diccionario que es la lista paginada
def paginar_lista(lista):
    res = dict()
    for pagina in range(1, numero_paginas(lista)+1):
        res[pagina] = lista[(pagina - 1) * numero_objetos_por_pagina : pagina * numero_objetos_por_pagina]
    return res
