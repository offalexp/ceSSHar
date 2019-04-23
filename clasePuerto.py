#!/usr/bin/env python
# coding=utf-8

class clasePuerto(object):
    def __init__(self):
        self.nombre = ""
        self.velocidad = 10 # puede ser 10, 100 o 1000
        self.velocidadMaxima = 10 # normalmente es 100 o 1000
        self.troncal = False
        self.erroresInput = 0
        self.erroresCRC = 0
        self.confiabilidad = 1
        self.carga = 0
        return None
    def esTroncal(self):
        # devuelve true/false segun el puerto este configurado como TRUNK
        return self.troncal
    def procesarDatosEstado(self, infoCruda):
        # aqui tomariamos los datos crudos del switch y los asignariamos a cada atributo
        return None
    def tieneProblemas(self):
        # este metodo analiza los datos del puerto
        # los compara con umbrales establecidos
        # y devuelve true/false segun el puerto tenga problemas
        return False
    def leerValoresReferencia(self):
        # este metodo carga los valores de referencia
        # que podrian tomarse por ejemplo de un archivo de config
        return True