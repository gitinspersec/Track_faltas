from django.db import models
from datetime import date

# Create your models here.

class Faltas(models.Model):
    data = models.DateField(default=date.today,null=True)

    def __str__(self):
        return f'{self.data}'

class Aluno(models.Model):
    name= models.CharField(max_length=200)
    password= models.CharField(max_length=200,null=True)
    isAdmin = models.BooleanField(default=False)
    faltas = models.ManyToManyField(Faltas, blank=True)

    def __str__(self):
        return f'{self.id}. {self.name}'
    
    def numero_de_faltas(self):
        return self.faltas.count()