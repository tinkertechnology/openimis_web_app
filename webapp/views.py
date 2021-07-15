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
