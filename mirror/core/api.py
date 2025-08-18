import os
import json
from .models import Sample, Image, Task, TestCase, Platform, UserProfile
from config.settings import REPORT_ROOT
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import get_chart_data, get_task_data, get_sample_data, update_sample_status, update_task_status, get_testcase_data

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
        -4 - no task id provided
        -5 - no task found by id
    """
    task_id = request.GET.get('tsk_id')
    log_full_path = request.GET.get('log')
    if not task_id:
        return HttpResponse(-4)

    try:
        task = Task.objects.get(pk=task_id)

        uploaded = request.FILES.get("file")
        if not uploaded and not log_full_path:
            return HttpResponse(-1)
        # if log file path has passed by the api request
        elif log_full_path:
            if task.log:
                task.log = f"{task.log}{log_full_path},"
            else:
                task.log = f"{log_full_path},"
            task.save()
            return HttpResponse(0)
        # if no log file path passed in the request
        else:
            if not SKIP_LOG_SIZE_CHECK and uploaded.size > MAX_FILE_SIZE:
                return HttpResponse(-2)     

            original_name = uploaded.name
            if not SKIP_LOG_EXTEN_CHECK and not is_allowed_filename(original_name):
                return HttpResponse(-3)

            # TODO need to add random string to make it save in case filename conflict
            safe_name = original_name
            report_saved_path = os.path.join(REPORT_ROOT, task_id)
            report_saved_path.mkdir(parents=True, exist_ok=True)
            full_path = os.path.join(report_saved_path, safe_name)      

            with open(full_path, 'wb') as f:
                for chunk in uploaded.chunks():
                    f.write(chunk)      
            if task.log:
                task.log = f"{task.log}{full_path},"
            else:
                task.log = f"{full_path},"
            task.save()

            return HttpResponse(0)

    except Exception as e:
        return HttpResponse(-5)


def charts_data(request, chart_type):
    """ 
    api for frontend request of chart data 
    Availble chart type:
        - sample_statistics
        - image
        - task_result_sum
        - task_st_this_week
    """
    return JsonResponse(get_chart_data(chart_type))


def search(request):
    """
    api for search,
    q: query item - [must]
    id: task/sample/testcase id - [optional]
    """
    res = None
    q = request.GET.get("q", None)
    if q is None:
        return JsonResponse({})

    item_id = request.GET.get("id", None)

    if q == 'tsk':
        res = get_task_data(item_id)
    elif q == 'spl':
        ssid = request.GET.get("ssid", None)
        st = request.GET.get("st", None)
        res = get_sample_data(item_id, ssid, st)
    elif q == 'tc':
        res = get_testcase_data(item_id)
    else:
        return JsonResponse({})

    if res is None:
        return JsonResponse({})
    return JsonResponse({'data': res})


def update_status(request):
    """
    api for update status
    params: tsk_id, spl_id, st
    return value:
         0: success
         1: fail
        -1: param error
    """
    stat = request.GET.get("st", None)
    tsk_id = request.GET.get("tsk_id", None)
    spl_id = request.GET.get("spl_id", None)

    if tsk_id and not spl_id:
        res = update_task_status(tsk_id, stat)
    elif spl_id and not tsk_id:
        res = update_sample_status(spl_id, stat)
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
        build_phase = request.POST.get('build')
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

            sample = Sample(ip=ip, service_tag=st, ssid=ssid, platform=plat, dpn=dpn, remark=remark, status='10', owner=owner, build_phase=build_phase)
            sample.save()
            res = 0
        except Exception as e:
            res = -2
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
            res = 0
        except Exception as e:
            res = -2
    else:
        res = -1

    return HttpResponse(res)


@csrf_exempt
def add_image(request):
    """
    api for add image
    """
    if request.method == "POST":
        img_name = request.POST.get('name')
        img_cat = request.POST.get('cat')
        img_ver = request.POST.get('img_ver')
        kern_ver = request.POST.get('kern_ver')
        rel_date = request.POST.get('date')
        path = request.POST.get('path')
        size = request.POST.get('size')
        checksum = request.POST.get('checksum')

        try:
            new_image = Image.objects.create(
                image_name=img_name,
                category=img_cat,
                image_version=img_ver,
                kernel_version=kern_ver,
                release_date=rel_date,
                file_path=path,
                file_size=size,
                sha256_hash=checksum,
                )
            new_image.save()
            res = 0
        except Exception as e:
            res = -2
    else:
        res = -1
    return HttpResponse(res)