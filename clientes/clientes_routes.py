from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash
from datetime import date, datetime, timedelta
from pyparsing import removeQuotes
from werkzeug.security import generate_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from app import app


#Creamos la Blueprint
clientes = Blueprint('clientes', __name__, template_folder='templates', static_folder='static', static_url_path='/clientes/static')

#Importamos la base de datos
from app import mysql


#ENTRENADOR

#Página principal

@clientes.route('/clientes/')
@login_required
def index() :
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
    return render_template('index_clientes.html', nClases = nClases, nombreRutina = nombreRutina)


#Rutina

@clientes.route('/clientes/rutina')
@login_required
def rutina() :
    diaSemana = datetime.today().weekday()
    diasSemana = ['lunes','martes','miercoles','jueves','viernes']
    strDiaSemana = diasSemana[diaSemana]
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
            strGrupos += grupos[i] + ","
        grupos = strGrupos[:len(strGrupos) - 1] + " y " + grupos[len(grupos) - 1]
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
        return render_template('rutina_cliente.html', datosRutina = datosRutina, ejercicios = ejercicios, pesos = pesos, dia = strDiaSemana, datosEjercicios = datosEjercicios, grupos = grupos)
    else :
        return redirect('/clientes/elegir_rutina')


@clientes.route('/clientes/elegir_rutina')
@login_required
def elegir_rutina() :
    cur = mysql.connection.cursor()
    intensidades = ['baja','media','alta']
    rutinas = dict()
    for intensidad in intensidades :
        cur.execute('SELECT * FROM rutinas WHERE intensidad = %s', [intensidad])
        rutinas[intensidad] = cur.fetchall()
    return render_template('elegir_rutina.html', rutinas = rutinas)


@clientes.route('/clientes/elegir_rutina/<string:id>')
@login_required
def elegir_rutina_id(id) :
    dni = current_user.dni
    cur = mysql.connection.cursor()
    cur.execute('INSERT INTO rutinas_clientes (dniCliente, idRutina) VALUES (%s, %s) ON DUPLICATE KEY UPDATE idrutina=%s', (dni, id, id))
    cur.connection.commit()
    return redirect('/clientes/rutina')


@clientes.route('/clientes/cambiar_pesos', methods=['POST'])
@login_required
def cambiar_pesos() :
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


#Sección clases

@clientes.route('/clientes/clases')
@login_required
def clases() :
    hoy = date.today()
    dia_semana = datetime.today().weekday()
    lunes = hoy - timedelta(days=dia_semana)
    return redirect('/clientes/clases/' + str(lunes) + '_0')

@clientes.route('/clientes/clases/<string:aux>')
@login_required
def clases_fecha(aux) :
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
    return render_template('clases.html', dias = dias, clases = clases, horas = horas, clasesApuntado = clasesApuntado, lunes = lunes)

@clientes.route('/clientes/apuntar_a_clase/<string:cadena>', methods=['POST'])
@login_required
def add_clase(cadena) :
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
    if request.method == 'POST':
        fecha = cadena.split('_')[0]
        hora = cadena.split('_')[1]
        dni = current_user.dni
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM clases_clientes WHERE dniCliente = %s', [dni])
        cur.execute('UPDATE clases SET plazas_actuales = (plazas_actuales + 1) WHERE (fecha = %s AND hora = %s)', (fecha, hora))
        mysql.connection.commit()
        flash('Te has desapuntado de la clase')
    return redirect(url_for('.clases'))


#Sección perfil

@clientes.route('/clientes/perfil')
@login_required
def perfil() :
    return render_template('perfil_cliente.html')


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
    return render_template('404_cliente.html')