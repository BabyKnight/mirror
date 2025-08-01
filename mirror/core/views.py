from django.forms.models import model_to_dict
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from .models import Sample, Image, Task, TestCase
from datetime import datetime, timezone, timedelta
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth, TruncDate
from django.views.decorators.csrf import csrf_exempt
import os


def ping(request):
    x_forward_for = request.META.get('HTTP_X_FORWARD_FOR')
    if x_forward_for:
        client_ip = x_forward_for.split(',')[0].strip()
    else:
        client_ip = request.META.get('REMOTE_ADDR')
    return HttpResponse("Hello "+ client_ip)


def dummy_view(request, *args, **kwargs):
    return JsonResponse({'detail': 'Not implimented yet'}, status=501)


def index(request):

    now = datetime.now(timezone.utc)

    # total samples by month
    start_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_last_month = (start_of_this_month - timedelta(days=1)).replace(day=1)

    total_sample_this_month = Sample.objects.filter(
                time_created__gte=start_of_this_month,
                time_created__lt=now
            ).count()

    total_sample_last_month = Sample.objects.filter(
                time_created__gte=start_of_last_month,
                time_created__lt=start_of_this_month
            ).count()
    total_sample_delta = total_sample_this_month - total_sample_last_month
    sample_trend = {
                'title': 'Total Sample (this month)',
                'data': total_sample_this_month,
                'delta': total_sample_delta,
            }

    # total image by week
    start_of_week = now - timedelta(days=now.weekday())
    start_of_this_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    start_of_last_week = start_of_this_week - timedelta(days=7)
    end_of_last_week = start_of_this_week - timedelta(seconds=1)

    total_image_this_week = Image.objects.filter(
                release_date__gte=start_of_this_week,
                release_date__lt=now
            ).count()

    total_image_last_week = Image.objects.filter(
                release_date__gte=start_of_last_week,
                release_date__lt=end_of_last_week
            ).count()
    total_image_delta = total_image_this_week - total_image_last_week
    image_trend = {
                'title': 'Image Release (this Week)',
                'data': total_image_this_week,
                'delta': total_image_delta
            }

    # total tasks by month
    total_task_this_month = Task.objects.filter(
                time_trigger__gte=start_of_this_month,
                time_trigger__lt=now
            ).count()

    total_task_last_month = Task.objects.filter(
                time_trigger__gte=start_of_last_month,
                time_trigger__lt=start_of_this_month
            ).count()
    total_task_delta = total_task_this_month - total_task_last_month
    task_trend = {
                'title': 'Total Task (this month)',
                'data': total_task_this_month,
                'delta': total_task_delta
            }

    # task failure rate by week
    total_failed_task_this_month = Task.objects.filter(
                result=False,
                time_trigger__gte=start_of_this_month,
                time_trigger__lt=now
            ).count()

    total_failed_task_last_month = Task.objects.filter(
                result=False,
                time_trigger__gte=start_of_last_month,
                time_trigger__lt=start_of_this_month
            ).count()
    if total_task_last_month == 0:
        failure_rate_last_month = 0
    else:
        failure_rate_last_month = total_failed_task_last_month / total_task_last_month

    if total_task_this_month == 0:
        failure_rate_this_month = 0
    else:
        failure_rate_this_month = total_failed_task_this_month / total_task_this_month
    failure_rate_delta = round((failure_rate_this_month - failure_rate_last_month), 2)
    fr_trend = {
                'title':'Task Failure Rate (this month)',
                'data': round(failure_rate_this_month, 2),
                'delta': failure_rate_delta
            }

    # image chart
    image_chart_data = get_chart_data('image')
    task_sum_chart_data = get_chart_data('task_result_sum')
    task_st_chart_data = get_chart_data('task_st_this_week')

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

    context = {
        "trends": [sample_trend, image_trend, task_trend, fr_trend],
        "image_chart_data": image_chart_data,
        "task_sum_chart_data": task_sum_chart_data,
        "task_st_chart_data": task_st_chart_data,
        "activity_list": activity_list,
        "task_list": task_list,
    }
    return render(request, 'index.html', context)


