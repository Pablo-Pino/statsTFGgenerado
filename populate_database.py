from django.contrib.auth.models import User
from websecurityapp.models.actividad_models import Actividad, SesionActividad
from websecurityapp.models.perfil_models import Usuario, Anexo
from websecurityapp.models.oferta_models import Oferta, Solicitud
from datetime import date

# DJANGO USERS Y USUARIOS

django_user_1 = User.objects.create_user(
    'usuario1',
    'federico@gmail.com',
    'usuario1',
    first_name = 'Federico',
    last_name = 'Garcia Prieto'
)

django_user_2 = User.objects.create_user(
    'usuario2',
    'sarac@gmail.com',
    'usuario2',
    first_name = 'Sarah',
    last_name = 'Connor'
)

django_user_3 = User.objects.create_user(
    'usuario3',
    'juann@gmail.com',
    'usuario3',
    first_name = 'Juan',
    last_name = 'Nieves'
)

usuario_1 = Usuario(
    django_user = django_user_1,
    telefono = '123456789',
    empresa_u_equipo = 'Equipo Garcia',
    vetado = False,
    es_admin = False
)

usuario_2 = Usuario(
    django_user = django_user_2,
    vetado = False,
    es_admin = True
)

usuario_3 = Usuario(
    django_user = django_user_3,
    telefono = '357809201',
    empresa_u_equipo = 'Microsoft S.A.',
    vetado = False,
    es_admin = False
)

usuarios = [
    usuario_1,
    usuario_2,
    usuario_3
]

for usuario in usuarios:
    usuario.full_clean()
    usuario.save()



# ANEXOS

anexo_1 = Anexo(
    usuario = usuario_1,
    anexo = 'http://garcia1ertrabajo.com/'
)

anexo_2 = Anexo(
    usuario = usuario_1,
    anexo = 'http://garciaempresa.com/'
)

anexo_3 = Anexo(
    usuario = usuario_1,
    anexo = 'http://garciaofertas.com/'
)

anexo_4 = Anexo(
    usuario = usuario_1,
    anexo = 'http://garciainfo.com/'
)

anexo_5 = Anexo(
    usuario = usuario_2,
    anexo = 'http://normasdelsistema.com/'
)

anexos = [
    anexo_1,
    anexo_2,
    anexo_3,
    anexo_4,
    anexo_5
]

for anexo in anexos:
    anexo.full_clean()
    anexo.save()



# ACTIVIDADES

actividad_1 = Actividad(
    titulo = 'SQL por Federico',
    enlace = 'http://sqlfederico.com/',
    descripcion = 'Un tutorial de SQLi basico por Federico. Comentarios son bienvenidos.',
    comentable = True,
    autor = usuario_1,
    borrador = False,
    vetada = False,
    fecha_creacion = date(2019, 11, 20),
    identificador = 'ACT-12345ASDxc',
)

actividad_2 = Actividad(
    titulo = 'JPQL',
    enlace = 'http://jpqlfed.com/',
    descripcion = 'Ejercicios del lenguaje JPQL, que conecta Java con bases de datos',
    comentable = False,
    autor = usuario_1,
    borrador = False,
    vetada = False,
    fecha_creacion = date(2019, 12, 12),
    identificador = 'ACT-ASDFGCVBnm',
)

actividad_3 = Actividad(
    titulo = 'Angular en detalles',
    enlace = 'http://jpqlfed.com/',
    descripcion = 'Tutoriales avanzados de Angular. Aun por completar.',
    comentable = False,
    autor = usuario_1,
    borrador = True,
    vetada = False,
    fecha_creacion = date(2020, 1, 1),
    identificador = 'ACT-forgton345',
)

actividad_4 = Actividad(
    titulo = 'Actividad de prueba',
    enlace = 'http://prueba.com/',
    descripcion = 'Para ver que todo funciona bien.',
    comentable = False,
    autor = usuario_2,
    borrador = False,
    vetada = False,
    fecha_creacion = date(2019, 11, 10),
    identificador = 'ACT-A23D5Gdefg',
)

actividad_5 = Actividad(
    titulo = 'Vendo coche',
    enlace = 'http://cochesgratis.com/',
    descripcion = 'El Ferrari esta como nuevo',
    comentable = True,
    autor = usuario_3,
    borrador = False,
    vetada = True,
    fecha_creacion = date(2019, 11, 20),
    identificador = 'ACT-456gtIOMDF',
    motivo_veto = 'Esto no es una página de compraventa'
)

