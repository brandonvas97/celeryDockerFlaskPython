# project/server/main/views.py

from celery.result import AsyncResult
from flask import render_template, Blueprint, jsonify, request, current_app
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from celery import shared_task, Celery
from datetime import datetime
from time import sleep
from psycopg2.extras import RealDictCursor
import requests
import json
#import sqlite3
import psycopg2
import os
import math
import csv

#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#db_path = os.path.join(BASE_DIR, "test.db")
#conn = sqlite3.connect(db_path, check_same_thread=False)

from project.server.tasks import create_task, insert_data, test_connection


main_blueprint = Blueprint("main", __name__,)


@main_blueprint.route("/", methods=["GET"])
def home():
    return render_template("main/home.html")


@main_blueprint.route("/tasks", methods=["POST"])
def run_task():
    content = request.json
    task_type = content["type"]
    task = create_task.delay(int(task_type))
    return jsonify({"task_id": task.id}), 202


@main_blueprint.route("/tasks/<task_id>", methods=["GET"])
def get_status(task_id):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    return jsonify(result), 200


@main_blueprint.route("/login", methods=["POST"])
def login():
    content = request.json
    usuario = content.get("usuario", None)
    contraseña = content.get("contraseña", None)
    if usuario is None or contraseña is None:
        response = {'respuesta': "Campos faltantes por enviar"}
        return jsonify(response)
    parametros = {
        "host": "postgres",
        "port": 5432,
        "user": "postgres",
        "password": "postgres",
        "database": "postgres"
    }
    conn = psycopg2.connect(**parametros)
    contraseña = contraseña.encode('utf-8')
    hex1 = contraseña.hex()
    sql = f"SELECT * FROM usuarios WHERE usuario = '{usuario}' AND contraseña = '{hex1}'"
    cursor = conn.cursor()
    cursor.execute(sql)
    resultados = cursor.fetchall()
    if len(resultados) > 0:
        access_token = create_access_token(identity=usuario)
        response = {'token': access_token}
        return jsonify(response)
    else:
        response = {'respuesta': "Credenciales no validas"}
        return jsonify(response)


