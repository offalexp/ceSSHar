#!/usr/bin/env python
# coding=utf-8
from claseCrassh import claseCrassh

class Switch(object):
   
    def __init__(self):
        self.ip = "192.168.1.20"
        self.hostname = "prueba"
        self.ubicacion = "algun lado"
        self.marca = "Cisko"
        self.modelo = "2019 con GNC"
        self.sistemaOperativo = "IOS 501"
        self.usuario = "admin"
        self.password = "1234"
        self.conectado = False
        self.objCrassh = claseCrassh()
        return None
    def getIP(self):
        return self.ip
    def setIP(self, direccionIP):
        # aca se podria usar una validacion de formato de IP
        self.ip = direccionIP
        return None
    def verificarConectividad(self):
        # implementar un ping aqui
        return None
    def getHostname(self):
        return self.hostname
    def conectar(self):
        nombre = self.objCrassh.connect(self.ip, self.usuario, self.password, True, self.password)
        if not nombre:
            self.conectado = False 
        else:
            self.hostname = nombre
            self.conectado = True
        return None
    def traerInformacion(self):
        # carga los datos del switch a partir de lo que obtenga del mismo
        # si falla retorna false
        return True
    def setCredenciales(self, usuario, password):
        self.usuario = usuario
        self.password = password
        return None
    


    



