import os
import time
import sqlite3
import requests
import json
from datetime import datetime
import psycopg2

from celery import Celery

#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#db_path = os.path.join(BASE_DIR, "main/test.db")
#conn = sqlite3.connect(db_path, check_same_thread=False)


celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")


@celery.task(name="create_task")
def create_task(task_type):
    time.sleep(int(task_type) * 10)
    return True

@celery.task(bind=True)
def insert_data(self, lista_datos, cedula):
    result = 0
    parametros = {
        "host": "postgres",
        "port": 5432,
        "user": "postgres",
        "password": "postgres",
        "database": "postgres"
    }
    conn = psycopg2.connect(**parametros)
    for item in lista_datos:
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
                                VALUES('{formatdate}', '{idJuicio}','{item["nombreDelito"]}','{nombresLitigante}','{nombresLitiganteDem}','{cedula}','{nombreTipoAccion}','{i["tipo"]}','{formatdate2}');'''
                    #print(sql)
                    cur = conn.cursor()
                    cur.execute(sql)
                    conn.commit()
    return result


@celery.task(bind=True)
def test_connection(self):
    result = 0
    url = 'https://api.funcionjudicial.gob.ec/EXPEL-CONSULTA-CAUSAS-SERVICE/api/consulta-causas/informacion/buscarCausas?page=1&size=300'
    documento = "0968599020001"
    body = {
        "numeroCausa": "",
        "actor": {
            "cedulaActor": "0968599020001",
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
    res = requests.post(url=url, json=body)
    print(res.status_code)
    lista_registros = json.loads(res.text)
    return result