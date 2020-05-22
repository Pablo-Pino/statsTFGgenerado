from websecurityapp.models.actividad_models import SesionActividad
from rest_framework import serializers

class SesionActividadSerializer(serializers.ModelSerializer):

    class Meta:
        model = SesionActividad
        fields = ['token']