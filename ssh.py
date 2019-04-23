#!/usr/bin/env python
# coding=utf-8

# requisitos: 
# bottle

try:
    import logging
    from claseCrassh import claseCrassh
    import logging.handlers
    import itertools
    import configparser
    import os, sys
    from bottle import route, run
except Exception as e:
    print("No se pudo importar un modulo requerido: " + str(e))



class SwVerif(object):       # en Python todas las clases heredan de object
    puertos = []
    conexion = claseCrassh()
    estadoPuertos = dict()
    _ARCHIVO_CONFIG = 'swOffal.ini'
    DIRECTORIO_CONFIG = "config"
    LOG_FILENAME = "swOffal.log"
    DIRECTORIO_LOG = "logs"
    TAMANIO_LOG = 200000 # en bytes
    CUANTOS_LOGS_GUARDO = 20

    def __init__(self):         # este es el constructor, el metodo que se llama al instanciar el objeto
        self.config = configparser.ConfigParser()
    def cargar(self):
        respuesta = False
        try:
            # usaremos nuestro propio log
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.DEBUG)
            # obtengo el directorio actual del archivo python
            dir_path = os.path.dirname(os.path.realpath(__file__))
            # cambio el directorio para que sea el del archivo python
            os.chdir(dir_path)
            # creamos los logs en un directorio aparte
            os.chdir(self.DIRECTORIO_LOG)        
            # rotacion de logs (notar que indico el tamaño y cuantos se retienen)
            handler = logging.handlers.RotatingFileHandler(
            self.LOG_FILENAME, maxBytes=self.TAMANIO_LOG, backupCount=self.CUANTOS_LOGS_GUARDO)
            # formato de los mensajes de log
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            # ejemplo de entrada manual al log
            self.logger.info("Inicio del programa")
        except Exception as e:
            print("No se pudo crear el objeto de logging: " + str(e))         
        try:
            # eso es para que pueda abrir el archivo INI con ruta relativa
            dir_path = os.path.dirname(os.path.realpath(__file__))
            os.chdir(dir_path)
            os.chdir(self.DIRECTORIO_CONFIG)
            # hago mis validaciones primero
            if not self.verificarExisteArchivo(self._ARCHIVO_CONFIG):
                raise FileNotFoundError
            if not self.verificarAccesoLecturaArchivo(self._ARCHIVO_CONFIG):
                raise IOError
            # leemos el archivo y validamos que lo haya encontrado (vuelvo a permitir excepciones en config.read)
            if (len(self.config.read(self._ARCHIVO_CONFIG))==0):
                self.logger.error('No se pudo abrir el archivo')
            self.config.read(self._ARCHIVO_CONFIG)
            # ahora leemos las secciones del archivo
            self.equipos = self.config.sections()
            respuesta = True
        except (configparser.ParsingError):
            self.logger.error('Hubo un error al tratar de leer el archivo de configuracion', exc_info=True)
        except (configparser.NoSectionError):
            self.logger.error('No se pudo encontrar una sección requerida en el archivo ' + self._ARCHIVO_CONFIG, exc_info=True)
        except (configparser.DuplicateSectionError):
            self.logger.error('Una de las secciones se halló duplicada en ' + self._ARCHIVO_CONFIG , exc_info=True)
        except (configparser.NoOptionError):
            self.logger.error('No se pudo encontrar la opcion requerida en el archivo ' + self._ARCHIVO_CONFIG , exc_info=True)            
        except (configparser.DuplicateOptionError):
            self.logger.error('Se encuentra duplicada la opcion en el archivo ' + self._ARCHIVO_CONFIG , exc_info=True)            
        except FileNotFoundError as fnfError:
            self.logger.error("(cargar) El archivo de configuracion " + self._ARCHIVO_CONFIG + " no existe" + str(fnfError), exc_info=True)             
        except IOError as ioerr:
            self.logger.error("(cargar) El archivo de configuracion " + self._ARCHIVO_CONFIG + " existe pero no se pudo leer" + str(ioerr), exc_info=True)  
        except KeyError as e:
            self.logger.error('Error en archivo de configuracion '+ self._ARCHIVO_CONFIG +'. Verifique la clave ' + str(e) + ' ¿está cargada correctamente? ' + self._ARCHIVO_CONFIG , exc_info=True)            
        except Exception as e1:
            self.logger.error('Error inesperado ' + str(e1) , exc_info=True)            
        finally:
            return(respuesta)
    def leerCredenciales(self, equipo):
        self.__username = self.config.get(equipo, 'username')
        self.__password = self.config.get(equipo, 'password')
    def cargarPuertosDesdeArchivo(self, equipo):
        # recibe un nombre de equipo y trae los puertos que aparecen 
        # para ese equipo en el archivo de configuracion
        self.puertos = [e.strip() for e in self.config.get(equipo, "puertos").split(',')]
    def agregarPuerto(self, nombrePuerto):
        print(self.puertos)
        # recibe un nombre de puerto y lo agrega a la lista de verificacion
        self.puertos.append(nombrePuerto)
    def conectar(self, equipo):
        # abre la conexion SSH al equipo, usando el usuario y pass que leyó del archivo de config
        nombre = self.conexion.connect(equipo, self.__username, self.__password)
        self.nombreEquipo = nombre
        if (nombre==""):
            return(False)
        else:
            return(True)
    def estaConectado(self):
        # devuelve True si está conectado (o False sino)
        return(self.conexion)
    def verificarPuertos(self):
        # recorre los puertos de la lista y ejecuta el comando en cada uno
        # luego procesa el estado y lo guarda 
        for puerto in self.puertos:
            output = self.conexion.send_command("Show interface " + puerto, self.nombreEquipo)
            words = output.split()
            gig_ind = words.index(puerto)+6 
            gig_fin = (gig_ind + 3)
            rel_ind = words.index('reliability')
            rel_fin = (rel_ind + 2)
            txl_ind = words.index('txload')
            txl_fin = (txl_ind + 2)
            rxl_ind = words.index('rxload')
            rxl_fin = (rxl_ind +2)
            crc_ind = words.index('CRC,')
            crc_men = (crc_ind - 4)
            col_ind = words.index('collisions,')
            col_men = (col_ind - 4)
            stringSw = ' '.join(words[gig_ind:gig_fin])
            stringSw1 = ' '.join(words[rel_ind:rel_fin])
            stringSw3 = ' '.join(words[crc_men:crc_ind+1])
            stringSw4 = ' '.join(words[col_men:col_ind+1])
            txl_texto = ' '.join(words[txl_ind:txl_fin])
            rxl_texto = ' '.join(words[rxl_ind:rxl_fin])    
            txl_indb = txl_texto.index('/')
            rxl_indb = rxl_texto.index('/')
            txl_indv = txl_texto.index(' ')
            rxl_indv = rxl_texto.index(' ')
            txl_dividendo = int(''.join(txl_texto[txl_indb-1:txl_indb]))
            txl_divisor = int(''.join(rxl_texto[txl_indb+1:]))
            rxl_dividendo = int(''.join(txl_texto[rxl_indb-1:rxl_indb]))
            rxl_divisor = int(''.join(rxl_texto[rxl_indb+1:]))
            resultado_txl = txl_dividendo/txl_divisor
            resultado_rxl = rxl_dividendo/rxl_divisor
            
            stringSw2 = ('txload %'+str("{0:.3f}".format(resultado_txl)) + ', rxload %'+str("{0:.3f}".format(resultado_rxl)))



            self.estadoPuertos[puerto] = (stringSw, stringSw1, stringSw2, stringSw3, stringSw4)

    def verEstadoPuertos(self):
        # muestra el estado de cada puerto
        for puerto in self.puertos:
            print("Estado de: " + puerto)
            print(self.estadoPuertos[puerto])
    def desconectar(self):
        # cierra la sesion SSH
        self.conexion.disconnect()
    def verificarExisteArchivo(self, archivo):
        # notar que la excepcion ocurre solamente si hubo un fallo al tratar de determinar la existencia
        try:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            os.chdir(dir_path)
            os.chdir(self.DIRECTORIO_CONFIG)
            respuesta = os.access(archivo, os.F_OK)
        except Exception as e:
            self.logger.error('(verificarExiste): Error al intentar determinar la existencia del archivo: ' + str(e) , exc_info=True)
            respuesta = False
        return (respuesta)
    def verificarAccesoLecturaArchivo(self, archivo):
        # notar que la excepcion ocurre solamente si hubo un fallo al tratar de determinar la posibilidad de lectura        
        try:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            os.chdir(dir_path)
            os.chdir(self.DIRECTORIO_CONFIG)
            respuesta = os.access(archivo, os.R_OK)
        except Exception as e:
            self.logger.error('(verificarAccesoLectura): Error al intentar determinar la existencia del archivo: ' + str(e) , exc_info=True)
            respuesta = False
        return (respuesta)
    def verificarAccesoEscrituraArchivo(self, archivo):
        # notar que la excepcion ocurre solamente si hubo un fallo al tratar de determinar la posibilidad de escritura        
        try:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            os.chdir(dir_path)
            os.chdir(self.DIRECTORIO_CONFIG)
            respuesta = os.access(archivo, os.W_OK)
        except Exception as e:
            self.logger.error('(verificarAccesoEscritura): Error al intentar determinar la existencia del archivo: ' + str(e) , exc_info=True)
            respuesta = False
        return (respuesta)        
    


prueba = SwVerif()
"prueba.cargar()"

        
        

""" 
# prueba.agregarPuerto("GigabitEthernet0/4")
# prueba.agregarPuerto("GigabitEthernet0/5")
prueba.agregarPuerto("GigabitEthernet0/11")
prueba.conectar()
prueba.verificarPuertos()
prueba.verEstadoPuertos()
prueba.desconectar()
"""
