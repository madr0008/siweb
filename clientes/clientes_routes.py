from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash
from datetime import date, datetime, timedelta
from pyparsing import removeQuotes
from werkzeug.security import generate_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from app import app
from os.path import exists


#Creamos la Blueprint
clientes = Blueprint('clientes', __name__, template_folder='templates', static_folder='static', static_url_path='/clientes/static')

#Importamos la base de datos
from app import mysql

#Función para comprobar el tipo de usuario
def comprobarTipo() :
    if current_user.tipo != 'clientes' :
        logout_user()
        return False
    return True


#CLIENTE

#Página principal

@clientes.route('/clientes/')
@login_required
def index() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    cur = mysql.connection.cursor()
    dni = current_user.dni
    hoy = date.today()
    dia_semana = datetime.today().weekday()
    lunes = hoy - timedelta(days=dia_semana)
    viernes = lunes + timedelta(7)
    cur.execute('SELECT COUNT(*) FROM clases_clientes WHERE ((fecha BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE)) AND (dniCliente = %s))', (lunes, viernes, dni))
    nClases = cur.fetchone()[0]
    cur.execute('SELECT nombre FROM rutinas, rutinas_clientes WHERE ((idRutina = id) AND (dniCliente = %s))', [dni])
    nombreRutina = cur.fetchone()
    if nombreRutina != None :
        nombreRutina = nombreRutina[0]
    else :
        nombreRutina = "Ninguna"
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('index_clientes.html', nClases = nClases, nombreRutina = nombreRutina, foto = foto)


#Rutina

@clientes.route('/clientes/rutina')
@login_required
def rutina() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    diaSemana = datetime.today().weekday()
    diasSemana = ['lunes','martes','miercoles','jueves','viernes', 'sabado', 'domingo']
    strDiaSemana = diasSemana[diaSemana]
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    if diaSemana > 4 :
        return render_template('rutina_cliente_no.html', dia = strDiaSemana, foto = foto)
    cur = mysql.connection.cursor()
    sql = 'SELECT idRutina, ' + strDiaSemana + ' FROM rutinas_clientes WHERE dniCliente = %s'
    cur.execute(sql, [current_user.dni])
    aux = cur.fetchone()
    if aux != None :
        idRutina = aux[0]
        strPesos = aux[1]
        cur.execute('SELECT * FROM rutinas WHERE id = %s', [idRutina])
        datosRutina = cur.fetchone()
        sql = 'SELECT ' + strDiaSemana + ' FROM dias_rutinas WHERE idRutina = %s'
        cur.execute(sql, [idRutina])
        ejcs = cur.fetchone()[0].split(',')
        ejercicios = list()
        datosEjercicios = dict()
        listaPesos = strPesos.split(',')
        pesos = dict()
        grupos = list()
        for ejc in ejcs :
                if len(ejc) > 0 :
                    campos = ejc.split('-')
                    ejercicios.append([int(campos[0]), int(campos[1]), int(campos[2])])
                    cur.execute('SELECT * FROM ejercicios WHERE id = %s', [int(campos[0])])
                    datosEjercicios[int(campos[0])] = cur.fetchone()
                    if datosEjercicios[int(campos[0])][3] not in grupos :
                        grupos.append(datosEjercicios[int(campos[0])][3])
        strGrupos = ""
        for i in range(len(grupos) - 1) :
            strGrupos += grupos[i] + ", "
        if len(grupos) > 1 :
            grupos = strGrupos[:len(strGrupos) - 2] + " y " + grupos[len(grupos) - 1]
        else :
            grupos = grupos[len(grupos) - 1]
        cont = 0
        if len(listaPesos) > 1 or listaPesos[0] != '' :
            for ejc in ejercicios :
                try :
                    pesos[ejc[0]] = listaPesos[cont]
                except :
                    pesos[ejc[0]] = 0
                cont +=1
        else :
            for ejc in ejercicios :
                pesos[ejc[0]] = 0
        return render_template('rutina_cliente.html', datosRutina = datosRutina, ejercicios = ejercicios, pesos = pesos, dia = strDiaSemana, datosEjercicios = datosEjercicios, grupos = grupos, foto = foto)
    else :
        return redirect('/clientes/elegir_rutina')


