from django.shortcuts import render

# Create your views here.
from django.views.decorators.clickjacking import xframe_options_exempt

@xframe_options_exempt
def temp_insuree_reg(request):
    response = render(request, 'temp_insuree_reg.html', {})
    #response['X-Frame-Options'] = 'no-cache'
    return response
    #return render(request, 'temp_insuree_reg.html', {})

def temp_insuree_reg_html(request):
    return render(request, 'temp_insuree_reg.html', {})


from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import connection

def get_policy_inquiry(chfid):
    with connection.cursor() as cur:
        sql = f""" EXEC[dbo].[uspPolicyInquiryApp] @CHFID="{chfid}";"""
        cur.execute(sql)

        next = True
        res = []

        while next:
            try:
                res = cur.fetchall()
                return res
                print('res',res)
            except:
                pass
            finally:
                next = cur.nextset()
        return None

import json

import decimal
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)

class getInsureeBalance(APIView):
    authentication_classes = [] #disables authentication
    permission_classes = [] #disables permission
    
    def get(self, request, *args, **kwargs):
        insuree_balance = get_policy_inquiry(request.GET.get('chfid'))
        print(insuree_balance)
        # policy_length = len(insuree_balance) - 1
        json1 = {
                "name" : "",
               "chfid" : "",
                "date_of_birth" : "",
                "gender" : "",
                "balance" : 0.0,
                "first_service_hospital" : "",
                "expiry_date" : "",
                "status" : ""
            }

        if insuree_balance:
            json1 = {
                "name" : insuree_balance[0][2],
                "chfid" : insuree_balance[0][0],
                "date_of_birth" : insuree_balance[0][3],
                "gender" : insuree_balance[0][4],
                "balance" : insuree_balance[0][12],
                "first_service_hospital" : insuree_balance[0][6],
                "expiry_date" : insuree_balance[0][7],
                "status" : insuree_balance[0][8]
            }
        for x in insuree_balance:
            pass
        return Response(        
            #json.dumps(insuree_balance, cls=DecimalEncoder)
            json1
            )

"""

[
        "047775276",
        "Updated\\",
        "BIRENDRA SAUD",
        "07/04/2002 (20 Yrs)",
        "Male",
        "HIB-3500",
        "प्रथम सेवा बिन्दु: Seti Zonal Hospital",
        "16/11/2021",
        "निष्कृय",
        1.0,
        null,
        null,
        174990.32,
        174990.32
    ],
"""
from  .models    import AppSettings 
class appConfig(APIView):
    authentication_classes = [] #disables authentication
    permission_classes = [] #disables permission
    def get(self, request):
        config = AppSettings.objects.all().first()
        if config:
            return Response({"app_url" : config.site_url, "app_version": config.app_version}, 200)
        return Response({})
