from django.shortcuts import render

# Create your views here.
def temp_insuree_reg(request):
    return render(request, 'temp_insuree_reg.html', {})
