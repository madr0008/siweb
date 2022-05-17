from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from flask_login import LoginManager, login_user, logout_user, login_required
from flask import send_from_directory
from models.ModelUser import ModelUser
import os

app = Flask(__name__)

#Conexión a la base de datos
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345'
app.config['MYSQL_DB'] = 'retofit'
mysql = MySQL(app)

#Carpeta uploads
app.config['UPLOAD_FOLDER'] = os.path.join('uploads')

#Inicialización de sesión
app.secret_key = 'mysecretkey'

#Login
login_manager_app = LoginManager(app)

@login_manager_app.user_loader
def load_user(email) :
    return ModelUser.get_by_email(mysql, email)

from admin import admin_routes
from public import public_routes
from entrenadores import entrenadores_routes
from clientes import clientes_routes

#Registramos los blueprints
app.register_blueprint(admin_routes.admin)
app.register_blueprint(public_routes.public)
app.register_blueprint(entrenadores_routes.entrenadores)
app.register_blueprint(clientes_routes.clientes)

@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith('/admin/') :
        return redirect(url_for('admin.error404'))
    elif request.path.startswith('/entrenadores/') :
        return redirect(url_for('entrenadores.error404'))
    elif request.path.startswith('/clientes/') :
        return redirect(url_for('clientes.error404'))
    else :
        return redirect(url_for('public.error404'))

#Cargar imágenes
@app.route('/uploads/<nombre>')
def uploads(nombre) :
    return send_from_directory(app.config['UPLOAD_FOLDER'],nombre)


if __name__ == '__main__' :
    app.run(debug=True)