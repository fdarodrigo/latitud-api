# No arquivo models.py do seu app "core"
from django.db import models

class Imovel(models.Model):
    endereco = models.CharField(max_length=255)
    valor_aluguel = models.DecimalField(max_digits=10, decimal_places=2)
    quartos = models.PositiveIntegerField()
    area = models.DecimalField(max_digits=10, decimal_places=2)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.endereco
