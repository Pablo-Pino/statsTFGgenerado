from django.shortcuts import render
from django.http import HttpResponse, QueryDict, HttpResponseRedirect
from django.views import View
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.urls import reverse

from websecurityapp.exceptions import UnallowedUserException
from websecurityapp.models.perfil_models import Usuario

# Create your views here.

class HomeView(View):
    template_name = 'master_page/master_page.html'
    
    def get(self, request):
        context = {}
        user = request.user
        if user:
            context.update({
                'user': user,
                'home': True,
            })
        return render(request, self.template_name, context)

class EjercicioMock1View(View):
    template_name = 'utils/ejercicio_mock_1.html'

    def get(self, request):
        return render(request, self.template_name, {})

class EjercicioMock2View(View):
    template_name = 'utils/ejercicio_mock_2.html'

    def get(self, request):
        return render(request, self.template_name, {})

class EjercicioMock3View(View):
    template_name = 'utils/ejercicio_mock_3.html'

    def get(self, request):
        return render(request, self.template_name, {})



    
    


