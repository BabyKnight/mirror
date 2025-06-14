from django.forms.models import model_to_dict
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import Sample, Image, Task, TestCase
from datetime import datetime, timezone


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


    now = datetime.now(timezone.utc)

    # recent activity
    all_task = Task.objects.order_by('-time_trigger')[:5]
    activity_list = []

    for i in all_task:
        activity = {}
        activity['user'] = i.trigger_by.user.get_full_name()
        activity['detail'] = "Trigger " +   i.get_task_category_display() + " on " + i.sample.sku +"."

        total_sec = (now - i.time_trigger).total_seconds()
        if total_sec < 3600:
            activity['time'] = str(int(total_sec // 60)) + ' Minutes Ago'
        elif total_sec < 86400:
            activity['time'] = str(int(total_sec // 3600)) + ' Hours Ago'
        else:
            activity['time'] = str(int(total_sec // 86400)) + ' Days Ago'


        activity_list.append(activity)


    # search for Task
    all_task = Task.objects.all()
    task_list = []

    #now = datetime.now(timezone.utc)

    for i in all_task:
        tsk = model_to_dict(i)
        tsk['type'] = i.task_category[0]
        tsk['platform_name'] = i.sample.platform
        tsk['sku'] = i.sample.sku
        tsk['image_cat'] = i.image.category
        tsk['kernel_ver'] = i.image.kernel_version.split('-')[-1]
        tsk['trigger_by'] = i.trigger_by.user.get_full_name()
        tsk['st'] = i.status[0]
        total_sec = (now - i.time_trigger).total_seconds()
        if total_sec < 3600:
            tsk['trigger_at'] = str(int(total_sec // 60)) + ' Minutes Ago'
        elif total_sec < 86400:
            tsk['trigger_at'] = str(int(total_sec // 3600)) + ' Hours Ago'
        else:
            tsk['trigger_at'] = str(int(total_sec // 86400)) + ' Days Ago'

        task_list.append(tsk)


    # search for Samples
    samples = Sample.objects.all()
    sample_list = []

    for i in samples:
        sp = model_to_dict(i)
        if i.owner:
            sp['owner'] = i.owner.user.get_full_name()
        else:
            sp['owner'] = ""
        if i.current_user:
            sp['current_user'] = i.current_user.user.get_full_name()
        else:
            sp['current_user'] = ""
        sp['st'] = i.status.code[0]
        sample_list.append(sp)


    # search for Images
    images = Image.objects.all()
    img_list = []

    for i in images:
        img = model_to_dict(i)
        img['release_date'] = i.release_date.strftime("%Y-%m-%d")
        img['kernel_main_version'] = i.kernel_version.split("-")[0]
        img['kernel_build_version'] = i.kernel_version.split("-")[1]
        img_list.append(img)


    # search for Test cases
    tc = TestCase.objects.all()
    tc_list = []

    for i in tc:
        tc_list.append(model_to_dict(i))

    context = {
        "samples": samples,
        "platforms": platforms,
        "failed_cases": failed_cases,
        "tasks": tasks,
        "sample_list": sample_list,
        "image_list": img_list,
        "testcase_list": tc_list,
        "task_list": task_list,
        "activity_list": activity_list
        }
    return render(request, 'index.html', context)
