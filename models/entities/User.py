from werkzeug.security import check_password_hash
from flask_login import UserMixin


class User(UserMixin):

    def __init__(self, email, password, tipo="", nombre="", apellidos="", dni="", fecha_inicio="", fecha_ult="", extension="") -> None:
        self.id = email
        self.password = password
        self.tipo = tipo
        self.nombre = nombre
        self.apellidos = apellidos
        self.dni = dni
        self.fecha_inicio = fecha_inicio
        self.fecha_ult = fecha_ult
        self.extension = extension

    @classmethod
    def check_password(self, hashed_password, password):
        return check_password_hash(hashed_password, password)