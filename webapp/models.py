from django.db import models
from insuree.apps import InsureeConfig
from insuree import models as insuree_models

# Create your models here.
class InsureeAuth(models.Model):
    insuree = models.OneToOneField(insuree_models.Insuree, on_delete=models.DO_NOTHING,
                                db_column='InsureeID', blank=True, null=True, related_name="verified_insurees")
    token = models.CharField(max_length=300)
    otp = models.CharField(max_length=10, null=True, blank=True)
    password = models.CharField(max_length=50)

    def __str__(self):
        name = ''
        if self.insuree.other_names:
            name= self.insuree.other_names
        return name



class Notice(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    active = models.BooleanField(default=True)
    created_at =  models.DateTimeField(verbose_name='date added', auto_now_add=True)
    updated_at =   models.DateTimeField(verbose_name='date updated', auto_now_add=True)
    
    def __str__(self):
        return self.title

