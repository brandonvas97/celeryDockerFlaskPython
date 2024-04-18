from flask.cli import FlaskGroup
from flask import Flask, jsonify, request, g
import requests
import json
from datetime import datetime, timedelta
from project.server import create_app
from celery import shared_task


app = create_app()
cli = FlaskGroup(create_app=create_app)

@shared_task(ignore_result=False) #-Line 4
def long_running_task(iterations) -> int:#-Line 5
    result = 0
    for i in iterations:
        print("/celery: ", i["id"])
        #sleep(2) 
    return result #-Line 6

@app.route("/buscar", methods=["POST"])
def buscar():
    content = request.json
    criterio = content.get("criterio", None)
    documento = content.get("documento", None)
    if criterio is None or documento is None:
        response = {'respuesta': "Campos faltantes por enviar"}
        return jsonify(response)
    if criterio == "Actor/Ofendido":
        url = 'https://api.funcionjudicial.gob.ec/EXPEL-CONSULTA-CAUSAS-SERVICE/api/consulta-causas/informacion/buscarCausas?page=1&size=300'
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
        length = len(lista_registros)
        print((length/2)-1)
        primera_lista = lista_registros[0:int((length/2)-1)]
        segunda_lista = lista_registros[int(length/2):length-1]
        result = long_running_task.delay(segunda_lista)
        for item in primera_lista:
            idJuicio = item["idJuicio"]
            url = f"https://api.funcionjudicial.gob.ec/EXPEL-CONSULTA-CAUSAS-CLEX-SERVICE/api/consulta-causas-clex/informacion/getIncidenteJudicatura/{idJuicio}"
            res = requests.get(url)
            lista_detalles = json.loads(res.text)
            nombreJudicatura = lista_detalles[0]["nombreJudicatura"]
            idJudicatura = lista_detalles[0]["idJudicatura"]
            idIncidenteJudicatura = lista_detalles[0]["lstIncidenteJudicatura"][0]["idIncidenteJudicatura"]
            idMovimientoJuicioIncidente = lista_detalles[0]["lstIncidenteJudicatura"][0]["idMovimientoJuicioIncidente"]
            incidente = lista_detalles[0]["lstIncidenteJudicatura"][0]["incidente"]
            
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
            lista_actuaciones = res.text
            #print(lista_actuaciones)
            print(item["id"])
        response = {'respuesta': "OK"}
        return jsonify(response)
    
if __name__ == "__main__":
    cli()