@clientes.route('/clientes/elegir_rutina')
@login_required
def elegir_rutina() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    cur = mysql.connection.cursor()
    intensidades = ['baja','media','alta']
    rutinas = dict()
    for intensidad in intensidades :
        cur.execute('SELECT * FROM rutinas WHERE intensidad = %s', [intensidad])
        rutinas[intensidad] = cur.fetchall()
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('elegir_rutina.html', rutinas = rutinas, foto = foto)


@clientes.route('/clientes/elegir_rutina/<string:id>')
@login_required
def elegir_rutina_id(id) :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    dni = current_user.dni
    cur = mysql.connection.cursor()
    cur.execute('INSERT INTO rutinas_clientes (dniCliente, idRutina) VALUES (%s, %s) ON DUPLICATE KEY UPDATE idRutina=%s', (dni, id, id))
    cur.connection.commit()
    return redirect('/clientes/rutina')


@clientes.route('/clientes/cambiar_pesos', methods=['POST'])
@login_required
def cambiar_pesos() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    if request.method == 'POST':
        dni = current_user.dni
        diaSemana = datetime.today().weekday()
        diasSemana = ['lunes','martes','miercoles','jueves','viernes']
        strDiaSemana = diasSemana[diaSemana]
        cur = mysql.connection.cursor()
        sql = 'SELECT idRutina, ' + strDiaSemana + ' FROM rutinas_clientes WHERE dniCliente = %s'
        cur.execute(sql, [current_user.dni])
        aux = cur.fetchone()
        pesosAntiguos = aux[1]
        pesos = ""
        aux = request.form.getlist('pesos')
        for peso in aux[:len(aux) - 1] :
            pesos += str(peso) + ','
        pesos = pesos[:len(pesos) - 1]
        if pesos != pesosAntiguos :
            sql = 'UPDATE rutinas_clientes SET ' + strDiaSemana + ' = %s WHERE dniCliente = %s'
        cur.execute(sql, (pesos, dni))
        mysql.connection.commit()
        return redirect('/clientes')



#Dieta

@clientes.route('/clientes/dieta')
@login_required
def dieta() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    diaSemana = datetime.today().weekday()
    diasSemana = ['lunes','martes','miercoles','jueves','viernes', 'sabado', 'domingo']
    strDiaSemana = diasSemana[diaSemana]
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    if diaSemana > 4 :
        return render_template('rutina_dieta_no.html', dia = strDiaSemana, foto = foto)
    cur = mysql.connection.cursor()
    sql = 'SELECT idDieta, ' + strDiaSemana + ' FROM dietas_clientes WHERE dniCliente = %s'
    cur.execute(sql, [current_user.dni])
    aux = cur.fetchone()
    if aux != None :
        idDieta = aux[0]
        cur.execute('SELECT * FROM dietas WHERE id = %s', [idDieta])
        datosDieta = cur.fetchone()
        sql = 'SELECT ' + strDiaSemana + ' FROM dias_dietas WHERE idDieta = %s'
        cur.execute(sql, [idDieta])
        comis = cur.fetchone()[0].split(',')
        comidas = list()
        datosComidas = dict()
        macros = list()
        for comi in comis :
                if len(comi) > 0 :
                    campos = comi.split('-')
                    comidas.append([int(campos[0]), int(campos[1])])
                    cur.execute('SELECT * FROM comidas WHERE id = %s', [int(campos[0])])
                    datosComidas[int(campos[0])] = cur.fetchone()
                    if datosComidas[int(campos[0])][3] not in macros :
                        macros.append(datosComidas[int(campos[0])][3])
        strMacros = ""
        for i in range(len(macros) - 1) :
            strMacros += macros[i] + ", "
        if len(macros) > 1 :
            macros = strMacros[:len(strMacros) - 2] + " y " + macros[len(macros) - 1]
        elif len(macros) == 1 :
            macros = macros[len(macros) - 1]
        return render_template('dieta_cliente.html', datosDieta = datosDieta, comidas = comidas, dia = strDiaSemana, datosComidas = datosComidas, macros = macros, foto = foto)
    else :
        return redirect('/clientes/elegir_dieta')


