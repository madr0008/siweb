from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash
from datetime import date, datetime, timedelta
from pyparsing import removeQuotes
from werkzeug.security import generate_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from app import app
from os.path import exists


#Creamos la Blueprint
entrenadores = Blueprint('entrenadores', __name__, template_folder='templates', static_folder='static', static_url_path='/entrenadores/static')

#Importamos la base de datos
from app import mysql

#Función para comprobar el tipo de usuario
def comprobarTipo() :
    if current_user.tipo != 'trabajadores' :
        logout_user()
        return False
    return True


#ENTRENADOR

#Página principal

@entrenadores.route('/entrenadores/')
@login_required
def index() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    cur = mysql.connection.cursor()
    cur.execute('SELECT COUNT(*) FROM ejercicios')
    nEjercicios = cur.fetchall()[0][0]
    cur.execute('SELECT COUNT(*) FROM rutinas')
    nRutinas = cur.fetchall()[0][0]
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('index_entrenadores.html', nEjercicios = nEjercicios, nRutinas = nRutinas, nComidas = 0, nDietas = 0, foto = foto)


#Sección ejercicios

@entrenadores.route('/entrenadores/ejercicios')
@login_required
def ejercicios() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('ejercicios.html', foto = foto)

@entrenadores.route('/entrenadores/ejercicios/<string:grupo>')
@login_required
def grupo(grupo) :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    grupos = ['Espalda','Brazos','Pecho','Piernas','Hombros','Abdomen']
    cur = mysql.connection.cursor()
    cur.execute('SELECT id, nombre, descripcion, extension FROM ejercicios WHERE grupo = %s', [grupo])
    ejcs = cur.fetchall()
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('grupo.html', grupo = grupo.capitalize(), grupos = grupos, ejercicios = ejcs, foto = foto)

@entrenadores.route('/entrenadores/ejercicios/add_ejercicio', methods=['POST'])
@login_required
def add_ejercicio() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        grupo = request.form['grupo']
        imagen = request.files['imagen']
        aux = imagen.filename.split('.')
        extension = aux[len(aux) - 1]
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO ejercicios (nombre, descripcion, grupo, extension) VALUES(%s,%s,%s,%s)', (nombre, descripcion, grupo, extension))
        mysql.connection.commit()
        cur.execute('SELECT MAX(id) FROM ejercicios')
        id = cur.fetchone()[0]
        imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], str(id) + '.' + extension))
        flash('Se ha añadido el ejercicio')
    return redirect('/entrenadores/ejercicios/' + grupo.lower())

@entrenadores.route('/entrenadores/ejercicios/eliminar_ejercicio/<string:aux>')
@login_required
def eliminar_ejercicio(aux) :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    id = aux.split('_')[0]
    grupo = aux.split('_')[1]
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM ejercicios WHERE id = %s', [id])
    mysql.connection.commit()
    flash('Se ha eliminado el ejercicio')
    return redirect('/entrenadores/ejercicios/' + grupo.lower())


#Sección rutinas

@entrenadores.route('/entrenadores/rutinas')
@login_required
def rutinas() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    intensidades = ['baja','media','alta']
    rutinas = dict()
    cur = mysql.connection.cursor()
    for intensidad in intensidades :
        cur.execute('SELECT * FROM rutinas WHERE intensidad = %s', [intensidad])
        rutinas[intensidad] = cur.fetchall()
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('rutinas.html', rutinas = rutinas, foto = foto)

@entrenadores.route('/entrenadores/rutinas/add_rutina', methods=['POST'])
@login_required
def add_rutina() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        intensidad = request.form['intensidad']
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO rutinas (nombre, descripcion, intensidad) VALUES(%s,%s,%s)', (nombre, descripcion, intensidad))
        mysql.connection.commit()
    flash('Se ha insertado la rutina_' + intensidad)
    return redirect('/entrenadores/rutinas#' + intensidad)

@entrenadores.route('/entrenadores/rutinas/eliminar_rutina/<string:s>')
@login_required
def eliminar_rutina(s) :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    id = s.split('_')[0]
    intensidad = s.split('_')[1]
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM rutinas WHERE id = %s', [id])
    cur.execute('DELETE FROM dias_rutinas WHERE idRutina = %s', [id])
    mysql.connection.commit()
    flash('Se ha eliminado la rutina_' + intensidad)
    return redirect('/entrenadores/rutinas#' + intensidad)

