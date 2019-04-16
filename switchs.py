from django.db import models

class  Switch(models.Model):
    ip = models.CharField(max_length=16)
    hostname = models.TextField()
    ubicacion = models.CharField(max_length=20)
    marca = models.CharField()
    modelo = models.CharField()
    firmware = models.CharField()


