import email
from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash
from datetime import date, datetime, timedelta
from werkzeug.security import generate_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from os.path import exists

#Creamos la Blueprint
admin = Blueprint('admin', __name__, template_folder='templates', static_folder='static', static_url_path='/admin/static')

#Importamos la base de datos
from app import mysql

#Importamos el objeto app
from app import app

#Función para comprobar el tipo de usuario
def comprobarTipo() :
    if current_user.tipo != 'admins' :
        logout_user()
        return False
    return True


#ADMINISTRADOR

#Página principal

@admin.route('/admin/')
@login_required
def index() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    cur = mysql.connection.cursor()
    cur.execute('SELECT COUNT(*) FROM clientes')
    nClientes = cur.fetchall()[0][0]
    cur.execute('SELECT COUNT(*) FROM trabajadores')
    nTrabajadores = cur.fetchall()[0][0]
    hoy = date.today()
    dia_semana = datetime.today().weekday()
    lunes = hoy - timedelta(days=dia_semana)
    viernes = lunes + timedelta(4)
    cur.execute('SELECT COUNT(*) FROM clases WHERE fecha BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE)', (lunes, viernes))
    nClases = cur.fetchall()[0][0]
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('index_admin.html', nClientes = nClientes, nTrabajadores = nTrabajadores, nClases = nClases, foto = foto)

#Sección calendario

@admin.route('/admin/calendario')
@login_required
def calendario() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    hoy = date.today()
    dia_semana = datetime.today().weekday()
    lunes = hoy - timedelta(days=dia_semana)
    return redirect('/admin/calendario/' + str(lunes) + '_0')


@admin.route('/admin/calendario/<string:aux>')
@login_required
def calendario_fecha(aux) :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    aux = aux.split('_')
    if aux[1] == '0' :
        lunes = datetime.strptime(aux[0], '%Y-%m-%d').date()
    elif aux[1] == '+' :
        lunes = datetime.strptime(aux[0], '%Y-%m-%d').date() + timedelta(7)
    else :
        lunes = datetime.strptime(aux[0], '%Y-%m-%d').date() - timedelta(7)
    dias = list()
    for i in range(5) :
        dias.append((lunes + timedelta(days=i)))
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM clases WHERE fecha BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE)', (dias[0], dias[4]))
    aux = cur.fetchall()
    clases = dict()
    for c in aux:
        clases[c[1],c[2]] = [c[0],c[3],c[4]]
    horas = ['9:00-10:00','10:00-11:00','11:00-12:00','12:00-13:00','16:00-17:00','17:00-18:00','18:00-19:00','19:00-20:00']
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('calendario.html', dias = dias, clases = clases, horas=horas, lunes = lunes, foto = foto)


@admin.route('/admin/add_clase/<string:cadena>', methods=['POST'])
@login_required
def add_clase(cadena) :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    if request.method == 'POST':
        nombre = request.form['nombre']
        plazas = int(request.form['plazas'])
        fecha = cadena.split('_')[0]
        hora = cadena.split('_')[1]
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO clases VALUES(%s,%s,%s,%s,%s)', (nombre, fecha, hora, plazas, plazas))
        mysql.connection.commit()
        flash('Se ha añadido la clase')
        fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
        dia_semana = fecha.weekday()
        lunes = fecha - timedelta(days=dia_semana)
    return redirect('/admin/calendario/' + str(lunes) + '_0')


@admin.route('/admin/calendario/copiar_semana/<string:aux>')
@login_required
def copiar_semana(aux) :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    lunes = datetime.strptime(aux, '%Y-%m-%d').date()
    lunes_anterior = lunes - timedelta(7)
    viernes_anterior = lunes_anterior + timedelta(5)
    cur = mysql.connection.cursor()
    cur.execute('SELECT nombre, fecha, hora, plazas FROM clases WHERE fecha BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE)', (lunes_anterior, viernes_anterior))
    aux = cur.fetchall()
    for c in aux:
        nueva_fecha = c[1] + timedelta(7)
        cur.execute('INSERT INTO clases VALUES(%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE nombre=%s, plazas=%s, plazas_actuales=%s', (c[0], nueva_fecha, c[2], c[3], c[3], c[0], c[3], c[3]))
    mysql.connection.commit()
    flash('Se han copiado las clases de la semana pasada')
    return redirect('/admin/calendario/' + str(lunes) + '_0')


#Sección clientes

@admin.route('/admin/clientes')
@login_required
def clientes() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM clientes')
    datos = cur.fetchall()
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('clientes.html', datos = datos, foto = foto)

