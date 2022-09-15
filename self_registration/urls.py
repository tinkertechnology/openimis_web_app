from django.urls import path
from . import views

urlpatterns = [
    path('temp_insuree_reg/',views.temp_insuree_reg)
]
