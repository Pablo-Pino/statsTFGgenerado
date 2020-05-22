from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from websecurityapp.serializers.sesionactividad_serializer import SesionActividadSerializer
from websecurityapp.models.actividad_models import SesionActividad, Actividad
from websecurityapp.models.perfil_models import Usuario
from websecurityapp.services import sesionactividad_services
from django.views.decorators.csrf import csrf_exempt

class SesionActividadComienzo(APIView):

    def get(self, request, identificador, format=None):
        # Se trata de crear al sesion
        actividad = Actividad.objects.get(identificador = identificador)
        try:
            sesionactividad = sesionactividad_services.crea_sesionactividad(request, actividad)
        # Manda un mensaje de error si no ha logrrado crear la sesión
        except Usuario.DoesNotExist as e:
            json_response = JsonResponse({'status': 'Se debe iniciar sesión para acceder a la actividad'}, status=500, safe=False)
            return json_response
        # Manda el token
        serializer = SesionActividadSerializer(sesionactividad)
        data = serializer.data
        # Se incluye un mensaje de éxito
        data['status'] = 'Se ha comenzado la actividad correctamente'
        json_response = JsonResponse(data, safe=False)
        return json_response

class SesionActividadFinal(APIView):
    parser_classes = [JSONParser]

    def post(self, request, identificador, format=None):
        # Si el usuario no está autenticado se manda un mensaje de error
        if request.user.id == None:
            json_response = JsonResponse({'status': 'El usuario debe estar autenticado'}, status=500)
            return json_response
        # Se trata de eliminar el objeto sesión y marcar la actividad como resuelta
        try:
            serializer = SesionActividadSerializer(data=request.data)
            if serializer.is_valid():
                # Elimina la sesion y marca la actividad como resuelta
                actividad = Actividad.objects.get(identificador = identificador)
                sesionactividad_services.elimina_sesionactividad(request, actividad)
                # Manda un mensaje de éxito
                sesionactividad_services.añade_actividad_realizada(request, actividad)
                json_response = JsonResponse({'status': 'Se ha realizado correctamente la actividad'}, status=201)
                return json_response
            # Si el serializer no es válido, manda un mensaje de error
            json_response = JsonResponse(serializer.errors, status=500)
        # Si se ha producido algún error, se manda un mensaje de error
        except Exception as e:
            json_response = JsonResponse({'status': 'Se ha producido un error en la conexión con el servidor'}, status=500)
        return json_response


