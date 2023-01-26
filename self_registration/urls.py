from django.urls import path
from . import views

urlpatterns = [
    path('temp_insuree_reg/',views.temp_insuree_reg),
    path('get_insuree_details', views.getInsureeBalance.as_view(), name="getInsureeBalance"),
    path('appconfig',views.appConfig.as_view())

]
