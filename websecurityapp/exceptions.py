class UnallowedUserException(Exception):
    def __init__(self):
        self.msg = 'No tienes los permisos o requisitos necesarios para realizar esta accion'