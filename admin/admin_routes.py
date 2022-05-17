import email
from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash
from datetime import date, datetime, timedelta
from werkzeug.security import generate_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required


#Creamos la Blueprint
admin = Blueprint('admin', __name__, template_folder='templates', static_folder='static', static_url_path='/admin/static')

#Importamos la base de datos
from app import mysql


#ADMINISTRADOR

#Página principal

@admin.route('/admin/')
@login_required
def index() :
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
    return render_template('index_admin.html', nClientes = nClientes, nTrabajadores = nTrabajadores, nClases = nClases)

#Sección calendario

@admin.route('/admin/calendario')
@login_required
def calendario() :
    hoy = date.today()
    dia_semana = datetime.today().weekday()
    lunes = hoy - timedelta(days=dia_semana)
    dias = list()
    for i in range(5) :
        dias.append((lunes + timedelta(days=i)))
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM clases WHERE fecha BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE)', (dias[0], dias[4]))
    aux = cur.fetchall()
    clases = dict()
    for c in aux:
        clases[c[1],c[2]] = [c[0],c[3],c[4]]
    print(clases)
    horas = ['9:00-10:00','10:00-11:00','11:00-12:00','12:00-13:00','16:00-17:00','17:00-18:00','18:00-19:00','19:00-20:00']
    return render_template('calendario.html', dias = dias, clases = clases, horas=horas)

@admin.route('/admin/add_clase/<string:cadena>', methods=['POST'])
@login_required
def add_clase(cadena) :
    if request.method == 'POST':
        nombre = request.form['nombre']
        plazas = int(request.form['plazas'])
        fecha = cadena.split('_')[0]
        hora = cadena.split('_')[1]
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO clases VALUES(%s,%s,%s,%s,%s)', (nombre, fecha, hora, plazas, plazas))
        mysql.connection.commit()
        flash('Se ha añadido la clase')
    return redirect(url_for('.calendario'))

#Sección clientes

@admin.route('/admin/clientes')
@login_required
def clientes() :
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM clientes')
    datos = cur.fetchall()
    print(datos)
    return render_template('clientes.html', datos=datos)

@admin.route('/admin/add_cliente', methods=['POST'])
@login_required
def add_cliente() :
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
        cur.execute('INSERT INTO login VALUES(%s,%s,%s)', (email, passwd, tabla))
        mysql.connection.commit()
        flash('Se ha añadido el cliente con contraseña 12345')
    return redirect(url_for('.clientes'))

@admin.route('/admin/eliminar_cliente/<string:id>')
@login_required
def eliminar_cliente(id) :
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
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM trabajadores')
    datos = cur.fetchall()
    return render_template('trabajadores.html', datos=datos)

@admin.route('/admin/add_trabajador', methods=['POST'])
@login_required
def add_trabajador() :
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
        cur.execute('INSERT INTO login VALUES(%s,%s,%s)', (email, passwd, tabla))
        mysql.connection.commit()
        flash('Se ha añadido el trabajador con contraseña 12345')
    return redirect(url_for('.trabajadores'))

@admin.route('/admin/eliminar_trabajador/<string:id>')
@login_required
def eliminar_trabajador(id) :
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
    return render_template('perfil.html')

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
    return render_template('404.html')