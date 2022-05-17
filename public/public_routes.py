from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash
from models.ModelUser import ModelUser
from models.entities.User import User
from flask_login import LoginManager, login_user, logout_user, login_required

#Creamos la Blueprint
public = Blueprint('public', __name__, template_folder='templates', static_folder='static', static_url_path='/public/static')

#Importamos la base de datos
from app import mysql


#PÁGINA PÚBLICA

#Página principal

@public.route('/')
def index() :
    return render_template('index_public.html')

#Contacto

@public.route('/contacto')
def contacto() :
    return render_template('contacto.html')

#Precios

@public.route('/precios')
def precios() :
    return render_template('precios.html')

#Login

@public.route('/login', methods=['GET', 'POST'])
def login() :
    if request.method == 'POST':
        user = User(request.form['email'], request.form['password'])
        logged_user = ModelUser.login(mysql, user)
       
        #cur.execute('SELECT * FROM login WHERE email=%s', [email])
        if logged_user != None :
            if logged_user.password :
                login_user(logged_user)
                if logged_user.tipo == 'admins':
                    return redirect(url_for('admin.index'))
                elif logged_user.tipo == 'clientes':
                    return redirect(url_for('clientes.index'))
                elif logged_user.tipo == 'trabajadores':
                    return redirect(url_for('entrenadores.index'))
            else :
                flash("Contraseña incorrecta")
        else :
            flash("Email inválido")

    return render_template('login.html')


#Blog

@public.route('/blog')
def blog() :
    return render_template('blog.html')


@public.route('/blog/articulo')
def articulo() :
    return render_template('blog-post.html')


#Páginas de error

@public.route('/404')
def error404() :
    return render_template('public_404.html')

@public.app_errorhandler(401)
def handle_401(err):
    return redirect(url_for('public.login'))