from websecurityapp.models.oferta_models import Solicitud, Oferta

# Dados un usuario y una lista de ofertas, devuelve por separado las ofertas solicitables y la ofertas retirables
# por el usuario
def get_ofertas_solicitables_y_ofertas_retirables(usuario, ofertas):
    ofertas_solicitables = []
    ofertas_solicitadas = []
    ofertas_retirables = []
    # Obtiene las ofertas solicitadas por el usuario
    solicitudes_usuario = list(Solicitud.objects.filter(usuario=usuario).only('oferta').distinct())
    for solicitud in solicitudes_usuario:
        ofertas_solicitadas.append(solicitud.oferta)
    # Por cada oferta de la lista de ofertas
    for oferta in ofertas:
        # Obtiene las ofertas retirables
        if not oferta.cerrada and not oferta.vetada and oferta in ofertas_solicitadas:
            ofertas_retirables.append(oferta)
        # Filtra parcialmente las ofertas para retirar parte de las que no son solicitables
        elif not oferta.borrador and not oferta.cerrada and not oferta.vetada and not oferta in ofertas_solicitadas:
            es_solicitable = True
            # Si uno de los requisitos de la oferta no ha sido resuelto por el usuario, o el usuario es el autor de la
            # oferta, entonces la oferta no es solicitable
            for actividad_requerida in oferta.actividades.all():
                if not actividad_requerida in usuario.actividades_realizadas.all() or usuario == oferta.autor:
                    es_solicitable = False
                    break
                # Si la actividad está vetada, entonces la oferta no es solicitable
                elif actividad_requerida.vetada:
                    es_solicitable = False
                    break
            # Si la oferta es solicitable, entonces es añadida al listado de ofertas solicitables
            if es_solicitable:
                ofertas_solicitables.append(oferta)
    return [ofertas_solicitables, ofertas_retirables]

# Indica si un oferta es retirable o solicitable
def es_oferta_solicitable_o_retirable(usuario, oferta):
    es_solicitada = Solicitud.objects.filter(usuario=usuario, oferta=oferta).exists()
    retirable = False
    solicitable = False
    # Si la oferta ha sido solicitada, comprueba si se puede retirar la solicitud
    if es_solicitada:
        if not oferta.vetada and not oferta.cerrada:
            retirable = True
    # Si la oferta no ha sido solicitada, comprueba si se puede solicitar
    else:
        if not oferta.cerrada and not oferta.vetada and not oferta.borrador:
            solicitable = True
            for actividad_requerida in oferta.actividades.all():
                # Si uno de los requisitos de la oferta no ha sido resuelto por el usuario, o el usuario es el autor
                # de la oferta, entonces la oferta no es solicitable
                if not actividad_requerida in usuario.actividades_realizadas.all() or usuario == oferta.autor:
                    solicitable = False
                    break
                # Si uno de los requisitos está vetado, entonces la actividad no es solicitable
                elif actividad_requerida.vetada:
                    solicitable = False
                    break
    return [solicitable, retirable]

# Filtra una lista de ofertas para obtener aquellas ofertas que tienen requisitos vetados
def get_ofertas_con_actividades_vetadas(ofertas):
    res = []
    for oferta in ofertas:
        for actividad in oferta.actividades.all():
            if actividad.vetada:
                res.append(oferta)
                break
    return res

# Indica si la oferta dada tiene algún requisito vetado
def tiene_actividad_vetada(oferta):
    res = False
    for actividad in oferta.actividades.all():
        if actividad.vetada:
            res = True
            break
    return res