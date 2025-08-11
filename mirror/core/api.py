import os
import json
from .models import Sample, Image, Task, TestCase, Platform, UserProfile
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import get_chart_data, get_task_data, get_sample_data, update_sample_status, update_task_status

SKIP_LOG_EXTEN_CHECK = True
SKIP_LOG_SIZE_CHECK = True
MAX_FILE_SIZE = 300 * 1024 * 1024

def is_allowed_filename(filename):
    ALLOWED_EXTENSIONS = {'gz', 'tgz', 'zip', '7z', 'log'}
    ext = filename.rsplit('.', 1)[-1].lower()
    return ext in ALLOWED_EXTENSIONS


def ping(request):
    x_forward_for = request.META.get('HTTP_X_FORWARD_FOR')
    if x_forward_for:
        client_ip = x_forward_for.split(',')[0].strip()
    else:
        client_ip = request.META.get('REMOTE_ADDR')
    return HttpResponse('OK', status=200)


@csrf_exempt
def log_upload(request):
    """
    api for upload log from tested client to server
    retuen code:
         0 - file upload success
        -1 - no file upload
        -2 - file too large
        -3 - file type is not alowed
    """
    uploaded = request.FILES.get("file")
    if not uploaded:
        return HttpResponse(-1, status=400)

    if not SKIP_LOG_SIZE_CHECK and uploaded.size > MAX_FILE_SIZE:
        return HttpResponse(-2, status=413)

    original_name = uploaded.name
    if not SKIP_LOG_EXTEN_CHECK and not is_allowed_filename(original_name):
        return HttpResponse(-3, status=400)

    # TODO need to add random string to make it save in case filename conflict
    safe_name = original_name
    save_path = os.path.join('/tmp', safe_name)

    with open(save_path, 'wb') as f:
        for chunk in uploaded.chunks():
            f.write(chunk)

    return HttpResponse(0, status=200)


def charts_data(request, chart_type):
    """ 
    api for frontend request of chart data 
    Availble chart type:
        - platform
        - image
        - task_result_sum
        - task_st_this_week
    """
    return JsonResponse(get_chart_data(chart_type))


def search(request):
    """
    api for search,
    q: query item - [must]
    c, ssid, st, id: criteria - [optional]
    """
    q = request.GET.get("q", None)
    if q is None:
        return JsonResponse({})
    if q == 'tsk':
        c = request.GET.get("c", None)
        res = get_task_data(c)
    elif q == 'spl':
        sample_id = request.GET.get("id", None)
        ssid = request.GET.get("ssid", None)
        st = request.GET.get("st", None)
        res = get_sample_data(sample_id, ssid, st)
    else:
        return JsonResponse({})

    return JsonResponse({'data': res})


def update_status(request, item=None):
    """
    api for update status
    Valid item: spl(sample), tsk(task)
    return value:
         0: success
         1: fail
        -1: param error
    """
    stat = request.GET.get("stat", None)
    if stat is None:
        return HttpResponse(-1, status=200)

    if item == 'tsk':
        tsk_id = request.GET.get("id", None)
        res = update_task_status(tsk_id, stat)
    elif item == 'spl':
        ssid = request.GET.get("ssid", None)
        st = request.GET.get("st", None)
        res = update_sample_status(ssid, st, stat)
    else:
        res = -1
    return HttpResponse(res)


def add_sample(request):
    """
    api for add sample
    """
    if request.method == 'POST':
        plat_id = request.POST.get('platform')
        owner_id = request.POST.get('owner')
        dpn = request.POST.get('dpn')
        st = request.POST.get('st')
        ssid = request.POST.get('ssid')
        ip = request.POST.get('ip')
        if ip is None:
            x_forward_for = request.META.get('HTTP_X_FORWARD_FOR')
            if x_forward_for:
                client_ip = x_forward_for.split(',')[0].strip()
            else:
                client_ip = request.META.get('REMOTE_ADDR')
        remark = request.POST.get('remark')

        try:
            plat = Platform.objects.get(pk=plat_id)
            owner = UserProfile.objects.get(user__id=owner_id)

            sample = Sample(ip=ip, service_tag=st, ssid=ssid, platform=plat, dpn=dpn, remark=remark, status='10', owner=owner)
            sample.save()
            res = 0
        except Exception as e:
            raise -2
    else:
        res = -1
    
    return HttpResponse(res)


def add_task(request):
    """
    api for add task
    """
    if request.method == 'POST':
        sample_id = request.POST.get('sample')
        user_id = request.POST.get('contact')
        image_id = request.POST.get('image')
        task_category = request.POST.get('taskCategory')
        tc_list = request.POST.get('testcases')

        try:
            trigger_by = UserProfile.objects.get(user__id=user_id)
            sample = Sample.objects.get(pk=sample_id)

            if task_category == 'i' or task_category == 'f':
                image = Image.objects.get(pk=image_id)
            else:
                image = None

            new_task = Task.objects.create(sample=sample, trigger_by=trigger_by, image=image, task_category=task_category)

            if task_category == 't' or task_category == 'f':
                new_task.testcases.set(tc_list)

            new_task.save()
            res = 1
        except Exception as e:
            raise -2
    else:
        res = -1

    return HttpResponse(res)