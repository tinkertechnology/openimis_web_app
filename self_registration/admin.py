from django.contrib import admin

# Register your models here.
from .models import  Profile, Notice, ChfidTempInsuree, AppSettings
admin.site.register([Profile, Notice, ChfidTempInsuree, AppSettings])


