from django.shortcuts import render
from django.http import HttpResponse

def ping(request):
    x_forward_for = request.META.get('HTTP_X_FORWARD_FOR')
    if x_forward_for:
        client_ip = x_forward_for.split(',')[0].strip()
    else:
        client_ip = request.META.get('REMOTE_ADDR')
    return HttpResponse("Hello"+ client_ip)