actividad_6 = Actividad(
    titulo = 'Una actividad extraña',
    enlace = 'http://testing.com/',
    descripcion = 'Para ver cómo funciona la lógica de la aplicación',
    comentable = False,
    autor = usuario_1,
    borrador = False,
    vetada = True,
    fecha_creacion = date(2019, 11, 20),
    identificador = 'ACT-12345serfv',
    motivo_veto = 'El testeo es vital'
)

actividad_7 = Actividad(
    titulo = 'Mockingbird',
    enlace = 'http://localhost:8000/ejercicio/mock/1/',
    descripcion = 'Mock',
    comentable = False,
    autor = usuario_1,
    borrador = False,
    vetada = False,
    fecha_creacion = date(2019, 11, 20),
    identificador = 'ACT-332243565j',
    motivo_veto = None
)

actividad_8 = Actividad(
    titulo = 'Mockingbird2',
    enlace = 'http://localhost:8000/ejercicio/mock/2/',
    descripcion = 'Mock2',
    comentable = False,
    autor = usuario_2,
    borrador = False,
    vetada = False,
    fecha_creacion = date(2019, 11, 20),
    identificador = 'ACT-332243565g',
    motivo_veto = None
)

actividad_9 = Actividad(
    titulo = 'Mockingbird3',
    enlace = 'http://localhost:8000/ejercicio/mock/3/',
    descripcion = 'Mock3',
    comentable = False,
    autor = usuario_1,
    borrador = False,
    vetada = False,
    fecha_creacion = date(2019, 11, 20),
    identificador = 'ACT-332243565r',
    motivo_veto = None
)

actividades = [
    actividad_1,
    actividad_2,
    actividad_3,
    actividad_4,
    actividad_5,
    actividad_6,
    actividad_7,
    actividad_8,
    actividad_9,
]

for actividad in actividades:
    actividad.full_clean()
    actividad.save()



# RELACION USUARIO-ACTIVIDAD   ACTIVIDADES REALIZADAS

# Se indican las actividades que han realizado los usuarios

list_actividades = [actividad_7, actividad_1, actividad_2, actividad_4, actividad_8, actividad_9]
usuario_1.actividades_realizadas.set(list_actividades)
usuario_1.save()

list_actividades = [actividad_7, actividad_2, actividad_5, actividad_4, actividad_9]
usuario_2.actividades_realizadas.set(list_actividades)
usuario_2.save()

list_actividades = [actividad_9, actividad_6]
usuario_3.actividades_realizadas.set(list_actividades)
usuario_3.save()



# SESIONACTIVIDADES

sesionactividad_1 = SesionActividad(
    usuario = usuario_2,
    actividad = actividad_7,
    token = 'ASDFGHJKL'
)

sesionactividad_2 = SesionActividad(
    usuario = usuario_1,
    actividad = actividad_8,
    token = 'TRYTYTHESGHR'
)

sesionactividad_3 = SesionActividad(
    usuario = usuario_1,
    actividad = actividad_9,
    token = '234678799876543'
)

sesionactividades = [
    sesionactividad_1,
    sesionactividad_2,
    sesionactividad_3
]

for sesionactividad in sesionactividades:
    sesionactividad.full_clean()
    sesionactividad.save()



# OFERTAS

oferta_1 = Oferta(
    titulo = 'Oferta developer',
    descripcion = 'Se busca developer',
    autor = usuario_1,
    borrador = True,
    vetada = False,
    fecha_creacion = date(2019, 11, 20),
    identificador = 'OFR-12345ASDxc',
    cerrada = False,
    motivo_veto = None,
)

oferta_2 = Oferta(
    titulo = 'JPQL',
    descripcion = 'Se busca desarrollador de querys de Spring',
    autor = usuario_1,
    borrador = False,
    vetada = False,
    fecha_creacion = date(2019, 12, 12),
    identificador = 'OFR-Asfgrgreq2',
    cerrada = False,
    motivo_veto = None,
)

oferta_3 = Oferta(
    titulo = 'Parlo italiano',
    descripcion = 'Traductor de italiano-español. Para más información consultar en la página del grupo Itaes',
    autor = usuario_2,
    borrador = False,
    vetada = False,
    fecha_creacion = date(2017, 11, 12),
    identificador = 'OFR-ASDFGCVBnr',
    cerrada = False,
    motivo_veto = None,
)

oferta_4 = Oferta(
    titulo = 'JavaScript Senior con 10 años de experiencia',
    descripcion = 'El sueldo sería de 2000 $ al mes en Alemania con gastos de viviendia y transporte cubiertos',
    autor = usuario_2,
    borrador = True,
    vetada = False,
    fecha_creacion = date(2019, 6, 4),
    identificador = 'OFR-gredos12AS',
    cerrada = False,
    motivo_veto = None,
)

