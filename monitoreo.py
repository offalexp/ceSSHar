try:
    import logging
    from claseCrassh import clsCrassh
    import logging.handlers
    import itertools
    import configparser
    import os, sys
    from bottle import route, run
except Exception as e:
    print("No se pudo importar un modulo requerido: " + str(e))

def traeestado(swEelegido, swCmdElegido):
    config = configparser.ConfigParser()
    config.__username = "username"
    config.__password = "password"    
    nombre = self.conexion.connect(, config.__username, config.__password)
    config.nombreEquipo = nombre