@entrenadores.route('/entrenadores/rutinas/<string:id>')
@login_required
def rutina(id) :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM ejercicios')
    aux = cur.fetchall()
    ejercicios = dict()
    for ejercicio in aux :
        ejercicios[ejercicio[0]] = ejercicio
    cur.execute('SELECT * FROM rutinas WHERE id = %s', [id])
    datosRutina = cur.fetchone()
    cur.execute('SELECT * FROM dias_rutinas WHERE idRutina = %s', [id])
    aux = cur.fetchone()
    dias = ['Lunes','Martes','Miercoles','Jueves','Viernes']
    rutina = dict()
    grupos = dict()
    for i in range(len(dias)) :
        rutina[dias[i]] = list()
        grupos[dias[i]] = list()
        ejcs = aux[i + 1].split(',')
        for ejc in ejcs :
            if len(ejc) > 0 :
                campos = ejc.split('-')
                rutina[dias[i]].append([int(campos[0]), int(campos[1]), int(campos[2])])
                cur.execute('SELECT grupo FROM ejercicios WHERE id = %s', [int(campos[0])])
                grupo = cur.fetchone()[0]
                if grupo not in grupos[dias[i]] :
                        grupos[dias[i]].append(grupo)
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('rutina.html', datosRutina = datosRutina, rutina = rutina, ejercicios = ejercicios, grupos = grupos, foto = foto)

@entrenadores.route('/entrenadores/rutinas/add_ejc_a_rutina/<string:s>', methods=['POST'])
@login_required
def add_ejc_a_rutina(s) :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    if request.method == 'POST':
        id = s.split('_')[0]
        dia = s.split('_')[1]
        cur = mysql.connection.cursor()
        sql = 'SELECT ' + dia.lower() + ' FROM dias_rutinas WHERE idRutina = %s'
        cur.execute(sql, [id])
        str = cur.fetchone()[0]
        for ejercicio in request.form.getlist('ejercicios') :
            series = request.form['series_' + ejercicio]
            repeticiones = request.form['repeticiones_' + ejercicio]
            str += ',' + ejercicio + '-' + series + '-' + repeticiones
        if str[0] == ',' :
            str = str[1:]
        sql = 'UPDATE dias_rutinas SET ' + dia.lower() + ' = %s WHERE idRutina = %s'
        cur.execute(sql, (str, id))
        mysql.connection.commit()
        flash('Se ha añadido el ejercicio_' + dia)
        return redirect('/entrenadores/rutinas/' + id + '#' + dia)

@entrenadores.route('/entrenadores/rutinas/eliminar_ejc_de_rutina/<string:s>', methods=['POST'])
@login_required
def eliminar_ejc_de_rutina(s) :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    if request.method == 'POST':
        id = s.split('_')[0]
        dia = s.split('_')[1]
        cur = mysql.connection.cursor()
        sql = 'SELECT ' + dia.lower() + ' FROM dias_rutinas WHERE idRutina = %s'
        cur.execute(sql, [id])
        str = cur.fetchone()[0]
        nuevo = str
        for ejercicio in str.split(',') :
            if ejercicio.split('-')[0] in request.form.getlist('ejercicios') :
                nuevo = nuevo.replace(ejercicio,'')
        while ',,' in nuevo :
            nuevo = nuevo.replace(',,',',')
        if nuevo[0] == ',' :
            nuevo = nuevo[1:]
        if nuevo[len(nuevo) - 1] == ',' :
            nuevo = nuevo[:len(nuevo) - 1]
        sql = 'UPDATE dias_rutinas SET ' + dia.lower() + ' = %s WHERE idRutina = %s'
        cur.execute(sql, (nuevo, id))
        mysql.connection.commit()
        flash('Se ha eliminado el ejercicio_' + dia)
        return redirect('/entrenadores/rutinas/' + id + '#' + dia)


#Sección perfil

@entrenadores.route('/entrenadores/perfil')
@login_required
def perfil() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('perfil_entrenador.html', foto = foto)

@entrenadores.route('/entrenadores/cambiar_contrasena', methods=['POST'])
@login_required
def cambiar_contrasena() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    if request.method == 'POST' :
        nueva = request.form['nueva']
        confirmada = request.form['confirmada']
        cur = mysql.connection.cursor()
        if nueva == confirmada :
            passwd = generate_password_hash(nueva)
            cur.execute('UPDATE login SET password = %s WHERE email = %s', (passwd, current_user.id))
            mysql.connection.commit()
            flash('La contraseña se ha cambiado correctamente_0')
        else :
            flash('Las nuevas contraseñas no coinciden_1')
    return redirect('/entrenadores/perfil')

@entrenadores.route('/entrenadores/cambiar_foto', methods=['POST'])
@login_required
def cambiar_foto() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    if request.method == 'POST' :
        foto = request.files['foto']
        aux = foto.filename.split('.')
        extension = aux[len(aux) - 1]
        foto.save(os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.dni) + '.' + extension))
        cur = mysql.connection.cursor()
        cur.execute('UPDATE login SET extension = %s WHERE email = %s', (extension, current_user.id))
        mysql.connection.commit()
    return redirect('/entrenadores/perfil')


#Log out
@entrenadores.route('/entrenadores/logout')
@login_required
def logout() :
    logout_user()
    return redirect(url_for('public.login'))


#Páginas de error
@entrenadores.route('/entrenadores/404')
@login_required
def error404() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('404_entrenador.html', foto = foto)