@main_blueprint.route("/buscar", methods=["POST"])
@jwt_required()
def buscar():
    content = request.json
    criterio = content.get("criterio", None)
    documento = content.get("documento", None)
    parametros = {
        "host": "postgres",
        "port": 5432,
        "user": "postgres",
        "password": "postgres",
        "database": "postgres"
    }
    conn = psycopg2.connect(**parametros)
    
    if criterio is None or documento is None:
        response = {'respuesta': "Campos faltantes por enviar"}
        return jsonify(response)
    if criterio == "Actor/Ofendido" or criterio == "Demandado/Procesado":
        url = 'https://api.funcionjudicial.gob.ec/EXPEL-CONSULTA-CAUSAS-SERVICE/api/consulta-causas/informacion/buscarCausas?page=1&size=300'
        if criterio == "Actor/Ofendido":
            body = {
                "numeroCausa": "",
                "actor": {
                    "cedulaActor": documento,
                    "nombreActor": ""
                },
                "demandado": {
                    "cedulaDemandado": "",
                    "nombreDemandado": ""
                },
                "provincia": "",
                "numeroFiscalia": "",
                "recaptcha": "verdad",
                "first": 1,
                "pageSize": 300
            }
        elif criterio == "Demandado/Procesado":
            body = {
                "numeroCausa": "",
                "actor": {
                    "cedulaActor": "",
                    "nombreActor": ""
                },
                "demandado": {
                    "cedulaDemandado": documento,
                    "nombreDemandado": ""
                },
                "provincia": "",
                "numeroFiscalia": "",
                "recaptcha": "verdad",
                "first": 1,
                "pageSize": 300
            }
        res = requests.post(url=url, json=body)
        print(res.status_code)
        lista_registros = json.loads(res.text)
        length = len(lista_registros)
        print(length)
        #Ajuste del numero de tareas
        if length > 5:
            iteration = math.ceil(length/5)
            i = 5
            for y in range(1, iteration):
                j = i + 5
                if j > length:
                    j = length
                task_celery = insert_data.delay(lista_registros[i:j], documento)
                i += 5
            primera_lista = lista_registros[0:5]
        else:
            primera_lista = lista_registros[0:length]
        for item in primera_lista:
            idJuicio = item["idJuicio"]
            url = f"https://api.funcionjudicial.gob.ec/EXPEL-CONSULTA-CAUSAS-CLEX-SERVICE/api/consulta-causas-clex/informacion/getIncidenteJudicatura/{idJuicio}"
            url2 = f"https://api.funcionjudicial.gob.ec/EXPEL-CONSULTA-CAUSAS-SERVICE/api/consulta-causas/informacion/getInformacionJuicio/{idJuicio}"
            res = requests.get(url)
            lista_detalles = json.loads(res.text)
            res2 = requests.get(url2)
            lista_detalles_2 = json.loads(res2.text)
            if len(lista_detalles) > 0 and len(lista_detalles_2) > 0:
                nombreJudicatura = lista_detalles[0]["nombreJudicatura"]
                idJudicatura = lista_detalles[0]["idJudicatura"]
                idIncidenteJudicatura = lista_detalles[0]["lstIncidenteJudicatura"][0]["idIncidenteJudicatura"]
                idMovimientoJuicioIncidente = lista_detalles[0]["lstIncidenteJudicatura"][0]["idMovimientoJuicioIncidente"]
                incidente = lista_detalles[0]["lstIncidenteJudicatura"][0]["incidente"]

                lstIncidenteJudicatura = lista_detalles[0]["lstIncidenteJudicatura"][0]
                
                url = "https://api.funcionjudicial.gob.ec/EXPEL-CONSULTA-CAUSAS-SERVICE/api/consulta-causas/informacion/actuacionesJudiciales"
                body = {
                    "idMovimientoJuicioIncidente": idMovimientoJuicioIncidente,
                    "idJuicio": idJuicio,
                    "idJudicatura": idJudicatura,
                    "idIncidenteJudicatura": idIncidenteJudicatura,
                    "aplicativo": "web",
                    "nombreJudicatura": nombreJudicatura,
                    "incidente": incidente
                }
                res = requests.post(url=url, json=body)
                lista_actuaciones = json.loads(res.text)
                #print(lista_actuaciones)
                if len(lista_actuaciones) > 0:
                    for i in lista_actuaciones:
                        print(lista_actuaciones[0]["codigo"])
                        formatdate = datetime.strptime(item["fechaIngreso"][0:19], "%Y-%m-%dT%H:%M:%S")
                        formatdate = formatdate.strftime("%Y-%m-%d %H:%M")
                        formatdate2 = datetime.strptime(i["fecha"][0:19], "%Y-%m-%dT%H:%M:%S")
                        formatdate2 = formatdate2.strftime("%Y-%m-%d %H:%M")
                        nombresLitigante = "No registrado"
                        nombresLitiganteDem = "No registrado"
                        if lstIncidenteJudicatura.get("lstLitiganteActor", None) is not None:
                            if len(lstIncidenteJudicatura["lstLitiganteActor"]) > 0:
                                nombresLitigante = lstIncidenteJudicatura["lstLitiganteActor"][0]["nombresLitigante"]
                        if lstIncidenteJudicatura.get("lstLitiganteDemandado", None) is not None:
                            if len(lstIncidenteJudicatura["lstLitiganteDemandado"]) > 0:
                                nombresLitiganteDem = lstIncidenteJudicatura["lstLitiganteDemandado"][0]["nombresLitigante"]
                        nombreTipoAccion = lista_detalles_2[0]["nombreTipoAccion"]
                        sql = f'''INSERT INTO procesos(fecha, numproceso, accion, actores, procesados, cedulaactor, tipoaccion, tipojudicial, fechajudicial)
                                    VALUES('{formatdate}', '{idJuicio}','{item["nombreDelito"]}','{nombresLitigante}','{nombresLitiganteDem}','{documento}','{nombreTipoAccion}','{i["tipo"]}','{formatdate2}');'''
                        #print(sql)
                        cur = conn.cursor()
                        cur.execute(sql)
                        conn.commit()
        response = {'respuesta': "OK"}
        return jsonify(response)
    else:
        response = {'respuesta': "Criterio no encontrado"}
        return jsonify(response)


@main_blueprint.route("/consultar", methods=["POST"])
@jwt_required()
def consultar():
    content = request.json
    documento = content.get("documento", None)
    parametros = {
        "host": "postgres",
        "port": 5432,
        "user": "postgres",
        "password": "postgres",
        "database": "postgres"
    }
    conn = psycopg2.connect(**parametros, cursor_factory=RealDictCursor)
    
    if documento is None:
        response = {'respuesta': "Campos faltantes por enviar"}
        return jsonify(response)
    cursor = conn.cursor()
    sql = f"SELECT * FROM procesos WHERE cedulaactor = '{documento}'"
    cursor.execute(sql)
    resultados = cursor.fetchall()
    if len(resultados) == 0:
        response = {'respuesta': "Datos no encontrados para el documento dado"}
        return jsonify(response)
    data = []
    for i in resultados:
        data.append(i)
    json_data = json.dumps(data, indent=4, default=str, ensure_ascii=False)
    respuesta = data
    data = json.loads(json_data)
    header = data[0].keys()
    csv_file = 'datos.csv'
    csv_obj = open(csv_file, 'w')
    csv_writer = csv.writer(csv_obj)
    csv_writer.writerow(header)
    for item in data:
        csv_writer.writerow(item.values())
    response = {'respuesta': respuesta}
    return jsonify(response)



@main_blueprint.route("/prueba", methods=["POST"])
@jwt_required()
def prueba():
    id_tareas = []
    for i in range(1, 15):
        task_celery = test_connection.delay()
        id_tareas.append(task_celery.id)
    
    sleep(2)
    for i in id_tareas:
        res = AsyncResult(task_celery.id).state
        if res != "SUCCESS":
            response = {'respuesta': "Test fallido"}
            return jsonify(response)
    response = {'respuesta': "Test realizado"}
    return jsonify(response)