def dashboard(request):
    now = datetime.now(timezone.utc)

    # total samples by month
    start_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_last_month = (start_of_this_month - timedelta(days=1)).replace(day=1)

    total_sample_this_month = Sample.objects.filter(
                time_created__gte=start_of_this_month,
                time_created__lt=now
            ).count()

    total_sample_last_month = Sample.objects.filter(
                time_created__gte=start_of_last_month,
                time_created__lt=start_of_this_month
            ).count()
    total_sample_delta = total_sample_this_month - total_sample_last_month
    sample_trend = {
                'title': 'Total Sample (this month)',
                'data': total_sample_this_month,
                'delta': total_sample_delta,
            }

    # total image by week
    start_of_week = now - timedelta(days=now.weekday())
    start_of_this_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    start_of_last_week = start_of_this_week - timedelta(days=7)
    end_of_last_week = start_of_this_week - timedelta(seconds=1)

    total_image_this_week = Image.objects.filter(
                release_date__gte=start_of_this_week,
                release_date__lt=now
            ).count()

    total_image_last_week = Image.objects.filter(
                release_date__gte=start_of_last_week,
                release_date__lt=end_of_last_week
            ).count()
    total_image_delta = total_image_this_week - total_image_last_week
    image_trend = {
                'title': 'Image Release (this Week)',
                'data': total_image_this_week,
                'delta': total_image_delta
            }

    # total tasks by month
    total_task_this_month = Task.objects.filter(
                time_trigger__gte=start_of_this_month,
                time_trigger__lt=now
            ).count()

    total_task_last_month = Task.objects.filter(
                time_trigger__gte=start_of_last_month,
                time_trigger__lt=start_of_this_month
            ).count()
    total_task_delta = total_task_this_month - total_task_last_month
    task_trend = {
                'title': 'Total Task (this month)',
                'data': total_task_this_month,
                'delta': total_task_delta
            }

    # task failure rate by week
    total_failed_task_this_month = Task.objects.filter(
                result=False,
                time_trigger__gte=start_of_this_month,
                time_trigger__lt=now
            ).count()

    total_failed_task_last_month = Task.objects.filter(
                result=False,
                time_trigger__gte=start_of_last_month,
                time_trigger__lt=start_of_this_month
            ).count()
    failure_rate_last_month = total_failed_task_last_month / total_task_last_month
    failure_rate_this_month = total_failed_task_this_month / total_task_this_month
    failure_rate_delta = round((failure_rate_this_month - failure_rate_last_month), 2)
    fr_trend = {
                'title':'Task Failure Rate (this month)',
                'data': round(failure_rate_this_month, 2),
                'delta': failure_rate_delta
            }

    # image chart
    image_chart_data = get_chart_data('image')
    task_sum_chart_data = get_chart_data('task_result_sum')
    task_st_chart_data = get_chart_data('task_st_this_week')

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

    context = {
        "trends": [sample_trend, image_trend, task_trend, fr_trend],
        "image_chart_data": image_chart_data,
        "task_sum_chart_data": task_sum_chart_data,
        "task_st_chart_data": task_st_chart_data,
        "activity_list": activity_list,
        "task_list": task_list,
    }
    return render(request, 'dashboard.html', context)


def sample(request):
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

    context = {
        "sample_list": sample_list
        }

    return render(request, 'sample.html', context)


def image(request):
    # search for Images
    images = Image.objects.all()
    img_list = []

    for i in images:
        img = model_to_dict(i)
        img['release_date'] = i.release_date.strftime("%Y-%m-%d")
        img['kernel_main_version'] = i.kernel_version.split("-")[0]
        img['kernel_build_version'] = i.kernel_version.split("-")[1]
        img_list.append(img)

        context = {
        "image_list": img_list
        }

    return render(request, 'image.html', context)


def task(request):
    all_task = Task.objects.all()
    task_list = []

    now = datetime.now(timezone.utc)

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

    context = {
        "task_list": task_list
        }

    return render(request, 'task.html', context)


def testcase(request):
    tc = TestCase.objects.all()
    tc_list = []

    for i in tc:
        tc_list.append(model_to_dict(i))

    context = {
        "testcase_list": tc_list,
        }

    return render(request, 'test_case.html', context)


def platform(request):
    template_name = f"platform.html"
    html = render_to_string(template_name)
    return HttpResponse(html)


def chart(request, chart_type):
    """ 
    api for frontend request of chart data 
    Availble chart type:
        - platform
        - image
        - task_result_sum
        - task_st_this_week
    """
    return JsonResponse(get_chart_data(chart_type))