@admin.route('/admin/add_cliente', methods=['POST'])
@login_required
def add_cliente() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellidos = request.form['apellidos']
        dni = request.form['dni']
        email = request.form['email']
        cur = mysql.connection.cursor()
        fecha = date.today().strftime("%Y-%m-%d")
        cur.execute('INSERT INTO clientes VALUES(%s,%s,%s,%s,%s,%s)', (nombre, apellidos, dni, email, fecha, fecha))
        passwd = generate_password_hash('12345')
        tabla = 'clientes'
        cur.execute('INSERT INTO login VALUES(%s,%s,%s,%s)', (email, passwd, tabla, "jpeg"))
        mysql.connection.commit()
        flash('Se ha añadido el cliente con contraseña 12345')
    return redirect(url_for('.clientes'))

@admin.route('/admin/eliminar_cliente/<string:id>')
@login_required
def eliminar_cliente(id) :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    cur = mysql.connection.cursor()
    cur.execute('SELECT email FROM clientes WHERE dni = %s', [id])
    email = cur.fetchone()
    cur.execute('DELETE FROM clientes WHERE dni = %s', [id])
    cur.execute('DELETE FROM login WHERE email = %s', [email])
    mysql.connection.commit()
    flash('Se ha eliminado el cliente')
    return redirect(url_for('.clientes'))

@admin.route('/admin/pago_cliente/<string:id>')
@login_required
def pago_cliente(id) :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    cur = mysql.connection.cursor()
    fecha = date.today().strftime("%Y-%m-%d")
    cur.execute('UPDATE clientes SET fecha_ult_pago = %s WHERE dni = %s', (fecha, id))
    mysql.connection.commit()
    flash('Se ha actualizado el pago')
    return redirect(url_for('.clientes'))

#Sección trabajadores

@admin.route('/admin/trabajadores')
@login_required
def trabajadores() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM trabajadores')
    datos = cur.fetchall()
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('trabajadores.html', datos=datos, foto=foto)

@admin.route('/admin/add_trabajador', methods=['POST'])
@login_required
def add_trabajador() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellidos = request.form['apellidos']
        dni = request.form['dni']
        email = request.form['email']
        cur = mysql.connection.cursor()
        fecha = date.today().strftime("%Y-%m-%d")
        cur.execute('INSERT INTO trabajadores VALUES(%s,%s,%s,%s,%s,%s)', (nombre, apellidos, dni, email, fecha, fecha))
        passwd = generate_password_hash('12345')
        tabla = 'trabajadores'
        cur.execute('INSERT INTO login VALUES(%s,%s,%s,%s)', (email, passwd, tabla, "jpeg"))
        mysql.connection.commit()
        flash('Se ha añadido el trabajador con contraseña 12345')
    return redirect(url_for('.trabajadores'))

@admin.route('/admin/eliminar_trabajador/<string:id>')
@login_required
def eliminar_trabajador(id) :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    cur = mysql.connection.cursor()
    cur.execute('SELECT email FROM trabajadores WHERE dni = %s', [id])
    email = cur.fetchone()
    cur.execute('DELETE FROM trabajadores WHERE dni = %s', [id])
    cur.execute('DELETE FROM login WHERE email = %s', [email])
    mysql.connection.commit()
    flash('Se ha eliminado el trabajador')
    return redirect(url_for('.trabajadores'))

@admin.route('/admin/cobro_trabajador/<string:id>')
@login_required
def cobro_trabajador(id) :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    cur = mysql.connection.cursor()
    fecha = date.today().strftime("%Y-%m-%d")
    cur.execute('UPDATE trabajadores SET fecha_ult_cobro = %s WHERE dni = %s', (fecha, id))
    mysql.connection.commit()
    flash('Se ha actualizado el cobro')
    return redirect(url_for('.trabajadores'))

#Sección perfil

@admin.route('/admin/perfil')
@login_required
def perfil() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('perfil.html', foto = foto)

@admin.route('/admin/cambiar_contrasena', methods=['POST'])
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
    return redirect(url_for('.perfil'))

@admin.route('/admin/cambiar_foto', methods=['POST'])
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
    return redirect(url_for('.perfil'))


#Log out
@admin.route('/admin/logout')
@login_required
def logout() :
    logout_user()
    return redirect(url_for('public.login'))


#Páginas de error
@admin.route('/admin/404')
@login_required
def error404() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('404.html', foto = foto)