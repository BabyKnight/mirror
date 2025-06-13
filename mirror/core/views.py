from django.forms.models import model_to_dict
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import Sample, Image, Task


def ping(request):
    x_forward_for = request.META.get('HTTP_X_FORWARD_FOR')
    if x_forward_for:
        client_ip = x_forward_for.split(',')[0].strip()
    else:
        client_ip = request.META.get('REMOTE_ADDR')
    return HttpResponse("Hello "+ client_ip)


def dummy_view(request, *args, **kwargs):
    return JsonResponse({'detail': 'Not implimented yet'}, status=501)


def dashboard(request):
    context = {}
    samples = {
        "total": 60,
        "changes": -0.12
        }
    platforms = {
        "total": 30,
        "changes": 2
        }
    failed_cases = {
        "total": 20,
        "changes": -0.18
        }
    tasks = {
        "total": 25,
        "changes": 0
        }

    # search for Task
    # search for Samples
    samples = Sample.objects.all()
    sample_list = []

    for i in samples:
        sample_info = model_to_dict(i)
        sample_list.append(sample_info)

    # search for Images

    context = {
        "samples": samples,
        "platforms": platforms,
        "failed_cases": failed_cases,
        "tasks": tasks,
        "sample_list": sample_list
        }
    return render(request, 'index.html', context)
