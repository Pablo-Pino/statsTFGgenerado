from django.contrib.auth.models import User
from django.db import transaction
from datetime import date
from random import choice
from django.contrib.auth.hashers import make_password

def genera_identificador():
    random_string = 'QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm1234567890'
    res = ''
    while(len(res) < 10):
        res = res + choice(random_string)
    return res
    