oferta_5 = Oferta(
    titulo = 'Java de instituto',
    descripcion = '''Se ofrece un puesto de profesor de Informática para alumnos de Bachillerato. Se piden conocimientos básicos de Java y capacidad para la enseñanza''',
    autor = usuario_3,
    borrador = False,
    vetada = False,
    fecha_creacion = date(2019, 12, 3),
    identificador = 'OFR-GNORegre43',
    cerrada = False,
    motivo_veto = None,
)

oferta_6 = Oferta(
    titulo = 'Limpiapiscinas',
    descripcion = 'Alguien interesado par limpiar la piscina de mi casa ?',
    autor = usuario_3,
    borrador = False,
    vetada = True,
    fecha_creacion = date(2019, 12, 12),
    identificador = 'OFR-ASDFG123wm',
    cerrada = False,
    motivo_veto = 'No tiene nada que ver con la informática o la ciberseguridad',
)

oferta_7 = Oferta(
    titulo = 'Proyecto de la Nasa',
    descripcion = 'April\'s Fools!',
    autor = usuario_1,
    borrador = False,
    vetada = True,
    fecha_creacion = date(2019, 4, 1),
    identificador = 'OFR-ASDdrgt67d',
    cerrada = False,
    motivo_veto = 'Evitemos contenido innecesario',
)

oferta_8 = Oferta(
    titulo = 'Experto en API REST',
    descripcion = '''Se buscan ingenieros con competencias en el diseño de API REST. Se requiere conocimientos de PHP''',
    autor = usuario_1,
    borrador = True,
    vetada = False,
    fecha_creacion = date(2019, 12, 3),
    identificador = 'OFR-ASDFGCLOB0',
    cerrada = False,
    motivo_veto = None,
)

oferta_9 = Oferta(
    titulo = 'Big Data en Madrid',
    descripcion = '''Si te interesa la oferta, puedes contactar con nosotros en datosgrandes.es. Puedes encontrar nuestras oficinas en la C/Toronto nº 43 en Madrid o Avd de los Reyes en Barcelona nº 2.''',
    autor = usuario_1,
    borrador = False,
    vetada = False,
    fecha_creacion = date(2019, 1, 23),
    identificador = 'OFR-ASDFGCohuh',
    cerrada = True,
    motivo_veto = None,
)

oferta_10 = Oferta(
    titulo = 'Spring Web Developer en Almería',
    descripcion = 'Aunque una de las actividades es un poco extraña se puede hacer bien',
    autor = usuario_1,
    borrador = False,
    vetada = False,
    fecha_creacion = date(2019, 1, 23),
    identificador = 'OFR-ASDFGCoh45',
    cerrada = False,
    motivo_veto = None,
)

ofertas = [
    oferta_1,
    oferta_2,
    oferta_3,
    oferta_4,
    oferta_5,
    oferta_6,
    oferta_7,
    oferta_8,
    oferta_9,
    oferta_10
]

for oferta in ofertas:
    oferta.full_clean()
    oferta.save()

# No usar actividades 3, 5 o 6
oferta_1.actividades.set([actividad_1, actividad_2])
oferta_2.actividades.set([actividad_7],)
oferta_3.actividades.set([actividad_8],)
oferta_4.actividades.set([actividad_9],)
oferta_5.actividades.set([actividad_7, actividad_9])
oferta_6.actividades.set([actividad_2])
oferta_7.actividades.set([actividad_4])
oferta_8.actividades.set([actividad_7, actividad_1, actividad_2])
oferta_9.actividades.set([actividad_9])
oferta_10.actividades.set([actividad_5, actividad_9])


for oferta in ofertas:
    oferta.full_clean()
    oferta.save()



# SOLICITUDES

solicitud_1 = Solicitud(
    usuario=usuario_2,
    oferta=oferta_2
)

solicitud_2 = Solicitud(
    usuario=usuario_1,
    oferta=oferta_6
)

solicitud_3 = Solicitud(
    usuario=usuario_1,
    oferta=oferta_3
)

solicitud_4 = Solicitud(
    usuario=usuario_3,
    oferta=oferta_9,
)

solicitudes = [
    solicitud_1,
    solicitud_2,
    solicitud_3,
    solicitud_4
]

for solicitud in solicitudes:
    solicitud.full_clean()
    solicitud.save()


