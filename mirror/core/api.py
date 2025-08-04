import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import get_chart_data

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
    return JsonResponse({'detail': 'Hello'}, status=200)


@csrf_exempt
def log_upload(request):
    """
    api for upload log from tested client to server
    """
    uploaded = request.FILES.get("file")
    if not uploaded:
        print('not file uploaded')
        return JsonResponse({'detail': 'Not file uploaded'}, status=400)

    if not SKIP_LOG_SIZE_CHECK and uploaded.size > MAX_FILE_SIZE:
        return JsonResponse({'detail': 'File too large'}, status=413)

    original_name = uploaded.name
    if not SKIP_LOG_EXTEN_CHECK and not is_allowed_filename(original_name):
        return JsonResponse({'detail': 'File type not allowed'}, status=400)

    # TODO need to add random string to make it save in case filename conflict
    safe_name = original_name
    save_path = os.path.join('/tmp', safe_name)

    with open(save_path, 'wb') as f:
        for chunk in uploaded.chunks():
            f.write(chunk)

    return JsonResponse({'detail': 'File uploaded'}, status=200)


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