@clientes.route('/clientes/elegir_dieta')
@login_required
def elegir_dieta() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    cur = mysql.connection.cursor()
    objetivos = ['bajar peso','mantener peso','subir peso']
    dietas = dict()
    for objetivo in objetivos :
        cur.execute('SELECT * FROM dietas WHERE objetivo = %s', [objetivo])
        dietas[objetivo] = cur.fetchall()
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('elegir_dieta.html', dietas = dietas, foto = foto)


@clientes.route('/clientes/elegir_dieta/<string:id>')
@login_required
def elegir_dieta_id(id) :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    dni = current_user.dni
    cur = mysql.connection.cursor()
    cur.execute('INSERT INTO dietas_clientes (dniCliente, idDieta) VALUES (%s, %s) ON DUPLICATE KEY UPDATE idDieta=%s', (dni, id, id))
    cur.connection.commit()
    return redirect('/clientes/dieta')



#Sección clases

@clientes.route('/clientes/clases')
@login_required
def clases() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    hoy = date.today()
    dia_semana = datetime.today().weekday()
    lunes = hoy - timedelta(days=dia_semana)
    return redirect('/clientes/clases/' + str(lunes) + '_0')

@clientes.route('/clientes/clases/<string:aux>')
@login_required
def clases_fecha(aux) :
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
    dni = current_user.dni
    cur.execute('SELECT fecha, hora FROM clases_clientes WHERE ((fecha BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE)) AND (dniCliente = %s))', (dias[0], dias[4], dni))
    clasesApuntado = cur.fetchall()
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('clases.html', dias = dias, clases = clases, horas = horas, clasesApuntado = clasesApuntado, lunes = lunes, foto = foto)

@clientes.route('/clientes/apuntar_a_clase/<string:cadena>', methods=['POST'])
@login_required
def add_clase(cadena) :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    if request.method == 'POST':
        fecha = cadena.split('_')[0]
        hora = cadena.split('_')[1]
        dni = current_user.dni
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO clases_clientes VALUES(%s,%s,%s)', (dni, fecha, hora))
        cur.execute('UPDATE clases SET plazas_actuales = (plazas_actuales - 1) WHERE (fecha = %s AND hora = %s)', (fecha, hora))
        mysql.connection.commit()
        flash('Te has apuntado a la clase')
    return redirect(url_for('.clases'))


@clientes.route('/clientes/desapuntar_de_clase/<string:cadena>', methods=['POST'])
@login_required
def eliminar_clase(cadena) :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    if request.method == 'POST':
        fecha = cadena.split('_')[0]
        hora = cadena.split('_')[1]
        dni = current_user.dni
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM clases_clientes WHERE (dniCliente = %s AND fecha = %s AND hora = %s)', (dni, fecha, hora))
        cur.execute('UPDATE clases SET plazas_actuales = (plazas_actuales + 1) WHERE (fecha = %s AND hora = %s)', (fecha, hora))
        mysql.connection.commit()
        flash('Te has desapuntado de la clase')
    return redirect(url_for('.clases'))


#Sección perfil

@clientes.route('/clientes/perfil')
@login_required
def perfil() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('perfil_cliente.html', foto = foto)

@clientes.route('/clientes/cambiar_contrasena', methods=['POST'])
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
    return redirect('/clientes/perfil')

@clientes.route('/clientes/cambiar_foto', methods=['POST'])
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
    return redirect('/clientes/perfil')


#Log out
@clientes.route('/clientes/logout')
@login_required
def logout() :
    logout_user()
    return redirect(url_for('public.login'))


#Páginas de error
@clientes.route('/clientes/404')
@login_required
def error404() :
    if not comprobarTipo() :
        return redirect(url_for('public.login'))
    foto = "default.jpeg"
    if exists(app.config['UPLOAD_FOLDER'] + "/" + str(current_user.dni) + '.' + current_user.extension) :
        foto = str(current_user.dni) + '.' + current_user.extension
    return render_template('404_cliente.html', foto = foto)