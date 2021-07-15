from django.contrib import admin

# Register your models here.
from .models import  Profile, Notice, ChfidTempInsuree
admin.site.register(Profile)
admin.site.register(Notice)
admin.site.register(ChfidTempInsuree)
