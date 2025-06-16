from django.forms.models import model_to_dict
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from .models import Sample, Image, Task, TestCase
from datetime import datetime, timezone, timedelta
from django.db.models import Count
from django.db.models.functions import TruncMonth


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

    # image chart
    image_chart_data = get_chart_data('image')



    context = {
        "image_chart_data": image_chart_data,
    }
    return render(request, 'index.html', context)




def index_backup(request):

    # time defined for filter
    now = datetime.now(timezone.utc)
    first_day_of_month = now.replace(day=1)
    start_of_week = now - timedelta(days=now.weekday())
    six_month_ago = now - timedelta(days=180)


    sample_added_this_month = Sample.objects.filter(time_created__gte=first_day_of_month)
    sample_count_this_month = sample_added_this_month.count()


    tsk_this_week = Task.objects.filter(time_trigger__gte=start_of_week)
    tsk_count_this_week = tsk_this_week.count()

    
    # Images released count statistics in last 6 month
    img_cat_info = Image.objects.filter(release_date__gte=six_month_ago).annotate(
        month=TruncMonth('release_date')).values('month', 'category').annotate(count=Count('id')).order_by('month', 'category')
    for i in img_cat_info:
        i['month'] = i['month'].strftime('%b')

    # Tasks result count statistics in last 6 month
    tsk_res_info = Task.objects.filter(time_trigger__gte=six_month_ago).annotate(
        month=TruncMonth('time_trigger')).values('month', 'result').annotate(count=Count('id')).order_by('month', 'result')
    for i in tsk_res_info:
        i['month'] = i['month'].strftime('%b')




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
        - task
        - sample
    """
    return JsonResponse(get_chart_data(chart_type))


def get_chart_data(chart_type):
    """ 
    method to get chart data by chart type
    Availble chart type:
        - platform
        - image
        - task
        - sample
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
                dataset[i][past_6_month.index(info_by_month['month'])] = info_by_month['count']
     
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