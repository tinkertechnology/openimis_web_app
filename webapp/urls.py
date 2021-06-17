
from django.core.exceptions import PermissionDenied
from django.urls import path

from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

from django.contrib.auth.models import User
from .models import InsureeAuth
import json
def entry_insuree(function):
    def wrap(request, *args, **kwargs):
        print(request.POST)
        payload = json.loads(request.body.decode('utf-8'))
        print(payload)
        #-H 'Insuree-Token: F008CA1' \
        token=request.META.get('HTTP_INSUREE_TOKEN')
        print(token)
        if token:
            insuree=InsureeAuth.objects.filter(token=token).first()
            if insuree:
                return function(request, *args, **kwargs)
        raise PermissionDenied("No insuree token")
    
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


urlpatterns = [
    #"/api/webapp/graphql"
    path("graphql/", entry_insuree(csrf_exempt(GraphQLView.as_view(graphiql=True)))),
]