def get_chart_data(chart_type):
    """ 
    method to get chart data by chart type
    Availble chart type:
        - platform
        - image
        - task_result_sum
        - task_st_this_week
    """

    # time defined for filter
    now = datetime.now(timezone.utc)
    first_day_of_month = now.replace(day=1)
    start_of_week = now - timedelta(days=now.weekday())
    six_month_ago = now - timedelta(days=180)

    label = []

    if chart_type == 'image':

        # label for the bar chart (past 6 month)
        past_6_month = []
        label_m = []
        for i in range(6):
            month_date = now - timedelta(days=(30 * i))
            label_m.append(month_date.strftime('%b'))
        past_6_month = label_m[::-1]
        label = past_6_month

        # category list
        cat_list = []
        for i in Image.CATEGORY_CHOICES:
            cat_list.append(i[0])

        # Images released count statistics in last 6 month
        img_cat_info = Image.objects.filter(release_date__gte=six_month_ago).annotate(
            month=TruncMonth('release_date')).values('month', 'category').annotate(count=Count('id')).order_by('month', 'category')
        for i in img_cat_info:
            i['month'] = i['month'].strftime('%b')

        dataset = {}
        for i in cat_list:
            dataset[i] = [0] * 6
        for info_by_month in img_cat_info:
            dataset[info_by_month['category']][past_6_month.index(info_by_month['month'])] = info_by_month['count']
     
    elif chart_type == 'task_result_sum':

        # label for the bar chart (past 6 month)
        past_6_month = []
        label_m = []
        for i in range(6):
            month_date = now - timedelta(days=(30 * i))
            label_m.append(month_date.strftime('%b'))
        past_6_month = label_m[::-1]
        label = past_6_month

        task_types = []
        for i in Task.TASK_CHOICES:
            task_types.append(i[0])

        task_sum = Task.objects.filter(time_trigger__gte=six_month_ago).annotate(
            month=TruncMonth('time_trigger')).values('month', 'task_category').annotate(
                result_pass=Count('id', filter=Q(result=True)), result_fail=Count('id', filter=Q(result=False))).order_by('month', 'task_category')
        for i in task_sum:
            i['month'] = i['month'].strftime('%b')

        dataset = {}
        for i in task_types:
            dataset[i] = {
                'pass': [0] * 6,
                'fail': [0] * 6,
            }
        for i in task_sum:
            dataset[i['task_category']]['pass'][past_6_month.index(i['month'])] += i['result_pass']
            dataset[i['task_category']]['fail'][past_6_month.index(i['month'])] += i['result_fail']

        # count task_cat 'full' in 'install' and 'test' and remove task_cat 'full' (install and test)
        for key in dataset['f']:
            dataset['i'][key] = [data_i + data_f for data_i, data_f in zip(dataset['i'][key], dataset['f'][key])]
            dataset['t'][key] = [data_i + data_f for data_i, data_f in zip(dataset['t'][key], dataset['f'][key])]

    elif chart_type == 'task_st_this_week':

        # label for the chart (weekday)
        day_of_week = []
        for i in range(7):
            day = now - timedelta(days=i)
            day_of_week.append(day.strftime('%a'))
        label = day_of_week[::-1]

        dataset = [0] * 7

        task_per_day = Task.objects.filter(time_trigger__gte=start_of_week).annotate(
            day=TruncDate('time_trigger')).values('day').annotate(count=Count('id')).order_by('day')
        for i in task_per_day:
            dataset[label.index(i['day'].strftime('%a'))] = i['count']


    elif chart_type == 'platform':
        pass


    else:
        sample_added_this_month = Sample.objects.filter(time_created__gte=first_day_of_month)
        sample_count_this_month = sample_added_this_month.count()


        tsk_this_week = Task.objects.filter(time_trigger__gte=start_of_week)
        tsk_count_this_week = tsk_this_week.count()

    context = {
        "label": label,
        'dataset': dataset,
    }

    return context


def is_allowed_filename(filename):
    ALLOWED_EXTENSIONS = {'gz', 'tgz', 'zip', '7z'}
    ext = filename.rsplit('.', 1)[-1].lower()
    return ext in ALLOWED_EXTENSIONS


@csrf_exempt
def log_upload(request):

    #TODO to define somewhere else 
    MAX_FILE_SIZE = 300 * 1024 * 1024


    uploaded = request.FILES.get("file")
    if not uploaded:
        print('not file uploaded')
        return JsonResponse({'detail': 'Not file uploaded'}, status=400)

    if uploaded.size > MAX_FILE_SIZE:
        return JsonResponse({'detail': 'File too large'}, status=413)

    original_name = uploaded.name
    if not is_allowed_filename(original_name):
        return JsonResponse({'detail': 'File type not allowed'}, status=400)

    #TODO need to add random string to make it save in case filename conflict
    safe_name = original_name
    save_path = os.path.join('/tmp', safe_name)

    with open(save_path, 'wb') as f:
        for chunk in uploaded.chunks():
            f.write(chunk)

    return JsonResponse({'detail': 'File uploaded'}, status=200)