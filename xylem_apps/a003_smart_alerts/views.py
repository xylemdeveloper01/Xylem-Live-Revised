from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def home(request):
    context = {
        'segment'  : 'index',
        #'products' : Product.objects.all()
    }
    return render(request,"a003/home.html")